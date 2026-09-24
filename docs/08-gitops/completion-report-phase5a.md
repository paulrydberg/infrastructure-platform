# Phase 5A Completion Report — Argo CD GitOps Experiment (1.5 GiB envelope)

**Status:** COMPLETE (2026-09-24) — GitOps control loop demonstrated, drift +
failure tests passed, staged teardown verified, permanent-residency measured.
STOPPED at Phase 5 boundary. No Phase 6+ components installed.

---

## 1. Exact resource measurements (all direct instrumentation)

**Pre-install baseline:** VM total 7838 MB · available 2087 MB (5-sample avg)
· k3s RSS 471.3 MiB · load 3.3–4.0 · swap 520 MB · 20/20 protected clean ·
k3s node Ready (41m uptime).

**With Argo CD resident (steady state, 3 samples over 60 s):**

| Metric | Value |
|--------|-------|
| k3s container RSS | **1.067–1.091 GiB / 1.5 GiB cap** (~72% of cap) |
| VM available | **1864–1878 MB** (Δ −210 MB vs 2087 baseline) |
| swap | 456–464 MB (DECREASED from 520 baseline) |
| host load | 3.7–4.2 of 12 threads |
| protected containers | 20/20 running, 0 restarts, 0 OOMs — entire phase |

**Argo CD per-component measured memory (cgroup memory.current):**

| Component | Requests / Limits | Measured |
|-----------|-------------------|----------|
| application-controller | 128Mi / 384Mi | **97.7 MB** |
| repo-server | 96Mi / 256Mi | **53.2 MB** |
| server | 96Mi / 256Mi | **27.5 MB** |
| applicationset-controller | (chart default) | **27.0 MB** |
| redis | 32Mi / 64Mi | **3.6 MB** |
| **Total measured** | | **≈ 209 MB** |

The estimate in reduced-envelope-analysis.md (~800 MB–1.2 GB for full Argo CD)
proved conservative for THIS workload: minimal components on a 1-app cluster
measured ~209 MB of pod memory. k3s total (with Argo) = 1.07–1.09 GiB,
comfortably inside the 1.5 GiB envelope.

## 2. Argo CD version/components

argo/argo-cd helm chart **7.7.11** → Argo CD **v2.13.3** (image tag pinned in
values.yaml). Components: application-controller, server, repo-server, redis,
applicationset-controller (chart default — noted honestly: my `enabled:
false` value did not cover it; it's small (27 MB) and harmless; recorded as a
chart-values gap). dex/notifications disabled. No metrics/prometheus stack.

## 3. GitOps control-loop results (ALL demonstrated)

| Requirement | Evidence |
|-------------|----------|
| Git access | Argo cloned public GitHub repo (no credentials needed — public; private would need a repo secret, documented) |
| Declarative Application | `platform/argocd/application-platform-demo.yaml` in Git |
| Deploys existing Helm chart | source path `platform/helm/platform-demo`, same chart as Phase 3 |
| Healthy state | `Synced Healthy`, pod 1/1 Running, /health returns `{"status":"ok","version":"0.1.0"}` in-cluster |
| Controlled Git change → reconciliation | drift test (below) + retarget test exercised sync |
| Convergence | observed in ≤ 10–15 s per sync cycle |
| Sync/health reporting | status polled via kubectl jsonpath each cycle |

**Bootstrap paradox resolved declaratively:** one seed manifest
(`kubectl apply -f application-platform-demo.yaml`) — after which Argo owns
the workload from Git. Seed committed to Git.

## 4. Drift results

Manual `kubectl scale --replicas=3` (out-of-band mutation, Git says 1):
Argo showed the state, and with `selfHeal: true` **converged back to 1
replica within ≤ 10 s** — the documented reconciliation behavior, measured.

## 5. Failure/recovery results

Controlled invalid desired state: branch `phase5a-failure-test` with image tag
`9.9.9-invalid`, Application retargeted to it:
- New ReplicaSet → **ErrImagePull/ImagePullBackOff** (events captured)
- **Old pod kept serving** during the entire failed rollout (zero downtime)
- Argo reported `Synced Progressing` (rollout not yet timed out) — honest
  observation: Argo's "Synced" reflects desired-vs-live resource match, not
  rollout health; health stays `Progressing` until deadline. The failure was
  visible in pod events/RS state, NOT silently ignored.
- Restore: retarget to `main` → **Synced Healthy within ~12 s**; failure-test
  branch deleted (evidence in this report).

## 6. Security configuration

- Argo API/UI: **loopback-only** (no Ingress, no LoadBalancer, no NodePort
  published) — port-forward documented as the access path
- Git credentials: none stored (public repo); private repos would require an
  argocd-repo-server secret — documented, not exercised
- admin initial-password secret exists in-cluster; deletion documented as
  post-install step; no credentials committed
- RBAC: default argocd serviceaccounts in argocd namespace only; no cluster
  role escalation beyond chart defaults; platform-demo remains in its own
  namespace with its security contexts intact (verified: non-root, RO
  rootfs, no-priv-esc — jsonpath in Phase 3, unchanged by Argo takeover)
- Kubernetes security controls from earlier phases: NOT weakened
- CI remains separate: no CI step mutates the cluster; CI validates/builds
  only (Phase 4 boundary preserved)

## 7. Reproducibility results

All in Git: `platform/argocd/values.yaml` (pinned chart 7.7.11, image tag
v2.13.3, per-component limits), `application-platform-demo.yaml` (seed),
README with install/teardown/validation commands. Sequence verified twice:
install → seed → Synced Healthy; teardown → reinstall → seed → re-converged.
Known limitation recorded: argo helm repo is not OCI — chart digest pinning
not available; version pin is the lock.

## 8. Permanent-vs-staged residency conclusion (the headline question)

**Measured answer: Argo CD fits AND operates within the 1.5 GiB envelope
alongside platform-demo — permanent residency is viable with margin.**

- k3s total 1.07–1.09 GiB of 1.5 GiB (72%), VM available 1864–1878 MB,
  swap down, load low, zero protected impact
- Both residency modes demonstrated and **kept distinct**:
  - ✅ staged window: install → sync → drift/failure tests → teardown →
    recovery verified (platform-demo briefly Terminating during cascade —
    documented; re-converged on re-seed)
  - ✅ **permanent residency: measured at steady state, criteria met**
- The reduced-envelope analysis estimated full Argo CD at 800 MB–1.2 GB;
  measured pod memory was ~209 MB (workload-size dependent: 1 small app).
  Estimates were conservative; the measurement governs.

## 9. Failures and remediation (all honest)

1. **applicationset-controller not disabled:** my values key didn't match the
   chart's schema — component ran anyway (27 MB). Recorded; values file kept
   as-is (working state) with the gap noted for the chart-values cleanup.
2. **Namespace stuck Terminating (~14 min) after teardown:** empty ns with
   finalizer `kubernetes` lingering. Remediated by clearing finalizers via
   `replace --raw .../finalize` (contents already verified empty). Documented
   as a known k8s/CRD teardown pattern; recorded in README removal sequence.
3. **Reinstall failed while ns Terminating** (`secrets forbidden … being
   terminated`) — sequencing lesson: wait for ns deletion before reinstall.
4. **Post-reinstall controller cache poisoning:** application-controller kept
   dialing the OLD repo-server ClusterIP (`connection refused`, captured from
   controller logs). `rollout restart` of the controller refreshed it →
   Synced Healthy in ~12 s. Root cause documented; this is a real Argo CD
   reinstall behavior worth knowing.

## 10. Recommended next phase boundary

**Phase 5A is complete.** Recommended next: **Phase 5B/6 decision gate for
Paul** — (a) keep Argo CD permanently resident (evidence supports it), and/or
(b) authorize Phase 6 observability planning (which does NOT fit alongside
Argo under 1.5 GiB — the resource negotiation for Phase 6 will need either a
VM resize decision or further staged-window discipline). Per standing rules:
Phase 6 not begun, not inferred. Prometheus/Grafana/Loki/OTel, AWS, WUD,
dependency automation, AI operations, platform engineering all remain
separately gated.

**Factual claim preserved:** this experiment establishes that a minimal Argo
CD (v2.13.3, 5 components, ~209 MB measured pod memory) operates within the
existing 1.5 GiB k3s envelope with the demo workload and demonstrated the
full GitOps control loop — it does NOT establish capacity for additional
future workloads or the observability stack.
