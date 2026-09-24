# Phase 6 Tier-A Experiment — metrics-server v0.7.2 (Full Report)

**Final classification: FUNCTIONAL VALIDATION SUCCESSFUL / SWAP GATE TRIGGERED
/ CAUSALITY UNCERTAIN → experiment closed by documented rollback.**

> ⚠️ **Prominent result — the swap gate fired.** Host swap rose from a flat
> 625.75 MB baseline to as much as 1260 MB during the observation window and
> did not return to baseline. Attribution analysis did not support
> metrics-server as the driver, but the evidence does not permit proven
> causality in either direction. The gate was applied as written: the
> experiment was closed via rollback rather than rationalized into a PASS.
> This result is recorded as a legitimate engineering outcome.

---

## 1. Objective

Convert the estimated (class [E]) Tier-A metrics-server resource envelope
into measured (class [M]) evidence under the decision-gate criteria, using
the existing 1.5 GiB k3s envelope, without destabilizing the platform or the
protected container fleet.

## 2. Environment

Mac Mini (8-core i7, 16 GB) · Docker Desktop VM 7.654 GiB · k3s v1.31.2+k3s1
in a hard-capped container (1.5 GiB / 2 cores) · Argo CD v2.13.3 resident
(~174 MB measured) · platform-demo workload · 20 protected coexisting
containers (out of scope, monitor-only).

## 3. Baseline (measured, 7 samples pre-install)

| Metric | Value [M] |
|--------|-----------|
| k3s RSS | 974–979 MiB (limit 1.5 GiB) |
| VM available | 1755–1911 MB |
| Swap | **625.75 MB flat** |
| Host load5 | 4.48–4.78 (12 threads) |
| API /readyz | 0.31–0.63 s |
| Argo / node / platform-demo | Synced Healthy / Ready / 1/1 Running healthy |
| Protected fleet | 20/20, 0 restarts, 0 OOMs |
| PVCs | 0 |

## 4–7. Component, integrity, compatibility, configuration

- **Version:** metrics-server **v0.7.2** (kubernetes-sigs official release)
- **Source:** `https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml`
- **Upstream manifest SHA-256:** `f103539a54ed72efe66616afc74a8bfaed651703cb3918797599046af5617441`
- **Image:** `registry.k8s.io/metrics-server/metrics-server:v0.7.2` (pinned)
- **Compatibility:** kubernetes-sigs matrix lists v0.7.x for K8s 1.30/1.31; cluster is v1.31.2+k3s1 — verified before install, not assumed
- **Configuration delta (only change):** Deployment resources
  `requests {cpu:50m, memory:64Mi} / limits {cpu:200m, memory:128Mi}`
- **Installed variant SHA-256:** `platform/metrics-server/manifests/components.yaml.sha256`
- **Install method:** `kubectl apply -f` from the Git-tracked manifest
  (source of truth = repository), committed at `71486b7`

## 8. Acceptance criteria (defined pre-install in the decision gate)

Success: pod Ready; node Ready; `kubectl top` functional; workloads healthy;
k3s ≤ 1.35 GiB sustained; VM avail ≥ ~1800 MB; swap flat; API within 2×
baseline; 60-min observation window. Abort: k3s > 1.35 GiB sustained;
protected restart/OOM; swap +~100 MB sustained >15 min; API 2× baseline;
metrics-server instability.

## 9–11. Installation, functional validation, observation

Installation: 9 objects applied, pod 1/1 Running in ~31 s.
Functional validation **[M]**:

```
kubectl top nodes → 3562bf44ad50  89m CPU  1016Mi MEM (12%)
kubectl top pods -A → all 8 pods with real CPU/memory numbers
metrics-server pod: 16–20 Mi measured (vs 60–100 MB estimated [E])
```

**Observation window: 12 samples over ~55 min (5-min intervals), plus
extended post-window monitoring to ~2.8 h total residency.**

| Metric | Baseline | During experiment | Change | Gate |
|--------|----------|-------------------|--------|------|
| k3s RSS | 974–979 MiB | 1005 MiB – 1.058 GiB | +~50–80 MiB steady-state | PASS (≤1.35 GiB) |
| k3s limit | 1.5 GiB | 1.5 GiB | unchanged | — |
| VM available | 1755–1911 MB | 1480–1988 MB (dip at swap event, recovered) | noisy | PASS w/ event |
| Swap | 625.75 MB flat | 628→660→716→**1239** MB, later 1143–1260 | **+up to ~634 MB** | **TRIGGERED** |
| Host load5 | 4.48–4.78 | 3.25–4.78 | within range | PASS |
| API latency | 0.31–0.63 s | 0.37–0.53 s | within range | PASS |
| Protected restarts | 0 | **0** | none | PASS |
| Protected OOMs | 0 | **0** (docker+k8s event logs clean) | none | PASS |
| Argo | Synced Healthy | Synced Healthy every sample | none | PASS |
| platform-demo | healthy | healthy every sample | none | PASS |
| metrics-server | — | Running 0 restarts, 16–20 Mi | stable | PASS |

## 12. The swap event (prominent)

At ~07:11, swap jumped 716 → 1239 MB within one 5-min interval, while
**k3s RSS simultaneously decreased** (1.058 → 1.01 GiB) and VM available
dipped to 1480 MB then recovered over the following hour. Swap never
returned to the 625 MB baseline; it continued drifting (1143–1345 MB)
including **after** metrics-server removal.

## 13. Attribution analysis (read-only, bounded)

Evidence collected:

1. **metrics-server stability:** 0 restarts, 0 evictions, constant 16–20 Mi
   across the entire window — no behavioral change around the event
2. **k3s RSS vs swap correlation across 27 samples:** Pearson **r = 0.131**
   (near zero) — the container hosting k3s+metrics-server shows no
   statistical relationship with swap growth
3. **k3s did not grow at the event** — it fell while swap spiked
4. **Kubernetes:** node conditions MemoryPressure=False, no OOMKilling /
   Evicted events anywhere in the cluster
5. **Docker:** zero OOM events in the 4 h event stream
6. **Protected fleet:** 20/20 running, 0 restarts, 0 OOMs; clickhouse
   (largest consumer) 1.823–1.953 GiB, no restart, running since 2026-09-23
7. **Temporal correlation:** the single swap step-change coincided with no
   observable change in any k3s-side metric

**Classification: CORRELATED_BUT_CAUSALITY_UNCERTAIN** — the evidence
*does not support* ATTRIBUTED_TO_METRICS_SERVER (its host container shrank
at the event, r≈0.13, zero k8s/docker OOMs, pod constant) but background
host pressure is also not *proven* as the cause; no single workload was
directly observed causing the step.

## 14. Control comparison (bounded, per authorization)

metrics-server removed via the documented method (`kubectl delete -f`, the
Git-tracked manifest). Result:

- swap **remained 1345.5 MB, flat, over 4 post-removal samples** — removal
  did not restore the baseline (does not exonerate; swap also did not
  *continue growing* without it)
- k3s RSS 1.004–1.008 GiB, clickhouse 1.853–1.953 GiB (its own drift),
  Argo Synced Healthy, node Ready, platform-demo healthy
- zero residual resources: APIService gone, no pods, no containers

Control conclusion: removal neither reverted swap nor stopped further
drift — consistent with a host-level/protected-fleet pressure driver, but
insufficient to prove causality. **Rollback was executed anyway** per the
conservative gate interpretation (CAUSALITY UNCERTAIN → close conservatively).

## 15–17. Rollback validation, failures, lessons

**Rollback:** clean — metrics APIService, pods, service, RBAC all removed;
cluster verified back to pre-experiment workload state; Argo untouched
throughout (the experiment never modified it).

**Failures:** none in installation, functionality, or metrics-server
stability. The gate failure was environmental-swap, not component failure.

**Lessons:**
1. Host-level swap pressure can contaminate single-host envelope experiments
   — coexisting workloads share the swap resource even when their containers
   are untouched; swap baselines must be re-validated per experiment session.
2. A flat pre-baseline (625.75 for 7 samples) does not guarantee host
   stability for the following hour.
3. metrics-server measured footprint ([M] 16–20 Mi) was far below the [E]
   estimate (60–100 MB) — the estimate class was conservative.
4. The near-zero k3s↔swap correlation is useful evidence discipline: check
   the driver container's own trajectory before accepting blame.

## 18. Final classification

**FUNCTIONAL VALIDATION SUCCESSFUL / SWAP GATE TRIGGERED / CAUSALITY
UNCERTAIN — experiment closed via documented rollback.**

metrics-server is **experimentally validated, NOT an implemented persistent
capability.** Re-introduction requires a new authorization and a re-validated
swap baseline (and ideally a host whose swap pressure is understood).

## 19. Next Phase 6 decision (for Paul, evidence-based)

- The 1.5 GiB in-cluster envelope comfortably hosted Tier A's function
  (k3s peak 1.058 GiB) — in-cluster memory is NOT the blocker.
- The shared-host swap pressure IS the blocker for clean gate passes.
- Options: (a) re-run Tier A with a fresh swap-flat baseline and a
  pre-agreed host-attribution protocol, (b) characterize the host swap
  driver first (read-only, protected fleet remains out of scope), (c) defer
  Tier B/C (would add 10–100× more memory pressure on the same host),
  (d) VM resize decision remains available but unchanged.
