# AI Architecture — infrastructure-platform

**Status:** Design (Phase 0; AI is NOT part of the deterministic core)

## Position in the architecture

AI is an optional reasoning layer above a fully functional deterministic
platform (spec §3–6). With every AI capability removed, the platform must
still: deploy, monitor, alert, roll back, rebuild, and validate.

## Design (from spec §4–6, §61–65, adapted to measured hardware)

### Task lifecycle

```
EVENT → DETECT → CLASSIFY → deterministic handling
  → unresolved? → reasoning valuable?
    → QUEUE (AI task, states per spec §5)
    → resource check (this host: CPU/RAM/disk + Hermes daily token budget)
    → provider/model selection (API-based; no local GPU — see constraints)
    → inference → analysis → proposal
    → branch/PR → CI → security/policy → staging
    → authorization → GitOps deploy → observe → report
```

### Task states (spec §5, verbatim)

PENDING / WAITING_FOR_RESOURCES / RUNNING / COMPLETED / FAILED / TIMED_OUT /
CANCELLED / REJECTED / WAITING_FOR_APPROVAL / VALIDATION_FAILED

### Resource governance on THIS host (documented deviation)

Spec §5 contemplates CPU/RAM/GPU/VRAM gates. Measured reality: no discrete
GPU, 16 GB shared RAM already ~60% consumed by Docker VM, and a host-level
daily LLM token budget (soft $2.50/day, hard $3.00/day). Therefore:

- GPU/VRAM gates → not applicable (recorded, not silently dropped)
- token cost + rate limits → first-class governed resources alongside CPU/RAM
- local inference → deferred unless hardware changes (would need its own ADR)
- AI workload scheduling must yield to platform + coexisting production
  containers (WAITING_FOR_RESOURCES state is mandatory, not optional)

### Safety rules

The 20 rules of spec §66 are adopted verbatim as binding, including:
inspect before modifying, never fabricate test results, never expose secrets,
prefer branches/PRs, respect autonomy level, never make the platform
dependent on its own continued inference.

### Autonomy ladder (spec §39)

Start at Level 0–1 (observe/report). Higher levels are EARNED through
testing, observability, rollback capability, and demonstrated reliability —
each promotion recorded as an ADR.

### Provider abstraction (spec §62)

Providers are interchangeable records: {provider, model, capabilities, cost,
latency, context, resource requirements, availability}. Task classification
(spec §63) drives selection; the most expensive model is never the default.

### Observability of AI itself (spec §65)

Queue depth, wait time, execution time, token usage, failures, timeouts,
retries, provider availability, human rejection rate — all monitored as
platform metrics, so AI never becomes an opaque black box.
