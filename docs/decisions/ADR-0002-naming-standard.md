# ADR-0002 — Professional Repository Naming Standard & Positioning

**Status:** Accepted
**Date:** 2026-09-24
**Deciders:** Paul Rydberg (authorizer), Hermes CTO (author)
**Supersedes:** nothing (new decision domain)
**Complements:** ADR-0001; Phase 0 repository-architecture finding (unchanged)

## Context

Phase 0 concluded: monorepo → hybrid evolution, splits only on justified
engineering boundaries. Amendment 2 then supplied a professional repository
NAMING STANDARD (infrastructure-platform, infrastructure-as-code,
container-platform, deployment-platform, observability-platform,
security-platform, operations-automation, incident-management, ai-operations)
plus employment-portfolio positioning rules (environment described honestly;
system named by engineering function; no hobby-context names; priority order
correctness → … → portfolio visibility).

## Problem

The naming standard could be misread as a mandate to create repositories. It
must instead operate WITHIN the Phase 0 architecture without weakening the
boundary rule — and the naming/positioning choice itself is an architectural
decision that belongs on the record.

## Options

1. Treat names as a build list — rejected: violates Amendment 1 §31,
   Clarification 1, and Amendment 2's own critical rule.
2. Ignore naming until repos exist — rejected: naming shapes README/docs/
   positioning written in Phase 1; retrofitting is a history rewrite.
3. Adopt the naming standard as the preferred naming layer over the earned-
   boundary architecture; record positioning rules — selected.

## Decision

1. **Phase 0 conclusion stands unmodified:** flagship
   `infrastructure-platform` first; additional repositories only when
   boundary criteria are satisfied and documented via ADR.
2. **Amendment 2's names are adopted** as the preferred professional naming
   standard for any repository the architecture eventually justifies. Hobby-
   context public names are prohibited.
3. **Candidate evolution recorded** (NOT committed): infrastructure-platform
   → + infrastructure-as-code / operations-automation / ai-operations;
   container-platform, deployment-platform, observability-platform,
   security-platform, incident-management remain available options.
4. **Positioning adopted:** environment = personal development/validation
   environment (stated honestly); system = professionally named engineering
   platform; capability claims only where implementation substantiates them.
5. **Portfolio priority order adopted** (Amendment 2, 10 levels).
6. Documentation integrated: docs/architecture/github-repository-architecture.md,
   docs/architecture/repository-source-of-truth.md,
   docs/career-evidence/capability-matrix.md,
   docs/career-evidence/engineering-evidence.md.

## Rationale

The boundary rule (when to split) and the naming standard (what to call a
split) are orthogonal. Adopting the naming layer now prevents unprofessional
naming from ever becoming load-bearing in READMEs, CI, docs, or releases,
without creating premature structure.

## Consequences

- Positive: consistent professional naming from the first commit; honest
  positioning framework; no retrofit cost later.
- Negative/cost: none material; the candidate-state list must be policed so
  it is never treated as a roadmap commitment (mitigated by this ADR + the
  boundary rule in OPERATING-INSTRUCTIONS.md).

## Alternatives considered

Documented above.

## Future reconsideration

Any actual repository split gets its own ADR (per Amendment 2 boundary rule).
If the flagship repo needs renaming before first push (not expected — name
verified available), that would be a new ADR.
