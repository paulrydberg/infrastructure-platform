#!/bin/bash
# Level 4 failure tests A/B/C + recovery — disposable working-copy method.
# Method: the failure conditions are injected into a THROWAWAY copy of the
# Application manifest (failure B/C) or via a bogus helm values override
# (failure A); the committed source on main is never modified. The known-good
# state is then restored and reconciliation re-verified (recovery test).
set -u
export PATH="$HOME/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# repo root (defect L4-FT-1: dirname "$0" alone put the script in bootstrap/,
# so every repo-relative path was one level deep and the whole suite ran
# against wrong inputs — preserved as failed-run evidence)
cd "$(dirname "$0")/.."
KCFG=/tmp/l4ft/kubeconfig/kubeconfig.yaml
PASS=0; FAIL=0
note() { echo "$1"; }
assert_eq() { # assert_eq <label> <actual> <expected>
  if [ "$2" = "$3" ]; then note "PASS  $1 (=$3)"; PASS=$((PASS+1));
  else note "FAIL  $1 (got '$2' want '$3')"; FAIL=$((FAIL+1)); fi
}

echo "== setup: disposable cluster via runner machinery =="
rm -rf /tmp/l4ft; mkdir -p /tmp/l4ft/kubeconfig
cat > /tmp/l4ft/compose.yaml <<'YAML'
services:
  k3s:
    image: rancher/k3s:v1.31.2-k3s1
    container_name: reconstruct-k3s-disposable
    command: server --disable=traefik --disable=servicelb --disable=metrics-server --write-kubeconfig=/output/kubeconfig.yaml --write-kubeconfig-mode=600 --tls-san=127.0.0.1
    privileged: true
    ports:
      - "127.0.0.1:16443:6443"
    volumes:
      - ./kubeconfig:/output
YAML
(cd /tmp/l4ft && docker compose -p reconstruct-k3s-disposable up -d --quiet-pull >/dev/null 2>&1)
# stale disposable state guard (same lesson as the runner)
if docker ps -a --format '{{.Names}}' | grep -q '^reconstruct-k3s-disposable$'; then
  docker rm -f reconstruct-k3s-disposable >/dev/null 2>&1
  docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1
  sleep 3
fi
# bounded 300s readiness poll (observed: k3s can take >120s when Docker is
# still releasing the previous disposable run's port)
for i in $(seq 1 60); do sleep 5; if KUBECONFIG=$KCFG kubectl get nodes 2>/dev/null | grep -q ' Ready '; then break; fi; done
sed -i '' 's#server: https://127.0.0.1:6443#server: https://127.0.0.1:16443#' $KCFG 2>/dev/null
assert_eq "disposable k3s Ready" "$(KUBECONFIG=$KCFG kubectl get nodes 2>/dev/null | grep -c ' Ready ')" "1"
if [ "$(KUBECONFIG=$KCFG kubectl get nodes 2>/dev/null | grep -c ' Ready ')" != "1" ]; then
  echo "SETUP FAILED — cluster never became Ready; aborting (no bogus verdicts)"; exit 9
fi

helm repo add argo https://argoproj.github.io/argo-helm >/dev/null 2>&1
helm install argocd argo/argo-cd --namespace argocd --create-namespace --version 7.7.11 \
  --values "$PWD/platform/argocd/values.yaml" --kubeconfig "$KCFG" >/dev/null 2>&1
for i in $(seq 1 48); do sleep 5
  A=$(KUBECONFIG=$KCFG kubectl -n argocd get deploy argocd-repo-server -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
  S=$(KUBECONFIG=$KCFG kubectl -n argocd get deploy argocd-server -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
  [ "${A:-0}" = "1" ] && [ "${S:-0}" = "1" ] && break; done
assert_eq "argocd ready" "$A/$S" "1/1"
docker save platform-demo:0.1.0 | docker exec -i reconstruct-k3s-disposable ctr -n k8s.io images import - >/dev/null 2>&1

echo "== FAILURE TEST B: invalid source path in Application =="
sed 's#path: platform/helm/platform-demo#path: platform/helm/does-not-exist#' \
  platform/argocd/application-platform-demo.yaml > /tmp/l4ft/app-bad-path.yaml
KUBECONFIG=$KCFG kubectl apply -f /tmp/l4ft/app-bad-path.yaml >/dev/null 2>&1
B_SYNC=""; for i in $(seq 1 24); do sleep 5
  B_SYNC=$(KUBECONFIG=$KCFG kubectl -n argocd get app platform-demo -o jsonpath='{.status.sync.status}' 2>/dev/null)
  [ "$B_SYNC" = "Error" ] || [ "$B_SYNC" = "Unknown" ] && break; done
B_COND=$(KUBECONFIG=$KCFG kubectl -n argocd get app platform-demo -o jsonpath='{.status.conditions[?(@.type=="ComparisonError")].message}' 2>/dev/null | head -c 80)
note "observed: sync=$B_SYNC condition='$B_COND'"
assert_eq "B: Argo does NOT report Synced for invalid path (sync=$B_SYNC)" \
  "$([ "$B_SYNC" != "Synced" ] && echo yes)" "yes"

echo "== RECOVERY (restore known-good Application from Git) =="
RECOVER_BEGIN=$(date -u +%s)
KUBECONFIG=$KCFG kubectl apply -f platform/argocd/application-platform-demo.yaml >/dev/null 2>&1
R_OK=0; for i in $(seq 1 60); do sleep 5
  SS=$(KUBECONFIG=$KCFG kubectl -n argocd get app platform-demo -o jsonpath='{.status.sync.status}' 2>/dev/null)
  HS=$(KUBECONFIG=$KCFG kubectl -n argocd get app platform-demo -o jsonpath='{.status.health.status}' 2>/dev/null)
  [ "$SS" = "Synced" ] && [ "$HS" = "Healthy" ] && { R_OK=1; break; }; done
RECOVER_SECS=$(( $(date -u +%s) - RECOVER_BEGIN ))
assert_eq "recovery: Synced+Healthy (~${RECOVER_SECS}s)" "$R_OK" "1"
assert_eq "recovery: deployment 1/1" \
  "$(KUBECONFIG=$KCFG kubectl -n platform-demo get deploy platform-demo -o jsonpath='{.status.readyReplicas}' 2>/dev/null)" "1"

echo "== FAILURE TEST C: bad image tag in Application (helm parameter override) =="
KUBECONFIG=$KCFG kubectl -n argocd patch app platform-demo --type merge -p \
  '{"spec":{"source":{"helm":{"parameters":[{"name":"image.tag","value":"9.9.9-nonexistent"}]}}}}' >/dev/null 2>&1
KUBECONFIG=$KCFG kubectl -n argocd annotate app platform-demo argocd.argoproj.io/refresh=normal --overwrite >/dev/null 2>&1
C_OK=0; for i in $(seq 1 30); do sleep 5
  C_HS=$(KUBECONFIG=$KCFG kubectl -n argocd get app platform-demo -o jsonpath='{.status.health.status}' 2>/dev/null)
  C_DEG=$(KUBECONFIG=$KCFG kubectl -n platform-demo get pods --field-selector=status.phase!=Running,status.phase!=Pending 2>/dev/null | grep -c platform-demo)
  if [ "$C_HS" != "Healthy" ] || [ "${C_DEG:-0}" != "0" ]; then C_OK=1; break; fi; done
note "observed: health=$C_HS degraded_pods=${C_DEG:-0}"
assert_eq "C: Argo does NOT report Healthy for bad image (health=$C_HS)" \
  "$([ "$C_HS" != "Healthy" ] && echo yes)" "yes"

echo "== RECOVERY C (revert to declared source) =="
KUBECONFIG=$KCFG kubectl -n argocd patch app platform-demo --type json -p \
  '[{"op":"remove","path":"/spec/source/helm"}]' >/dev/null 2>&1
KUBECONFIG=$KCFG kubectl -n argocd annotate app platform-demo argocd.argoproj.io/refresh=normal --overwrite >/dev/null 2>&1
for i in $(seq 1 60); do sleep 5
  SS=$(KUBECONFIG=$KCFG kubectl -n argocd get app platform-demo -o jsonpath='{.status.sync.status}' 2>/dev/null)
  HS=$(KUBECONFIG=$KCFG kubectl -n argocd get app platform-demo -o jsonpath='{.status.health.status}' 2>/dev/null)
  [ "$SS" = "Synced" ] && [ "$HS" = "Healthy" ] && break; done
assert_eq "recovery C: Synced+Healthy restored" "$SS/$HS" "Synced/Healthy"

echo "== teardown =="
KUBECONFIG=$KCFG kubectl -n argocd delete app platform-demo --wait=false >/dev/null 2>&1
helm uninstall argocd -n argocd --kubeconfig "$KCFG" >/dev/null 2>&1
KUBECONFIG=$KCFG kubectl delete ns argocd platform-demo --wait=false >/dev/null 2>&1
docker compose -p reconstruct-k3s-disposable down -v --timeout 30 >/dev/null 2>&1
assert_eq "teardown: disposable container gone" \
  "$(docker ps -a --format '{{.Names}}' | grep -c '^reconstruct-k3s-disposable$')" "0"
assert_eq "protected fleet untouched" "$(docker ps --format '{{.Names}}' | grep -c k3s-server)" "1"

echo "== RESULT: pass=$PASS fail=$FAIL =="
[ "$FAIL" = "0" ] && echo "LEVEL 4 FAILURE TESTS: ALL PASS" || echo "LEVEL 4 FAILURE TESTS: FAILURES PRESENT"
exit "$FAIL"
