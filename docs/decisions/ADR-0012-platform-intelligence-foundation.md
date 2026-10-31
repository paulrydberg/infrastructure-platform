# ADR-0012: Platform-Intelligence Foundation — Deterministic Collectors Before Resident Stacks

**Status:** PROPOSED (adopted as working direction by the 2026-10-30 CTO
directive; final ACCEPTANCE gated on Paul's review)
**Date:** 2026-10-30
**Deciders:** Paul (directive scope) with Hermes CTO analysis

## Context

Phase 6 (closed 2026-09-24) established that the host's binding constraint
is in-cluster memory (k3s 1.5 GiB cap; ~488 MiB headroom [M]) and codified
the residency≠pressure gate doctrine. The 2026-10-30 refresh
(`observability-architecture-assessment-2026-10-30.md`) adds new evidence:
host free space now oscillates 13–36 GiB [M] (9 scheduled-gate FAILs), host
swap residency reached 11.1 GiB [M], and the platform's continuous
telemetry remains absent while its *deterministic evidence machinery*
(validation records, readiness evaluator, health checks) works well.

Tier-B (Prometheus/Grafana/Loki) estimates (+500–900 MB [E]) remain
unmeasured and cannot safely run as residents under either constraint.

## Problem

How should the platform gain operational intelligence — for capacity
forecasting, deployment readiness, drift detection, and incident evidence —
without installing resident observability stacks that the measured
environment cannot yet support?

## Options considered

**A. Deploy the minimal resident stack now.** Rejected: Tier-B estimates
exceed measured in-cluster headroom; host storage oscillation makes any
disk-growing TSDB/log store a gate risk; converting [E]→[M] first is the
established methodology.

**B. Staged observation windows only.** Valid as the [E]→[M] conversion
means (Phase-5A precedent) but produces no continuous capability between
windows and requires the capacity gate to pass first.

**C. Deterministic collector/evaluator layer (RECOMMENDED).** Build the
platform-intelligence capabilities (snapshot collection, readiness
evaluation, drift detection, evidence bundling, forecasting) as
repo-owned, schema-validated, zero-inference scripts. They consume
point-in-time read-only probes, produce machine-readable evidence, and
require no resident services.

## Decision

Adopt **C**: the platform-intelligence layer is deterministic collectors
and evaluators first (`platform-intelligence-capability-roadmap.md`,
PI-1…PI-6). Resident stacks (PI-7) stay RED behind the capacity gate and a
separate authorization. The deterministic layer:

1. produces schema-validated JSON evidence with provenance (timestamp,
   tool versions, thresholds used);
2. reuses — never weakens — the existing gate thresholds
   (`bootstrap.sh` 50 GiB deployment gate, reconstruct.sh memory gate,
   readiness criteria);
3. fails closed: missing evidence → INSUFFICIENT_DATA / NOT_READY, never
   inferred success;
4. keeps LLM inference at 0 for all verdict paths (Phase 11 boundary).

## Consequences

- The platform gains forecasting/readiness/drift/evidence capabilities
  that work at ANY capacity level, unblocking intelligence work during the
  storage remediation (per the 2026-10-30 capacity-gate scope decision).
- When the capacity gate passes and Tier-B windows are authorized, the
  collector layer provides the sampling scaffolding the windows need.
- New artifacts land in the repo with tests; CI runs the full existing
  suite unchanged (additive).

## Related

- ADR-0011 (repository architecture) — unchanged; artifacts live in this
  monorepo.
- Phase 6 chain — this ADR implements its "methodology upgraded" outcome.
