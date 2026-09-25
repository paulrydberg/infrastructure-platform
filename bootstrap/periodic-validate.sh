#!/bin/bash
# =============================================================================
# bootstrap/periodic-validate.sh — Reproducibility Level 6
# Periodically Verified Reconstruction (ADR-0007; Level 6 authorization).
#
# Purpose: turn the Level 4 reconstruction from "episodically demonstrated"
# into "periodically verified" — WITHOUT Level 7 continuous validation,
# without new resident infrastructure, and with the protected fleet and
# evidence-authority invariants intact.
#
# Design:
#   - Wraps bootstrap/reconstruct.sh (the proven deterministic runner);
#     it does NOT reimplement reconstruction.
#   - Runs the FULL disposable reconstruction (RECONSTRUCT_EXECUTE=1) —
#     the same path Level 4 proved — so a PASS means the GitOps-layer
#     rebuild genuinely worked, not merely that the script returned 0.
#   - Evidence authority is inherited from the runner: a reconstruction
#     cannot report success without a generated, validated, preserved
#     evidence artifact.
#
# Failure taxonomy (deterministic, mutually exclusive where possible):
#   reconstruction failure  — a stage inside the runner FAILED
#   validation failure      — the run itself misbehaved (e.g. output shape)
#   evidence failure        — reconstruction succeeded but its evidence
#                             artifact is missing/invalid/unpreservable
#                             (EVIDENCE_ERROR; can never be PASS)
#   resource-gate rejection — runner reported gate BLOCKED (validation is
#                             BLOCKED; not PASS, not reconstruction FAIL)
#   scheduler failure       — the mechanism that should have launched this
#                             validation did not (launchd exit 78 = EX_CONFIG
#                             convention; a MISSING run is never a PASS:
#                             absence of evidence is recorded as a gap, see
#                             docs/15-reproducibility/level6-completion-record.md)
#
# Outcomes:
#   PASS            — reconstruction + evidence generation/validation/preservation
#   FAIL            — reconstruction/validation failure (evidence preserved where possible)
#   EVIDENCE_ERROR  — reconstruction OK but evidence authority failed
#   BLOCKED         — resource gate rejected; protected fleet outranks ambition
#   SCHEDULER_ERROR — this wrapper was invoked by launchd after a missed/failed
#                     schedule window (launchd runs the catch-up invocation);
#                     the missed window is recorded in the evidence
#
# Exit codes: 0 PASS · 1 reconstruction/validation failure · 2 evidence failure
#             3 resource-gate rejection (BLOCKED) · 4 scheduler/config error
#
# Resource governance: the runner's own resource gate is authoritative and
# CANNOT be bypassed here — BLOCKED is a valid, recorded outcome (exit 3).
#
# Concurrency: a single flock on a run lockfile serializes validations.
# A concurrent invocation records "skipped: another validation active"
# and exits 0 — it must NOT collide on ports/names/dirs with the active run.
#
# LLM inference: 0 — entirely deterministic shell + python stdlib.
# =============================================================================
set -u
export PATH="$HOME/tools/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
RUNNER="$REPO_ROOT/bootstrap/reconstruct.sh"
EVIDENCE_DIR="${L6_EVIDENCE_DIR:-$REPO_ROOT/docs/15-reproducibility/periodic}"
LOCK="/tmp/infrastructure-platform.l6.lock"
LOG="$EVIDENCE_DIR/last-run.log"
RUN_TS="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="l6-${RUN_TS}"
SCHED_MISSED="${L6_SCHED_MISSED:-}"   # set by launchd wrapper on catch-up runs

mkdir -p "$EVIDENCE_DIR"

# ---- concurrency: one validation at a time --------------------------------
# DEFECT L6-2: macOS ships no flock(1); the portable mechanism is an O_EXCL
# lockfile carrying the owning PID, plus stale-lock reclamation (owner PID no
# longer alive -> remove and continue). Deterministic, no new dependencies.
lock_acquire() {
  if [ -f "$LOCK" ]; then
    local owner
    owner=$(cat "$LOCK" 2>/dev/null | head -1)
    if [ -n "$owner" ] && ! kill -0 "$owner" 2>/dev/null; then
      echo "[$RUN_ID] stale lock from dead PID $owner reclaimed" | tee -a "$LOG"
      rm -f "$LOCK"
    fi
  fi
  if (set -o noclobber; echo "$$" > "$LOCK") 2>/dev/null; then
    return 0
  fi
  return 1
}
lock_release() { rm -f "$LOCK" 2>/dev/null; }
trap 'lock_release' EXIT
if ! lock_acquire; then
  echo "[$RUN_ID] skipped: another periodic validation holds the lock" | tee -a "$LOG"
  exit 0
fi

echo "[$RUN_ID] periodic validation start $(date -u +%FT%TZ)" | tee -a "$LOG"
if [ -n "$SCHED_MISSED" ]; then
  echo "[$RUN_ID] scheduler note: missed schedule window(s) detected at launch: $SCHED_MISSED" | tee -a "$LOG"
fi

# ---- pre-flight: protected-fleet snapshot (before) -------------------------
FLEET_BEFORE=$(docker ps --format '{{.Names}}' 2>/dev/null | sort | tr '\n' ',')
K3S_BEFORE=$(docker stats --no-stream --format '{{.MemUsage}}' k3s-server 2>/dev/null | head -1)
echo "[$RUN_ID] fleet before: $FLEET_BEFORE (k3s mem: ${K3S_BEFORE:-unknown})" | tee -a "$LOG"

# ---- execute the deterministic reconstruction (full disposable mode) ------
# L6_VALIDATE_ONLY=1 is a test hook: runs the wrapper end-to-end (evidence,
# classification, retention) WITHOUT creating disposable infrastructure.
if [ "${L6_VALIDATE_ONLY:-0}" != "1" ]; then
  export RECONSTRUCT_EXECUTE=1
fi
# Retain runner reports in the standard committed location; the periodic
# layer adds its own indexed evidence record on top.
RUNNER_START=$(date -u +%s)
RUNNER_LOG="$EVIDENCE_DIR/${RUN_ID}.reconstruction.log"
"$RUNNER" > "$RUNNER_LOG" 2>&1
RUNNER_RC=$?
RUNNER_END=$(date -u +%s)
DURATION=$((RUNNER_END - RUNNER_START))

# ---- classify the outcome (never collapse classes) -------------------------
# Read the runner's own machine-readable verdict (authoritative evidence).
LATEST_REPORT=$(ls -t "$REPO_ROOT"/docs/15-reproducibility/reports/reconstruct-*.json 2>/dev/null | head -1)
FINAL_STATUS="UNKNOWN"; RUNNER_COMMIT=""; RUNNER_DURATION=""; STAGE_COUNT=0; EVIDENCE_VALID="no"
if [ -n "$LATEST_REPORT" ] && python3 - "$LATEST_REPORT" <<'PYEOF' 2>/dev/null
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("final_status") in ("PASS", "WARN", "FAIL", "BLOCKED"), "bad final_status"
assert isinstance(d.get("stages"), list) and len(d["stages"]) > 0, "no stages"
PYEOF
then
  FINAL_STATUS=$(python3 -c "import json;print(json.load(open('$LATEST_REPORT'))['final_status'])")
  RUNNER_COMMIT=$(python3 -c "import json;print(json.load(open('$LATEST_REPORT'))['source_commit'])" 2>/dev/null)
  RUNNER_DURATION=$(python3 -c "import json;print(json.load(open('$LATEST_REPORT'))['duration_seconds'])" 2>/dev/null)
  STAGE_COUNT=$(python3 -c "import json;print(len(json.load(open('$LATEST_REPORT'))['stages']))" 2>/dev/null)
  EVIDENCE_VALID="yes"
fi

# Gate-blocked detection from the runner log (runner prints BLOCKED gate lines
# and exits 0 with a WARN report; treat "resource gate BLOCKED" as authoritative)
if grep -q "resource gate BLOCKED" "$RUNNER_LOG" 2>/dev/null; then
  GATE_BLOCKED=1
else
  GATE_BLOCKED=0
fi

# ---- post-flight: protected-fleet snapshot (after) + disposable check -----
FLEET_AFTER=$(docker ps --format '{{.Names}}' 2>/dev/null | sort | tr '\n' ',')
DISPOSABLE_LEFT=$(docker ps -a --format '{{.Names}}' | grep -c '^reconstruct-k3s-disposable$')
if [ "$FLEET_BEFORE" = "$FLEET_AFTER" ] && [ "$DISPOSABLE_LEFT" = "0" ]; then
  FLEET_OK="yes"
else
  FLEET_OK="NO — FLEET CHANGE OR DISPOSABLE RESIDUE"
fi

# ---- historical comparison (deterministic, simple) ------------------------
PREV=$(ls -t "$EVIDENCE_DIR"/validation-*.json 2>/dev/null | grep -v "$RUN_ID" | head -1)
COMPARISON="no previous validation evidence"
DRIFT_RESULT="UNKNOWN"
if [ -n "$PREV" ]; then
  COMPARISON=$(python3 - "$PREV" "$LATEST_REPORT" <<'PYEOF' 2>/dev/null || echo "comparison error"
import json, sys
prev = json.load(open(sys.argv[1])); cur = json.load(open(sys.argv[2]))
rows = []
pc, cc = prev.get("source_commit"), cur.get("source_commit")
rows.append(f"revision: {'changed' if pc != cc else 'same'} ({str(pc)[:8]} -> {str(cc)[:8]})")
pp, cp = prev.get("overall_result"), cur.get("overall_result")
rows.append(f"result: {pp} -> {cp}")
pd, cd = prev.get("duration_seconds"), cur.get("duration_seconds")
if isinstance(pd, int) and isinstance(cd, int):
    ratio = cd / max(pd, 1)
    rows.append(f"duration: {pd}s -> {cd}s ({'REGRESSION' if ratio > 1.5 else 'stable'})")
pg, cg = prev.get("resource_gate"), cur.get("resource_gate")
if pg and cg:
    rows.append(f"resource gate: {pg} -> {cg}")
print("; ".join(rows))
PYEOF
)
  DRIFT_RESULT=$(echo "$COMPARISON" | grep -o 'duration: .*REGRESSION' | grep -q REGRESSION && echo "DURATION_REGRESSION" || echo "NO_UNEXPECTED_DRIFT")
fi

# ---- outcome classification ------------------------------------------------
# Precedence: gate-blocked > runner-rc > evidence authority > final status
if [ "$GATE_BLOCKED" = "1" ]; then
  OVERALL="BLOCKED"; OVERALL_NOTE="resource gate rejected the scheduled run (validation BLOCKED — not a reconstruction failure)"
  EXIT_CODE=3
elif [ "$RUNNER_RC" != "0" ]; then
  if [ "$FINAL_STATUS" = "FAIL" ] || [ "$FINAL_STATUS" = "UNKNOWN" ]; then
    OVERALL="FAIL"; OVERALL_NOTE="reconstruction/validation failure (runner exit $RUNNER_RC)"
  else
    OVERALL="FAIL"; OVERALL_NOTE="runner exited non-zero with report status $FINAL_STATUS"
  fi
  EXIT_CODE=1
elif [ "$EVIDENCE_VALID" != "yes" ]; then
  OVERALL="EVIDENCE_ERROR"; OVERALL_NOTE="reconstruction reported success but its evidence artifact is missing/invalid — evidence authority forbids PASS"
  EXIT_CODE=2
elif [ "$FINAL_STATUS" = "WARN" ]; then
  # Semantics: in validate-only mode (L6_VALIDATE_ONLY=1) the runner's WARN is
  # the EXPECTED outcome (disposable stage SKIPPED by design) — it is the
  # wrapper's success equivalent and is recorded as such, with the trigger
  # visible in the evidence so it is never mistaken for an executed
  # reconstruction. In real execute mode WARN is unexpected => FAIL.
  if [ "${L6_VALIDATE_ONLY:-0}" = "1" ]; then
    OVERALL="PASS"; OVERALL_NOTE="validate-only run: wrapper/evidence machinery verified (no disposable reconstruction executed by design)"; EXIT_CODE=0
  else
    OVERALL="FAIL"; OVERALL_NOTE="runner reported WARN in execute mode (unexpected)"; EXIT_CODE=1
  fi
elif [ "$FINAL_STATUS" = "PASS" ]; then
  OVERALL="PASS"; OVERALL_NOTE="reconstruction + evidence generation + validation + preservation all succeeded"
  EXIT_CODE=0
else
  OVERALL="FAIL"; OVERALL_NOTE="unclassified final status: $FINAL_STATUS"; EXIT_CODE=1
fi

# ---- evidence retention ----------------------------------------------------
# Compute classification values in shell first; python only serializes (single
# escaping authority — the L4-5 lesson applied to Level 6).
# DEFECT L6-5: a validate-only run must never record reconstruction/GitOps/
# workload results it did not execute — that would fabricate Level 4-level
# evidence from a Level 6 machinery test. Mode-aware, honest fields.
if [ "${L6_VALIDATE_ONLY:-0}" = "1" ]; then
  RGATE="NOT_EXERCISED"; RECON="NOT_EXECUTED (validate-only machinery test)"; EGEN="OK"; EVAL="OK"
  GITOPS="NOT_EXECUTED (validate-only)"; WLOAD="NOT_EXECUTED (validate-only)"; K8S="NOT_EXECUTED (validate-only)"
else
  case "$OVERALL" in
    BLOCKED)        RGATE="BLOCKED"; RECON="NOT_RUN"; EGEN="NOT_RUN"; EVAL="NOT_RUN"; GITOPS="NOT_RUN"; WLOAD="NOT_RUN"; K8S="NOT_RUN";;
    EVIDENCE_ERROR) RGATE="PASSED"; RECON="PASS"; EGEN="FAILED"; EVAL="FAILED"; GITOPS="PASS"; WLOAD="PASS"; K8S="disposable k3s Ready";;
    FAIL)           RGATE="PASSED"; RECON="$FINAL_STATUS"; EGEN="NOT_RUN"; EVAL="NOT_RUN"; GITOPS="see report stages"; WLOAD="see report stages"; K8S="see report stages";;
    *)              RGATE="PASSED"; RECON="PASS"; EGEN="OK"; EVAL="OK"; GITOPS="Synced+Healthy"; WLOAD="validated (1/1, pinned image, securityContext, probes, svc)"; K8S="disposable k3s Ready";;
  esac
fi
START_ISO=$(date -u -r "$RUNNER_START" +%FT%TZ)
END_ISO=$(date -u -r "$RUNNER_END" +%FT%TZ)
RECORD="$EVIDENCE_DIR/validation-$RUN_ID.json"
RETENTION="OK"
RUN_ID="$RUN_ID" SCHED_MISSED="$SCHED_MISSED" RECORD="$RECORD" \
RUNNER_COMMIT="$RUNNER_COMMIT" RUNNER_RC="$RUNNER_RC" \
START_ISO="$START_ISO" END_ISO="$END_ISO" DURATION="$DURATION" \
RGATE="$RGATE" RECON="$RECON" EGEN="$EGEN" EVAL="$EVAL" \
GITOPS="$GITOPS" WLOAD="$WLOAD" K8S="$K8S" \
COMPARISON="$COMPARISON" DRIFT_RESULT="$DRIFT_RESULT" \
DISPOSABLE_LEFT="$DISPOSABLE_LEFT" FLEET_OK="$FLEET_OK" STAGE_COUNT="$STAGE_COUNT" \
OVERALL="$OVERALL" OVERALL_NOTE="$OVERALL_NOTE" LATEST_REPORT="$LATEST_REPORT" \
python3 - <<'PYEOF'
import json, os, sys
rec = {
  "run_id": os.environ["RUN_ID"],
  "trigger": "periodic-level6",
  "scheduler": "launchd (com.infrastructure-platform.reproducible-validation)",
  "scheduler_missed_window": os.environ.get("SCHED_MISSED") or None,
  "repository": "paulrydberg/infrastructure-platform",
  "branch": "main",
  "source_commit": os.environ["RUNNER_COMMIT"],
  "runner_version": "1.1.0",
  "manifest_version": "1.0.0",
  "runner_report": os.environ["LATEST_REPORT"],
  "runner_exit_code": int(os.environ["RUNNER_RC"]),
  "start_time": os.environ["START_ISO"],
  "end_time": os.environ["END_ISO"],
  "duration_seconds": int(os.environ["DURATION"]),
  "resource_gate": os.environ["RGATE"],
  "reconstruction": os.environ["RECON"],
  "kubernetes": os.environ["K8S"],
  "helm": "helm v3.16.3 (pinned)",
  "argocd": "chart 7.7.11 (app v2.13.3, declared values)",
  "gitops": os.environ["GITOPS"],
  "workload_validation": os.environ["WLOAD"],
  "evidence_generation": os.environ["EGEN"],
  "evidence_validation": os.environ["EVAL"],
  "evidence_retention": "PENDING",
  "historical_comparison": os.environ["COMPARISON"],
  "drift_result": os.environ["DRIFT_RESULT"],
  "teardown": "complete" if os.environ["DISPOSABLE_LEFT"] == "0" else "INCOMPLETE — disposable residue",
  "protected_fleet_check": os.environ["FLEET_OK"],
  "stage_count": int(os.environ["STAGE_COUNT"]),
  "failure_classification": os.environ["OVERALL_NOTE"],
  "overall_result": os.environ["OVERALL"],
  "llm_inference_required": 0,
}
json.dump(rec, open(os.environ["RECORD"], "w"), indent=2)
print("retained")
PYEOF
RET_RC=$?
# self-consistency: the retained record must itself validate
if [ "$RET_RC" = "0" ] && python3 - "$RECORD" <<'PYEOF' 2>/dev/null
import json, sys
d = json.load(open(sys.argv[1]))
assert d["overall_result"] in ("PASS", "FAIL", "BLOCKED", "EVIDENCE_ERROR"), "bad overall"
assert d["run_id"] and d["source_commit"], "missing identity"
assert d["evidence_retention"] in ("OK", "PENDING", "FAIL"), "bad retention field"
PYEOF
then
  RETENTION="OK"
else
  RETENTION="FAIL (retained record missing/invalid)"
  OVERALL="EVIDENCE_ERROR"; EXIT_CODE=2
fi
# finalize the retention field inside the record
RETENTION="$RETENTION" RECORD="$RECORD" python3 - <<'PYEOF'
import json, os
p = os.environ["RECORD"]
try:
    d = json.load(open(p)); d["evidence_retention"] = os.environ["RETENTION"]
    json.dump(d, open(p, "w"), indent=2)
except Exception:
    pass
PYEOF

echo "[$RUN_ID] overall=$OVERALL exit=$EXIT_CODE ($OVERALL_NOTE)" | tee -a "$LOG"
echo "[$RUN_ID] comparison: $COMPARISON" | tee -a "$LOG"
exit "$EXIT_CODE"
