# Phase 2 Evaluation — Kubernetes Architecture (19-point analysis)

**Status:** Complete (2026-09-24) — READ-ONLY; no k3s installed, no config changed
**Companion doc:** resource-negotiation-report.md (measurements + options)

## 1. Kubernetes architecture evaluation

Single-node local cluster for development/validation; architecture mirroring
the target EKS pattern (declarative workloads, health probes, resource
requests/limits) at 1/100th the scale. Control plane = k3s server with
embedded datastore (sqlite) — etcd is unnecessary for one node and adds
~500 MB + quorum complexity with zero benefit here.

## 2. k3s suitability analysis

| Criterion | k3s | kind | minikube | microk8s |
|-----------|-----|------|----------|----------|
| Runs as plain Docker container on macOS/Intel | ✅ | ⚠️ needs nested virtualization layer (slow on Intel mac) | ⚠️ VM driver | ⚠️ snap-only |
| Footprint | ~512–900 MB | ~1 GB+ | 1.5 GB+ | ~1 GB |
| Reproducible via compose + pinned image | ✅ | ⚠️ | ❌ | ❌ |
| Hard resource caps via compose | ✅ (cgroup) | ⚠️ | ❌ | ❌ |
| Production-adjacent (actual edge deployments) | ✅ | dev-only tool | dev-only | close |
| No Docker Desktop settings changes | ✅ | ⚠️ | ❌ | ❌ |

**Verdict:** k3s — it's the only option that runs as an ordinary hard-capped
Docker container (coexistence-safe), is itself production-deployed software
(evidence-grade, not a toy), and matches the spec's §20 presumption. This
analysis becomes the evidence base for ADR-0004 at implementation time.

## 3–7. Resource analysis

See resource-negotiation-report.md (measured): VM has ≈4.5–5 GiB free inside
its 7.654 GiB; k3s envelope ≤ 2.5 GiB / 2 cores hard-capped; observability
full stack does NOT fit (Phase 6, separate negotiation); metrics-server only.

## 8. Storage requirements

k3s local-path provisioner (VM-local). Phase 2 workloads stateless. VM-local
storage documented as non-durable (survives container restarts via named
volume; does not survive Docker Desktop reset without backup) — recorded in
reproducibility contract as a known exception (spec §8).

## 9. Networking requirements

Dedicated bridge network for k3s; API server on 127.0.0.1:6443 (verified
free); default k3s CIDRs (10.42/16 pods, 10.43/16 services) conflict-free
with host LAN (10.0.0.0/24) and Docker's default pools; Traefik + ServiceLB
DISABLED (disable-flags) — no ingress in Phase 2; NodePort mapped selectively
for validation. EKS portability: kubeconfig-based access identical; ingress
design deferred to when a real need exists (spec §81 discipline).

## 10. Kubernetes persistence requirements

k3s state (sqlite + kubelet) in a named volume → clean destroy/recreate
cycles for reconstruction testing. Application state: none in Phase 2.

## 11. Failure & resource-exhaustion scenarios

Analyzed in resource-negotiation-report.md §11–12. Key design choice: k3s
runs UNDER a hard cap and therefore loses contention first by design —
protecting both the host and the protected workloads. Kubernetes-restart and
VM-restart survival are part of the validation plan.

## 12. Resource contention analysis

Measured: host CPU ~80% idle (12 threads), VM ~5 GiB free, protected workloads
consume ~2.4 GiB inside the VM. k3s's 2.5 GiB cap fits inside free VM memory
with ~2 GiB still unallocated for bursts. Contention loser = k3s (bounded).
Only risk that changes host behavior: none identified under Option A.

## 13. Local development/validation architecture

```
macOS host (protected workloads untouched)
└── Docker Desktop VM (7.654 GiB, UNCHANGED)
    ├── 20 protected containers (existing compose projects)
    ├── platform-demo (Phase 1, capped 128M)
    └── [AUTHORIZED OPTION A ONLY] k3s container (cap 2.5 GiB / 2 cores)
        ├── kube-apiserver/controller/scheduler/kubelet (embedded)
        ├── sqlite datastore (named volume)
        └── test/validation workloads (Phase 2)
```

## 14. Future AWS/EKS compatibility implications

Kubernetes-native definitions from day one (no compose-only coupling beyond
the cluster container itself). k3s is CNCF-conformant → manifests portable to
EKS. Deviations to document: local-path storage → EBS CSI on EKS; NodePort →
ALB/nginx later; sqlite → EKS managed control plane. All deviations live in
docs/11-cloud/ when Phase 8 arrives.

## 15. Kubernetes reproducibility requirements

Cluster defined as code: pinned k3s image tag + compose file in Git
(bootstrap/platform/kubernetes/). Reconstruction test = `docker compose down
-v && docker compose up -d` → node Ready → test workload healthy. Level 2
target: "Automated Kubernetes Reconstruction" — the exit criterion for Phase 2.

## 16. Kubernetes security baseline

- API server bound to loopback only (no LAN exposure)
- Traefik/ServiceLB disabled (smaller surface)
- k3s container non-privileged except required capabilities/volumes
  (k3s needs specific caps; documented exactly which, no blanket --privileged)
- kubeconfig 0600, never committed; CI secret-scan guards
- test namespaces with ResourceQuotas from the first workload
- protected containers remain outside the cluster entirely (no k3s networking
  touching host services)

## 17. Helm/GitOps integration implications

Phase 2 keeps raw manifests (spec §21: plain manifests where clearer). Helm
arrives Phase 3, Argo CD Phase 5 — both deploy INTO this cluster without
architecture change. k3s version pinned in Git from day one (upgrade strategy
= rebuild from source, fitting the reproducibility model).

## 18. Phase 2 implementation plan (staged, authorization-gated)

| Step | Action | Gate |
|------|--------|------|
| 2.1 | Commit k3s compose definition (pinned image, caps, disables) to Git | covered by Phase 2 authorization |
| 2.2 | Start cluster; validate node Ready, workload scheduling | same |
| 2.3 | Resource-cap verification under load + rejection-conditions check | same |
| 2.4 | Failure tests: kill k3s container, VM-restart survival | same |
| 2.5 | Reconstruction test: down -v → up → Ready (Level 2 evidence) | same |
| 2.6 | docs/05-kubernetes/* + completion report | same |
| — | Docker Desktop VM change (Option B) | **SEPARATE authorization — NOT planned for Phase 2** |

## 19. Phase 2 validation & rollback plan

- **Validation:** before/after docker stats all 21 containers; host load
  trace; node Ready; test pod runs; all 5 rejection conditions explicitly
  checked; idempotence + reconstruction tests recorded.
- **Rollback:** `docker compose down -v` on the k3s project → host returns to
  Phase 1 state exactly. One command. No settings to revert (Option A).

---

## STOP CONDITION HONORED

This evaluation is complete. No k3s installed. No Docker Desktop change. No
workloads deployed. Awaiting: (1) Phase 2 implementation authorization on
Option A basis, or (2) Paul's decision among options if he prefers B or an
alternative. This document does not choose for him.
