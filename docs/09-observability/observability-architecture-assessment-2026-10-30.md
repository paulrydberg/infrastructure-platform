# Observability Architecture Assessment — 2026-10-30 (READ-ONLY / PLANNING)

**Status:** Assessment complete. Nothing installed, nothing reconfigured,
no gates changed. This document refreshes `capacity-analysis.md` (2026-09-24)
with 2026-10-30 measurements, evaluates the four deployment postures the
operator requested, and defines the platform-intelligence capability roadmap
in `platform-intelligence-capability-roadmap.md`.
**Evidence classes:** **[M]** measured on this host 2026-10-30 · **[D]**
documented upstream requirement · **[E]** estimate · **[A]** assumption.

---

## 1. Current-state assessment (2026-10-30, all [M] unless noted)

### Host (macmini)

| Metric | Value | vs 2026-09-24 baseline |
|---|---|---|
| Host Data volume free | **26 GiB** (oscillated 13→36 GiB across the day; 9 scheduled-gate FAILs at 13–35 GiB) | was 189 GiB — materially worse; TM snapshot pinning + Nextcloud growth (158G) |
| Host swap | **11.1 GiB used of 12 GiB** (pressure NORMAL; residency-dominated per `resource-gate-principles.md`) | was 0.5–0.7 GiB — materially worse |
| Docker VM memory | 7.654 GiB total | unchanged |
| Fleet containers | 24 (protected fleet + k3s + platform stack) | was 22 |

### In-VM / k3s

| Metric | Value | Class |
|---|---|---|
| k3s-server container | **1.066–1.067 GiB of 1.5 GiB cap (71%)** | [M] |
| platform-demo | 107 MiB of 128 MiB limit | [M] |
| k3s pod set | argocd ×5, coredns, local-path-provisioner, platform-demo — all Running, 29d age | [M] |
| Argo CD restart counts | controller 58 · appset 80 · redis 74 · repo 55 · server 65 (29d) | [M] — OOMKill-restart signature already known from Phase 5A; unchanged behavior |
| VM root filesystem | 687G, 49G used, **603G free (8%)** | [M] |
| VM available memory (`free -m`) | 7838 total / **2952 MB available** | [M] — improved vs Sep-24's ~1840 MB available |
| metrics-server | **not installed** (`kubectl top` fails) — Phase 6 rollback intact | [M] |

### Existing telemetry, logging, tracing capabilities (measured)

- **Metrics:** none continuous. metrics-server not resident; evidence comes
  from point-in-time `docker stats`/`kubectl` sampling by documented runs.
- **Logging:** container stdout via Docker json-file (unindexed, unqueried);
  host logs via `hermes logs` (agent/gateway/adaptive-runtime). No aggregation.
- **Tracing:** Langfuse **server is healthy** (v3.175.0 at :3010, API-verified
  2026-10-30) but the **Hermes→Langfuse export path is dead since 2026-06-02**
  (~150 days, long-running P0 `t_f7d0b4ae`) — traced to placeholder-format
  credentials in the gateway environment (verified 2026-10-30: gateway
  launchd env carries no Langfuse key set; `sk-lf-` prefix validation fails).
  Repair is Hermes-runtime work — explicitly out of scope here.
- **Operational evidence stores that already work:** Level 6 validation
  records (19 records, schema-validated), readiness evaluator (NOT_READY,
  deterministic), daily health checks (6 PASS / 1 INFO, 2026-10-30), kanban
  blocked-task automation (31 blocked tasks tracked deterministically).

**Binding constraints, restated with 2026-10-30 evidence:** in-cluster memory
(k3s 1.5 GiB hard cap, ~488 MiB headroom [M]) outranks everything for
in-cluster components; host free-space **oscillation** (13–36 GiB [M]) makes
any host-disk-growing component (TSDB, log segments, trace backend) a gate
risk regardless of its memory footprint; VM-disk (603G free [M]) is NOT
binding.

## 2. Deployment-posture comparison

The four postures requested, evaluated against the binding constraints.
Component footprints inherit the Sep-24 matrix (`capacity-analysis.md` §4:
metrics-server [M] 16–20 MiB; Prometheus-min [E] 500–900 MB; Grafana [E]
100–200 MB; Loki [E] 300–500 MB; Alertmanager [D] 30–60 MB; OTel+backend [E]
300–800 MB).

| Posture | Added memory | Gate risk | Failure domain | Operational complexity | Verdict |
|---|---|---|---|---|---|
| **1. Minimal footprint** (metrics-server only, permanent) | 16–20 MiB [M] | none measured | none (stateless) | ~zero | **VIABLE but low value alone** — `kubectl top` without history |
| **2. Staged deployment** (Tier-B stack in scheduled observation windows; Phase-5A install→measure→remove precedent) | 500–900 MB [E] *during windows only* | bounded by pre-defined abort gates; VM returns to baseline after | window-scoped; no continuous history, no real-time alerting | medium (window orchestration + evidence capture) | **VIABLE for [E]→[M] conversion** — the honest next step before any permanent claim |
| **3. Externalized** (Grafana Cloud free tier / remote-write sinks) | ~0 local; agent 30–80 MB [E] | low memory; **new** third-party dependency + infra-detail egress (privacy/sanitization gate) + network dependence | external outage = blind platform; data leaves the operator's trust boundary | low local / new external | **Recorded alternative, not evaluated further** without authorization (Sep-24 memo position unchanged) |
| **4. Hybrid** (local deterministic evidence + control-plane visibility; storage-heavy telemetry external or absent) | local part = posture-1 scale; deterministic collectors ~0 | lowest of all postures | local collectors fail closed (missing evidence ≠ false confidence) | low | **RECOMMENDED** — see ADR-0012 |

**Explicit recommendation:** posture **4**, with posture **2** as the
authorized-means to convert Tier-B estimates into measurements when (and only
when) the 50 GiB deployment gate passes. Postures 1 and 3 are not adopted.
The full Prometheus/Grafana/Loki/OTel stack remains inappropriate for this
host today — the recommendation is component-independent evaluation, exactly
as the operator directed.

## 3. Storage/retention modeling (posture 2/4 preconditions) [E]

- Prometheus-min TSDB at this fleet (~200 active series, 30s scrapes):
  ≈1–3 GB/week [E, inherited from Sep-24 matrix] — **unacceptable on the host
  volume during an oscillation regime (13–36 GiB free [M])**; acceptable
  inside the VM (603G [M]) for a bounded observation window with retention
  ≤48h and pre-defined teardown.
- Loki/log segments: retention-bound; same verdict — window-scoped only.
- Trace backends: storage-hungriest; Tier C stays deferred (engineering-
  usefulness rule, spec §81) — no current diagnostic need demonstrated.
- Deterministic JSON evidence collectors (posture 4): ~2–10 KB/sample,
  cron-grade — negligible on any storage regime.

## 4. What this assessment does NOT establish

- No [E]→[M] conversion for Tier B: no Prometheus/Loki/Grafana has run here.
- No alert-content design (depends on metrics that do not exist yet).
- No Langfuse export repair (Hermes-runtime scope, separately gated).
- No VM-resize decision (Paul's, with the Sep-24 §8 implications unchanged).

## 5. Next-step recommendation

Proceed in `platform-intelligence-capability-roadmap.md`: implement the
deterministic capability layer (GREEN, repo-only), stage Tier-B window
design (AMBER, awaiting gate + authorization), keep resident stacks RED.
