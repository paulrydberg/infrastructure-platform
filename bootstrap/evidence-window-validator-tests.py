#!/usr/bin/env python3
"""Tests for PI-2/PI-6 evidence_window_validator.py (ADR-0012).

Run: python3 evidence-window-validator-tests.py
Synthetic only — builds fake snapshot dirs in temp space; touches nothing live.
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
_spec = importlib.util.spec_from_file_location("evw", HERE / "evidence_window_validator.py")
evw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(evw)

NOW = calendar.timegm(time.gmtime())


def _snap(ts_s, gate=50, free=28.0):
    return {
        "schema_version": "1.0.0",
        "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts_s)),
        "host": {"free_disk_gib": free, "swap_used_mib": 11102},
        "gates": {"capacity_gate_gib": gate,
                  "capacity_gate_pass": free >= gate},
        "provenance": {"tool": "platform_state_collector.py"},
    }


def _write_dir(tmp, ts_list, gate=50, corrupt=None, missing_key=None):
    d = Path(tmp) / "snaps"
    d.mkdir(parents=True, exist_ok=True)
    for i, ts in enumerate(ts_list):
        p = d / f"pi1-{time.strftime('%Y%m%d-%H%M%SZ', time.gmtime(ts))}.json"
        if corrupt is not None and i == corrupt:
            p.write_text("{not json")
        elif missing_key is not None and i == missing_key:
            # valid timestamp but missing evidence keys (host/gates absent)
            p.write_text(json.dumps({
                "schema_version": "1.0.0",
                "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                  time.gmtime(ts)),
                "note": "structurally parseable, evidence keys missing",
            }))
        else:
            p.write_text(json.dumps(_snap(ts, gate=gate)))
    return d


class TestQualified(unittest.TestCase):
    def test_01_full_hourly_window_qualifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            ts = [NOW - 3600 * (14 * 24 - h - 1) for h in range(14 * 24)]
            d = _write_dir(tmp, ts)
            v, ok = evw.validate_window(d, days=14, now_s=NOW)
            self.assertTrue(ok)
            self.assertTrue(v["window_qualified"])
            self.assertTrue(v["criteria_results"]["c1_coverage"]["pass"])

    def test_02_empty_dir_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_dir(tmp, [])
            v, ok = evw.validate_window(d, days=14, now_s=NOW)
            self.assertFalse(ok)
            self.assertFalse(v["window_qualified"])

    def test_03_missing_dir_is_insufficient(self):
        v, ok = evw.validate_window("/nonexistent-snaps", days=14, now_s=NOW)
        self.assertFalse(ok)
        self.assertFalse(v["window_qualified"])
        self.assertTrue(any("not found" in e for e in v["errors"]))


class TestCriteria(unittest.TestCase):
    def _dir_with_coverage(self, tmp, frac, days=14):
        total = days * 24
        ts = [NOW - 3600 * (total - h - 1) for h in range(int(total * frac))]
        return _write_dir(tmp, ts)

    def test_10_coverage_below_90_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._dir_with_coverage(tmp, 0.5)
            v, ok = evw.validate_window(d, days=14, now_s=NOW)
            self.assertFalse(v["criteria_results"]["c1_coverage"]["pass"])
            self.assertFalse(ok)

    def test_11_gap_over_6h_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            # 95% coverage but one 8-hour hole
            ts = [NOW - 3600 * (14 * 24 - h - 1) for h in range(int(14 * 24 * 0.95))
                  if h not in (100, 101, 102, 103, 104, 105, 106, 107)]
            d = _write_dir(tmp, ts)
            v, ok = evw.validate_window(d, days=14, now_s=NOW)
            self.assertFalse(v["criteria_results"]["c3_gap_discipline"]["pass"])
            self.assertFalse(ok)

    def test_12_malformed_snapshots_counted(self):
        """Malformed snapshots are excluded AND counted as evidence — never
        silently dropped. Schema ratio reflects only parseable records."""
        with tempfile.TemporaryDirectory() as tmp:
            ts = [NOW - 3600 * (14 * 24 - h - 1) for h in range(14 * 24)]
            d = _write_dir(tmp, ts, corrupt=5)
            v, ok = evw.validate_window(d, days=14, now_s=NOW)
            self.assertEqual(v["malformed_count"], 1)
            self.assertEqual(v["snapshot_count"], 14 * 24 - 1)
            self.assertTrue(any("malformed" in e for e in v["errors"]))

    def test_13_threshold_change_fails_c4(self):
        with tempfile.TemporaryDirectory() as tmp:
            total = 14 * 24
            ts = [NOW - 3600 * (total - h - 1) for h in range(total)]
            d = Path(tmp) / "snaps"
            d.mkdir()
            for i, t in enumerate(ts):
                gate = 50 if i < total - 5 else 55  # threshold changed mid-window
                (d / f"pi1-{time.strftime('%Y%m%d-%H%M%SZ', time.gmtime(t))}.json").write_text(
                    json.dumps(_snap(t, gate=gate)))
            v, ok = evw.validate_window(d, days=14, now_s=NOW)
            self.assertFalse(v["criteria_results"]["c4_threshold_stability"]["pass"])
            self.assertFalse(ok)

    def test_14_missing_host_key_fails_schema_validity(self):
        """Parseable snapshots missing required evidence keys count against
        schema validity (invalid-but-parseable is not valid)."""
        with tempfile.TemporaryDirectory() as tmp:
            total = 14 * 24
            ts = [NOW - 3600 * (total - h - 1) for h in range(total)]
            d = _write_dir(tmp, ts, missing_key=total // 2)
            v, ok = evw.validate_window(d, days=14, now_s=NOW)
            c2 = v["criteria_results"]["c2_schema_valid"]
            self.assertLess(c2["ratio"], 1.0)
            self.assertEqual(c2["valid"], total - 1)


class TestContract(unittest.TestCase):
    def test_20_zero_inference_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_dir(tmp, [NOW - 3600])
            v, _ = evw.validate_window(d, days=14, now_s=NOW)
            self.assertEqual(v["llm_inference_required"], 0)
            self.assertTrue(v["read_only"])

    def test_21_verdict_is_json_serializable(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_dir(tmp, [NOW - 3600])
            v, _ = evw.validate_window(d, days=14, now_s=NOW)
            json.dumps(v)  # must not raise

    def test_22_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _write_dir(tmp, [NOW - 3600, NOW - 7200])
            out = Path(tmp) / "v.json"
            rc = evw.main(["--dir", str(d), "--days", "14", "-o", str(out)])
            self.assertEqual(rc, 0)
            loaded = json.loads(out.read_text())
            self.assertIn("window_qualified", loaded)
            self.assertIn("criteria_results", loaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
