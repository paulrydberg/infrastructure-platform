# ADR-0011: Repository Architecture — Monorepo Now, Hybrid Extraction Later

**Status:** ACCEPTED (architecture decision recorded; repository creation
and any extraction remain separately authorization-gated)
**Date:** 2026-10-30
**Deciders:** Paul (authorization gate) with Hermes CTO analysis

## Context

The repository-architecture analysis (15-point discovery,
`docs/01-discovery/github-portfolio-and-repository-architecture.md`) and the
source-of-truth matrix (`docs/architecture/repository-source-of-truth.md`,
Amendment 2) converged on a recommendation but the decision itself was
pending. This ADR records it.

The project currently operates a single public monorepo
(`paulrydberg/infrastructure-platform`) containing: documentation and
decision records, bootstrap/reproducibility tooling, the platform-demo
application and Helm chart, CI workflows, and the policy/security pipeline.
Several future domains were always expected to become separate repositories
(cloud IaC, AI operations) because their state models differ from Git
(IaC remote state, queue state).

## Problem

Should the project remain a monorepo permanently, split into per-domain
repositories now, or adopt a staged (hybrid) path — and what must be true
before any split happens?

## Options considered

**A. Permanent monorepo.** Simplest; one clone reconstructs everything.
Rejected long-term: future domains (IaC state, AI operations queue state)
have state models and audience-separation needs that conflict with a single
public tree; monorepo grows unboundedly in history size and review noise.

**B. Immediate multi-repo split.** Clean domain boundaries on day one.
Rejected now: the platform's core reproducibility claim — "a fresh machine
reconstructs from Git" — is demonstrably working against exactly one
repository; splitting before the evidence accumulates multiplies
cross-reference pinning overhead (multiple remotes, multiple CI surfaces,
secret-scoping per repo) with no evidence-driven need, and would invalidate
the reconstruction manifest for no measured benefit.

**C. Hybrid, staged (RECOMMENDED).** Stay monorepo while the platform
portfolio core is the active workstream; extract a domain into its own
repository only when that domain has real, deployed content and its state
model demands separation. Every extraction event follows the documented
procedure (source-of-truth matrix update → reconstruction-manifest update →
external-dependency register → re-run reconstruction validation → roadmap
record).

## Decision

Adopt **C — monorepo now, evidence-gated hybrid extraction later.**

Rules (binding on future work):

1. The flagship repository is and stays
   `paulrydberg/infrastructure-platform` until an extraction ADR is
   approved by Paul.
2. One domain = exactly one owning repository at any time (never split a
   domain's truth across repos).
3. Cross-references use immutable pins (image@sha256, chart version,
   commit SHA) so a future split cannot silently repoint truth.
4. The dependency direction stays acyclic:
   applications → platform contracts → flagship portfolio.
5. Secrets remain external to all repositories regardless of count
   (Amendment 2 invariant; unchanged).
6. An extraction is complete only when the platform can still reconstruct
   itself from the new layout — re-validated, not assumed.

## Consequences

- No new repositories are created by this ADR. GitHub Projects setup and
  the portfolio docs tree (§16/§28) proceed inside the monorepo as work
  becomes real.
- Future Phase 8 (AWS/IaC) and AI-operations work start inside the
  monorepo (`infrastructure/`, `ai/` paths per the source-of-truth matrix)
  and carry a pre-written extraction trigger: real deployment + state-model
  separation + operator authorization.
- The Reconstruction Manifest remains single-repository today; the
  extraction event procedure in the source-of-truth matrix is the
  contract that keeps it authoritative after any split.

## Related decisions

- ADR-0003 (flagship repository creation, branch protection, secret
  scanning) — unchanged.
- ADR-0007 (post-Level-4 roadmap re-sequencing) — unchanged.
- Source-of-truth matrix v1 — this ADR is the decision it awaited.
