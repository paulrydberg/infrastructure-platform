# ADR-0005: Phase 7C Policy Selected by Historical Simulation;
# Enforcement Deferred Behind Shadow-Mode Gate

**Status:** Accepted (design decision; implementation NOT authorized yet)
**Date:** 2026-09-24
**Supersedes (refines):** the threshold sketch in ADR-0004 / phase7c-proposal.md

## Context

ADR-0004 proposed CI-first thresholds ("CRITICAL-with-fix > 0; HIGH-with-fix
older than 30 days") without testing them against historical data. The
simulation record (phase7c-policy-simulation.md) evaluated candidate
policies against the project's two authoritative scan inventories
(7A alpine3.20: CRIT 2 / HIGH 16; 7B alpine3.22: CRIT 0 / HIGH 10).

## Decision

1. Adopt **R1 (CRITICAL-with-fix blocks)**, **R2 (persistence rule for
   fix-listed HIGHs across 2 consecutive scans)**, **R4 (HIGH config
   findings in rendered deployable manifests only)** as the candidate
   enforcement policy, with **R3** as the non-blocking warning channel.
2. **Reject** raw severity counts (P1) and any HIGH-with-fix rule (P3):
   both permanently block on the three upstream-waiting CVEs — converting
   documented, non-remediable findings into permanent build noise.
3. **Reject the 30-day age rule as designed** (P4): the table scanner
   output carries no per-finding dates; honest age gating requires Trivy
   JSON output and new parsing, deferred to implementation.
4. Scope any config gate to **rendered deployable manifests**, preserving
   the Tier-A evidence manifest as untouched history.
5. **Enforcement remains gated:** R1–R4 run in shadow mode for ≥2 real CI
   cycles with recorded verdicts before any exit-code change; the flip
   requires Paul's explicit authorization.

## Rationale

The simulation is the evidence: P2 alone discriminates correctly between
the vulnerable and remediated states with zero standing exceptions, and
P2 re-run on the 7A inventory fails exactly as intended (regression
detection). Persistence (R2) closes the "new HIGH ignored forever" gap
that P2 deliberately leaves to the debt register. Render-scoping (R4)
prevents evidence-document findings from blocking deployment configuration.

## Consequences

- Implementation (when authorized) must add: JSON-based finding
  extraction, previous-run artifact retention, an in-repo unit-tested
  evaluator, and shadow-verdict artifacts.
- The three no-fix-listed HIGH CVEs remain permanently non-blocking by
  design; visibility is maintained via the debt register and R3 warnings.
- Historical reports and the reconciliation notes remain untouched.

## Alternatives considered

- **P1/P3 (raw counts)** — rejected: permanent red pipeline on
  un-actionable findings (the exact failure mode the core question
  prohibits).
- **P4 age-based now** — rejected: cannot be implemented honestly from
  table output.
- **Skip shadow mode** — rejected: violates the project's evidence-before-
  enforcement principle and the authorized progression.

## References

- docs/07-security/phase7c-policy-simulation.md (evidence)
- docs/07-security/phase7c-proposal.md (original design)
- docs/07-security/security-debt-register.md (dispositions)
- ADR-0004 (registry-dependent deferral, unchanged)

## Refinement (2026-09-24, policy-model pass)

The full policy model (docs/07-security/phase7c-policy-model.md) simulated
the four candidate families (A severity-only, B severity+fix, C +age,
D +exceptions) against three historical states (7A baseline; post-base-
remediation; current). Consequences observed: A fails at every state
including today (permanent noise); B catches the historical Criticals but
lets fix-listed HIGHs persist unaddressed; C requires date-carrying scan
output (JSON) before it can be honest; D gives the no-fix population a
bounded, auditable home via expiring exceptions. The R1/R2/R4 selection
stands; the D-layer exception model (Git-tracked, expiring, review-gated)
is carried into the shadow-mode design as the terminal state of the same
policy. Shadow mode and enforcement remain unauthorized.
