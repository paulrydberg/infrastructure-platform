# ADR-0001 — Project Foundation

**Status:** Accepted
**Date:** 2026-09-24
**Deciders:** Paul Rydberg (authorizer), Hermes CTO (author)

## Context

A greenfield infrastructure/platform engineering project is beginning on a
shared Mac Mini (2018 Intel, 16 GB, macOS 15.7.9) that simultaneously hosts
~20 production containers and Hermes agent infrastructure for other projects.
Master specification + Amendment 1 + Clarification 1 define goals: self-
reconstruction, deterministic-first operation, optional AI, honest portfolio.
Phase 0 discovery (2026-09-24, read-only) measured the environment and the
GitHub account state (135 repos, 133 private, no infrastructure-platform
repo, no orgs, no cloud account).

## Problem

The project needs a documented foundation: where its source of truth lives,
what the working structure is, and which constraints bind all future
decisions — before any installation or implementation begins.

## Options

1. Begin implementation immediately, document later — rejected: violates
   spec §91 and the reproducibility contract.
2. Documentation-only foundation in a non-versioned local directory —
   rejected: the project would itself violate its core principle (state
   existing only on one machine).
3. Documentation-first foundation under version control, implementation
   deferred behind explicit authorization gates — selected.

## Decision

1. Project source of truth = GitHub repository `paulrydberg/infrastructure-
   platform` (monorepo start, hybrid extraction possible via future ADRs —
   full analysis in docs/01-discovery/github-portfolio-and-repository-
   architecture.md; formal repo decision = ADR-0011 at creation time).
2. Working structure = the existing `~/.hermes/projects/infrastructure-
   platform/` documentation tree, migrated into the repository at Phase 1 start.
3. Binding constraints adopted (see OPERATING-INSTRUCTIONS.md): read-only
   discovery per phase gate; deterministic-first; no manufactured portfolio
   activity; secrets never in source; coexisting production services untouchable.
4. Phase 0 closes with the discovery report; Phase 1 (container foundation +
   repo creation/push) begins only on explicit authorization.

## Rationale

Option 3 is the only option consistent with the spec's own operating rules
(inspect before changing, record decisions, never depend on undocumented
state) and with the reproducibility contract, which currently shows the
project's own documentation as NOT reconstructible — the first debt to retire.

## Consequences

- Positive: foundation is reviewable; every later phase inherits an auditable
  baseline; the portfolio emerges from the record itself.
- Negative/cost: documentation overhead per phase (accepted — documentation
  is priority 10 but a first-class system per spec §45).
- Neutral: repo visibility (public/private) remains an open Paul decision.

## Alternatives considered

Documented above. No other repository names were considered — spec §54 fixes
the professional naming convention, and the name is verified available.

## Future reconsideration

Revisit if: (a) the host's shared-workload situation changes materially,
(b) additional operators join, (c) cloud phase (8) requires state-boundary
separation — each would trigger a new ADR, not a edit of this one.
