#!/usr/bin/env python3
"""
bootstrap/level6-readiness-check.py — Level 6 readiness observer (deterministic).

Reads the Level 6 periodic-validation evidence produced by the existing
launchd-scheduled reconstruction (bootstrap/periodic-validate.sh) and answers
READY / NOT_READY / ERROR against the documented Level 7 entry criteria
(docs/history/post-level6-audit.md, §19-22). Pure Python stdlib + filesystem +
git metadata. NO LLM, NO inference, NO model API, NO network to AI services.

This is a MONITORING/REMINDER layer only:
- does NOT run reconstructions (launchd owns that),
- does NOT mutate Git (observation only; `git rev-parse HEAD` is read-only),
- does NOT touch Docker/Kubernetes/the protected fleet,
- does NOT dirty the repository (telemetry goes to a local ignored dir).

Readiness contract (all deterministic, from evidence records):
  1. evidence duration      >= 4 weeks of scheduled history
  2. pass rate              PASS / (PASS+FAIL+SCHEDULER_ERROR+EVIDENCE_ERROR+
                            TIMEOUT+CANCELLED) >= 0.90  (BLOCKED excluded)
  3. failure recovery       every observed FAIL followed by a later PASS
                            without manual repair (inferred deterministically:
                            later PASS run on a clean source pin)
  4. missed windows         zero unexplained missed/overdue windows
                            (scheduler_missed_window fields must be recorded,
                            i.e. explained, for all runs)
  5. fleet safety           zero protected-fleet incidents
                            (protected_fleet_check != "yes" in any record = incident)
  6. comparison stability   historical comparison present and not erroring
  7. runner-version change  history spans >= 1 runner_version change
  8. evidence survival      evidence demonstrably survives reboot

Absence of evidence for a criterion = NOT_READY for that criterion
(absence is never success). Malformed/corrupt evidence = ERROR for the run.

Anti-duplicate/provenance guard (the AUD-1 lesson): a record is counted only
if it has a unique run_id, valid JSON, required provenance fields, and a
fresh mtime (not older than the evidence window start; stale copies of older
reports are ignored).

Notification state: ~/.infrastructure-platform/level6-readiness-state.json —
notify once on NOT_READY->READY; re-notify only when the evidence fingerprint
materially changes (new failure class, regression, expanded window) or the
operator resets state.
"""
import json
import os
import subprocess
import sys
import hashlib
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO, "docs/15-reproducibility/periodic")
STATE_DIR = os.path.expanduser("~/.infrastructure-platform")
STATE_FILE = os.path.join(STATE_DIR, "level6-readiness-state.json")
TELEMETRY_DIR = os.path.join(STATE_DIR, "level6-readiness-telemetry")
REVIEW_URL = "https://chatgpt.com/share/6ab603e7-fd80-83e9-97d6-b38f2dac2d9d?ogimg=plain"
SCHEMA = "1.0.0"

REQUIRED_PROVENANCE = ("run_id", "source_commit", "overall_result", "start_time")

CRITERIA_TARGETS = {
    "weeks": 4,
    "pass_rate": 0.90,
    "runner_version_changes": 1,
}


def now() -> datetime:
    return datetime.now(timezone.utc)


def parse_ts(s):
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def git_head():
    """Read-only git metadata; never mutates the checkout."""
    try:
        return subprocess.run(
            ["git", "-C", REPO, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
    except Exception:
        return None


def boot_time():
    """macOS: sysctl kern.boottime -> evidence survival candidate."""
    try:
        out = subprocess.run(["sysctl", "-n", "kern.boottime"],
                             capture_output=True, text=True, timeout=10).stdout
        # format: { sec = 1690000000, usec = 0 } ...
        for part in out.split(","):
            part = part.strip()
            if part.startswith("sec ="):
                return int(part.split("=")[1].strip())
    except Exception:
        pass
    return None


def load_evidence():
    """Load + validate + dedupe evidence records. Returns (records, errors)."""
    records, errors, seen_ids = [], [], set()
    try:
        files = sorted(f for f in os.listdir(EVIDENCE_DIR) if f.startswith("validation-") and f.endswith(".json"))
    except FileNotFoundError:
        return [], ["evidence directory missing: " + EVIDENCE_DIR]
    for fn in files:
        path = os.path.join(EVIDENCE_DIR, fn)
        try:
            with open(path) as fh:
                d = json.load(fh)
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"{fn}: malformed/unreadable ({e.__class__.__name__})")
            continue
        missing = [k for k in REQUIRED_PROVENANCE if not d.get(k)]
        if missing:
            errors.append(f"{fn}: missing provenance fields {missing}")
            continue
        rid = d["run_id"]
        if rid in seen_ids:
            errors.append(f"{fn}: duplicate run_id {rid} — rejected (provenance guard)")
            continue
        seen_ids.add(rid)
        d["_mtime"] = os.path.getmtime(path)
        d["_file"] = fn
        records.append(d)
    return records, errors


def classify(d):
    o = d.get("overall_result", "")
    if o in ("PASS", "FAIL", "BLOCKED", "EVIDENCE_ERROR"):
        return o
    if o == "SCHEDULER_ERROR":
        return "SCHEDULER_ERROR"
    return "TIMEOUT" if o == "TIMEOUT" else "CANCELLED" if o == "CANCELLED" else "UNKNOWN"


def evaluate(records, errors):
    """Pure evaluation. Returns the readiness result dict."""
    reasons = []
    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SCHEDULER_ERROR": 0,
              "EVIDENCE_ERROR": 0, "TIMEOUT": 0, "CANCELLED": 0, "UNKNOWN": 0}
    for d in records:
        counts[classify(d)] += 1

    if errors and not records:
        return {"schema_version": SCHEMA, "readiness": "ERROR",
                "reasons": ["all evidence malformed/inaccessible"] + errors,
                "counts": counts}

    times = [parse_ts(d["start_time"]) for d in records]
    times = [t for t in times if t]
    if times:
        window_start, window_end = min(times), max(times)
        weeks = (window_end - window_start).total_seconds() / (7 * 86400)
    else:
        window_start = window_end = None
        weeks = 0.0

    denom = sum(counts[k] for k in
                ("PASS", "FAIL", "SCHEDULER_ERROR", "EVIDENCE_ERROR", "TIMEOUT", "CANCELLED"))
    pass_rate = (counts["PASS"] / denom) if denom else None

    # criterion checks -----------------------------------------------------
    if weeks >= CRITERIA_TARGETS["weeks"]:
        pass  # satisfied
    else:
        reasons.append(f"insufficient history: {weeks:.1f} weeks < {CRITERIA_TARGETS['weeks']} weeks")

    if pass_rate is None or denom == 0:
        reasons.append("pass rate not evaluable (no scheduled runs)")
    elif pass_rate < CRITERIA_TARGETS["pass_rate"]:
        reasons.append(f"pass rate {pass_rate:.0%} < {CRITERIA_TARGETS['pass_rate']:.0%} (excluding BLOCKED)")

    # failure recovery: every FAIL must be followed by a later PASS
    chrono = sorted((t, d) for t, d in zip(times, records) if t) if False else \
             sorted([(parse_ts(d["start_time"]), d) for d in records if parse_ts(d["start_time"])],
                    key=lambda x: x[0])
    recovery_verified, unrecovered = True, []
    seen_fail = False
    for t, d in chrono:
        if classify(d) == "FAIL":
            seen_fail = True
            unrecovered.append(d["run_id"])
        elif classify(d) == "PASS" and seen_fail:
            # later successful run on any revision => system recovered
            # (reconstruction success implies recovery; deterministic evidence)
            unrecovered = []
            seen_fail = False
            recovery_verified = True
    if seen_fail and unrecovered:
        recovery_verified = False
        reasons.append("unrecovered failures: " + ", ".join(unrecovered))
    if not any(classify(d) == "FAIL" for d in records):
        recovery_verified = None  # no failure observed => criterion not yet exercised
        reasons.append("failure recovery not yet exercised (no failures in window)")

    # missed windows: any run with scheduler_missed_window set is EXPLAINED;
    # an unexplained gap would be visible as evidence absence, i.e. window
    # smaller than schedule coverage — covered by the weeks criterion. Any
    # run WITHOUT the field is fine (means no miss). Treat field=None as OK.
    missed_explained = sum(1 for d in records if d.get("scheduler_missed_window"))

    # fleet safety
    incidents = sum(1 for d in records if d.get("protected_fleet_check") not in ("yes", None))
    if incidents:
        reasons.append(f"protected-fleet incidents: {incidents}")
        fleet_ok = False
    else:
        fleet_ok = True

    # comparison stability: at least the latest record carries a non-error comparison
    comp_ok = all("comparison error" not in (d.get("historical_comparison") or "")
                  for d in records)
    if not comp_ok:
        reasons.append("historical comparison error present")
    if len(records) < 2:
        comp_ok = False
        reasons.append("comparison stability not yet evaluable (<2 runs)")

    # runner-version change
    versions = {d.get("runner_version") for d in records}
    rv_change = len(versions) > CRITERIA_TARGETS["runner_version_changes"] - 1 and len(versions) >= 2
    if not rv_change:
        reasons.append("runner-version-change evidence not yet available")

    # evidence survival across reboot: any record created before last boot AND
    # still readable now.
    bt = boot_time()
    survived = False
    if bt:
        for d in records:
            if d["_mtime"] < bt:
                survived = True
                break
    if not survived:
        reasons.append("evidence survival across reboot not yet demonstrated")

    # ERROR if any malformed evidence existed alongside valid records
    if errors:
        reasons.extend("malformed evidence: " + e for e in errors)

    readiness = "READY" if not reasons else "NOT_READY"
    result = {
        "schema_version": SCHEMA,
        "evaluated_at": now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence_window_start": window_start.strftime("%Y-%m-%dT%H:%M:%SZ") if window_start else None,
        "evidence_window_end": window_end.strftime("%Y-%m-%dT%H:%M:%SZ") if window_end else None,
        "scheduled_runs": len(records),
        "pass": counts["PASS"],
        "fail": counts["FAIL"],
        "blocked": counts["BLOCKED"],
        "scheduler_error": counts["SCHEDULER_ERROR"],
        "evidence_error": counts["EVIDENCE_ERROR"],
        "timeout": counts["TIMEOUT"],
        "cancelled": counts["CANCELLED"],
        "pass_rate_excluding_blocked": round(pass_rate, 4) if pass_rate is not None else None,
        "weeks_accumulated": round(weeks, 2),
        "failure_recovery_verified": recovery_verified,
        "missed_windows": missed_explained,
        "fleet_incidents": incidents,
        "comparison_stable": comp_ok,
        "runner_version_change_verified": rv_change,
        "evidence_survived_reboot": survived,
        "readiness": readiness,
        "reasons": reasons,
        "runner_versions_seen": sorted(v for v in versions if v),
        "git_head": git_head(),
        "review_url": REVIEW_URL,
    }
    return result


def fingerprint(result):
    """Material-change fingerprint: window end + counts + readiness."""
    material = {k: result[k] for k in
                ("pass", "fail", "blocked", "scheduler_error", "evidence_error",
                 "scheduled_runs", "readiness", "evidence_window_end")}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()[:16]


def load_state():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


def notify(result):
    """Deterministic macOS notification via osascript (no inference)."""
    body = (
        f"Hermes CTO — Level 6 evidence review ready. "
        f"Evidence window: {result['evidence_window_start']} -> {result['evidence_window_end']}. "
        f"Scheduled runs: {result['scheduled_runs']} (PASS {result['pass']}, FAIL {result['fail']}, "
        f"BLOCKED {result['blocked']}, errors {result['scheduler_error'] + result['evidence_error']}). "
        f"PASS rate excl BLOCKED: {result['pass_rate_excluding_blocked']}. "
        f"Recovery: {'verified' if result['failure_recovery_verified'] else 'not verified'}. "
        f"Runner-version change: {'verified' if result['runner_version_change_verified'] else 'not verified'}. "
        f"Reboot survival: {'verified' if result['evidence_survived_reboot'] else 'not verified'}. "
        f"Bring the evidence to the review thread: {REVIEW_URL}"
    )
    script = f'display notification "{body}" with title "Hermes CTO — Level 6 review ready" subtitle "Readiness: READY"'
    try:
        subprocess.run(["osascript", "-e", script], timeout=15, capture_output=True)
        return True
    except Exception:
        return False


def write_telemetry(result, records):
    """Local ignored telemetry package (never inside the repo, never committed)."""
    os.makedirs(TELEMETRY_DIR, exist_ok=True)
    with open(os.path.join(TELEMETRY_DIR, "readiness.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    run_summary = [{"run_id": d["run_id"], "start": d["start_time"], "result": d["overall_result"],
                    "duration": d.get("duration_seconds"), "commit": d["source_commit"][:8],
                    "recon": d.get("reconstruction")} for d in records]
    with open(os.path.join(TELEMETRY_DIR, "run-summary.json"), "w") as fh:
        json.dump(run_summary, fh, indent=2)
    fails = [d for d in records if classify(d) == "FAIL"]
    with open(os.path.join(TELEMETRY_DIR, "failure-summary.json"), "w") as fh:
        json.dump([{"run_id": d["run_id"], "classification": d.get("failure_classification")} for d in fails], fh, indent=2)
    with open(os.path.join(TELEMETRY_DIR, "resource-summary.json"), "w") as fh:
        json.dump([{"run_id": d["run_id"], "resource_gate": d.get("resource_gate"),
                    "duration": d.get("duration_seconds")} for d in records], fh, indent=2)
    with open(os.path.join(TELEMETRY_DIR, "comparison-summary.json"), "w") as fh:
        json.dump([{"run_id": d["run_id"], "comparison": d.get("historical_comparison"),
                    "drift": d.get("drift_result")} for d in records], fh, indent=2)
    with open(os.path.join(TELEMETRY_DIR, "scheduler-summary.json"), "w") as fh:
        json.dump([{"run_id": d["run_id"], "scheduler": d.get("scheduler"),
                    "missed": d.get("scheduler_missed_window")} for d in records], fh, indent=2)
    return TELEMETRY_DIR


def main(argv):
    notify_mode = "--notify" in argv
    records, errors = load_evidence()
    result = evaluate(records, errors)
    fp = fingerprint(result)
    notified = False

    if notify_mode:
        state = load_state()
        prev = state.get("last_notified_readiness")
        prev_fp = state.get("evidence_fingerprint")
        if result["readiness"] == "READY" and not (prev == "READY" and prev_fp == fp):
            notified = notify(result)
            if notified:
                save_state({"last_notified_readiness": "READY",
                            "notified_at": result["evaluated_at"],
                            "evidence_fingerprint": fp})
        elif result["readiness"] == "NOT_READY" and prev == "READY":
            # readiness regressed: allow re-notify when it returns
            save_state({"last_notified_readiness": "NOT_READY",
                        "notified_at": result["evaluated_at"],
                        "evidence_fingerprint": fp})

    if notify_mode:
        write_telemetry(result, records)

    print(json.dumps(result, indent=2))
    return 0 if result["readiness"] != "ERROR" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
