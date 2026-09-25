#!/bin/bash
# Report-authority test suite (defect L4-6).
#
# Validates the evidence-authority invariant in bootstrap/reconstruct.sh:
#   reconstruction success AND report generation AND validation AND
#   preservation == PASS; any report-authority failure == FAIL + exit 1.
#
# Method: extract the REAL emit_report/report_validate functions from the
# runner into scratch scenario scripts and execute them — no Kubernetes, no
# Docker, no disposable infrastructure. Deterministic injected failures only.
set -u
RUNNER="$(cd "$(dirname "$0")" && pwd)/reconstruct.sh"
T="$(mktemp -d /tmp/report-authority-tests.XXXXXX)"
trap 'rm -rf "$T"' EXIT
PASS=0; FAILN=0
check() { # check <label> <actual> <expected>
  if [ "$2" = "$3" ]; then echo "PASS  $1"; PASS=$((PASS+1));
  else echo "FAIL  $1 (got '$2' want '$3')"; FAILN=$((FAILN+1)); fi
}

# Extract START_TS default + stage()/emit_report()/report_validate() functions.
awk '/^START_TS=/{f=1} /^# ---------- stage 1/{f=0} f' "$RUNNER" > "$T/funcs.sh"
bash -n "$T/funcs.sh" || { echo "FATAL: extracted runner functions invalid"; exit 9; }

# run_scenario <name> <final_status> <tsv> [poison] -> prints "EMIT_RC=<n> VAL_RC=<n>"
run_scenario() {
  local name="$1" status="$2" tsv="$3" poison="${4:-}"
  local dir="$T/$name"
  mkdir -p "$dir"
  local rdir="$dir"
  if [ "$poison" = "empty-dir" ]; then
    rdir="$dir/no-such-subdir"   # generation failure: nonexistent target dir
  fi
  local report="$rdir/reconstruct-test.json"
  rm -f "$report"
  cat > "$dir/scenario.sh" <<SCEOF
source "$T/funcs.sh"
START_TS=\$(date -u +%s)
export RECONSTRUCT_REPORT_DIR="$rdir"
export REPORT="$report"
export STAGES_TSV="$tsv"
emit_report '$status' >/dev/null 2>&1
echo "EMIT_RC=\$?"
if report_validate '$report' '$status' 2>/dev/null; then echo "VAL_RC=0"; else echo "VAL_RC=1"; fi
SCEOF
  local out
  out=$(bash "$dir/scenario.sh" 2>/dev/null)
  local erc vrc
  erc=$(echo "$out" | sed -n 's/.*EMIT_RC=\([0-9]*\).*/\1/p')
  vrc=$(echo "$out" | sed -n 's/.*VAL_RC=\([0-9]*\).*/\1/p')
  echo "$erc $vrc"
}

good_tsv="$T/good.tsv"
printf 'prerequisites\tPASS\tok\nsource\tPASS\tpin\nworkload\tPASS\t1/1\n' > "$good_tsv"

echo "== Test A: success + successful report =="
read -r a_emit a_val <<< "$(run_scenario a PASS "$good_tsv")"
check "A: emit_report exits 0" "$a_emit" "0"
check "A: report validates"    "$a_val" "0"
check "A: report artifact preserved" "$([ -s "$T/a/reconstruct-test.json" ] && echo yes || echo no)" "yes"
python3 -c "import json; d=json.load(open('$T/a/reconstruct-test.json')); assert d['final_status']=='PASS' and len(d['stages'])==3" 2>/dev/null
check "A: report content valid (status+stages)" "$?" "0"

echo "== Test B: success + report GENERATION failure =="
read -r b_emit b_val <<< "$(run_scenario b PASS "$good_tsv" empty-dir)"
if [ "$b_emit" != "0" ] || [ "$b_val" != "0" ]; then authority=fail; else authority=pass; fi
check "B: evidence authority = FAIL on generation failure" "$authority" "fail"

echo "== Test C: malformed report detected =="
mkdir -p "$T/c"
rv_scenario() { # rv_scenario <report> <expected> -> prints R=<0|1>
  cat > "$T/c/rv.sh" <<SCEOF
source "$T/funcs.sh"
if report_validate '$1' '$2' 2>/dev/null; then echo "R=0"; else echo "R=1"; fi
SCEOF
  bash "$T/c/rv.sh" 2>/dev/null | sed 's/R=//'
}
printf 'not json at all {{{' > "$T/c/reconstruct-test.json"
check "C: malformed report rejected by validation" "$(rv_scenario "$T/c/reconstruct-test.json" PASS)" "1"
printf '{"final_status": "PASS", "stages": [{"stage":"x","status":"PASS","detail":""}]}' > "$T/c/reconstruct-test.json"
check "C: status-mismatched report rejected (want FAIL, report says PASS)" "$(rv_scenario "$T/c/reconstruct-test.json" FAIL)" "1"
printf '{"final_status": null, "stages": []}' > "$T/c/reconstruct-test.json"
check "C: empty-stages/null-status report rejected" "$(rv_scenario "$T/c/reconstruct-test.json" PASS)" "1"

echo "== Test D: reconstruction failure + failure report preserved =="
read -r d_emit d_val <<< "$(run_scenario d FAIL "$good_tsv")"
check "D: FAIL report generates" "$d_emit" "0"
check "D: FAIL report validates as FAIL" "$d_val" "0"

echo "== Test E: preservation failure cannot become PASS =="
mkdir -p "$T/e"
printf '{"final_status": "PA' > "$T/e/reconstruct-test.json"
cat > "$T/e/scenario.sh" <<SCEOF
source "$T/funcs.sh"
if report_validate '$T/e/reconstruct-test.json' 'PASS' 2>/dev/null; then echo "R=0"; else echo "R=1"; fi
SCEOF
check "E: corrupted/preserved-bad report rejected" "$(bash "$T/e/scenario.sh" 2>/dev/null | sed 's/R=//')" "1"

echo "== RESULT: pass=$PASS fail=$FAILN =="
[ "$FAILN" = "0" ] && echo "REPORT-AUTHORITY TESTS: ALL PASS" || echo "REPORT-AUTHORITY TESTS: FAILURES PRESENT"
exit "$FAILN"
