# Success Criteria — infrastructure-platform

**Status:** Defined (master spec §92/§93 + Amendment 1 §51; formalized 2026-09-24)

## First milestone (§92) — the gate to Phase 1

NOT "install Kubernetes". The first milestone is a documented, version-
controlled, reproducible engineering foundation:

- [ ] Discovery report (this Phase 0 deliverable set)
- [ ] Hardware/software inventory — ✅ done (see ../01-discovery/)
- [ ] Resource baseline — ✅ done (snapshot; steady-state re-measure in Phase 1)
- [ ] Architecture document
- [ ] Reproducibility architecture
- [ ] Reproducibility contract
- [ ] Reconstruction manifest
- [ ] Initial roadmap
- [ ] Threat model
- [ ] Resource model
- [ ] Initial ADRs
- [ ] Repository structure (earned via ADR-0011 after repo-architecture discovery)
- [ ] Bootstrap design
- [ ] Initial validation strategy
- [ ] Clear Phase 1 exit criteria

## Final success condition (§93)

Demonstrated capabilities: IaC + containers + Kubernetes + Helm + CI/CD +
GitOps + observability + security + dependency automation + container update
detection + incident response + disaster recovery + reproducibility + failure
testing + resource governance + optional AI operations — and critically:
**THE PLATFORM CAN RECONSTRUCT THE PLATFORM**, from a fresh environment,
with no hidden dependence on the original machine.

## Portfolio success criteria (Amendment 1 §51)

An external technical reviewer inspecting the GitHub presence can reasonably
conclude concrete evidence of: Linux, containers, Kubernetes, Helm, GitOps,
CI/CD, Terraform/OpenTofu, AWS, observability, security, automation,
reliability, DR, platform engineering, AI-assisted operations — with
repositories having clear responsibilities, professional READMEs, honest Git
history, real issues/PRs, functional CI/CD and security checks, and releases
representing real milestones.

## Anti-criteria (failures of success)

- Any claim of maturity not demonstrated (spec Rule 21)
- Any manufactured portfolio activity (Clarification 1)
- Any AI dependency in the deterministic core (spec §3)
- Any undocumented manual intervention treated as acceptable debt (spec §32)
