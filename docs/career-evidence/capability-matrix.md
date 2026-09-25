# Capability Matrix — infrastructure-platform

**Status:** Honest, re-issued after Level 6 and post-Level-6 audit (2026-09-25)

Maturity labels (Amendment 1 §24): Design / Prototype / Experimental /
Functional / Tested / Production-like / Operational / Continuously Validated.
Additional states used: "Analysis only" (work performed, nothing deployed)
and "Not applicable yet".

| Capability | Evidence (current) | Maturity | Portfolio-visible? | Remaining gap |
|-----------|--------------------|----------|--------------------|---------------|
| Linux/macOS system administration | operator environment; Phase 0 discovery | Functional (environment-level) | no — not yet a project artifact | evidence through bootstrap + ops docs |
| Docker operations | 20 production containers on host (other projects) | Functional (environment-level) | no | this project's own versioned workloads |
| Documentation engineering | 30+ file doc set, ADRs, verbatim records, CI link validation | Functional | **yes — repo live** | — |
| Repository/Git strategy | Phase 0 analysis, ADR-0001/0002/0003, source-of-truth matrix | Functional | **yes — repo live, protected** | release cadence as work continues |
| Container build/orchestration | platform-demo 0.1.0 (pinned base, non-root, healthcheck, resource limits, compose); CI-built | **Tested** | **yes — v0.1.0 release** | registry publication (later phase) |
| CI validation gates | ci.yml: secret scan, syntax, compose config, doc links — green run on PR #1 (initial gates) | **Tested** (superseded by full CI/CD row below) | **yes — Actions runs public** | superseded — see CI/CD row |
| Bootstrap validation | bootstrap.sh, 10 checks, idempotent ×2 verified | **Tested** | **yes** | full-environment install automation (Phases 17–18) |
| Release management | v0.1.0 tag + GitHub release with honest notes | Functional | **yes** | cadence per phase |
| Reconstruction (app-level) | destroy → rebuild from source demonstrated (Level 1) | **Tested** | **yes — PR #1 evidence** | superseded by platform-level row below |
| Kubernetes (k3s, single node, 1.5 GiB envelope) | k3s v1.31.2 resident; fundamentals (namespace/quota/probes/services), drift self-heal, Level 2 reconstruction (down -v → Ready ~8 s) — Phase 2 evidence | **Tested** | **yes — repo + Actions** | multi-node/upgrade scenarios |
| Helm packaging | platform-demo chart: lint/template/install/upgrade/rollback/reconstruction all validated — Phase 3 evidence | **Tested** | **yes** | chart repo/OCI publication |
| CI/CD (GitHub Actions) | 2-job pipeline (validate→build) w/ SHA-pinned actions, checksum-gated tools, chart↔compose consistency, kubeconform; controlled failure modes demonstrated — Phase 4 evidence | **Tested** | **yes — public runs** | registry publish job |
| GitOps (Argo CD) | v2.13.3 minimal footprint (~209 MB measured); control loop, drift self-heal, failure/recovery, staged teardown + permanent residency — Phase 5A evidence | **Tested** | **yes** | multi-app scale, SSO/RBAC hardening |
| Observability stack | capacity analysis + Tier-A metrics-server experiment complete; metrics-server functionally validated but rolled back on conservative resource gate; no persistent stack retained | Experimental (validated, not retained) | yes (evidence-linked) | re-evaluate only if a demonstrated diagnostic need emerges |
| Container/image security scanning | Phase 7A/7B Trivy + Gitleaks + SPDX SBOM; 7C schema-validated deterministic policy evaluator and enforcement are active in CI, with artifact-preserving blocking and rollback tests | **Tested / enforced** | yes (evidence-linked) | registry/signing/provenance and additional controls are separate future decisions |
| Security (Trivy/Gitleaks/SBOM/policy) | CI scanning, SBOM, deterministic policy evaluation and enforcement; Phase 7 enforcement active and independently preserved through Level 6 | **Tested / enforced** | yes | registry/signing/provenance and additional controls are separate future decisions |
| Terraform/OpenTofu + AWS | no cloud account exists | Not implemented | no | separate future authorization if evidence establishes a need |
| Dependency automation (Renovate/WUD) | none | Not implemented | no | future consumer of the Level-6 validation substrate; not currently authorized |
| Incident response | none (no incidents yet — accurate) | Not applicable yet | no | first real incident + postmortem |
| Disaster recovery / reconstruction | reconstruction manifest v1.0.0 + deterministic runner; **Level 3 and Level 4 demonstrated**; **Level 6 periodically verified reconstruction mechanism demonstrated** with launchd scheduling, resource gating, evidence authority, historical comparison, failure/recovery and teardown; post-Level-6 audit found/fixed AUD-1 and reconciled eight Level-6 defect identifiers | **Tested / verified** | yes (completion records + retained evidence) | longitudinal Level-6 history; Level 7 continuous validation; Level 5 DR only if meaningful project-owned state appears |
| AI operations (controlled, deterministic-first) | architecture doc; host budget governance exists; no operational dependency on LLM inference | Design | no | only introduce when deterministic mechanisms reach a demonstrated reasoning boundary |

## Current reproducibility qualification

Level 6 is **mechanism demonstrated, longitudinal history not yet accumulated**. The post-Level-6 audit found and fixed AUD-1 (stale runner-report inheritance) and reconciled the Level-6 defect record to eight distinct identifiers plus the audit-found defect. The next project activity is passive accumulation of scheduled validation history; Level 7 is not claimed.

## Positioning rule (Amendment 2)

Names describe the SYSTEM (professional engineering function); documentation
describes the ENVIRONMENT honestly (personal development/validation
environment). No capability above is claimed beyond its maturity label, and
nothing becomes portfolio-visible until the implementation substantiates it.

## Reporting cadence

Re-issued: at each phase completion, at each release, and at each repository
extraction. Historical versions are preserved (git history — do not rewrite).
