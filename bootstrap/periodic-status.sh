#!/bin/bash
# =============================================================================
# bootstrap/periodic-status.sh — Level 6 scheduler-failure visibility
#
# The scheduler must not become a hidden dependency (§5/§14): a MISSING run is
# NOT a successful reconstruction. This read-only checker inspects the
# periodic evidence directory and answers "when did validation last actually
# execute, and is it overdue?" — the mechanism by which scheduler outage
# becomes a visible, classifiable condition (SCHEDULER_ERROR) rather than
# silence.
#
# Deterministic; exit codes:
#   0 healthy (last validation within the expected window and PASS/BLOCKED)
#   1 OVERDUE — no validation within max_age (scheduler may be failing)
#   2 STALE-NEVER-RUN — no evidence exists at all
#   3 last validation FAILED / EVIDENCE_ERROR (reconstruction/evidence problem)
# =============================================================================
set -u
export PATH="$HOME/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVIDENCE_DIR="${L6_EVIDENCE_DIR:-$REPO_ROOT/docs/15-reproducibility/periodic}"
# Twice-weekly schedule => anything older than 10 days is overdue
MAX_AGE_DAYS="${L6_MAX_AGE_DAYS:-10}"

if ! ls "$EVIDENCE_DIR"/validation-*.json >/dev/null 2>&1; then
  echo "SCHEDULER_ERROR: no periodic validation evidence exists — the scheduler has never successfully invoked the validation (a missing run is NOT a PASS)"
  exit 2
fi

LATEST=$(ls -t "$EVIDENCE_DIR"/validation-*.json | head -1)
python3 - "$LATEST" "$MAX_AGE_DAYS" <<'PYEOF'
import json, os, sys, datetime
p, max_age = sys.argv[1], int(sys.argv[2])
d = json.load(open(p))
age_days = (datetime.datetime.now(datetime.timezone.utc) -
            datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc)).days
print(f"last validation: {d['run_id']} at {d['start_time']} overall={d['overall_result']} age={age_days}d")
print(f"scheduler window: max {max_age}d")
if age_days > max_age:
    print("SCHEDULER_ERROR: last validation is OVERDUE — the scheduler has not produced evidence within the expected window")
    sys.exit(1)
if d["overall_result"] in ("FAIL", "EVIDENCE_ERROR"):
    print("VALIDATION_PROBLEM: last validation did not succeed (see its evidence record)")
    sys.exit(3)
print("OK: periodic validation is current and its last outcome was PASS or BLOCKED")
PYEOF
exit $?
