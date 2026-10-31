#!/usr/bin/env python3
"""Tests for PI-4 drift_detector.py (ADR-0012). Synthetic, non-destructive.

Run: python3 pi4-drift-detector-tests.py
"""
import calendar
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("drift_detector", HERE / "drift_detector.py")
dd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dd)

NOW = calendar.timegm(time.gmtime())  # real clock; CLI tests run against it


def _declared(**over):
    state = {
        "replicas": 1,
        "image_tag": "0.1.0",
        "resources": {"limits": {"memory": "64Mi", "cpu": "200m"}},
        "security_context": {"run_as_non_root": True,
                             "read_only_root_filesystem": True},
    }
    state.update(over.pop("state", {}))
    rec = {"schema_version": "1.0.0", "record_type": "declared_state",
           "collected_at_utc": "2026-10-30T12:00:00Z", "state": state}
    rec.update(over)
    return rec


def _observed(state=None, age_s=60, **over):
    base_state = {
        "replicas": 1,
        "image_tag": "0.1.0",
        "resources": {"limits": {"memory": "64Mi", "cpu": "200m"}},
        "security_context": {"run_as_non_root": True,
                             "read_only_root_filesystem": True},
    }
    if state is not None:
        base_state.update(state)
    ts = dd.time.strftime("%Y-%m-%dT%H:%M:%SZ", dd.time.gmtime(NOW - age_s))
    rec = {"schema_version": "1.0.0", "record_type": "observed_state",
           "collected_at_utc": ts, "state": base_state}
    rec.update(over)
    return rec


class TestConverged(unittest.TestCase):
    def test_01_identical_state_converged(self):
        v = dd.compare(_declared(), _observed(), now_s=NOW)
        self.assertEqual(v["verdict"], "CONVERGED")
        self.assertEqual(v["drifted_fields"], [])
        self.assertEqual(v["llm_inference_required"], 0)

    def test_02_runtime_variation_ignored(self):
        """Restarts/status changes are NOT drift — readiness (PI-3) domain."""
        v = dd.compare(_declared(), _observed(state={"restarts": "999"}), now_s=NOW)
        self.assertEqual(v["verdict"], "CONVERGED")


class TestDrift(unittest.TestCase):
    def test_10_image_tag_drift(self):
        v = dd.compare(_declared(), _observed(state={"image_tag": "0.2.0"}), now_s=NOW)
        self.assertEqual(v["verdict"], "DRIFT")
        self.assertIn("deployment.image_tag", v["drifted_fields"])

    def test_11_replica_drift(self):
        v = dd.compare(_declared(), _observed(state={"replicas": 3}), now_s=NOW)
        self.assertEqual(v["verdict"], "DRIFT")

    def test_12_security_context_drift(self):
        v = dd.compare(_declared(), _observed(
            state={"security_context": {"run_as_non_root": False,
                                        "read_only_root_filesystem": True}}),
            now_s=NOW)
        self.assertEqual(v["verdict"], "DRIFT")
        self.assertIn("deployment.run_as_non_root", v["drifted_fields"])

    def test_13_resource_drift(self):
        v = dd.compare(_declared(), _observed(
            state={"resources": {"limits": {"memory": "128Mi", "cpu": "200m"}}}),
            now_s=NOW)
        self.assertEqual(v["verdict"], "DRIFT")
        self.assertIn("deployment.memory_limit", v["drifted_fields"])

    def test_14_compared_fields_have_provenance(self):
        v = dd.compare(_declared(), _observed(), now_s=NOW)
        self.assertGreaterEqual(len(v["compared_fields"]), 6)
        for f in v["compared_fields"]:
            self.assertIn("comparison", f)
            self.assertIn("declared", f)
            self.assertIn("observed", f)


class TestFailClosed(unittest.TestCase):
    def test_20_stale_observed_is_not_pass(self):
        v = dd.compare(_declared(), _observed(age_s=3600), now_s=NOW)
        self.assertEqual(v["verdict"], "STALE_EVIDENCE")

    def test_21_missing_observed_file(self):
        v, _ = dd._load_json("/nonexistent/x.json"), None
        # CLI path
        import argparse
        out = dd.main(["--baseline", "/nonexistent/b.json",
                       "--observed", "/nonexistent/o.json"])
        # main returns 0 and emits INSUFFICIENT_DATA verdict JSON to stdout

    def test_22_missing_field_in_one_record_is_insufficient(self):
        b = _declared()
        del b["state"]["image_tag"]
        v = dd.compare(b, _observed(), now_s=NOW)
        self.assertEqual(v["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("deployment.image_tag", v["incomparable_fields"])

    def test_23_malformed_json_is_insufficient(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not json")
            p = f.name
        rec, err = dd._load_json(p)
        self.assertIsNone(rec)
        self.assertIn("malformed", err)

    def test_24_missing_required_keys_is_insufficient(self):
        v = dd.compare({"schema_version": "1.0.0"}, _observed(), now_s=NOW)
        self.assertEqual(v["verdict"], "INSUFFICIENT_DATA")

    def test_25_schema_mismatch_detected(self):
        v = dd.compare(_declared(schema_version="0.9.0"), _observed(), now_s=NOW)
        self.assertEqual(v["verdict"], "SCHEMA_MISMATCH")

    def test_26_unparseable_timestamp_is_insufficient(self):
        o = _observed()
        o["collected_at_utc"] = "not-a-timestamp"
        v = dd.compare(_declared(), o, now_s=NOW)
        self.assertEqual(v["verdict"], "INSUFFICIENT_DATA")

    def test_27_record_type_mismatch_is_insufficient(self):
        v = dd.compare(_declared(record_type="observed_state"), _observed(), now_s=NOW)
        self.assertEqual(v["verdict"], "INSUFFICIENT_DATA")

    def test_28_never_returns_clean_verdict_on_error(self):
        """Any error path must NOT produce CONVERGED/DRIFT with empty errors."""
        cases = [
            ({"schema_version": "1.0.0"}, _observed()),
            (_declared(schema_version="9.9.9"), _observed()),
            (_declared(), _observed(age_s=99999)),
        ]
        for b, o in cases:
            v = dd.compare(b, o, now_s=NOW)
            self.assertNotEqual(v["verdict"], "CONVERGED")
            self.assertTrue(v["errors"])


class TestContract(unittest.TestCase):
    def test_30_read_only_flag(self):
        v = dd.compare(_declared(), _observed(), now_s=NOW)
        self.assertTrue(v["read_only"])

    def test_31_runtime_fields_listed_as_excluded(self):
        v = dd.compare(_declared(), _observed(), now_s=NOW)
        self.assertIn("restarts", v["runtime_variation_excluded"])
        self.assertIn("status", v["runtime_variation_excluded"])


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="pi4-cli-"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_40_cli_roundtrip(self):
        b = self.tmp / "b.json"
        o = self.tmp / "o.json"
        b.write_text(json.dumps(_declared()))
        o.write_text(json.dumps(_observed()))
        out = self.tmp / "v.json"
        rc = dd.main(["--baseline", str(b), "--observed", str(o), "-o", str(out)])
        self.assertEqual(rc, 0)
        v = json.loads(out.read_text())
        self.assertEqual(v["verdict"], "CONVERGED")

    def test_41_cli_drift_verdict_written(self):
        b = self.tmp / "b.json"
        o = self.tmp / "o.json"
        b.write_text(json.dumps(_declared()))
        o.write_text(json.dumps(_observed(state={"replicas": 5})))
        out = self.tmp / "v.json"
        rc = dd.main(["--baseline", str(b), "--observed", str(o), "-o", str(out)])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.read_text())["verdict"], "DRIFT")

    def test_42_cli_missing_files_exit_zero_with_insufficient(self):
        """Detector evaluates even unreadable inputs — verdict is data."""
        out = self.tmp / "v.json"
        rc = dd.main(["--baseline", "/nope.json", "--observed", "/nope2.json",
                      "-o", str(out)])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.read_text())["verdict"], "INSUFFICIENT_DATA")


if __name__ == "__main__":
    unittest.main(verbosity=2)
