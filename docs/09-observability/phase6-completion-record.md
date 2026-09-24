# Phase 6 — Observability: Completion & Decision Record (2026-09-24)

**Status: Phase 6 CLOSED.** No observability component is installed or
retained. metrics-server is experimentally validated, not retained. Tier B/C
remain unimplemented and unauthorized. This record ties the complete Phase 6
chain together; each linked document is the authoritative detail.

## The complete chain

```
capacity analysis (read-only, 6-sample baseline)
    ↓
Tier-A decision gate → GO recommendation (bounded experiment design)
    ↓
metrics-server v0.7.2 experiment (pinned, Git-sourced)
    ↓
swap-gate event (625.75 → ~1260 MB during 55-min window)
    ↓
conservative rollback (causality uncertain → gate applied as written)
    ↓
swap-driver characterization (read-only, idle-host decline observed)
    ↓
resource-gate refinement (residency ≠ pressure principle)
    ↓
Phase 6 decision (this document)
```

Authoritative artifacts, in order:

1. **Capacity analysis** — `capacity-analysis.md` (read-only baseline,
   architecture matrix A–E, Tier-A 60–100 MB [E] estimate, storage NOT
   binding — memory is)
2. **Decision gate** — `decision-gate-report.md` (12-point report, GO with
   pre-defined abort/success criteria and 60-min window)
3. **Experiment** — `tier-a-experiment.md` + `tier-a-observation.log`
   (pinned v0.7.2, upstream SHA-256 verified, sole delta = resource limits)
4. **Characterization** — `swap-driver-characterization.md` (read-only)
5. **Refined principle** — `resource-gate-principles.md` (reusable platform
   doctrine)

## Tier-A final classification (unchanged, verbatim)

**FUNCTIONAL VALIDATION SUCCESSFUL / SWAP GATE TRIGGERED / CAUSALITY
UNCERTAIN** — closed via documented rollback. This is not retroactively
upgraded to a clean PASS. The subsequent characterization showed the
gate *indicator* (raw swap-used) was too coarse, which is legitimate
engineering history: experiment → gate fired → conservative rollback →
characterization → gate interpretation improved.

## The measured facts that matter [M]

- metrics-server: **16–20 MiB** footprint (vs 60–100 MB [E] estimate) — the
  estimate class was conservative; `kubectl top` worked; 0 restarts
- k3s: **1.005–1.058 GiB of 1.5 GiB** through the entire window (in-cluster
  memory was never the constraint)
- Protected fleet: **0 restarts, 0 OOMs** across the whole experiment
- Argo CD: Synced Healthy every sample; platform-demo healthy
- Host: pressure level NORMAL, 76% free, swap-in activity zero at rest,
  swap declining when idle — the swap event was residency, not pressure
- No repeatable swap driver identified; clickhouse temporally associated
  with normal variation (±8.3%), causality NOT established

## What this does NOT establish

- **Nothing about Prometheus/Grafana/Loki sizing.** The Tier-A result does
  not extrapolate: Tier B's minimal Prometheus-oriented stack is still the
  **+500–900 MB [E]** estimate and is a different order of magnitude from a
  16–20 MiB metrics-server. Its decision requires its own measured analysis:
  Prometheus memory behavior, storage/retention, scrape cardinality, query
  workload, Grafana overhead, persistence, failure/restart behavior,
  protected-fleet interaction, and whether the observability value justifies
  the envelope. Tier B remains a separate, unauthorized capacity question.

## Phase 6 outcome for the platform

1. **Methodology upgraded:** resource governance must measure actual
   pressure and degradation, not merely resource residency — codified in
   `resource-gate-principles.md` (primary vs secondary signals; swap-used
   insufficient alone on macOS/Docker Desktop).
2. **Reproducibility demonstrated:** pinned manifest under Git, SHA-256
   verified, clean documented rollback, zero residual resources.
3. **In-cluster headroom confirmed:** ~442 MiB remained at experiment peak;
   the 1.5 GiB envelope remains experimentally sound for the current fleet.
4. **Portfolio evidence:** a complete honest arc — estimate → gate →
   failure → investigation → principle — preserved in public Git history.

## Next

See the roadmap decision memo for candidate next phases. No Tier B, no
metrics-server re-run, no VM resize, no protected-workload changes.
