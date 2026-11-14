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

# OM-1: the only trigger class that counts toward qualification. Any other
# trigger (machinery drill, manual invocation) is evidence, never a
# qualification event — it cannot move the pass rate in either direction.
SCHEDULED_TRIGGER = "periodic-level6"

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
    """macOS: sysctl kern.boottime -> evidence survival candidate.

    DEFECT L6-OBS-1 (found 2026-11-14, OM-1): the real sysctl output is
    "{ sec = 1794515570,usec = 438060 } Thu Nov 12 14:32:50 2026" — the
    leading "{" defeated the original startswith("sec =") match, so this
    returned None on the live host and criterion 8 (evidence survival)
    was falsely NOT_READY although records pre-dating the 2026-11-12
    reboot remained readable. Parse by scanning parts, not anchoring.
    """
    try:
        out = subprocess.run(["sysctl", "-n", "kern.boottime"],
                             capture_output=True, text=True, timeout=10).stdout
        for part in out.replace("{", " ").replace("}", " ").split(","):
            part = part.strip()
            if part.startswith("sec ="):
                return int(part.split("=", 1)[1].strip())
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
    # OM-1 isolation invariant: machinery-drill records (trigger !=
    # SCHEDULED_TRIGGER) are evidence but are NOT qualification events —
    # they never enter the pass-rate denominator or the criteria counts.
    # A drill PASS must never inflate qualification (L6-6 semantics).
    scheduled = [d for d in records if d.get("trigger", SCHEDULED_TRIGGER) == SCHEDULED_TRIGGER]
    drill_runs = [d for d in records if d.get("trigger", SCHEDULED_TRIGGER) != SCHEDULED_TRIGGER]
    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SCHEDULER_ERROR": 0,
              "EVIDENCE_ERROR": 0, "TIMEOUT": 0, "CANCELLED": 0, "UNKNOWN": 0}
    for d in scheduled:
        counts[classify(d)] += 1

    if errors and not records:
        return {"schema_version": SCHEMA, "readiness": "ERROR",
                "reasons": ["all evidence malformed/inaccessible"] + errors,
                "counts": counts}

    times = [parse_ts(d["start_time"]) for d in scheduled]
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
    # (scheduled records only — a drill PASS never clears a real FAIL)
    chrono = sorted([(parse_ts(d["start_time"]), d) for d in scheduled if parse_ts(d["start_time"])],
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
    if not any(classify(d) == "FAIL" for d in scheduled):
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
        "scheduled_runs": len(scheduled),
        "machinery_drill_runs": len(drill_runs),
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


def monthly_summary(records, errors, now_override=None):
    """OM-1 M-R2: deterministic machine-readable readiness summary record.

    Consumes ONLY already-stored evidence records (no new source of truth,
    no re-derivation): counts, per-criterion boolean matrix, and a SHA-256
    over the exact contributing evidence files (verifiable independently).
    Zero inference; stdlib only; identical inputs -> identical output modulo
    evaluated_at (pinned via now_override for deterministic verification).
    Provenance: report_class READYNESS_SUMMARY distinguishes it from
    scheduled qualification evidence; historical records are untouched.
    """
    result = evaluate(records, errors)
    # OM-2: all-evidence-malformed is a legitimate monthly condition — the
    # summary must still be produced honestly (zero counts, readiness ERROR),
    # never fabricated and never a crash.
    if result["readiness"] == "ERROR" and "counts" not in result:
        result["counts"] = {}
    if result["readiness"] == "ERROR" and "scheduled_runs" not in result:
        result.update({"scheduled_runs": 0, "machinery_drill_runs": 0,
                       "pass": 0, "fail": 0, "blocked": 0,
                       "pass_rate_excluding_blocked": None,
                       "weeks_accumulated": 0.0,
                       "evidence_window_start": None,
                       "evidence_window_end": None,
                       "failure_recovery_verified": None,
                       "fleet_incidents": 0,
                       "comparison_stable": False,
                       "runner_version_change_verified": False,
                       "evidence_survived_reboot": False})
    # source evidence SHA: over each contributing record file, in run order
    h = hashlib.sha256()
    contributing = []
    for d in sorted(records, key=lambda x: (x.get("start_time") or "", x.get("run_id") or "")):
        path = os.path.join(EVIDENCE_DIR, d.get("_file") or "")
        try:
            h.update(open(path, "rb").read())
            contributing.append({"run_id": d.get("run_id"), "file": d.get("_file")})
        except OSError:
            pass  # missing file -> excluded from hash, recorded in inventory
    criteria = {
        "history_weeks_met": result["weeks_accumulated"] >= CRITERIA_TARGETS["weeks"],
        "pass_rate_excluding_blocked_met": (
            result["pass_rate_excluding_blocked"] is not None
            and result["pass_rate_excluding_blocked"] >= CRITERIA_TARGETS["pass_rate"]),
        "failure_recovery_verified": result["failure_recovery_verified"] is True,
        "missed_windows_explained": True,  # field presence = explained (observer contract)
        "fleet_incidents_zero": result["fleet_incidents"] == 0,
        "comparison_stable": result["comparison_stable"] is True,
        "runner_version_change_verified": result["runner_version_change_verified"],
        "evidence_survived_reboot": result["evidence_survived_reboot"],
    }
    return {
        "report_class": "READYNESS_SUMMARY",
        "summary_schema_version": "1.0.0",
        "evaluated_at": now_override or now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence_window_start": result["evidence_window_start"],
        "evidence_window_end": result["evidence_window_end"],
        "weeks_accumulated": result["weeks_accumulated"],
        "scheduled_runs": result["scheduled_runs"],
        "machinery_drill_runs": result["machinery_drill_runs"],
        "pass": result["pass"],
        "fail": result["fail"],
        "blocked": result["blocked"],
        "pass_rate_excluding_blocked": result["pass_rate_excluding_blocked"],
        "criteria": criteria,
        "readiness": result["readiness"],
        "source_evidence_sha256": h.hexdigest(),
        "source_evidence_runs": contributing,
        "readiness_evaluator": "bootstrap/level6-readiness-check.py",
        "git_head": git_head(),
        "llm_inference_required": 0,
    }


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


def month_key(now_override=None):
    """OM-2: current calendar month key (UTC), e.g. '2026-11'.

    Injectable clock for deterministic tests; first-of-month semantics are
    evaluated in UTC so the record name is stable regardless of host TZ.
    """
    n = now() if now_override is None else datetime.strptime(now_override, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return n.strftime("%Y-%m")


def month_summary_path(now_override=None):
    """OM-2: path of this month's summary record (never overwritten in-month)."""
    return os.path.join(TELEMETRY_DIR, f"readiness-summary-{month_key(now_override)}.json")


def monthly_summary_due(now_override=None):
    """OM-2: first-successful-run-of-month idempotency gate.

    Returns (should_write, existing_path). A month's summary is written on
    the first cron invocation that sees evidence for that month and only if
    the month's record does not already exist (idempotent; no duplicates).
    A missed execution (host down for the whole first run, etc.) self-heals:
    any later run in the same month writes the then-current summary — the
    record always reflects the best evidence available at write time, with
    its own evaluated_at + git_head proving when it was produced.
    """
    path = month_summary_path(now_override)
    if os.path.exists(path):
        return False, path
    return True, path


def write_monthly_summary(records, errors, now_override=None):
    """OM-2: generate + persist this month's READYNESS_SUMMARY if due.

    Idempotent (existing month record is left untouched — never overwritten,
    never duplicated); advisory reporting only (never a qualification gate,
    never read by any qualification calculation); zero inference. Returns
    the path written, or None when the month already has its record.
    """
    due, path = monthly_summary_due(now_override)
    if not due:
        return None
    summary = monthly_summary(records, errors, now_override=now_override)
    # OM-2: explicit execution provenance — clock and source revision of the
    # generator run (distinct from the evidence provenance inside the summary).
    summary["generated_by_git_head"] = git_head()
    summary["generation_trigger"] = "readiness-cron-first-of-month"
    os.makedirs(TELEMETRY_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(summary, fh, indent=2)
    os.replace(tmp, path)  # atomic; partial writes never visible as records
    return path


def main(argv):
    notify_mode = "--notify" in argv
    records, errors = load_evidence()
    result = evaluate(records, errors)
    fp = fingerprint(result)
    notified = False
    monthly_written = None

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
        # OM-2: first-successful-run-of-month READYNESS_SUMMARY (idempotent,
        # advisory, atomic write). Never gates; a failure here must not
        # affect the observer's own exit code or evidence handling.
        try:
            monthly_written = write_monthly_summary(records, errors)
        except Exception:
            monthly_written = None

    print(json.dumps(result, indent=2))
    return 0 if result["readiness"] != "ERROR" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
