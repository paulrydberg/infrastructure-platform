# Initial Vision — infrastructure-platform

**Status:** Defined (2026-09-24, from Paul's verbatim prompts)

## The original vision

Paul's master specification (2026-09-24) establishes the founding vision:

> «Build an infrastructure platform that can prove what it is, explain how it
> works, survive failure, reproduce itself, operate deterministically without
> AI, use AI intelligently when useful, and provide a complete engineering
> record of how it evolved from an empty machine into a functioning platform.»

The founding intent, in Paul's own framing:

- "This is not merely a homelab / Kubernetes install / AI agent project /
  portfolio website" — it is a coherent, reproducible, observable, secure,
  GitOps-managed, IaC-driven engineering platform.
- The machine is disposable; the source of truth is persistent.
- Self-reconstructing, NOT self-modifying.
- Deterministic first, AI as an optional escalation layer.
- A real engineering system first; portfolio evidence emerging from its quality.

## Constraints at founding

- Single shared Mac Mini (2018 Intel, 16 GB) already running production
  workloads for other projects.
- No cloud account, no cluster, no IaC at start (verified by Phase 0 discovery).
- Solo operator with an AI CTO (this system) as the engineering executor.

## Assumptions made at founding

- k3s is the presumptive local Kubernetes choice, pending discovery (spec §20
  requires justification — this assumption is explicitly NOT yet an ADR).
- Argo CD presumptive GitOps choice, pending Phase 5 evaluation.
- AWS is the target cloud, pending account existence (none found in discovery).

## Alternatives considered at founding

Recorded honestly: none were formally evaluated yet — the master spec
names candidate technologies but defers all selection decisions to
justified ADRs during the relevant phases. This document will be updated
as alternatives are actually evaluated (spec §46: do not rewrite history —
the empty evaluation record IS the accurate history at this point).

## What changed since founding

Nothing yet — the project is at the discovery boundary. This document is the
baseline against which future change will be recorded.
