#!/usr/bin/env python3
"""Baseline selection for the R2 persistence rule (Phase 7C defect CI-R2-2).

Defect (2026-10-26): the baseline fetch only considered runs with CI
conclusion "success". When a run fails at the FINAL enforcement step —
after its evidence artifacts were successfully generated and uploaded —
no newer successful run can ever exist, so no run can ever find a
baseline again: main stays red indefinitely. This is the deadlock.

Fix scope: BASELINE SELECTION ONLY. The evaluator, its schema
validation, all rule semantics, and the enforcement gate are untouched.
A candidate prior run qualifies only if:

  - same repository and same branch/ref as the current run,
  - produced by this workflow (ci.yml),
  - not the current run itself (its own HEAD is excluded),
  - it has an artifact literally named "security-evidence",
  - the artifact contains a trivy-report.json that passes the SAME
    validate_scan() used on the current scan (imported, not copied).

A missing, malformed, or unverifiable candidate is skipped, and if no
candidate qualifies the caller proceeds exactly as before: no baseline
file is produced, the evaluator records R2 = UNKNOWN. UNKNOWN never
becomes PASS. Nothing here can upgrade a verdict.

Deterministic, stdlib-only, no inference. Network access is limited to
the `gh` CLI with the workflow's own token, invoked by the caller.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import shadow_evaluator  # noqa: E402  (single validation authority)

ARTIFACT_NAME = "security-evidence"
EVIDENCE_FILE = "trivy-report.json"
# Contract: on success __main__ prints exactly this string (bare path);
# the ci.yml baseline step case-matches this exact text. Tested by
# test_baseline_selector.test_7_workflow_contract — keep them in sync.
BASELINE_PATH = "/tmp/baseline-evidence/" + EVIDENCE_FILE


def _gh(args, timeout=60):
    """Run gh CLI; raise RuntimeError on failure. Testable seam."""
    out = subprocess.run(["gh"] + args, capture_output=True, text=True,
                         timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError("gh %s failed: %s" % (args[0], out.stderr.strip()[:200]))
    return out.stdout


def list_candidate_runs(ref, current_sha, current_run_id, limit=30):
    """Most recent runs on this ref from this workflow, oldest→newest,
    excluding the current run. Any conclusion (a failed run's evidence
    is real evidence — that is the deadlock fix). Raises RuntimeError."""
    runs = json.loads(_gh([
        "run", "list", "--branch", ref,
        "--limit", str(limit),
        "--json", "databaseId,headSha,workflowName,conclusion",
    ]))
    out = []
    for r in runs:
        if str(r.get("databaseId")) == str(current_run_id):
            continue  # never use the current run as its own baseline
        if r.get("workflowName") != "ci":
            continue  # only evidence produced by this workflow
        if r.get("headSha") == current_sha:
            continue  # same-commit rerun: stale evidence, not a baseline
        out.append(r)
    out.reverse()  # oldest first so iteration prefers the newest eligible
    return out


def download_evidence(run_id, dest):
    """Download a run's security-evidence artifact. Returns True on success."""
    subprocess.run(["rm", "-rf", dest], check=True)
    try:
        _gh(["run", "download", str(run_id), "-n", ARTIFACT_NAME, "-D", dest],
            timeout=120)
        return True
    except (RuntimeError, subprocess.TimeoutExpired):
        return False


def select_baseline(ref, current_sha, current_run_id, dest="/tmp/baseline-evidence"):
    """Return path to a validated baseline trivy-report.json, or None.
    All retrieval/validation failures are skipped, never fatal. On None
    no file is left at `dest` (fail-closed downstream); on success the
    validated file remains at `dest` for the caller to copy into place."""
    try:
        candidates = list_candidate_runs(ref, current_sha, current_run_id)
    except (RuntimeError, subprocess.SubprocessError, OSError, ValueError):
        # cannot enumerate candidates -> cannot verify anything -> fail closed
        return None
    for run in candidates:
        rid = run["databaseId"]
        try:
            if not download_evidence(rid, dest):
                continue
            path = os.path.join(dest, EVIDENCE_FILE)
            if not os.path.isfile(path):
                subprocess.run(["rm", "-rf", dest], check=False)
                continue
            data = json.load(open(path))
            ok, _problems = shadow_evaluator.validate_scan(data)
            if ok:
                return path  # keep in place: caller consumes it
            subprocess.run(["rm", "-rf", dest], check=False)
        except (json.JSONDecodeError, OSError, ValueError, RuntimeError,
                subprocess.SubprocessError):
            # any retrieval/validation failure: skip candidate, never fatal,
            # never leave a half-validated file behind (fail-closed)
            subprocess.run(["rm", "-rf", dest], check=False)
    return None


if __name__ == "__main__":
    ref = os.environ.get("GITHUB_REF_NAME") or sys.argv[1]
    sha = os.environ.get("GITHUB_SHA") or sys.argv[2]
    run_id = os.environ.get("GITHUB_RUN_ID") or sys.argv[3]
    try:
        path = select_baseline(ref, sha, run_id, dest="/tmp/baseline-evidence")
    except RuntimeError as e:
        # API failure = cannot verify any candidate = fail closed (no file)
        print("baseline selection: API error (%s) -> no baseline (R2=UNKNOWN)" % e)
        path = None
    # Contract (tested in test_baseline_selector.test_7_workflow_contract):
    # on success print the bare canonical path and nothing else; the ci.yml
    # baseline step case-matches this exact string to copy the file.
    if path:
        print(BASELINE_PATH)
    else:
        print("previous scan: UNAVAILABLE (R2=UNKNOWN this cycle)")
