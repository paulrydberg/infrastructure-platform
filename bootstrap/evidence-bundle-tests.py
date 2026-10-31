#!/usr/bin/env python3
"""Tests for PI-5 evidence_bundle_builder.py (ADR-0012).

Run: python3 evidence-bundle-tests.py
Covers: normal build, incomplete-data, malformed-input, tamper-evidence,
fail-closed semantics, zero-inference contract.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "evidence_bundle_builder", HERE / "evidence_bundle_builder.py")
ebb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ebb)


class TestProbeSemantics(unittest.TestCase):
    def test_01_probe_success_is_ok(self):
        rec = ebb._probe("t", ["echo", "hi"])
        self.assertEqual(rec["status"], "ok")
        self.assertEqual(rec["exit_code"], 0)
        self.assertTrue(rec["collected_at_utc"])

    def test_02_probe_failure_is_recorded_not_silent(self):
        rec = ebb._probe("t", ["false"])
        self.assertEqual(rec["status"], "probe_failed")
        self.assertNotEqual(rec["exit_code"], 0)

    def test_03_probe_missing_binary_is_explicit_error_state(self):
        rec = ebb._probe("t", ["/nonexistent/binary-xyz"])
        self.assertEqual(rec["status"], "probe_failed")
        self.assertTrue(rec["stderr"] or rec["exit_code"] != 0)

    def test_04_probe_record_has_command_provenance(self):
        rec = ebb._probe("t", ["echo", "hi"])
        self.assertEqual(rec["command"], ["echo", "hi"])
        self.assertIn("probe", rec)


class TestBuildBundle(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ebb-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_10_build_produces_manifest_and_files(self):
        mdir = self.tmp / "bundle"
        m, errs = ebb.build_bundle(mdir, "test-label")
        self.assertEqual(errs, [])
        self.assertEqual(m["label"], "test-label")
        self.assertTrue((mdir / "manifest.json").is_file())
        self.assertGreaterEqual(len(m["files"]), 5)
        for f in m["files"]:
            self.assertIn(f["status"], ("ok", "probe_failed", "malformed_output",
                                        "skipped_no_inputs"))
            self.assertEqual(len(f["sha256"]), 64)

    def test_10b_drift_probe_explicit_skip_without_inputs(self):
        """Without PI4_BASELINE/PI4_OBSERVED the drift probe records an
        explicit skip — never silent absence from the bundle."""
        mdir = self.tmp / "bundle-skip"
        m, errs = ebb.build_bundle(mdir, "skip-test")
        self.assertEqual(errs, [])
        drift = [f for f in m["files"] if f["probe"] == "pi4_drift_verdict"]
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0]["status"], "skipped_no_inputs")

    def test_10c_drift_probe_embeds_verdict_with_inputs(self):
        """With both PI4 env inputs set, the drift verdict is embedded."""
        b = self.tmp / "b.json"
        o = self.tmp / "o.json"
        b.write_text(json.dumps({
            "schema_version": "1.0.0", "record_type": "declared_state",
            "collected_at_utc": "2026-10-30T12:00:00Z",
            "state": {"replicas": 1, "image_tag": "0.1.0",
                      "resources": {"limits": {"memory": "64Mi", "cpu": "200m"}},
                      "security_context": {"run_as_non_root": True,
                                           "read_only_root_filesystem": True}}}))
        o.write_text(json.dumps({
            "schema_version": "1.0.0", "record_type": "observed_state",
            "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "state": {"replicas": 7, "image_tag": "0.1.0",
                      "resources": {"limits": {"memory": "64Mi", "cpu": "200m"}},
                      "security_context": {"run_as_non_root": True,
                                           "read_only_root_filesystem": True}}}))
        mdir = self.tmp / "bundle-drift"
        old_b = os.environ.get("PI4_BASELINE")
        old_o = os.environ.get("PI4_OBSERVED")
        os.environ["PI4_BASELINE"] = str(b)
        os.environ["PI4_OBSERVED"] = str(o)
        try:
            m, errs = ebb.build_bundle(mdir, "drift-test")
        finally:
            if old_b is None: os.environ.pop("PI4_BASELINE", None)
            else: os.environ["PI4_BASELINE"] = old_b
            if old_o is None: os.environ.pop("PI4_OBSERVED", None)
            else: os.environ["PI4_OBSERVED"] = old_o
        self.assertEqual(errs, [])
        drift = [f for f in m["files"] if f["probe"] == "pi4_drift_verdict"]
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0]["status"], "ok")
        # verdict content lives inside the evidence file, not the manifest row
        evfile = mdir / drift[0]["file"]
        verdict_record = json.loads(evfile.read_text())
        self.assertEqual(verdict_record["verdict"], "DRIFT")
        self.assertTrue(verdict_record["baseline_id"])

    def test_11_bundle_never_reports_pass_when_probes_failed(self):
        """A failed probe forces collection_status away from 'complete'."""
        def fake_run(cmd, timeout=120):
            if cmd and cmd[0] == "docker":
                return 1, "", "docker daemon unreachable"
            return 0, "out", ""
        with mock.patch.object(ebb, "_run", side_effect=fake_run), \
             mock.patch.object(ebb, "COLLECTOR", Path("/nonexistent")):
            m, _ = ebb.build_bundle(self.tmp / "b2", "failcase")
        self.assertNotEqual(m["collection_status"], "complete")
        self.assertIn("docker_ps", m["failed_probes"])

    def test_12_missing_pi1_collector_is_degraded_not_fatal(self):
        with mock.patch.object(ebb, "COLLECTOR", Path("/nonexistent/collector.py")):
            m, errs = ebb.build_bundle(self.tmp / "b3", "nocollector")
        self.assertEqual(m["collection_status"], "degraded")
        self.assertTrue(any("collector not found" in e for e in errs))

    def test_13_malformed_pi1_output_is_recorded_not_fabricated(self):
        """PI-1 emitting garbage -> malformed_output state, bundle continues."""
        fake = mock.mock_open(read_data="{not valid json")
        with mock.patch.object(ebb, "_run", return_value=(0, "{not json", "")), \
             mock.patch.object(ebb, "COLLECTOR", HERE / "platform_state_collector.py"):
            m, errs = ebb.build_bundle(self.tmp / "b4", "malformed")
        self.assertTrue(any(e["status"] == "malformed_output"
                            for e in (json.loads((self.tmp / "b4" / f).read_text())
                                      for f in ["00-pi1_platform_state.json"])))
        self.assertNotEqual(m["collection_status"], "complete")

    def test_14_existing_bundle_dir_refused_no_overwrite(self):
        d = self.tmp / "b5"
        d.mkdir()
        (d / "keep.txt").write_text("precious")
        m, errs = ebb.build_bundle(d, "x")
        self.assertIsNone(m)
        self.assertTrue(any("already exists" in e for e in errs))
        self.assertEqual((d / "keep.txt").read_text(), "precious")

    def test_15_manifest_sha256_is_verifiable(self):
        mdir = self.tmp / "b6"
        m, _ = ebb.build_bundle(mdir, "hash")
        self.assertTrue(m["manifest_sha256"])
        self.assertEqual(len(m["manifest_sha256"]), 64)

    def test_16_zero_inference_contract(self):
        m, _ = ebb.build_bundle(self.tmp / "b7", "inf")
        self.assertEqual(m["provenance"]["llm_inference_required"], 0)

    def test_17_file_hashes_match_content(self):
        mdir = self.tmp / "b8"
        m, _ = ebb.build_bundle(mdir, "hashes")
        for f in m["files"]:
            p = mdir / f["file"]
            self.assertEqual(ebb.sha256_file(p), f["sha256"])


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ebb-cli-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_30_cli_end_to_end(self):
        d = self.tmp / "cli-bundle"
        rc = ebb.main(["-o", str(d), "--label", "cli-test"])
        self.assertEqual(rc, 0)
        m = json.loads((d / "manifest.json").read_text())
        self.assertEqual(m["label"], "cli-test")

    def test_31_cli_missing_out_dir_errors(self):
        self.assertEqual(ebb.main([]), 2)

    def test_32_cli_existing_dir_errors_cleanly(self):
        d = self.tmp / "exists"
        d.mkdir()
        rc = ebb.main(["-o", str(d)])
        self.assertEqual(rc, 2)


class TestLiveE2E(unittest.TestCase):
    def test_40_live_bundle_on_real_host(self):
        with tempfile.TemporaryDirectory(prefix="ebb-live-") as d:
            target = Path(d) / "bundle"  # builder needs a non-existent leaf dir
            rc = ebb.main(["-o", str(target), "--label", "live-e2e"])
            self.assertEqual(rc, 0)
            m = json.loads((target / "manifest.json").read_text())
            # On the real host, probes may fail (recorded) — but structure must hold
            self.assertIn(m["collection_status"],
                          ("complete", "complete_with_failed_probes", "degraded"))
            self.assertEqual(len(m["manifest_sha256"]), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
