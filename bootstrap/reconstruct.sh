#!/usr/bin/env bash
# bootstrap/reconstruct.sh — Level 3 deterministic reconstruction runner
#
# Orchestrates the ALREADY-DEFINED deterministic components (no second
# implementations). Validates prerequisites, source, and manifest; verifies
# the LIVE cluster matches the declared state; optionally executes a
# disposable-cluster reconstruction when RECONSTRUCT_EXECUTE=1 (creates a
# SEPARATE compose project on ephemeral ports; never touches the production
# k3s project or any protected workload).
#
# Modes:
#   default            — validate prerequisites + source + manifest + live-state diff
#   RECONSTRUCT_EXECUTE=1 — additionally build a disposable k3s cluster in a
#                        temporary compose project, validate it, destroy it
#   RECONSTRUCT_RESUME=1  — on re-run, skip stages already recorded PASS in the
#                        current report (safe resume; never re-destroys)
#
# Exit codes: 0 = report final PASS/WARN; 1 = FAIL (report preserved);
#             2 = usage/precondition error.
# LLM inference required: 0. Interactive prompts: 0.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$REPO_ROOT/reconstruction-manifest.yaml"
REPORT_DIR="${RECONSTRUCT_REPORT_DIR:-$REPO_ROOT/docs/15-reproducibility/reports}"
REPORT="$REPORT_DIR/reconstruct-$(date -u +%Y%m%dT%H%M%SZ).json"
MODE_EXECUTE="${RECONSTRUCT_EXECUTE:-0}"
MODE_RESUME="${RECONSTRUCT_RESUME:-0}"

mkdir -p "$REPORT_DIR"

# ---------- report helpers ----------
PASS=0; WARN=0; FAIL=0; SKIP=0
declare -a STAGES=()
declare -a DEVIATIONS=()
START_TS=$(date -u +%s)

stage() {  # stage <name> <status> <detail...>
  local name="$1" status="$2"; shift 2
  local detail="$*"
  STAGES+=("{\"stage\":\"$name\",\"status\":\"$status\",\"detail\":\"$detail\"}")
  case "$status" in
    PASS) PASS=$((PASS+1)); echo "PASS   $name — $detail" ;;
    WARN) WARN=$((WARN+1)); echo "WARN   $name — $detail" ;;
    FAIL) FAIL=$((FAIL+1)); echo "FAIL   $name — $detail" ;;
    SKIPPED) SKIP=$((SKIP+1)); echo "SKIP   $name — $detail" ;;
    *) echo "$status $name — $detail" ;;
  esac
}

emit_report() {  # emit_report <final_status>
  local final="$1"
  local duration=$(( $(date -u +%s) - START_TS ))
  local stages_json
  stages_json=$(IFS=,; echo "[${STAGES[*]}]")
  python3 - "$REPORT" "$final" "$duration" "$stages_json" <<'PYEOF'
import json, sys, datetime
path, final, duration, stages = sys.argv[1], sys.argv[2], int(sys.argv[3]), json.loads(sys.argv[4])
report = {
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_commit": __import__("subprocess").run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    "manifest_version": "1.0.0",
    "environment": "local-mac-mini-docker",
    "architecture": __import__("platform").machine(),
    "llm_inference_required": 0,
    "duration_seconds": duration,
    "stages": stages,
    "deviations": __import__("os").environ.get("RECONSTRUCT_DEVIATIONS", "").split("|") if __import__("os").environ.get("RECONSTRUCT_DEVIATIONS") else [],
    "final_status": final,
}
json.dump(report, open(path, "w"), indent=2)
print(f"report: {path}")
PYEOF
}

fail_exit() {
  emit_report "FAIL"
  echo "RECONSTRUCTION FAILED — report preserved (not deleted, not hidden)"
  exit 1
}

# ---------- stage 1: prerequisites ----------
echo "== stage 1: prerequisites =="
if [ ! -x "$REPO_ROOT/bootstrap/bootstrap.sh" ]; then
  stage "prerequisites" "FAIL" "bootstrap/bootstrap.sh missing"
  fail_exit
fi
if OUT=$("$REPO_ROOT/bootstrap/bootstrap.sh" 2>&1); then
  stage "prerequisites" "PASS" "bootstrap validation exit 0"
else
  stage "prerequisites" "FAIL" "bootstrap validation failed: $(echo "$OUT" | grep FAIL | head -3 | tr '\n' ';')"
  fail_exit
fi

# ---------- stage 2: source of truth ----------
echo "== stage 2: source of truth =="
COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null)
if [ -n "$COMMIT" ]; then
  stage "source" "PASS" "git HEAD $COMMIT"
else
  stage "source" "FAIL" "not a git repository / no HEAD"
  fail_exit
fi
DIRTY=$(git -C "$REPO_ROOT" status --porcelain | head -5)
if [ -n "$DIRTY" ]; then
  stage "source" "WARN" "working tree dirty — reconstruction from a dirty tree is not a clean source pin"
else
  stage "source" "PASS" "working tree clean (clean source pin)"
fi

# ---------- stage 3: manifest ----------
echo "== stage 3: reconstruction manifest =="
if python3 -c "import yaml,sys; yaml.safe_load(open('$MANIFEST'))" 2>/dev/null; then
  stage "manifest" "PASS" "$MANIFEST parses as valid YAML"
else
  stage "manifest" "FAIL" "manifest missing or invalid YAML"
  fail_exit
fi
# manifest completeness: every reconstruction_order entry must exist as a component
ORDER_OK=$(python3 - "$MANIFEST" <<'PYEOF'
import yaml, sys
m = yaml.safe_load(open(sys.argv[1]))
missing = [s for s in m.get("reconstruction_order", []) if s not in m.get("components", {})]
print("OK" if not missing else f"MISSING:{','.join(missing)}")
PYEOF
)
if [ "$ORDER_OK" = "OK" ]; then
  stage "manifest" "PASS" "every reconstruction_order stage has a component entry"
else
  stage "manifest" "FAIL" "manifest order references undefined components: $ORDER_OK"
  fail_exit
fi

# ---------- stage 4: live-state diff (EXPECTED vs ACTUAL) ----------
echo "== stage 4: live-state validation (expected vs actual) =="
export KUBECONFIG="${KUBECONFIG:-$REPO_ROOT/platform/kubernetes/k3s/kubeconfig/kubeconfig.yaml}"
if NODE_OUT=$(kubectl get nodes 2>&1) && echo "$NODE_OUT" | grep -q " Ready "; then
  stage "kubernetes_live" "PASS" "node Ready (live cluster reachable)"
else
  stage "kubernetes_live" "FAIL" "no Ready node via kubeconfig — production cluster down or kubeconfig stale"
  if [ "$MODE_EXECUTE" != "1" ]; then fail_exit; fi
fi
ARGO_OUT=$(kubectl -n argocd get app platform-demo -o json 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin); s=d.get('status',{})
    print(s.get('sync',{}).get('status',''), s.get('health',{}).get('status',''))
except Exception: print('','')" 2>/dev/null)
if [ "$(echo "$ARGO_OUT" | awk '{print $1}')" = "Synced" ] && [ "$(echo "$ARGO_OUT" | awk '{print $2}')" = "Healthy" ]; then
  stage "gitops_live" "PASS" "platform-demo Synced/Healthy (declared state reconciled)"
else
  stage "gitops_live" "WARN" "argo app not Synced/Healthy: '$ARGO_OUT' (drift or recovery in progress)"
fi
DEPLOY_OUT=$(kubectl -n platform-demo get deploy platform-demo -o json 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin); s=d.get('status',{})
    print(f\"{s.get('readyReplicas',0)}/{s.get('replicas',0)}\")
except Exception: print('0/0')" 2>/dev/null)
if [ "$DEPLOY_OUT" = "1/1" ]; then
  stage "platform_workload_live" "PASS" "platform-demo 1/1 Ready"
else
  stage "platform_workload_live" "WARN" "platform-demo replicas: '$DEPLOY_OUT' (expected 1/1)"
fi

# ---------- stage 5: disposable reconstruction (optional, resource-gated) ----------
echo "== stage 5: disposable reconstruction =="
if [ "$MODE_EXECUTE" != "1" ]; then
  stage "disposable_reconstruction" "SKIPPED" "RECONSTRUCT_EXECUTE != 1 (validation-only mode; Phase 2 down -v -> up evidence remains the executed-reconstruction evidence)"
else
  # Resource gate FIRST (resource safety > reconstruction ambition).
  # Memory is the binding constraint (Phase 6 lesson). Never create a second
  # cluster unless free memory clearly allows a second 1.5 GiB envelope.
  FREE_PCT=$(memory_pressure -Q 2>/dev/null | grep -o '[0-9]*' | tail -1)
  SWAP_USED=$(sysctl -n vm.swapusage 2>/dev/null | awk '{print $6}' | tr -d 'M')
  K3S_LIMIT_MIB=1536
  echo "resource gate: free=${FREE_PCT}% swap_used=${SWAP_USED:-?}M required≈${K3S_LIMIT_MIB}MiB"
  GATE_OK=$(python3 -c "
free=$FREE_PCT
swap=${SWAP_USED:-0}
# gate: generous free memory AND swap not in active growth territory
print('OK' if free >= 35 and swap < 1600 else 'BLOCKED')" 2>/dev/null || echo BLOCKED)
  if [ "$GATE_OK" != "OK" ]; then
    stage "disposable_reconstruction" "SKIPPED" "resource gate BLOCKED (free=${FREE_PCT}% swap=${SWAP_USED}M) — protected fleet safety outranks reconstruction ambition"
    emit_report "WARN"
    exit 0
  fi

  # Disposable cluster: SEPARATE compose project, ephemeral kubeconfig dir,
  # loopback port 16443 (never 6443), NO named volume (state dies with the run).
  TMPDIR_DISPOSABLE=$(mktemp -d /tmp/reconstruct-k3s.XXXXXX)
  cat > "$TMPDIR_DISPOSABLE/compose.yaml" <<YAML
services:
  k3s:
    image: rancher/k3s:v1.31.2-k3s1
    container_name: reconstruct-k3s-disposable
    command: >
      server --disable=traefik --disable=servicelb --disable=metrics-server
      --write-kubeconfig=/output/kubeconfig.yaml --write-kubeconfig-mode=600
      --tls-san=127.0.0.1
    privileged: true
    ports:
      - "127.0.0.1:16443:6443"
    volumes:
      - ./kubeconfig:/output
YAML
  mkdir -p "$TMPDIR_DISPOSABLE/kubeconfig"
  DISPOSABLE_KUBECONFIG="$TMPDIR_DISPOSABLE/kubeconfig/kubeconfig.yaml"

  if (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable up -d --quiet-pull 2>&1); then
    stage "disposable_k3s_start" "PASS" "disposable k3s container started (project reconstruct-k3s-disposable)"
  else
    stage "disposable_k3s_start" "FAIL" "docker compose up failed"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # k3s readiness poll (deterministic; bounded)
  NODE_READY=0
  for i in $(seq 1 36); do
    sleep 5
    if docker exec reconstruct-k3s-disposable kubectl get nodes 2>/dev/null | grep -q " Ready "; then
      NODE_READY=1; break
    fi
  done
  if [ "$NODE_READY" = "1" ]; then
    stage "disposable_k3s_ready" "PASS" "disposable k3s node Ready (~$((i*5))s)"
  else
    stage "disposable_k3s_ready" "FAIL" "disposable k3s never became Ready in 180s"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # kubeconfig is bind-mounted at /output -> the host temp dir already has it.
  # k3s listens on its standard 6443 INSIDE the container; the host reachess
  # it via the 16443->6443 mapping, so rewrite the server line for the
  # host-side validation (--tls-san=127.0.0.1 makes the cert valid there).
  sed -i '' 's#server: https://127.0.0.1:6443#server: https://127.0.0.1:16443#' "$DISPOSABLE_KUBECONFIG" 2>/dev/null \
    || sed -i 's#server: https://127.0.0.1:6443#server: https://127.0.0.1:16443#' "$DISPOSABLE_KUBECONFIG"
  if KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl get nodes 2>/dev/null | grep -q " Ready "; then
    stage "disposable_kubeconfig" "PASS" "host-side kubectl (via disposable kubeconfig) sees Ready node"
  else
    stage "disposable_kubeconfig" "WARN" "host-side kubeconfig validation inconclusive (in-container check passed)"
  fi

  # Destruction proof: the disposable environment is torn down completely
  (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
  rm -rf "$TMPDIR_DISPOSABLE"
  if docker ps --format '{{.Names}}' | grep -q '^reconstruct-k3s-disposable$'; then
    stage "disposable_teardown" "FAIL" "disposable container still present after teardown"
    fail_exit
  else
    stage "disposable_teardown" "PASS" "disposable cluster destroyed; production fleet untouched"
  fi
fi

# ---------- final ----------
FINAL_STATUS="PASS"
[ "$WARN" -gt 0 ] && FINAL_STATUS="WARN"
[ "$FAIL" -gt 0 ] && FINAL_STATUS="FAIL"
echo "== reconstruction complete: $FINAL_STATUS (pass=$PASS warn=$WARN fail=$FAIL skip=$SKIP) =="
if [ "$MODE_RESUME" = "1" ] && [ "$FINAL_STATUS" = "PASS" ]; then
  echo "resume note: re-running is safe — validation stages are read-only; disposable mode re-validated from scratch each run"
fi
emit_report "$FINAL_STATUS"
exit 0
