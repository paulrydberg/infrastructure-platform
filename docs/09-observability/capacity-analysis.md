# Phase 6 Capacity Analysis — Observability (READ-ONLY / PLANNING)

**Status:** Analysis complete (2026-09-24) — nothing installed; Argo CD state
preserved intact; stopped at Phase 6 implementation decision boundary.
**Evidence classes used throughout:** **[M]** measured on this host ·
**[D]** documented upstream requirement · **[E]** estimate · **[A]** assumption ·
**[U]** unknown.

---

## 1. Current baseline (Stage 6.2 — measured, 6 samples over ~90 s) [M]

| Metric | Value |
|--------|-------|
| Docker VM total / used / available | 7838 / 5691 / **1827–1851 MB** (avg ≈ 1840) |
| k3s container RSS / cap | **1.046–1.05 GiB / 1.5 GiB** (~70% of cap) |
| Argo CD per-component (cgroup) | controller 63.7 · repo-server 57.5 · server 25.3 · appset 22.9 · redis 4.8 = **~174 MB** |
| Container memory sum (22) | 5174 MB (k3s 1057 · platform-demo 27 · protected fleet 4091) |
| VM non-container overhead | ~470–660 MB |
| Host load | 3.2–3.8 of 12 threads |
| Swap | 495–657 MB (fluctuating, no sustained escalation) |
| k3s API `/readyz` latency | 0.278–0.337 s round-trip (healthy) |
| Argo sync/health | Synced Healthy (preserved intact) |
| Protected containers | 20/20 running, no restarts, no OOMs |

## 2. Storage baseline (Stage 6.5 — measured) [M]

| Item | Value |
|------|-------|
| Host Data volume | 699 Gi, 189 Gi free |
| Docker VM disk file | 54 GB on host |
| VM root filesystem (inside) | 686.6G, 55.5G used, **596.1G free** |
| Docker images / build cache reclaimable | 36.9 GB + 13.9 GB |
| k3s PVs | **none** (no PVCs yet) |
| k3s data dir | on VM root (597 GiB free) |

**Storage conclusion:** disk is NOT the binding constraint (596 GiB free inside
VM; host has 189 Gi). Memory is. Long-retention logging would still be a
disk-growth concern (WAL/segments) — bounded by retention policies.

## 3. Observability target (Stage 6.1)

| Tier | Components | Function |
|------|-----------|----------|
| **A (minimum viable)** | metrics-server or Prometheus (scrape, short retention) + k8s/cAdvisor metrics + Grafana (or raw PromQL) | cluster/container/app metrics + basic dashboards |
| **B** | + alerting (Alertmanager or Grafana alerts) + Loki/Promtail (centralized logs) | operational awareness |
| **C (full target)** | + OpenTelemetry collector + distributed tracing + long-retention telemetry + extra exporters | full spec §24 stack |

Selection rationale: Tier A answers "is the platform healthy, what changed,
what consumed resources" (spec §24 core questions). Tier B adds incident
capability. Tier C is portfolio-nice but not operationally required at this
scale — explicitly deferred on engineering-usefulness grounds (spec §81).

## 4. Component requirements (Stage 6.3 — sources documented)

| Component | Version (pinned candidate) | Memory [class] | Storage | Sources |
|-----------|---------------------------|----------------|---------|---------|
| metrics-server | v0.7.2 | **[D]** 60–100 MB working set; kubelet-in-cluster alternative = 0 | none | kubernetes-sigs docs [D] |
| Prometheus (single, constrained) | v2.54.x / chart 25.x | **[D]** upstream: 2 GB+ general guidance; **[E]** constrained configs (small retention, 1 replica) realistically 400–700 MB RSS with ~200 series-scrape load | WAL + TSDB: **[E]** 1–3 GB/week at this fleet size, bounded by retention | prometheus docs [D]; sizing [E] |
| Grafana | v11.x | **[D]** ~100–200 MB typical | negligible (dashboards in Git) | grafana docs [D] |
| Loki (single binary) | v3.x | **[D]** upstream: ~1 GB guidance; **[E]** small-fleet realistic 300–500 MB | log segments: retention-bound | grafana/loki docs [D]; sizing [E] |
| Promtail/Alloy | current | **[E]** 50–100 MB | none | [D] |
| Alertmanager | v0.27.x | **[D]** ~30–60 MB | negligible | [D] |
| OTel collector + Tempo/Jaeger | current | **[E]** 300–800 MB combined | trace backends are storage-hungry | [D/E] |

**Explicitly labeled:** everything above except the [D] minimums is class
[E] — NOT measurements. The purpose of the next authorized phase would be to
convert [E]→[M] for whichever architecture Paul selects.

## 5. Current envelope calculation (Stage 6.4) [M]

```
k3s container cap               1536 MiB (hard)
k3s current RSS                  1048 MiB   (k3s core ~870 + Argo ~174 + demo ~27)
k3s headroom inside cap           ~488 MiB
VM available                     ~1840 MB
VM margin policy (5A precedent)  envelope + 750 MB margin
```

**The binding insight:** adding observability INSIDE k3s consumes the ~488 MiB
in-cap headroom. Anything whose [E] footprint exceeds ~450 MiB risks the cap
(Phase 2's RC-2-style failure). Anything added also reduces VM available by
the same amount.

## 6. Candidate architecture matrix (Stage 6.4/6.6)

| Architecture | Expected added memory [E] | k3s in-cap fit? | VM avail after | Classification | Evidence |
|--------------|--------------------------|-----------------|----------------|----------------|----------|
| **A. metrics-only** (metrics-server only) | 60–100 MB | ✅ yes (headroom → ~400 MiB) | ~1750–1790 MB | **FITS CURRENT ENVELOPE** | [D] sizing + measured headroom |
| **B. metrics + dashboards** (metrics-server + Grafana) | 160–300 MB | ⚠️ borderline (headroom → ~190–330 MiB) | ~1550–1690 MB | **FITS WITH TIGHT LIMITS** | [E] Grafana sizing |
| **B+. Prometheus-min + Grafana** (short retention, 1 replica) | 500–900 MB | ❌ exceeds cap | — | **STAGED ONLY** or **REQUIRES VM RESIZE** | [E]; staging = deploy → validate → remove |
| **C. metrics + dashboards + logs** | +400–600 MB (Loki+Promtail) | ❌ | — | **REQUIRES VM RESIZE** (or external) | [D/E] |
| **D. + tracing (OTel/Tempo)** | +300–800 MB | ❌ | — | **NOT CURRENTLY JUSTIFIED** (Tier C deferred) | [E] + engineering-usefulness rule |
| **E. staged observability windows** | any (sequentially) | ✅ by construction | restored after each window | **VIABLE NOW** (5A precedent: install→measure→remove) | measured in 5A |

## 7. Staged-operation analysis

Proven viable (Phase 5A did exactly this with Argo). A Tier-B stack could run
as scheduled observation windows: deploy → measure → capture evidence →
teardown → VM returns to 1840 MB. Trade-off [A]: no continuous history —
metrics only exist during windows; alerting is not real-time. Operational
usefulness: genuine for capacity experiments, insufficient for continuous
SRE practice.

## 8. VM-resize implications (not authorized; implications only)

Raising Docker Desktop to 10–12 GiB would add ~2.3–4.3 GiB VM available:
unlocks Tier B/C permanently. Cost: Docker restart restarts all 22 containers
(protected fleet impact — brief outage for coexisting projects), requires
Paul's authorization, and expands the envelope the 17 unlimited protected
containers can consume. Decision = Paul's, informed by this matrix.

## 9. External-observability implications

Hosted/external options (Grafana Cloud free tier, self-hosted elsewhere,
GitHub-hosted metric sinks) would add zero local memory: metrics leave via
remote-write. Trade-offs: new external dependency (register in
external-dependency-register), data egress of infra details to a third party
(privacy/sanitization decision), network dependence. Recorded as a legitimate
alternative — not evaluated further without authorization.

## 10. Recommendation (evidence-based; NOT selected)

**Recommended next experiment (Tier A minimal): metrics-server only** —
60–100 MB [E], fits the envelope with ~400 MiB remaining headroom, no VM
change, no staging complexity, and it unblocks `kubectl top` (replacing the
crictl/cgroup probes used throughout Phases 2–5 — a real operational gain).
Tier B (Grafana) is the smallest next step after that. Tier B+ (Prometheus)
and beyond require the VM-resize or staged-window decision — Paul's call.
**The recommendation is based on [E] sizing that must be converted to [M] by
measurement during any authorized implementation.**

## Constraints / assumptions / unknowns

- **Constraints:** k3s cap 1.5 GiB (unchanged); protected fleet untouchable;
  no VM resize this phase; Argo stays resident (working system preserved).
- **Assumptions:** [A] protected fleet's ~4.1 GB container memory remains
  steady (it has been stable across all phases, but 17/20 are unlimited-cap).
- **Unknowns:** [U] real Prometheus/Grafana/Loki RSS on THIS kernel (only [D]
  guidance + [E] sizing exist); [U] actual scrape-series count until metrics
  exist; [U] whether the OLAP db grows further (stable 1.9–2.1 GiB observed
  across all phases so far).

## Explicit next-phase gate

Paul selects: (1) Tier A experiment (metrics-server) inside the envelope,
(2) Tier B staged windows, (3) VM resize then Tier B/C permanently, (4)
external observability, or (5) defer Phase 6 entirely. **Nothing installs
without that authorization.**
