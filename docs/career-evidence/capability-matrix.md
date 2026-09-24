# Capability Matrix — infrastructure-platform

**Status:** Honest baseline (2026-09-24, post-Phase 0; re-issued per phase
and eventually per-release)

Maturity labels (Amendment 1 §24): Design / Prototype / Experimental /
Functional / Tested / Production-like / Operational / Continuously Validated.

| Capability | Evidence (current) | Maturity | Portfolio-visible? | Remaining gap |
|-----------|--------------------|----------|--------------------|---------------|
| Linux/macOS system administration | operator environment; Phase 0 discovery | Functional (environment-level) | no — not yet a project artifact | evidence through bootstrap + ops docs |
| Docker operations | 20 production containers on host (other projects) | Functional (environment-level) | no | this project's own versioned workloads |
| Documentation engineering | 30-file doc set, ADRs, verbatim records | Functional | yes (once repo exists) | CI link validation (Phase 4) |
| Repository/Git strategy | Phase 0 analysis, ADR-0001/0002/0003, source-of-truth matrix | Functional | **yes — repo live, protected** | release cadence as work continues |
| Container build/orchestration | platform-demo 0.1.0 (pinned base, non-root, healthcheck, resource limits, compose) | **Tested** | **yes — v0.1.0 release** | registry publication (Phase 4) |
| CI validation gates | ci.yml: secret scan, syntax, compose config, doc links — green run on PR #1 | **Tested** | **yes — Actions runs public** | build+artifact jobs (Phase 4) |
| Bootstrap validation | bootstrap.sh, 10 checks, idempotent ×2 verified | **Tested** | **yes** | installation automation (Phase 2) |
| Release management | v0.1.0 tag + GitHub release with honest notes | Functional | **yes** | cadence per phase |
| Reconstruction (app-level) | destroy → rebuild from source demonstrated (Level 1) | **Tested** | **yes — PR #1 evidence** | cluster-level (Phase 2+) |
| Kubernetes | none | Not implemented | no | Phase 2 |
| Helm | none | Not implemented | no | Phase 3 |
| CI/CD (GitHub Actions) | none | Not implemented | no | Phase 4 |
| GitOps (Argo CD) | none | Not implemented | no | Phase 5 |
| Observability stack | none in this project | Not implemented | no | Phase 6 |
| Security (Trivy/Kyverno/SBOM) | none | Not implemented | no | Phase 7 |
| Terraform/OpenTofu + AWS | no cloud account exists | Not implemented | no | Phase 8 + account creation |
| Dependency automation (Renovate/WUD) | none | Not implemented | no | Phases 1/10 |
| Incident response | none (no incidents yet — accurate) | Not applicable yet | no | first real incident + postmortem |
| Disaster recovery / reconstruction | reproducibility contract v1, manifest v1 (Level 0) | Design | yes (design honesty) | Phase 17–18 demonstrations |
| AI operations (controlled, deterministic-first) | architecture doc; host budget governance exists | Design | no | Phases 11–15 |

## Positioning rule (Amendment 2)

Names describe the SYSTEM (professional engineering function); documentation
describes the ENVIRONMENT honestly (personal development/validation
environment). No capability above is claimed beyond its maturity label, and
nothing becomes portfolio-visible until the implementation substantiates it.

## Reporting cadence

Re-issued: at each phase completion, at each release, and at each repository
extraction. Historical versions are preserved (git history — do not rewrite).
