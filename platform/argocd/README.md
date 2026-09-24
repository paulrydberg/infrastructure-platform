# Argo CD — Phase 5A staged GitOps experiment
#
# Install (minimal, values above):
#   helm repo add argo https://argoproj.github.io/argo-helm
#   helm repo update
#   helm install argocd argo/argo-cd \
#     --namespace argocd --create-namespace \
#     --version 7.7.11 \
#     --values platform/argocd/values.yaml \
#     --kubeconfig platform/kubernetes/k3s/kubeconfig/kubeconfig.yaml
#
# Access (loopback only — never exposed publicly):
#   kubectl -n argocd port-forward svc/argocd-server 8081:443
#
# Bootstrap seed (the GitOps bootstrap paradox: Argo CD must be started once
# outside itself; afterwards it manages workloads from Git):
#   kubectl apply -f platform/argocd/application-platform-demo.yaml
#
# Removal (staged teardown):
#   kubectl delete -f platform/argocd/application-platform-demo.yaml
#   helm uninstall argocd -n argocd
#   kubectl delete ns argocd
#
# Chart pin: argo/argo-cd 7.7.11 → app version v2.13.3 (both recorded here;
# chart digest not used because the argo helm repo is not OCI — version pin
# is the lock; noted as a known limitation in the phase-5a report).
