# ADR-0007: Post-Level-4 Roadmap Re-Sequencing — Periodic Reproducibility Validation Selected

**Status:** ACCEPTED (decision recorded; implementation NOT authorized by this ADR)
**Date:** 2026-09-25
**Deciders:** Paul (authorization gate) with Hermes CTO analysis
**Supersedes:** none; refines the sequencing of ADR-0006 after Level 4

## Context

Level 4 (GitOps-layer reconstruction) is complete and independently audited.
The audit discovered and (under separate authorization, `aa4a6ac`) remediated
the evidence-authority defect L4-6: reconstruction success now requires
generated, validated, preserved evidence. The reproducibility maturity model
stands at Level 4 demonstrated. The original master-spec roadmap placed AWS
(Phase 8) next by number; ADR-0006 already rejected numeric ordering, and the
post-Level-4 diagnostic (`docs/history/roadmap-architecture-diagnostic.md`)
re-confirmed that rejection with fresh evidence.

## Existing evidence

- Runner + resource gate + evidence-authority gate: proven (20/20 clean path,
  11/11 report-authority tests, live poisoned-report regression exits 1).
- Failure injection and recovery: proven at Argo and application level (9/9).
- Memory: binding but managed constraint (1.5 GiB envelope; gate enforced
  before every disposable run; swap stable).
- No project-owned persistent state: DR (Level 5) has nothing to restore.
- Reconstruction correctness is proven **episodically** — only when run.

## Problem

Which capability comes next: tested DR (L5), periodic verification (L6),
continuous validation (L7), dependency automation, AWS/IaC, observability, or
AI maintenance?

## Options considered

1. **Level 5 DR** — rejected: no state exists to restore; inventing state to
   justify a phase violates the project's honesty rules.
2. **Level 7 continuous validation** — rejected for now: presupposes a proven
   scheduled model.
3. **Dependency automation** — valuable, but its safe test loop is scheduled
   reconstruction; building it on episodic validation inverts the dependency.
4. **AWS/IaC** — rejected: adds credentials/state/cost while the local
   abstraction is proven but not routinely verified; no current requirement.
5. **Observability** — rejected: no unresolved operational problem; every L4
   defect was root-caused with existing deterministic evidence; memory
   envelope argues against residency.
6. **AI maintenance** — rejected: deterministic limits not reached; no
   concrete first workflow.
7. **Level 6 periodic reproducibility validation** — SELECTED (below).

## Decision

The next implementation phase (when separately authorized) is **Level 6:
periodic reproducibility validation** — scheduled, resource-gated disposable
reconstruction with evidence retention and report-to-report drift comparison.
Sequencing consequence: dependency automation follows once scheduled
validation operates; AWS/IaC and AI remain deferred pending that foundation.

## Rationale

- Smallest implementation that converts Level 4 from a demonstrated capability
  into an operating one; reuses the entire proven machinery; no new
  technologies, credentials, or resident memory pressure.
- Fixes the actual bottleneck (temporal, not spatial): reconstruction truth
  over time, not another system component.
- Directly enables the next candidate: dependency-automation PRs can then be
  validated end-to-end by the scheduled machinery.

## Consequences

Easier: safe churn validation later; drift becomes observable; evidence
history becomes longitudinal. Harder: scheduling discipline required; a new
failure class (scheduled runs failing while humans sleep) must be visible by
design; report retention volume grows and needs a policy.

## Deferred alternatives

DR until project-owned state exists; Level 7 until L6 operates; AWS until
local verification is routine and a destroyable scope is justified;
observability until a demonstrated diagnostic gap; AI until deterministic
workflows reach their limit.

## Preconditions for the Level 6 authorization

Report authority stays enforced (done, `aa4a6ac`); resource gate unchanged;
scheduling mechanism adds no resident daemon; failure visibility without
auto-remediation.

## Future reconsideration triggers

A demonstrated operational problem the deterministic evidence cannot diagnose
(reconsiders observability); project-owned persistent state (reconsiders DR);
routine scheduled validation operating cleanly + a concrete cloud requirement
(reconsiders AWS); a deterministic workflow hitting a genuine reasoning limit
(reconsiders AI).

---

## Addendum — Implementation Outcome (2026-09-25, same day)

Level 6 was separately authorized and implemented (`cc654db`..`ddb628a`).
Result: **demonstrated**. Real scheduled runs exercised the full taxonomy
live — PASS, two BLOCKED (resource gate), one FAIL (dirty-tree WARN), then
PASS again — proving failure classes are distinguishable and a clean run
follows failure. Seven defects were found and fixed, six of them only
because validation ran on a schedule: a macOS-portability bug (no flock),
env/classification bugs, a mode-honesty bug, comparison-semantics bugs, and
two resource-gate signal corrections (raw swap-used threshold and
pageins-inclusive activity both conflated residency/readback with pressure —
the Phase 6 distinction chain has at least three failure modes). The gate
now follows the project's own principles: pressure level primary, pageout
activity secondary, free % context. Evidence retention and clean source
pinning were reconciled by classifying periodic evidence as retained local
runtime evidence (gitignored; representative records committed deliberately).

Deviations from the ADR's assumptions: none material. Level 7, dependency
automation, AWS, observability, and AI remain deferred under the conditions
recorded above.
