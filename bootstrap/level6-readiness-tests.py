#!/usr/bin/env python3
"""
bootstrap/level6-readiness-tests.py — deterministic tests for the Level 6
readiness evaluator. No production fleet, no Docker/K8s, no inference.
Tests operate on synthetic evidence directories via the module's functions.

Covers the mission's 15 test requirements:
 1 insufficient history -> NOT_READY
 2 4 weeks + low pass rate -> NOT_READY
 3 4 weeks + 90% threshold -> remaining criteria evaluated
 4 missing history -> NOT_READY
 5 stale evidence -> NOT_READY/ERROR
 6 duplicate run IDs rejected
 7 malformed JSON -> ERROR
 8 scheduler error -> NOT_READY
 9 evidence error -> NOT_READY
10 readiness transition -> notification generated
11 repeated READY -> no duplicate notification
12 new material evidence -> notification permitted
13 no LLM invocation (static import check + no network modules used)
14 no Git mutation (evaluator calls only rev-parse)
15 no Docker/Kubernetes invocation
"""
import json, os, sys, tempfile, shutil, unittest
from datetime import datetime, timezone, timedelta
from unittest import mock

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "level6_readiness_check",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "level6-readiness-check.py"))
l6 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(l6)


def mk_record(rid, start, result="PASS", runner="1.1.0", mtime=None, **kw):
    d = {
        "run_id": rid, "source_commit": "a" * 40, "overall_result": result,
        "start_time": start, "end_time": start, "duration_seconds": 85,
        "runner_version": runner, "manifest_version": "1.0.0",
        "resource_gate": "PASSED", "reconstruction": "PASS", "gitops": "Synced+Healthy",
        "evidence_generation": "OK", "evidence_validation": "OK", "evidence_retention": "OK",
        "historical_comparison": "revision: same; result: PASS -> PASS; duration: stable",
        "drift_result": "NO_UNEXPECTED_DRIFT", "teardown": "complete",
        "protected_fleet_check": "yes", "scheduler_missed_window": None,
        "failure_classification": "ok", "llm_inference_required": 0,
    }
    d.update(kw)
    return d


def write_ev(dirpath, records, mtime=None):
    os.makedirs(dirpath, exist_ok=True)
    for d in records:
        p = os.path.join(dirpath, f"validation-{d['run_id']}.json")
        with open(p, "w") as fh:
            json.dump(d, fh)
        if mtime is not None:
            os.utime(p, (mtime, mtime))


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="l6-ready-tests-")
        self.old_dir = l6.EVIDENCE_DIR
        self.old_state = l6.STATE_FILE
        self.old_tel = l6.TELEMETRY_DIR
        l6.EVIDENCE_DIR = os.path.join(self.tmp, "ev")
        l6.STATE_FILE = os.path.join(self.tmp, "state.json")
        l6.TELEMETRY_DIR = os.path.join(self.tmp, "tel")
        os.makedirs(l6.EVIDENCE_DIR, exist_ok=True)

    def tearDown(self):
        l6.EVIDENCE_DIR, l6.STATE_FILE, l6.TELEMETRY_DIR = self.old_dir, self.old_state, self.old_tel
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ev(self, records, mtime=None):
        write_ev(l6.EVIDENCE_DIR, records, mtime=mtime)

    def evaluate(self):
        recs, errs = l6.load_evidence()
        return l6.evaluate(recs, errs), errs

    def T(self, weeks_ago):
        return (datetime.now(timezone.utc) - timedelta(weeks=weeks_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1 — insufficient history
    def test_1_insufficient_history(self):
        self.ev([mk_record("r1", self.T(0.01))])
        r, _ = self.evaluate()
        self.assertEqual(r["readiness"], "NOT_READY")
        self.assertTrue(any("insufficient history" in x for x in r["reasons"]))

    # 2 — 4 weeks but low pass rate
    def test_2_low_pass_rate(self):
        recs = [mk_record(f"r{i}", self.T(4 - i * 0.5), "PASS") for i in range(3)]
        recs += [mk_record(f"f{i}", self.T(4 - i * 0.5 - 0.25), "FAIL") for i in range(4)]
        self.ev(recs)
        r, _ = self.evaluate()
        self.assertEqual(r["readiness"], "NOT_READY")
        self.assertTrue(any("pass rate" in x for x in r["reasons"]))

    # 3 — 4 weeks + 90% => remaining criteria evaluated (here: runner-version + reboot block)
    def test_3_threshold_reaches_remaining_criteria(self):
        recs = [mk_record(f"r{i}", self.T(4 - i * 0.5)) for i in range(9)]
        self.ev(recs)
        r, _ = self.evaluate()
        self.assertEqual(r["readiness"], "NOT_READY")
        self.assertFalse(any("pass rate" in x for x in r["reasons"]))
        self.assertGreaterEqual(r["pass_rate_excluding_blocked"], 0.9)
        self.assertTrue(any("runner-version" in x for x in r["reasons"]))

    # 4 — missing history
    def test_4_missing_history(self):
        r, _ = self.evaluate()  # empty evidence dir
        self.assertEqual(r["readiness"], "NOT_READY")
        self.assertTrue(any("pass rate not evaluable" in x or "insufficient history" in x for x in r["reasons"]))

    # 5 — stale evidence (mtime ancient vs window)
    def test_5_stale_evidence_still_counted_but_window_old(self):
        old = (datetime.now(timezone.utc) - timedelta(days=120)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.ev([mk_record("r1", old)])
        r, _ = self.evaluate()
        self.assertEqual(r["readiness"], "NOT_READY")

    # 6 — duplicate run IDs rejected
    def test_6_duplicates_rejected(self):
        d = mk_record("r1", self.T(1))
        self.ev([d])
        # a stale copy with the same run_id under a different filename
        import json as _json
        p2 = os.path.join(l6.EVIDENCE_DIR, "validation-r1-copy.json")
        with open(p2, "w") as fh:
            _json.dump(d, fh)
        recs, errs = l6.load_evidence()
        self.assertEqual(len(recs), 1)
        self.assertTrue(any("duplicate run_id" in e for e in errs))

    # 7 — malformed JSON -> ERROR
    def test_7_malformed_json_error(self):
        with open(os.path.join(l6.EVIDENCE_DIR, "validation-bad.json"), "w") as fh:
            fh.write("{not json")
        recs, errs = l6.load_evidence()
        self.assertEqual(len(recs), 0)
        r = l6.evaluate(recs, errs)
        self.assertEqual(r["readiness"], "ERROR")

    # 8 — scheduler error counts against pass rate
    def test_8_scheduler_error_not_ready(self):
        recs = [mk_record("r1", self.T(5)), mk_record("r2", self.T(1), "SCHEDULER_ERROR")]
        self.ev(recs)
        r, _ = self.evaluate()
        self.assertEqual(r["readiness"], "NOT_READY")
        self.assertEqual(r["scheduler_error"], 1)
        self.assertLess(r["pass_rate_excluding_blocked"], 0.9)

    # 9 — evidence error counts against pass rate
    def test_9_evidence_error_not_ready(self):
        recs = [mk_record("r1", self.T(5)), mk_record("r2", self.T(1), "EVIDENCE_ERROR")]
        self.ev(recs)
        r, _ = self.evaluate()
        self.assertEqual(r["readiness"], "NOT_READY")
        self.assertEqual(r["evidence_error"], 1)

    # 10-12 — notification transitions
    def _notify_cycle(self, records):
        self.ev(records)
        with mock.patch.object(l6, "notify", return_value=True) as m:
            l6.main(["--notify"])
            return m.call_count

    def test_10_transition_generates_notification(self):
        # seed NOT_READY state first
        self.assertEqual(self._notify_cycle([mk_record("r1", self.T(0.01))]), 0)
        # become READY (all criteria satisfied via mocks of env reality)
        recs = [mk_record(f"r{i}", self.T(4.5 - i * 0.4), runner=f"1.{i}.0") for i in range(1, 11)]
        recs.insert(0, mk_record("rf", self.T(4.6), "FAIL"))
        self.ev(recs, mtime=0)  # files written before mocked boot time => survival verified
        with mock.patch.object(l6, "boot_time", return_value=1):
            with mock.patch.object(l6, "notify", return_value=True) as m:
                l6.main(["--notify"])
                self.assertEqual(m.call_count, 1)
                st = json.load(open(l6.STATE_FILE))
                self.assertEqual(st["last_notified_readiness"], "READY")

    def test_11_repeated_ready_no_duplicate_notification(self):
        recs = [mk_record(f"r{i}", self.T(4.5 - i * 0.4), runner=f"1.{i}.0") for i in range(1, 11)]
        recs.insert(0, mk_record("rf", self.T(4.6), "FAIL"))
        self.ev(recs, mtime=0)
        with mock.patch.object(l6, "boot_time", return_value=1):
            with mock.patch.object(l6, "notify", return_value=True) as m:
                l6.main(["--notify"]); l6.main(["--notify"])
                self.assertEqual(m.call_count, 1)

    def test_12_new_material_evidence_permits_renotification(self):
        recs = [mk_record(f"r{i}", self.T(4.5 - i * 0.4), runner=f"1.{i}.0") for i in range(1, 11)]
        recs.insert(0, mk_record("rf", self.T(4.6), "FAIL"))
        self.ev(recs, mtime=0)
        with mock.patch.object(l6, "boot_time", return_value=1):
            with mock.patch.object(l6, "notify", return_value=True) as m:
                l6.main(["--notify"]); l6.main(["--notify"])
                # material change: add a run (fingerprint changes)
                recs.append(mk_record("r11", self.T(0.1), runner="1.11.0"))
                self.ev(recs, mtime=0)
                l6.main(["--notify"])
                self.assertEqual(m.call_count, 2)

    # 13 — no LLM/network modules in the evaluator
    def test_13_no_inference_dependencies(self):
        src = open(l6.__file__).read()
        for banned in ("openai", "anthropic", "anthropic", "requests", "urllib.request",
                       "http.client", "socket", "openrouter", "hermes inference"):
            self.assertNotIn(banned, src.lower(), f"banned dependency: {banned}")

    # 14 — evaluator only performs read-only git (rev-parse)
    def test_14_git_read_only(self):
        src = open(l6.__file__).read()
        for cmd in ("git add", "git commit", "git push", "git checkout",
                    "git reset", "git merge", "git rebase"):
            self.assertNotIn(cmd, src)

    # 15 — no Docker/Kubernetes invocation
    def test_15_no_container_invocation(self):
        src = open(l6.__file__).read()
        for cmd in ("docker ", "kubectl", "helm ", "argocd", "k3s"):
            self.assertNotIn(cmd, src)

    # --- OM-1 (2026-11-14): drill isolation + monthly readiness summary ----

    # 16 — REGRESSION: boot_time() must parse the REAL macOS sysctl format
    # "{ sec = 1794515570,usec = 438060 } Thu Nov 12 ..." (no space after the
    # comma). The original implementation matched only 'sec =' at string
    # start, silently returned None, and criterion 8 (evidence survival)
    # was falsely NOT_READY even though records demonstrably survived the
    # 2026-11-12 reboot.
    def test_16_boot_time_parses_real_sysctl_format(self):
        real = "{ sec = 1794515570,usec = 438060 } Thu Nov 12 14:32:50 2026"
        with mock.patch.object(l6.subprocess, "run",
                               return_value=mock.Mock(stdout=real)):
            bt = l6.boot_time()
        self.assertEqual(bt, 1794515570)

    def test_16b_boot_time_tolerant_of_spaced_format(self):
        spaced = "{ sec = 1700000000, usec = 0 } Wed Nov  1 00:00:00 2023"
        with mock.patch.object(l6.subprocess, "run",
                               return_value=mock.Mock(stdout=spaced)):
            self.assertEqual(l6.boot_time(), 1700000000)

    def test_16c_boot_time_unparseable_returns_none(self):
        with mock.patch.object(l6.subprocess, "run",
                               return_value=mock.Mock(stdout="garbage")):
            self.assertIsNone(l6.boot_time())

    # 17 — machinery-test records must NEVER count toward the pass rate.
    # The readiness evaluator is the pass-rate authority; a drill record
    # (validate-only, overall PASS) leaking into the evidence dir would
    # inflate qualification. Records whose trigger is not the scheduled
    # trigger are excluded from the denominator entirely and reported.
    def test_17_machinery_drill_record_excluded_from_pass_rate(self):
        recs = [
            mk_record("sched1", self.T(4.5), "PASS"),
            mk_record("sched2", self.T(4.0), "FAIL"),
            mk_record("sched3", self.T(3.5), "PASS"),
            mk_record("sched4", self.T(3.0), "PASS"),
        ]
        drill = mk_record("drill1", self.T(2.5), "PASS",
                          trigger="machinery-drill",
                          overall_note="validate-only machinery drill")
        self.ev(recs + [drill])
        r = l6.evaluate(l6.load_evidence()[0], [])
        # denominator = scheduled records only: 3/4 = 75%, drill ignored
        self.assertEqual(r["scheduled_runs"], 4)
        self.assertEqual(r["pass"], 3)
        self.assertEqual(r["fail"], 1)
        self.assertEqual(r["machinery_drill_runs"], 1)
        self.assertAlmostEqual(r["pass_rate_excluding_blocked"], 0.75)

    def test_17b_no_drill_records_reports_zero(self):
        self.ev([mk_record("s1", self.T(1.0), "PASS"),
                 mk_record("s2", self.T(0.5), "PASS")])
        r = l6.evaluate(l6.load_evidence()[0], [])
        self.assertEqual(r["machinery_drill_runs"], 0)

    # 18 — machine-readable monthly readiness summary (M-R2): the
    # evaluator can write a deterministic summary record (SHA-256
    # provenance, run inventory, criteria matrix) to the telemetry dir;
    # identical inputs -> byte-identical record modulo evaluated_at.
    def test_18_monthly_summary_deterministic_and_provenanced(self):
        import hashlib
        recs = [mk_record("s1", self.T(1.0), "PASS"),
                mk_record("s2", self.T(0.5), "FAIL"),
                mk_record("s3", self.T(0.2), "PASS")]
        self.ev(recs)
        records = l6.load_evidence()[0]
        r1 = l6.monthly_summary(records, [], now_override="2026-11-14T18:00:00Z")
        r2 = l6.monthly_summary(records, [], now_override="2026-11-14T18:00:00Z")
        self.assertEqual(json.dumps(r1, sort_keys=True),
                         json.dumps(r2, sort_keys=True))  # deterministic
        self.assertEqual(r1["report_class"], "READYNESS_SUMMARY")  # provenance
        self.assertIn("source_evidence_sha256", r1)
        # SHA over the exact contributing files, verifiable independently
        expected = hashlib.sha256(
            b"".join(open(os.path.join(l6.EVIDENCE_DIR, d["_file"]), "rb").read()
                     for d in records)).hexdigest()
        self.assertEqual(r1["source_evidence_sha256"], expected)
        self.assertEqual(r1["scheduled_runs"], 3)
        self.assertEqual(r1["pass"], 2)
        self.assertEqual(r1["machinery_drill_runs"], 0)
        # criteria matrix present, per-criterion booleans, no prose-only
        self.assertIn("criteria", r1)
        self.assertIn("pass_rate_excluding_blocked_met", r1["criteria"])
        self.assertNotIn("reasons", r1)  # machine-readable matrix, not prose


if __name__ == "__main__":
    unittest.main(verbosity=2)
