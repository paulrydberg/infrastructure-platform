# infrastructure-platform

> A production-oriented infrastructure platform implementing Kubernetes,
> GitOps, observability, security controls, reproducibility, and automated
> operations — developed and operated in a personal development/validation
> environment, with a reproducible local-to-cloud architecture and an AWS
> deployment path on the roadmap.

![CI](https://github.com/paulrydberg/infrastructure-platform/actions/workflows/ci.yml/badge.svg)

**CI/CD:** deterministic two-job pipeline (`validate` → `build`) running on
every pull request and push to `main` — secret scan, shell/Python syntax,
Compose validation, documentation links, Helm lint/template, chart↔Compose
consistency, Kubernetes schema validation (kubeconform), container build,
and real application tests. Controlled failure modes demonstrated via
[PR #2](https://github.com/paulrydberg/infrastructure-platform/pull/2).

## What this is

An infrastructure and platform engineering system built as a real,
operable platform — designed so it can **reconstruct itself from source**
(the machine is disposable; the source of truth is persistent) and operate
**deterministically with zero AI inference** in its core.

| Principle | Meaning here |
|-----------|--------------|
| Self-reconstructing, not self-modifying | all changes flow through Git: branch → PR → CI → policy → merge |
| Deterministic-first | the platform functions with AI disabled entirely |
| GitOps safety boundary | deployment authority lives in Git, never in ad-hoc shell access |
| Honest maturity labels | every subsystem carries Implemented/Tested/Planned status — no unearned claims |

## Environment (stated honestly)

This platform is developed and operated in a **personal
development/validation environment** on constrained shared hardware that
also runs unrelated workloads. That constraint is part of the engineering
story: resource governance, coexistence discipline, and reproducibility are
first-class concerns, not afterthoughts. Hardware/software/resource
baselines are measured and documented in
[`docs/01-discovery/`](docs/01-discovery/).

## Current status — implemented vs planned (honest)

| Capability | Status |
|-----------|--------|
| Phase 0 — Discovery, architecture baseline, threat model, reproducibility contract | ✅ Implemented (2026-09-24) |
| Repository + documentation foundation | ✅ Implemented |
| Phase 1 — Local container foundation | ✅ Implemented (v0.1.0) |
| Phase 2 — Kubernetes (k3s, 1.5 GiB envelope) | ✅ Implemented — fundamentals, drift self-heal, Level 2 reconstruction demonstrated |
| Phase 3 — Helm packaging | ✅ Implemented — lint/render/install/upgrade/rollback/reconstruction validated |
| Phase 4 — CI/CD (GitHub Actions) | ✅ Implemented — deterministic validate+build pipeline, failure modes demonstrated |
| Phase 5A — GitOps (Argo CD, minimal footprint) | ✅ Implemented — control loop, drift self-heal, failure/recovery demonstrated; measured ~209 MB |
| Phase 7B — Security triage & remediation | 🧪 CRITICALs remediated (base bump, verified by rescan), KSV-0118 root-caused & fixed via pod-level securityContext, full finding dispositions; enforcement still deferred |
| Phase 7A — Security (CI evidence) | 🔎 Trivy + gitleaks + SPDX SBOM in CI, evidence mode; policy enforcement is a future gate |
| Phase 6 — Observability | 📊 Analysis + Tier-A metrics-server experiment complete — functionally validated, closed on a host swap-pressure gate (rolled back); not a persistent capability |
| Security policy (thresholds/Kyverno) | 📋 Proposed (Phase 7C — ADR-0004; NOT implemented) |
| Registry/signing/provenance (digest-pinned deploys) | 📋 Deferred (requires registry decision; SBOM currently records OCI config digest only) |
| AWS (Terraform/OpenTofu, VPC/IAM/ECR/EKS) | 📋 Planned (Phase 8+) |
| Dependency automation (Renovate, WUD) | 📋 Planned (WUD deferred pending registry; Renovate Phase 10) |
| AI operations (optional, resource-governed, event-driven) | 📋 Planned (Phases 11–15) |
| Reproducibility/DR demonstrations | 📋 Planned (Phases 17–18) |

The authoritative, continuously updated version of this table lives in
[`docs/career-evidence/capability-matrix.md`](docs/career-evidence/capability-matrix.md).

## Documentation map

| Area | Path |
|------|------|
| Project origin (vision, goals, constraints) | [`docs/00-project-origin/`](docs/00-project-origin/) |
| Discovery (hardware, software, resources, GitHub analysis) | [`docs/01-discovery/`](docs/01-discovery/) |
| Architecture (system, logical, AI, reproducibility, threat model) | [`docs/02-architecture/`](docs/02-architecture/) |
| Architecture decision records | [`docs/decisions/`](docs/decisions/) |
| Repository architecture & source-of-truth | [`docs/architecture/`](docs/architecture/) |
| Career evidence (capability matrix, engineering evidence) | [`docs/career-evidence/`](docs/career-evidence/) |
| Reproducibility (contract, reconstruction manifest) | [`docs/15-reproducibility/`](docs/15-reproducibility/) |
| Roadmap status & session log | [`docs/ROADMAP-STATUS.md`](docs/ROADMAP-STATUS.md) |
| Operating instructions (per-session rules) | [`docs/OPERATING-INSTRUCTIONS.md`](docs/OPERATING-INSTRUCTIONS.md) |

## Repository architecture

Single flagship repository by deliberate decision ([ADR-0001](docs/decisions/ADR-0001-project-foundation.md),
[ADR-0002](docs/decisions/ADR-0002-naming-standard.md)): additional
repositories emerge only when genuine engineering boundaries justify them
(independent lifecycle, deployment, security or state boundaries). Platform
components live here until then:

```
infrastructure-platform/
├── bootstrap/          # (Phase 1) idempotent environment bootstrap
├── applications/       # (Phase 1+) versioned container workloads
├── platform/           # (Phase 2+) kubernetes/helm/gitops definitions
├── automation/         # operational automation (deterministic-first)
├── ai/                 # (Phase 11+) OPTIONAL AI operations layer
├── policies/           # policy-as-code
├── tests/              # validation, reconstruction tests
├── scripts/            # operational scripts
├── docs/               # the engineering record
└── .github/            # CI/CD
```

(Directories appear as they gain real content — no empty scaffolding.)

## Reproducibility

Demonstrated reconstruction maturity: **Level 2** — the deployed platform
(source → bootstrap → container runtime → k3s → Helm → workload) has been
destroyed and reconstructed from Git with no undocumented manual steps
(Phase 2/3 evidence; application-level reconstruction additionally shown in
Phase 1). Full-environment reconstruction — including coexisting host
services outside this project — is **not yet demonstrated** (that is the
Level 0→7 journey's remaining work, targeted in Phases 17–18). Long-term
target: Level 7 (continuously validated reconstruction) — claimed only when
demonstrated. The [reconstruction manifest](docs/15-reproducibility/reconstruction-manifest.md)
lists every component, its source of truth, and its restoration mechanism.

## License & attribution

See [LICENSE](LICENSE).
