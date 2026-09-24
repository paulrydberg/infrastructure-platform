# Phase 2 Completion Report — k3s Experiment (A″, 1.5 GiB Envelope)

**Status:** COMPLETE (2026-09-24) — all stages executed, all acceptance criteria
verified with measured values. STOPPED at Phase 2 → Phase 3 boundary.
**Released:** platform/kubernetes/k3s definition in repo (see commit history)

---

## Engineering history preserved (per authorization)

```
derived estimate (~4.5-5 GiB free)
      ↓ direct measurement (RC-1: 2465 MB available)
      ↓ estimate disproved
      ↓ 2.5 GiB deployment PREVENTED at pre-flight
      ↓ resource model corrected (direct instrumentation standard)
      ↓ smaller envelope evaluated (this experiment)
```

RC-1 record preserved unmodified: `experiment-optiona-rc1-abort.md`.

## Why 1.5 GiB was selected

Reduced-envelope analysis (reduced-envelope-analysis.md): the Phase 2
objectives (fundamentals, Helm, lifecycle, security, reproducibility) need
~100–200 MB above k3s idle; 1.5 GiB envelope leaves ~1.0 GiB VM buffer against
the 17-unlimited-container risk; full Argo CD does NOT fit and stays gated.
**Status: experimentally validated starting envelope — NOT a permanent
capacity guarantee.**

## Pre-start criterion (established before startup, replacing the old 3.0 GiB)

VM available ≥ **2304 MB** (1536 envelope + 768 margin), 5-sample average.
Stage 2.1 measured: 2435/2436/2436/2437/2438 → **avg 2436 MB → PASS**
(also: 20 protected containers verified, no unexpected restarts — the two
RestartCount=1 entries predate all project work, confirmed against RC-1
baseline; platform-demo healthy).

## What was built (source of truth)

`platform/kubernetes/k3s/compose.yaml` — pinned `rancher/k3s:v1.31.2-k3s1`
(digest sha256:c88e1cf829fd…a36), hard caps **1536 MiB / 2 cores**, sqlite
datastore, Traefik+ServiceLB+metrics-server DISABLED, API on 127.0.0.1:6443
only, named volume `k3s-data`, dedicated project. Plus
`test/fundamentals.yaml` (namespace+quota+deployment+probes+limits+security
context+service) and README with startup/teardown/validation procedures.

## Stage 2.2 — acceptance measurements (real values)

| Criterion | Measured |
|-----------|----------|
| k3s healthy | node `Ready` (v1.31.2+k3s1), `/readyz` passed |
| k3s RSS vs cap | **455–475 MiB / 1536 MiB** (≈30% of cap; cap never approached) |
| VM available | 2436 → **2065 MB** after k3s (Δ ≈ −371 MB) |
| Host load | 3.8–7.1 (1-min, of 12 threads) — within boundary |
| Swap | **584→552 MB** — DECREASED vs 680 MB baseline (no harmful growth) |
| Protected containers | 20/20 running, 0 new restarts, 0 OOMs |
| Docker stable | 24 defined / 22 running, no errors |
| Headroom retained | VM available 2065 MB >> protected-workload needs |
| Clean stop/restart | `compose stop && start` → node Ready again |

## Stage 2.3 — reproducibility (Level 2 evidence)

`docker compose down -v` (container+volume removed, verified gone)
→ `docker compose up -d` → **node Ready in ~8 s**, RSS 391 MiB.
`source → bootstrap → k3s → health validation` with zero undocumented steps.
One documented procedure quirk: manifests are applied via `docker cp` +
in-container kubectl (host kubectl has no kubeconfig context by design —
loopback-only API). Recorded in the k3s README.

## Stage 2.4 — Kubernetes fundamentals demonstrated (all measured)

- API + namespace `platform-test` + ResourceQuota **enforcement verified**:
  scale-to-5 rejected at pods=4 (`exceeded quota: test-quota` event captured)
- Deployment with readiness/liveness probes → pod 1/1 Running in ~6 s
- Service ClusterIP reached in-cluster via DNS (`demo.platform-test.svc…`)
- **Controlled failure/recovery:** pod deletion → self-healed in ~5 s;
  bad-image rollout → old pod kept serving, ErrImagePull isolated,
  `rollout undo` restored service — exactly the behavior GitOps safety
  boundaries will rely on later
- Security context verified: non-root (65534), read-only rootfs, no privilege
  escalation

## Stage 2.5 — resource observation (6 samples / 3 min, steady + transitions)

| sample | k3s | OLAP (protected) | VM avail | swap | load |
|--------|-----|------------------|----------|------|------|
| 1 | 475 MiB | 1.99 GiB | 2059 | 552 | 3.93 |
| 2 | 471 MiB | 2.09 GiB | 2064 | 552 | 7.07 |
| 3 | 472 MiB | 2.03 GiB | 2068 | 552 | 5.82 |
| 4 | 474 MiB | 1.97 GiB | 2038 | 552 | 4.64 |
| 5 | 460 MiB | 2.02 GiB | 2042 | 552 | 4.35 |
| 6 | 446 MiB | 2.04 GiB | 2040 | 552 | 3.81 |

Steady state: k3s ≈ 450–475 MiB (30% of cap); OLAP oscillates 1.97–2.09 GiB
(no material expansion during experiment); VM available stable 2038–2068 MB;
swap flat; host load within boundary. Workload-transition behavior: no
measurable spike beyond noise. Post-teardown: VM avail 2041 MB, k3s 432 MiB.

## Failures encountered (honest)

1. `docker compose exec -T k3s k3s kubectl …` returned empty → k3s image
   expects the `kubectl` symlink, not `k3s kubectl` subcommand (fixed).
2. First apply attempt passed a host path to in-container kubectl → "path
   does not exist" → `docker cp` step added to the documented procedure.
3. No OOMs, no cap approaches, no protected-workload anomalies — the envelope
   was never stressed to its boundary during normal operations.

## Rollback evidence

Rollback procedure (`compose down -v`) was effectively EXERCISED twice: the
reconstruction test (down -v → up) and the original RC-1 abort (nothing to
remove, verified clean). Host returned to identical state both times; 20
protected containers untouched throughout the entire experiment.

## Reproducibility record (per authorization)

- k3s v1.31.2+k3s1 (6da20424), image digest sha256:c88e1cf829fd84331c9ec92988509f17b5815527829326810da1a223e8b50a36
- Config: compose.yaml in Git (caps 1536MiB/2 cores, disables, loopback API)
- Volumes: `k3s-data` named volume (recreatable); kubeconfig output gitignored
- Networking: dedicated project network; 127.0.0.1:6443; default CIDRs
- Startup/teardown/validation/rollback: platform/kubernetes/k3s/README.md
- Dependencies: Docker Desktop VM (unmodified), alpine probe image
- Known constraints: privileged mode required (documented, bounded by
  loopback-only API + test-only workloads); VM-local storage non-durable
  across Docker Desktop resets; manifests applied via docker cp step

## Security implications

- API server loopback-only; no ingress controllers; no LB
- Test workloads run non-root, read-only rootfs, no privilege escalation,
  under ResourceQuota
- Privileged k3s container = documented known constraint (kubelet requirement
  in VM); blast radius bounded by project isolation; hardening alternatives
  logged for evaluation (not silently accepted)
- kubeconfig: gitignored, 0600 mode

## Factual claims (per the important distinction)

> "Phase 2 testing established that a resource-bounded k3s deployment
> (1.5 GiB / 2 cores, ~450–475 MiB observed steady-state) can operate within
> the existing Docker Desktop VM allocation without degrading protected
> workloads, and can be reconstructed from source. Larger-stack capacity
> (full Argo CD, observability) is NOT established by this experiment."

## Remaining constraints

- Full Argo CD does not fit 1.5 GiB (upstream ≥2 GB class) → Phase 5 gate with
  its own envelope decision (staged 1.75 GiB window is the documented option)
- Observability stack: Phase 6 gate (unchanged)
- privileged-mode k3s: hardening evaluation pending
- 17/20 protected containers unlimited-cap: environmental risk, unchanged
- metrics-server not installed (intentional); resource measurement via docker
  stats + /proc

## Phase 3 prerequisites (Helm)

1. Phase 2→3 authorization from Paul
2. Helm binary (client-side only; no in-cluster component) — install is a
   host change requiring the same validation discipline (bootstrap reports,
   does not install — first gate of Phase 3)
3. A small chart to package platform-demo (real work, not a demo-for-demo)
4. Envelope: no increase needed — Helm operations measured ~tens of MB
   transient; stays within 1.5 GiB

**STOPPED at the Phase 2 → Phase 3 authorization boundary.**
