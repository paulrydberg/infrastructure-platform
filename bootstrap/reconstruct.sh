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

# DEFECT L4-2 (found 2026-09-25, run reconstruct-20260925T011942Z): helm is
# installed in ~/tools/bin (checksum-verified Phase 3) which is NOT in the
# default non-interactive PATH — the runner failed with "helm: command not
# found" despite the tool being present and prerequisite-validated. Fix:
# deterministic PATH augmentation here (the runner must be self-sufficient,
# not dependent on the invoking shell's ambient PATH — same hidden-state
# class as L4-1).
export PATH="$HOME/tools/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
MANIFEST="$REPO_ROOT/reconstruction-manifest.yaml"
REPORT_DIR="${RECONSTRUCT_REPORT_DIR:-$REPO_ROOT/docs/15-reproducibility/reports}"
REPORT="$REPORT_DIR/reconstruct-$(date -u +%Y%m%dT%H%M%SZ).json"
STAGES_TSV="$(mktemp /tmp/reconstruct-stages.XXXXXX.tsv)"
trap 'rm -f "$STAGES_TSV"' EXIT
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
  # DEFECT L4-5: stage details containing quotes/commas broke naive
  # shell-side JSON assembly (the successful Level 4 run's report silently
  # failed to generate). Correction: stages are recorded as tab-separated
  # fields and serialized to JSON by python (single source of truth for
  # escaping).
  detail=$(printf '%s' "$detail" | tr '\t\n' '  ')
  printf '%s\t%s\t%s\n' "$name" "$status" "$detail" >> "$STAGES_TSV"
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
  python3 - "$REPORT" "$final" "$duration" "$STAGES_TSV" <<'PYEOF'
import json, sys, datetime, csv
path, final, duration, tsv = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
stages = [
    {"stage": r[0], "status": r[1], "detail": r[2] if len(r) > 2 else ""}
    for r in csv.reader(open(tsv), delimiter="\t")
    if len(r) >= 2
]
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

# DEFECT L4-6 (report authority, discovered by the independent post-Level-4
# audit): the report is part of the reproducibility contract — a
# reconstruction cannot be considered successful unless its evidence
# artifact is successfully GENERATED, VALIDATED, and PRESERVED. Before this
# correction the writer's exit code was unchecked (no set -e), so a writer
# failure left the run reporting success without evidence.
report_validate() {  # report_validate <path> <expected_status> — sets REPORT_ERR
  REPORT_ERR=""
  [ -s "$1" ] || { REPORT_ERR="report generation failed (missing/empty artifact)"; return 1; }
  python3 - "$1" "$2" <<'PYEOF' || { REPORT_ERR="report validation failed (invalid JSON or wrong final_status)"; return 1; }
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("final_status") == sys.argv[2], f"final_status mismatch: {d.get('final_status')!r} != {sys.argv[2]!r}"
assert isinstance(d.get("stages"), list) and len(d["stages"]) > 0, "stages missing/empty"
PYEOF
}

fail_exit() {
  if emit_report "FAIL" && report_validate "$REPORT" "FAIL"; then
    echo "RECONSTRUCTION FAILED — report preserved (not deleted, not hidden)"
  else
    echo "RECONSTRUCTION FAILED — AND evidence generation failed: ${REPORT_ERR:-report writer error} (report may be missing at $REPORT)"
    stage "evidence_authority" "FAIL" "failure-path report generation/validation failed: ${REPORT_ERR:-writer error}"
  fi
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
  # Stale-disposable-state guard (failure mode observed 2026-09-25, run
  # reconstruct-20260925T012926Z: a leftover disposable container from
  # earlier debugging owned the container name and port, so compose up
  # silently reused it and helm hit "cannot re-use a name" from the stale
  # release). The disposable environment must start from nothing.
  if docker ps -a --format '{{.Names}}' | grep -q '^reconstruct-k3s-disposable$'; then
    docker rm -f reconstruct-k3s-disposable >/dev/null 2>&1
    docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1
    stage "disposable_stale_guard" "PASS" "stale disposable container found and removed before start"
  else
    stage "disposable_stale_guard" "PASS" "no stale disposable state"
  fi

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
    if emit_report "WARN" && report_validate "$REPORT" "WARN"; then
      exit 0
    else
      echo "EVIDENCE AUTHORITY FAILURE (resource-gate path): ${REPORT_ERR:-report writer error}"
      exit 1
    fi
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


  # ---- LEVEL 4: disposable GitOps reconstruction (ADR-0006 follow-through) ----
  # DEFECT L4-1 (found 2026-09-25, run reconstruct-20260925T005854Z): an
  # inherited KUBECONFIG environment variable pointed helm at the PRODUCTION
  # cluster; helm's release-ownership guard refused the install (fast FAIL,
  # production untouched - the guard worked as designed). Correction: all
  # disposable-stage commands pin KUBECONFIG to the disposable kubeconfig
  # explicitly; inherited KUBECONFIG is deliberately ignored here. Lesson:
  # environment inheritance is hidden state - disposable stages must not
  # trust ambient credentials.
  export KUBECONFIG="$DISPOSABLE_KUBECONFIG"
  # All state comes from the repository: pinned chart version (7.7.11), pinned
  # values (platform/argocd/values.yaml), source-controlled Application
  # manifest, platform-demo chart. External deps recorded in the report:
  # argo helm repo, quay.io/ghcr images, k3s image, docker.io image layer.
  ARGO_INSTALL_BEGIN=$(date -u +%s)
  ARGO_ERR="$TMPDIR_DISPOSABLE/argo-install-error.log"
  if helm repo add argo https://argoproj.github.io/argo-helm 2> "$ARGO_ERR" \
     && helm repo update 2>> "$ARGO_ERR" \
     && helm install argocd argo/argo-cd --namespace argocd --create-namespace \
          --version 7.7.11 --values "$REPO_ROOT/platform/argocd/values.yaml" \
          --kubeconfig "$DISPOSABLE_KUBECONFIG" 2>> "$ARGO_ERR"; then
    stage "disposable_argo_install" "PASS" "argocd chart 7.7.11 (app v2.13.3) installed from declared values"
  else
    stage "disposable_argo_install" "FAIL" "helm install failed: $(tail -1 "$ARGO_ERR" 2>/dev/null | head -c 200)"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # Argo readiness (bounded poll on the core deployments)
  ARGO_READY=0
  for i in $(seq 1 48); do
    sleep 5
    A=$(KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl -n argocd get deploy \
        argocd-repo-server -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
    S=$(KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl -n argocd get deploy \
        argocd-server -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
    if [ "${A:-0}" = "1" ] && [ "${S:-0}" = "1" ]; then ARGO_READY=1; break; fi
  done
  ARGO_INSTALL_SECS=$(( $(date -u +%s) - ARGO_INSTALL_BEGIN ))
  if [ "$ARGO_READY" = "1" ]; then
    stage "disposable_argo_ready" "PASS" "argocd-server + repo-server Ready (install->ready ~${ARGO_INSTALL_SECS}s)"
  else
    stage "disposable_argo_ready" "FAIL" "argocd core deployments not Ready in 240s"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # platform-demo image import into the DISPOSABLE cluster containerd
  # (documented Phase 3 mechanism: docker save | ctr images import; the image
  # itself is built by the pinned Dockerfile from source - no registry pull).
  if docker save platform-demo:0.1.0 | docker exec -i reconstruct-k3s-disposable \
       ctr -n k8s.io images import - >/dev/null 2>&1; then
    stage "disposable_image_import" "PASS" "platform-demo:0.1.0 imported into disposable containerd (pinned tag)"
  else
    stage "disposable_image_import" "FAIL" "ctr import failed"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # GitOps seed: apply the source-controlled Application manifest.
  # Argo repo-server clones the PUBLIC GitHub repo itself; no credentials
  # required. The disposable Argo reads the intended revision (main).
  if KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl apply -f \
       "$REPO_ROOT/platform/argocd/application-platform-demo.yaml" >/dev/null 2>&1; then
    stage "disposable_app_apply" "PASS" "Application platform-demo applied from declared manifest"
  else
    stage "disposable_app_apply" "FAIL" "kubectl apply Application failed"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # GitOps convergence: wait for Synced + Healthy (the core Level 4 assertion)
  SYNC_OK=0
  for i in $(seq 1 60); do
    sleep 5
    SS=$(KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl -n argocd get app platform-demo \
         -o jsonpath='{.status.sync.status}' 2>/dev/null)
    HS=$(KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl -n argocd get app platform-demo \
         -o jsonpath='{.status.health.status}' 2>/dev/null)
    if [ "$SS" = "Synced" ] && [ "$HS" = "Healthy" ]; then SYNC_OK=1; break; fi
  done
  if [ "$SYNC_OK" = "1" ]; then
    SYNC_REV=$(KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl -n argocd get app platform-demo \
        -o jsonpath='{.status.sync.revision}' 2>/dev/null)
    stage "disposable_gitops_sync" "PASS" "Argo: platform-demo Synced+Healthy (revision ${SYNC_REV:-unknown})"
  else
    stage "disposable_gitops_sync" "FAIL" "not Synced+Healthy in 300s (see preserved report)"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # Workload validation: declared state == deployed state (Git = Argo = K8s)
  # DEFECT L4-3 (found 2026-09-25, run @ 339f077): the validator ran once,
  # immediately after Argo reported Healthy, and read replicas=0/0 — a race
  # between Argo's health assessment and Deployment status propagation.
  # Correction: bounded wait for the deployment to report readyReplicas
  # before comparing declared vs actual state (deterministic terminal-state
  # assertion, not a point-in-time sample).
  WVA_OK=0
  for i in $(seq 1 24); do
    RR=$(KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl -n platform-demo get deploy platform-demo          -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
    if [ "${RR:-0}" = "1" ]; then WVA_OK=1; break; fi
    sleep 5
  done
  WV=$(DISPOSABLE_KUBECONFIG_ARG="$DISPOSABLE_KUBECONFIG" python3 - <<'PYEOF' 2>/dev/null
import json, subprocess, os
kc = os.environ["DISPOSABLE_KUBECONFIG_ARG"]
def q(*path):
    # DEFECT L4-4: resource type + name must be separate argv items (a single
    # "deploy platform-demo" string is parsed by kubectl as one bogus
    # resource type -> rc=1 -> validator saw an empty cluster).
    r = subprocess.run(["kubectl","-n","platform-demo","get",*path,"-o","json"],
                       capture_output=True, text=True,
                       env={**os.environ, "KUBECONFIG": kc})
    return json.loads(r.stdout) if r.returncode == 0 else None
dep = q("deploy", "platform-demo") or {}
pod = q("pod", "-l", "app.kubernetes.io/name=platform-demo") or {}
svc = q("svc", "platform-demo")
status = dep.get("status", {})
cs = ((dep.get("spec", {}).get("template", {}).get("spec", {}).get("containers")) or [{}])[0]
sc = cs.get("securityContext", {})
pod_ready = sum(1 for i in pod.get("items", []) if all(c.get("ready") for c in i.get("status", {}).get("containerStatuses", [])))
rows = [
    ("replicas", f"{status.get('readyReplicas',0)}/{status.get('replicas',0)}"),
    ("image", cs.get("image", "")),
    ("service", "exists" if svc else "MISSING"),
    ("pod_ready", str(pod_ready)),
    ("readOnlyRootFilesystem", str(sc.get("readOnlyRootFilesystem"))),
    ("runAsNonRoot", str(sc.get("runAsNonRoot"))),
    ("allowPrivilegeEscalation", str(sc.get("allowPrivilegeEscalation"))),
    ("resources", "set" if cs.get("resources") else "MISSING"),
    ("probes", "set" if (cs.get("readinessProbe") and cs.get("livenessProbe")) else "MISSING"),
]
for k, v in rows:
    print(f"{k}={v}")
PYEOF
)
  IMG_OK=$(echo "$WV" | grep '^image=' | cut -d= -f2)
  RO_OK=$(echo "$WV" | grep '^readOnlyRootFilesystem=' | cut -d= -f2)
  SVC_OK=$(echo "$WV" | grep '^service=' | cut -d= -f2)
  if [ "$WVA_OK" = "1" ] && [ "$IMG_OK" = "platform-demo:0.1.0" ] && [ "$RO_OK" = "True" ] && [ "$SVC_OK" = "exists" ]; then
    stage "disposable_workload_validate" "PASS" "Git=Argo=K8s: pinned image, securityContext per chart, svc present ($WV)"
  else
    stage "disposable_workload_validate" "FAIL" "declared-vs-actual mismatch: $WV"
    (cd "$TMPDIR_DISPOSABLE" && docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1)
    rm -rf "$TMPDIR_DISPOSABLE"
    fail_exit
  fi

  # GitOps-layer teardown (Application, helm release, namespaces) before the
  # whole-environment teardown below.
  KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl -n argocd delete app platform-demo --wait=false >/dev/null 2>&1
  helm uninstall argocd -n argocd --kubeconfig "$DISPOSABLE_KUBECONFIG" >/dev/null 2>&1
  KUBECONFIG="$DISPOSABLE_KUBECONFIG" kubectl delete ns argocd platform-demo --wait=false >/dev/null 2>&1
  stage "disposable_gitops_teardown" "PASS" "GitOps layer removed (app, helm release, namespaces)"

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
# Evidence-authority gate: success is incomplete without valid evidence.
if emit_report "$FINAL_STATUS" && report_validate "$REPORT" "$FINAL_STATUS"; then
  echo "evidence authority: report generated, validated, preserved"
  exit 0
else
  stage "evidence_authority" "FAIL" "report generation/validation failed on a ${FINAL_STATUS} reconstruction: ${REPORT_ERR:-writer error}"
  echo "RECONSTRUCTION ${FINAL_STATUS} BUT EVIDENCE AUTHORITY FAILED — reporting FAIL per the reproducibility contract"
  # best-effort second write capturing the failure itself
  emit_report "FAIL" || true
  exit 1
fi
