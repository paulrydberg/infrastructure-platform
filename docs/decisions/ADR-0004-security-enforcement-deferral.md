# ADR-0004: Defer Security Enforcement and Registry-Dependent Controls;
# Sequence Phase 7C as CI-First Policy

**Status:** Accepted (design decision; implementation NOT authorized yet)
**Date:** 2026-09-24
**Context phase:** Phase 7B closeout / Phase 7C design preparation

## Context

Phases 7A/7B established CI security evidence (Trivy, gitleaks, SPDX SBOM,
image-reference policy) and verified remediation (CVE-2026-31789 base bump;
pod-level securityContext for KSV-0118). The platform is a single k3s
cluster inside a resource-constrained Docker Desktop VM, one demo
application, GitOps via Argo CD, no registry, no signing infrastructure.
Remaining image HIGHs: 4 unique CVEs with listed fixes (next base cycle)
and 3 unique CVEs without listed fixes (upstream). CI runs scanners in
evidence mode; the only deterministic gates are build/test/manifest/policy
checks.

Candidate next controls: severity thresholds, registry publication,
digest-pinned deployments, Kyverno admission policy, signing/provenance.

## Decision

1. **Defer** all registry-dependent controls (manifest-digest identity,
   digest-pinned deployment, cosign signing, SBOM attestation, SLSA-style
   provenance, signature verification) until a registry decision is
   separately authorized. A manifest digest does not exist for a
   local-only build; these controls are technically impossible before
   publication, and introducing a registry now adds credentials and
   infrastructure the current platform does not require.
2. **Sequence Phase 7C as CI-only policy first:** severity thresholds with
   expiring exceptions (shadow-mode, then enforced), extended deterministic
   image-reference checks. Zero runtime footprint; reversible by reverting
   one workflow commit.
3. **Stage Kyverno at audit-mode only**, and only after its resource
   footprint passes a pre-defined gate using the Phase 6 resource-gate
   principles (pressure/activity, not residency alone). Enforcement is a
   separate later gate.
4. **Keep enforcement deterministic.** Thresholds and exceptions live in
   Git; no LLM participates in detection, policy, or enforcement.

## Rationale

- Evidence: the current finding population is fully dispositioned; a raw
  severity-count policy would block on un-actionable upstream findings.
  Fix-available/age-based thresholds with expiring exceptions are the
  smallest policy that adds real protection without noise.
- The platform's demonstrated GitOps recovery and resource constraints
  favor reversible, CI-only increments before any cluster-resident
  component.
- Registry-dependent controls form a natural later sequence gated on the
  GHCR-vs-ECR decision and the first deployment that needs published
  images.

## Consequences

- The repository must keep describing the SBOM identity as an OCI config
  digest (not a registry manifest digest) until publication exists.
- Some findings (no-fix-listed upstream CVEs) remain visible warnings
  rather than failures — accepted, documented in the security-debt
  register.
- Kyverno audit-mode will add a small resident footprint to the k3s
  envelope when authorized; it must be measured before and after.
- Signing/provenance claims remain prohibited in all project documentation
  until the deferred chain is actually implemented.

## Alternatives considered

- **Implement thresholds + registry + signing together** — rejected:
  couples a reversible policy step to infrastructure decisions; violates
  the authorization-gate discipline.
- **Go straight to Kyverno enforce** — rejected: no audit evidence yet;
  enforcement without an observed baseline repeats the mistake Phase 6
  documented (policy from assumptions instead of evidence).
- **Defer all policy indefinitely** — rejected: CRITICAL-with-fix findings
  would again be invisible to CI (the 7A baseline had 2).

## References

- docs/07-security/phase7b-report.md (verified remediation record)
- docs/07-security/security-debt-register.md (live finding dispositions)
- docs/07-security/phase7c-proposal.md (design detail)
- docs/09-observability/resource-gate-principles.md (measure-before-gate)
