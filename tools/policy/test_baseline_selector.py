#!/usr/bin/env python3
"""Deterministic tests for tools/policy/baseline_selector.py (CI-R2-2).

Covers the six mandated scenarios:
  1. prior successful run with valid evidence  -> selected
  2. prior failed run with valid evidence      -> selected (deadlock fix)
  3. no eligible prior artifact                -> None (fail-closed)
  4. missing/malformed/corrupted evidence      -> skipped, None (fail-closed)
  5. current run excluded from baseline selection
  6. API/artifact retrieval errors             -> None (fail-closed)

stdlib-only, no network, no production findings as fixtures.
Run: python3 tools/policy/test_baseline_selector.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baseline_selector as bs
import shadow_evaluator as ev

VALID_SCAN = {"Results": [{"Target": "platform-demo:0.1.0 (alpine 3.22)",
                           "Vulnerabilities": [
                               {"VulnerabilityID": "CVE-2026-0001",
                                "PkgName": "musl", "Severity": "LOW"}]}]}
# structurally invalid: no Results key at all (P1 violation)
MALFORMED_SCAN = {"oops": True}
# valid JSON but corrupted semantics: no block carries a list
CORRUPTED_SCAN = {"Results": [{"Target": "x", "Class": "lang-pkgs"}]}


def run(run_id, sha, conclusion, wf="ci"):
    return {"databaseId": run_id, "headSha": sha,
            "workflowName": wf, "conclusion": conclusion}


class Base(unittest.TestCase):
    def setUp(self):
        self.dest = tempfile.mkdtemp()

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.dest], check=False)

    def seed_evidence(self, run_id, scan, dest=None):
        d = dest or os.path.join(self.dest, str(run_id))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "trivy-report.json"), "w") as f:
            json.dump(scan, f)
        return d

    def patch_download(self, mapping):
        """mapping: run_id -> scan dict | None (download fails).
        Returns (patch, fetched_list) where fetched_list records which
        run_ids the selector actually attempted to download."""
        fetched = []
        mapping = {str(k): v for k, v in mapping.items()}

        def fake_download(run_id, dest):
            fetched.append(str(run_id))
            scan = mapping.get(str(run_id))
            if scan is None:
                return False
            self.seed_evidence(run_id, scan, dest)
            return True
        return mock.patch.object(bs, "download_evidence", side_effect=fake_download), fetched


class TestBaselineSelection(Base):
    def test_1_prior_success_with_valid_evidence_selected(self):
        patch, _ = self.patch_download({111: VALID_SCAN})
        with mock.patch.object(bs, "list_candidate_runs", return_value=[
                run(111, "a", "success")]), patch:
            self.assertEqual(bs.select_baseline("main", "zz", 999, self.dest),
                             os.path.join(self.dest, "trivy-report.json"))

    def test_2_prior_failed_with_valid_evidence_selected(self):
        """The deadlock fix: a run that failed at enforcement (after its
        evidence upload) is an eligible baseline source."""
        patch, _ = self.patch_download({222: VALID_SCAN})
        with mock.patch.object(bs, "list_candidate_runs", return_value=[
                run(222, "b", "failure")]), patch:
            self.assertEqual(bs.select_baseline("main", "zz", 999, self.dest),
                             os.path.join(self.dest, "trivy-report.json"))

    def test_3_no_eligible_artifact_returns_none(self):
        patch, _ = self.patch_download({333: None})  # artifact download fails
        with mock.patch.object(bs, "list_candidate_runs", return_value=[
                run(333, "c", "success")]), patch:
            self.assertIsNone(bs.select_baseline("main", "zz", 999, self.dest))

    def test_4_malformed_and_corrupted_evidence_skipped(self):
        patch, _ = self.patch_download({441: MALFORMED_SCAN, 442: CORRUPTED_SCAN})
        with mock.patch.object(bs, "list_candidate_runs", return_value=[
                run(441, "d", "failure"), run(442, "e", "success")]), patch:
            self.assertIsNone(bs.select_baseline("main", "zz", 999, self.dest))

    def test_5_current_run_and_own_sha_excluded(self):
        """The current run must never be its own baseline; same-commit
        reruns are excluded too (stale evidence, not a baseline).
        Exercises list_candidate_runs directly — that is where the
        exclusion logic lives."""
        def fake_gh(args, timeout=60):
            return json.dumps([
                run(999, "zz", "failure"),    # current run id
                run(555, "zz", "failure"),    # same sha as current
                run(556, "f", "success"),
                run(557, "i", "success", wf="other.yml"),  # wrong workflow
            ])

        with mock.patch.object(bs, "_gh", side_effect=fake_gh):
            got = bs.list_candidate_runs("main", "zz", 999)
        # current run id, same-sha rerun, and foreign-workflow runs are gone
        self.assertEqual([r["databaseId"] for r in got], [556])

    def test_5b_newest_eligible_wins(self):
        newer = dict(VALID_SCAN)
        older = dict(VALID_SCAN)
        patch, _ = self.patch_download({771: older, 772: newer})
        with mock.patch.object(bs, "list_candidate_runs", return_value=[
                run(771, "g", "success"), run(772, "h", "failure")]), patch:
            path = bs.select_baseline("main", "zz", 999, self.dest)
            self.assertIsNotNone(path)
            with open(path) as f:
                self.assertEqual(json.load(f), newer)  # newest run's content

    def test_6_api_error_fails_closed(self):
        with mock.patch.object(bs, "list_candidate_runs",
                               side_effect=RuntimeError("gh failed")):
            self.assertIsNone(bs.select_baseline("main", "zz", 999, self.dest))

    def test_6b_evaluator_validator_is_the_authority(self):
        """The selector must use the evaluator's own validate_scan,
        not a copy — the two cannot drift."""
        self.assertIs(bs.shadow_evaluator, ev)

    def test_6c_non_dict_evidence_json_is_skipped(self):
        patch, _ = self.patch_download({881: ["not", "a", "dict"]})
        with mock.patch.object(bs, "list_candidate_runs", return_value=[
                run(881, "i", "success")]), patch:
            self.assertIsNone(bs.select_baseline("main", "zz", 999, self.dest))

    def test_6d_no_candidates_at_all_returns_none(self):
        with mock.patch.object(bs, "list_candidate_runs", return_value=[]):
            self.assertIsNone(bs.select_baseline("main", "zz", 999, self.dest))

    def test_7_workflow_contract(self):
        """Module output and the ci.yml baseline-step case pattern must
        not drift: the module must print exactly BASELINE_PATH on success
        and the workflow must case-match that exact string. (Guards the
        2026-10-26 handoff defect where the prefix 'previous scan: '
        broke the copy and R2 stayed UNKNOWN despite a valid baseline.)"""
        self.assertEqual(bs.BASELINE_PATH,
                         "/tmp/baseline-evidence/trivy-report.json")
        wf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "..", ".github", "workflows", "ci.yml")
        wf = open(wf_path).read()
        self.assertIn('case "$PREV" in', wf)
        self.assertIn(bs.BASELINE_PATH, wf)
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "baseline_selector.py")).read()
        self.assertIn("print(BASELINE_PATH)", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
