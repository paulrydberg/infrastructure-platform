# Initial Roadmap — infrastructure-platform

**Status:** Adopted (master spec §79 as baseline; adaptive per §80)

Baseline = the verbatim master spec (19 phases). Amendment 1 adds the
portfolio workstream; Clarification 1 disciplines it. Living status is
maintained in `../../docs/ROADMAP-STATUS.md` (single source for current
state — this document records the plan and per-phase requirements).

## Phase requirements (spec §80 — each phase must define)

objective · prerequisites · deliverables · dependencies · tests ·
exit criteria · risks · resource impact · security impact ·
reproducibility impact · documentation requirements

## Phase 0 — Discovery (current)

- **Objective:** complete measured inventory of host, resources, GitHub
  state, repo architecture options; produce all §92 first-milestone docs.
- **Deliverables:** discovery report set (../01-discovery/), origin docs,
  architecture docs, reproducibility contract v1, manifest v1, this roadmap,
  threat model, resource model, ADR-0001.
- **Exit criteria:** all artifacts exist; authorization boundary reached;
  findings reported to Paul.
- **Status:** complete pending Paul's review — READ-ONLY scope honored.

## Phase 1 — Local Container Foundation (proposed next)

- **Objective:** working, reproducible container foundation + first GitHub
  evidence.
- **Prerequisites:** repo authorized + created + pushed (gate 1); Docker
  coexistence rules agreed (gate 2 — no changes to existing containers).
- **Deliverables:** bootstrap/ skeleton (idempotent), first versioned
  application container (compose), health checks, logging, WUD evaluation,
  docs/03-foundation + docs/04-containers, v0.1.0 release candidate.
- **Tests:** build/start/stop/restart/recovery of the new app only.
- **Exit criteria:** fresh clone → bootstrap → app healthy, with zero
  undocumented manual steps (measured, reported honestly).
- **Risks:** shared Docker VM resource contention (mitigation: separate
  compose project, explicit limits).
- **Reproducibility impact:** reproducibility Level 0→1 target.

## Phases 2–19

Adopted as specified in the verbatim master spec §79 (Kubernetes → Final
Architecture), each with phase-scoped ADRs and exit criteria defined at
phase entry, not pre-asserted here. Deferred decisions are logged in the
discovery report and `../../docs/ROADMAP-STATUS.md`.

## Adaptivity rule (spec §80)

Reality overrides the roadmap through ADRs, never silent drift. The verbatim
prompts remain the architectural north star; changes are recorded, not
rewritten.
