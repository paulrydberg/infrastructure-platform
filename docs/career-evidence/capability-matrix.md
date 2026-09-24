# Capability Matrix — infrastructure-platform

**Status:** Honest, re-issued through Phase 6 decision gate (2026-09-24)

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
| Observability stack | capacity analysis + decision gate + Tier-A experiment complete; metrics-server functionally demonstrated but experiment CLOSED on host-swap gate (causality uncertain, rolled back) | Experimental (validated, not retained) | yes (evidence-linked) | Phase 6 re-run/defer decision |
| Container/image security scanning | 7A evidence + 7B verified remediation (CRITICAL 0, KSV-0118 0 on deployable manifests) + security-debt register with explicit dispositions; 7C policy design proposed in ADR-0004 — thresholds/registry/Kyverno/signing all NOT implemented | Tested (remediation verified; ENFORCEMENT not implemented; policy proposed only) | yes (evidence-linked) | 7C authorization gate |
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
