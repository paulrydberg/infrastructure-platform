# Metrics-Server — Tier A (Phase 6)

Single-purpose metrics collection for the k3s cluster: enables
`kubectl top nodes` / `kubectl top pods` (replaces ad-hoc cgroup probing).

## Version & integrity

- **Component:** metrics-server **v0.7.2** (kubernetes-sigs official release)
- **Source:** https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml
- **Upstream manifest SHA-256:** `f103539a54ed72efe66616afc74a8bfaed651703cb3918797599046af5617441`
- **Image (pinned, no floating tag):** `registry.k8s.io/metrics-server/metrics-server:v0.7.2`
- **Compatibility:** k3s v1.31.2+k3s1 (metrics-server v0.7.x supports Kubernetes 1.30/1.31 per the kubernetes-sigs compatibility matrix — verified before install)
- **Installed variant SHA-256:** see `manifests/components.yaml.sha256`
  (upstream manifest + explicit resource limits on the Deployment — the only
  local modification; no other changes)

## Configuration deltas vs upstream

Deployment container resources:

```yaml
resources:
  requests: {cpu: 50m, memory: 64Mi}
  limits:   {cpu: 200m, memory: 128Mi}
```

No k3s-specific flags required: the upstream default
`--kubelet-preferred-address-types=InternalIP,...` works with the
containerized k3s node (single node, InternalIP addressable).

## Install / remove

```bash
# install (reproducible from this repo)
kubectl apply -f platform/metrics-server/manifests/components.yaml

# remove (stateless — no PVCs, no CRDs, clean teardown)
kubectl delete -f platform/metrics-server/manifests/components.yaml
```

## Validation

```bash
kubectl get pods -n kube-system -l k8s-app=metrics-server   # 1/1 Running
kubectl top nodes && kubectl top pods -A                    # real numbers
```

## Security posture

- No elevated privileges, no hostNetwork, no hostPath mounts
- Standard RBAC from upstream manifest (aggregated metrics reader +
  auth-delegator RoleBindings — upstream defaults, unmodified)
- No new network exposure (in-cluster scrape of kubelet Summary API only)

## Experiment result

See `docs/09-observability/tier-a-experiment.md` for the full measured
experiment (baseline → install → 60-min observation → rollback validation).
