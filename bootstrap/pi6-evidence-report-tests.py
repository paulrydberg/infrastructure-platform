#!/usr/bin/env python3
"""PI-6 evidence-report tests — synthetic only, no live infrastructure."""

import calendar
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pi6", HERE / "pi6_evidence_report.py")
pi6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pi6)

NOW = calendar.timegm(time.gmtime())
SNAP_TOL = 300


def _snap(ts, **over):
    r = {
        "schema_version": "1.0.0",
        "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
        "host": {"free_disk_gib": 42.0},
        "gates": {"capacity_gate_gib": 50},
        "provenance": {},
    }
    r.update(over)
    return r


def _window_of(rows):
    """Build a snapshot dir with `rows` (list of snapshot dicts, oldest last)."""
    d = Path(tempfile.mkdtemp()) / "snaps"
    d.mkdir(parents=True)
    for i, rec in enumerate(rows):
        (d / f"pi1-{i:04d}.json").write_text(json.dumps(rec))
    return d


class TestAuthorityAdversarial(unittest.TestCase):
    def test_11_contradictory_snapshot_cannot_upgrade(self):
        """A snapshot claiming capacity_gate_pass=true while measuring below
        the threshold cannot upgrade authority — PI-3 re-derives the verdict
        from measured values, never trusting the snapshot's own claim, and
        the report authority stays deterministic on that verdict."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"; d.mkdir()
            snap = _snap(NOW - 3600)
            snap["gates"]["capacity_gate_pass"] = True  # contradiction
            (d / "pi1-c.json").write_text(json.dumps(snap))
            rpt, errs = pi6.build_report(d, now_s=NOW)
            self.assertEqual(rpt["pi3_readiness"]["verdict"], "INSUFFICIENT_DATA")
            self.assertNotEqual(rpt["authority"], "AUTHORITATIVE")

    def test_12_caller_mutation_of_report_cannot_upgrade(self):
        """build_report returns a fresh dict each call; mutating a prior
        report's authority field cannot leak into a subsequent build."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"; d.mkdir()
            (d / "pi1-a.json").write_text(json.dumps(_snap(NOW - 3600)))
            rpt, _ = pi6.build_report(d, now_s=NOW)
            self.assertEqual(rpt["authority"], "ADVISORY_ONLY")
            rpt["authority"] = "AUTHORITATIVE"          # caller tamper
            rpt["evidence"]["window_qualified"] = True  # caller tamper
            rpt2, _ = pi6.build_report(d, now_s=NOW)
            self.assertEqual(rpt2["authority"], "ADVISORY_ONLY")
            self.assertFalse(rpt2["evidence"]["window_qualified"])

    def test_13_null_free_disk_is_insufficient_not_authoritative(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"; d.mkdir()
            snap = _snap(NOW - 3600)
            snap["host"]["free_disk_gib"] = None
            (d / "pi1-n.json").write_text(json.dumps(snap))
            rpt, errs = pi6.build_report(d, now_s=NOW)
            self.assertIsNotNone(rpt)
            self.assertNotEqual(rpt["authority"], "AUTHORITATIVE")
            self.assertTrue(errs)  # degradation is visible

    def test_14_hash_identity_tracks_content(self):
        """The reported SHA-256 identifies the EXACT bytes consumed: mutate
        the snapshot after first build → hash must change on rebuild."""
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"; d.mkdir()
            p = d / "pi1-m.json"
            p.write_text(json.dumps(_snap(NOW - 3600)))
            r1, _ = pi6.build_report(d, now_s=NOW)
            self.assertEqual(r1["evidence"]["snapshot_sha256"],
                             hashlib.sha256(p.read_bytes()).hexdigest())
            obj = json.loads(p.read_text())
            obj["host"]["free_disk_gib"] = 41.0
            p.write_text(json.dumps(obj))
            r2, _ = pi6.build_report(d, now_s=NOW)
            self.assertNotEqual(r1["evidence"]["snapshot_sha256"],
                                r2["evidence"]["snapshot_sha256"])
            self.assertEqual(r2["evidence"]["snapshot_sha256"],
                             hashlib.sha256(p.read_bytes()).hexdigest())

    def test_15_insufficient_pi3_disqualifies_authority(self):
        """A qualified-or-not window whose latest snapshot lacks docker/k3s
        → PI-3 INSUFFICIENT_DATA → the report must be ADVISORY_ONLY, never
        AUTHORITATIVE (build_report evaluates the real 14-day window)."""
        espec = importlib.util.spec_from_file_location(
            "evw", HERE / "evidence_window_validator.py")
        evw = importlib.util.module_from_spec(espec)
        espec.loader.exec_module(evw)
        d = Path(tempfile.mkdtemp()) / "sq"; d.mkdir()
        for i in range(24):  # ends 1h before NOW: inside window, no anomaly
            t = NOW - 90000 + 1800 + 3600 * i
            (d / f"pi1-{i}.json").write_text(json.dumps(_snap(t)))
        wv, wok = evw.validate_window(d, days=14, now_s=NOW)
        self.assertFalse(wok, "24h fixture cannot qualify a 14-day window")
        rpt, errs = pi6.build_report(d, now_s=NOW)
        self.assertEqual(rpt["evidence"]["window_qualified"], False)
        self.assertEqual(rpt["pi3_readiness"]["verdict"], "INSUFFICIENT_DATA")
        self.assertEqual(rpt["authority"], "ADVISORY_ONLY")

    def test_16_report_reproducible_excluding_runtime_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"; d.mkdir()
            (d / "pi1-a.json").write_text(json.dumps(_snap(NOW - 3600)))
            r1, _ = pi6.build_report(d, now_s=NOW)
            r2, _ = pi6.build_report(d, now_s=NOW)
            a, b = dict(r1), dict(r2)
            a.pop("generated_at_utc")
            b.pop("generated_at_utc")
            self.assertEqual(json.dumps(a, sort_keys=True),
                             json.dumps(b, sort_keys=True))

    def test_17_advisory_note_never_implies_permission(self):
        """The advisory note must not contain remediation/execution language;
        advisory is informational only."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"; d.mkdir()
            (d / "pi1-a.json").write_text(json.dumps(_snap(NOW - 3600)))
            rpt, _ = pi6.build_report(d, now_s=NOW)
            note = rpt["note"].lower()
            for forbidden in ("execute", "remediat", "deploy", "fix ",
                              "apply"):
                self.assertNotIn(forbidden, note)


class TestAuthority(unittest.TestCase):
    def test_01_insufficient_data_when_dir_missing(self):
        rpt, errs = pi6.build_report("/nonexistent-snaps", now_s=NOW)
        self.assertIsNone(rpt)
        self.assertTrue(any("INSUFFICIENT_DATA" in e for e in errs))

    def test_02_insufficient_data_when_dir_empty(self):
        d = Path(tempfile.mkdtemp()) / "snaps"
        d.mkdir()
        rpt, errs = pi6.build_report(d, now_s=NOW)
        self.assertIsNone(rpt)
        self.assertTrue(any("no PI-1 snapshot" in e for e in errs))

    def test_03_fail_closed_on_unparseable_snapshot(self):
        d = Path(tempfile.mkdtemp()) / "snaps"
        d.mkdir()
        (d / "pi1-bad.json").write_text("{not json")
        rpt, errs = pi6.build_report(d, now_s=NOW)
        self.assertIsNone(rpt)
        self.assertTrue(any("unparseable" in e for e in errs))

    def test_04_advisory_only_on_unqualified_window(self):
        """Early window (2 snapshots) — evidence exists, window unqualified:
        report must be ADVISORY_ONLY and say why."""
        d = _window_of([_snap(NOW - 7200), _snap(NOW - 3600)])
        rpt, errs = pi6.build_report(d, now_s=NOW)
        self.assertIsNotNone(rpt)
        self.assertEqual(rpt["authority"], "ADVISORY_ONLY")
        self.assertFalse(rpt["evidence"]["window_qualified"])
        self.assertTrue(any("not qualified" in e for e in errs))

    def test_05_advisory_only_on_stale_snapshot(self):
        """Qualified-window fixtures can't be built cheaply; instead verify
        staleness logic directly: fresh window impossible at n=1, so assert
        the stale flag is computed correctly on an old snapshot."""
        d = _window_of([_snap(NOW - 10 * 3600)])
        rpt, _ = pi6.build_report(d, now_s=NOW)
        self.assertTrue(rpt["evidence"]["snapshot_stale"])
        self.assertEqual(rpt["evidence"]["snapshot_age_s"], 10 * 3600)
        self.assertTrue(any("stale" in e for e in _errs(rpt, d)))

    def test_06_snapshot_sha256_is_content_hash(self):
        d = _window_of([_snap(NOW - 3600)])
        snap_file = sorted(d.glob("pi1-*.json"))[-1]
        rpt, _ = pi6.build_report(d, now_s=NOW)
        import hashlib
        expect = hashlib.sha256(snap_file.read_bytes()).hexdigest()
        self.assertEqual(rpt["evidence"]["snapshot_sha256"], expect)

    def test_07_zero_inference_and_schema_fields(self):
        d = _window_of([_snap(NOW - 3600)])
        rpt, _ = pi6.build_report(d, now_s=NOW)
        self.assertEqual(rpt["llm_inference_required"], 0)
        for key in ("schema_version", "report_version", "authority",
                    "evidence", "pi3_readiness", "provenance"):
            self.assertIn(key, rpt)

    def test_08_explicit_snapshot_selection(self):
        d = _window_of([_snap(NOW - 7200), _snap(NOW - 3600)])
        older = sorted(d.glob("pi1-*.json"))[0]
        rpt, _ = pi6.build_report(d, snapshot_file=older, now_s=NOW)
        self.assertEqual(rpt["evidence"]["snapshot_file"], older.name)

    def test_09_deterministic_given_fixed_clock(self):
        d = _window_of([_snap(NOW - 3600)])
        r1, _ = pi6.build_report(d, now_s=NOW)
        r2, _ = pi6.build_report(d, now_s=NOW)
        r1.pop("generated_at_utc")
        r2.pop("generated_at_utc")
        self.assertEqual(json.dumps(r1, sort_keys=True),
                         json.dumps(r2, sort_keys=True))

    def test_10_unqualified_window_never_reports_authoritative(self):
        """The gate-preservation invariant: no authority upgrade on elapsed
        time. Even with 100% schema-valid snapshots, an unqualified window
        yields ADVISORY_ONLY, never AUTHORITATIVE."""
        d = _window_of([_snap(NOW - 3600 * i) for i in range(1, 4)])
        rpt, _ = pi6.build_report(d, now_s=NOW)
        self.assertNotEqual(rpt["authority"], "AUTHORITATIVE")


def _errs(rpt, d):
    """Recompute errors for note assertions (build_report already returns
    them; this helper keeps test_05 readable)."""
    _, errs = pi6.build_report(d, now_s=NOW)
    return errs


if __name__ == "__main__":
    unittest.main(verbosity=2)
