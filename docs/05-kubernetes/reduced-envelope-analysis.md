# Reduced-Envelope Analysis — Minimum Viable Local Kubernetes

**Status:** Complete (2026-09-24) — READ-ONLY; no k3s started, no limits changed, no host changes
**Mandate:** Paul's directive following RC-1 abort; decision remains Paul's
**Prepared for choice among:** A′ / A″ / B / C / D — none selected here

---

## 1. RC-1 baseline (measured, 2026-09-24)

Direct `/proc/meminfo` via probe container, 5 samples over 30 s:
VM available 2471 / 2427 / 2496 / 2435 / 2497 MB — **avg 2465 MB**, sustained
below the 3.0 GiB rejection threshold. k3s never started. 20/20 protected
containers unaffected.

## 2. Why the previous estimate was invalid

The evaluation derived "≈4.5–5 GiB free" as `VM allocation (7838 MB) − sum of
container usage (~2.4 GiB)`. That subtraction is methodologically wrong
because the VM's used memory includes kernel, Docker daemon, and
cache/buffer accounting beyond container cgroups. **Direct instrumentation
supersedes derived estimates** — accepted as authoritative by Paul.

## 3. Direct instrumentation methodology (the standard going forward)

- Probe container runs `free -m` inside the VM → `/proc/meminfo` values
  (total / used / buff-cache / **available**). "Available" is the correct
  gate metric (reclaimable-cache-adjusted), not "free".
- 5 samples, 6 s apart, average reported; single readings are never gates.
- Container-level truth via `docker stats --no-stream`.
- Restart-detection baseline via `State.StartedAt` + `RestartCount` for all
  protected containers before any experiment.

## 4. Current memory/CPU/swap state (measured 2026-09-24, second session)

| Metric | Value (measured) |
|--------|------------------|
| VM total / used / buff-cache / **available** | 7838 / 5015 / 2399 / **2509 MB** |
| Container usage sum (21) | **4353 MB** |
| VM non-container overhead (used − containers) | **~662 MB** |
| Largest consumer | OLAP db 1.96–2.01 GiB (stable across 60 s) within its 4 GiB cap |
| Host load | 5.19 / 4.84 / 4.43 (of 12 threads) |
| Host CPU idle | ~76% |
| Swap | 648 MB / 2 GB (stable vs 680 MB baseline) |

**Memory equation (the real constraint):**
`available (2509) = total (7838) − used − reclaimable cache`, where containers
hold 4353 MB + ~662 MB VM overhead. The dominant consumer is the protected
OLAP db (~2 GiB, legitimate, untouchable). 17/20 protected containers remain
unlimited-cap — a documented environmental constraint/risk, NOT an invitation
to modify them.

## 5. Candidate resource envelopes

Evidence classes: **[M]** measured on this host · **[D]** documented upstream
requirement · **[E]** estimate (labeled, not a fact) · **[A]** assumption ·
**[U]** unknown

### Component footprints

| Component | Footprint | Class |
|-----------|-----------|-------|
| k3s server idle (sqlite, Traefik+servicelb disabled) | **[D]** k3s docs: 512 MB min, 1 GB recommended; **[E]** community-measured idle 600–850 MB | D+E |
| k3s startup overhead | **[E]** transient +100–200 MB during first scheduling | E |
| containerd/kubelet runtime overhead | included in k3s RSS **[D]** | D |
| networking (flannel vxlan, single node) | **[E]** negligible memory, ~0 CPU idle | E |
| storage (local-path) | disk only, no RAM cost **[D]** | D |
| minimal test pod (alpine-class) | **[M]-class** platform-demo measured 13 MB; k8s pods similar | M/E |
| Helm (v3, client-side only — runs in k3s container exec, no in-cluster component) | **[E]** ~30–60 MB transient during install/upgrade | E |
| metrics-server (optional instrumentation) | **[D]** ~60–100 MB | D |
| Argo CD (full: server+repo+controller+redis) | **[D]** upstream: ≥ 2 GB node recommended; **[E]** realistic idle 800 MB–1.2 GB | D+E |
| Argo CD core (no UI server) | **[E]** ~400–600 MB | E |

### Envelope verdicts (cap → what fits, VM margin after envelope is consumed)

| Envelope | Contents | Verdict |
|----------|----------|---------|
| **1.0 GiB** | k3s idle alone (700–850) leaves ≤ 300 MB | **REJECT** — no workload headroom, OOM during first real test likely |
| **1.25 GiB** | k3s + 1 small workload + probes; Helm client ops | **MARGINAL** — fits fundamentals + Helm; ~350–450 MB in-cap headroom; Argo CD impossible |
| **1.5 GiB** | k3s + workloads + Helm + metrics-server | **VIABLE** — covers fundamentals, Helm, lifecycle, reproducibility, security-quota tests; ~600 MB headroom; full Argo CD no; Argo core marginal |
| **1.75 GiB** | above + Argo CD core (staged window) | **VIABLE+** — GitOps demonstrable in a temporary window; ~500–600 MB headroom |
| **2.0 GiB** | above + full Argo CD (staged window) | **POSSIBLE but risky now** — VM margin after envelope only ~0.5 GiB against a 2 GiB-capable OLAP db + 17 unlimited containers |

**VM-margin risk model (key numbers):** available today 2509 MB. Envelope X
consumed → VM margin ≈ 2509 − X. If the protected OLAP db grows toward its
4 GiB cap (+2 GiB potential) the VM needs that buffer. Envelope 1.5 GiB leaves
~1.0 GiB buffer; 2.0 GiB leaves ~0.5 GiB. The 17 unlimited containers make
large-buffer scenarios plausible, not hypothetical.

## 6. Minimum viable platform objectives (the actual Phase 2+ objectives)

| Objective | Needs in-cluster memory | Feasible at |
|-----------|------------------------|-------------|
| Kubernetes fundamentals (scheduling, probes, services, configmaps, quotas) | ~100–200 MB above k3s idle | 1.25 GiB |
| Helm (install/upgrade/rollback of a small chart) | client-side, ~50 MB transient | 1.25 GiB |
| Workload lifecycle + failure/recovery testing | negligible extra | 1.25 GiB |
| Reproducibility (reconstruction testing) | none extra | any |
| Security controls (quotas, security contexts, network policies) | negligible extra | 1.25 GiB |
| GitOps / Argo CD | 800 MB–1.2 GB full; 400–600 MB core | 1.75–2.0 GiB (staged) or deferred |

**Finding: the majority of the engineering objectives do NOT require a large
envelope. Only GitOps is memory-hungry, and only its full form.**

## 7. Staged-vs-resident architecture analysis (the architectural question)

**Finding: staged operation materially reduces the envelope.** The objectives
do not require simultaneous residency:

```
k3s (1.5 GiB cap)
  ↓ validate fundamentals (measure)
  ↓ Helm: install/upgrade/rollback small chart (measure)
  ↓ validate → helm uninstall (memory returned)
  ↓ GitOps window: Argo CD core deployed temporarily (1.75 GiB session cap
    OR staged after other workloads removed) (measure)
  ↓ validate reconciliation → remove/deallocate
  ↓ next experiment
```

Under staged operation, peak memory = max(stage), not sum(stage). Peak =
Argo CD window ≈ k3s-idle + ~0.6–1.2 GB ≈ 1.4–2.0 GiB — and only transiently.
**This is an architectural option with real engineering merit** (it also
matches the reproducibility philosophy: everything is declarative, deployed,
validated, and removed — residency is not ownership). It also provides
cleaner per-stage evidence for the portfolio.

## 8. Risk analysis

| Risk | Assessment |
|------|------------|
| Envelope too small → k3s OOM during tests | rejection-condition 2 catches it; stage aborts, nothing else affected |
| VM margin consumed by protected burst (OLAP toward 4 GiB cap) | envelope ≤ 1.5 GiB keeps ~1.0 GiB buffer; 2.0 GiB envelope = 0.5 GiB buffer — thin |
| Unlimited protected containers balloon | same buffer logic; k3s loses by design (capped); VM itself protected by buffer only — hence smaller envelope = safer |
| Swap escalation | bounded: k3s capped; RC-4 monitors |
| Docker instability | no config changes under A″; risk unchanged |

## 9. Acceptance criteria (for any future A″ run)

1. Pre-start: VM available ≥ envelope + 750 MB margin, measured 5-sample avg
2. k3s reaches Ready; test workload schedules and serves
3. Each stage's measured footprint recorded; envelope never exceeded in normal ops
4. All 5 original rejection conditions remain in force (adapted threshold:
   RC-1 becomes "VM available ≥ envelope + 750 MB sustained pre-start")
5. Post-stage teardown returns VM available to within 100 MB of pre-stage
6. Reconstruction test passes (down -v → up → Ready)

## 10. Rejection criteria (unchanged 5, plus)

Original RC-1 re-parameterized per envelope; RC-2/3/4/5 verbatim. Additional:
6. In-cap OOM kills during NORMAL staged operations (not induced failure tests)
7. Any stage that cannot complete within its declared envelope → that
   objective is recorded as "does not fit envelope X" — not silently retried

## 11. Rollback procedure

Unchanged and trivial: `docker compose down -v` on the k3s project. No Docker
Desktop settings, no protected-workload exposure at any point.

## 12. Reproducibility implications

Unchanged in kind: pinned k3s image + compose definition + cap values in Git.
The envelope number itself becomes a documented, versioned parameter — an
honest record that the platform runs within a measured constraint (spec §39:
realistic scale is more credible than pretending).

## 13. Portfolio/engineering evidence implications

The RC-1 abort + this analysis is itself high-quality evidence: measurement
methodology, honest failure, resource-governed architecture, staged
experimentation. A 1.5 GiB envelope that demonstrably hosts validated
fundamentals + Helm (+ staged GitOps) is MORE defensible in an interview than
an inflated cluster — it demonstrates capacity planning discipline. No
portfolio consideration justifies exceeding measured limits (priority order
binding).

## 14. Recommendation (evidence-based, NOT selected)

**A″ with a 1.5 GiB / 2-core envelope and staged validation** satisfies every
Phase 2 objective except full Argo CD; GitOps is achievable via a temporary
1.75 GiB window (Argo CD core) or deferral to Phase 5 with its own envelope
analysis. The margin analysis (1.0 GiB VM buffer retained) is what makes
1.5 GiB defensible against the 17-unlimited-container risk. If Paul prefers
full Argo CD demonstrated now, 1.75 GiB staged is the smallest defensible
step. **The choice is Paul's.**

## 15. Alternatives

A′ (wait for natural recovery — envelope unchanged, no new authorization
needed, but re-measure proves nothing about envelope adequacy), B (VM resize
— solves everything, restarts 21 containers), C (defer k8s entirely —
compose-only until AWS), D (hardware/environment separation). All remain
valid; none selected.

## 16. Remaining unknowns (explicitly not facts)

- [U] Real k3s idle RSS on THIS kernel/VM — the 600–850 MB is upstream+community
  class; first A″ run measures it before any other stage
- [U] Argo CD core real footprint — community range only
- [U] OLAP db growth trajectory (does it stabilize at 2 GiB or trend to 4 GiB?)
  — observable via weekly stats; affects future margin
- [U] Whether the OLAP db's memory is steady-state or cache-reclaimable under
  VM pressure — behavior under stress would reveal it, but stressing protected
  workloads is forbidden; treat as unknown and keep buffer
- [E→M conversion] Helm transient overhead — measured at its stage, not assumed
