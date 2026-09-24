# Startup / Teardown / Validation — k3s experiment (1.5 GiB envelope)

## Preconditions (Stage 2.1 gate, measured)

- VM available memory ≥ **2304 MB** (= 1536 MiB envelope + 768 MB margin),
  5-sample average via `docker run --rm alpine:3.20 free -m`
- Protected container count = 20 (21 total with platform-demo)
- No unexpected protected restarts vs baseline StartedAt/RestartCount
- platform-demo healthy

## Startup

```bash
cd platform/kubernetes/k3s
docker compose up -d
# wait for node Ready (first start pulls pod images):
docker compose exec k3s k3s kubectl get node -w   # until STATUS=Ready
```

kubeconfig lands at `platform/kubernetes/k3s/kubeconfig/kubeconfig.yaml`
(gitignored). Point kubectl at it:

```bash
kubectl --kubeconfig kubeconfig/kubeconfig.yaml get nodes
```

## Teardown (rollback)

```bash
docker compose down -v   # removes container + k3s-data volume
```

No Docker Desktop settings are touched by this experiment at any point.

## Reconstruction (Stage 2.3 target)

```bash
docker compose down -v && docker compose up -d
# -> node Ready, test namespace/workloads re-appliable from Git manifests
```

## Dependencies

- rancher/k3s:v1.31.2-k3s1 (digest recorded in phase-2 report)
- alpine:3.20 (probe image, memory measurement)
- Docker Desktop VM (UNMODIFIED — 7.654 GiB allocation, shared with protected workloads)

## Known Mac/Docker-specific constraints

- privileged mode required (embedded kubelet cgroup requirements) — documented, bounded
- VM-local storage is non-durable across Docker Desktop resets (named volume
  survives container recreation, not VM deletion) — recorded in the
  reproducibility contract as a known exception
- k3s networking uses its own netns; no host services are reachable from
  cluster pods by default
