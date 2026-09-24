# infrastructure-platform

> A production-oriented infrastructure platform implementing Kubernetes,
> GitOps, observability, security controls, reproducibility, and automated
> operations — developed and operated in a personal development/validation
> environment, with a reproducible local-to-cloud architecture and an AWS
> deployment path on the roadmap.

**Status badges / CI:** coming with Phase 1 CI implementation.

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
| Phase 1 — Local container foundation | 🔄 In progress |
| Kubernetes (k3s or justified alternative) | 📋 Planned (Phase 2) |
| Helm packaging | 📋 Planned (Phase 3) |
| CI/CD (GitHub Actions) | 📋 Planned (Phase 4) |
| GitOps (Argo CD) | 📋 Planned (Phase 5) |
| Observability (Prometheus/Grafana/Loki/OTel) | 📋 Planned (Phase 6) |
| Security (Trivy/Kyverno/SBOM) | 📋 Planned (Phase 7) |
| AWS (Terraform/OpenTofu, VPC/IAM/ECR/EKS) | 📋 Planned (Phase 8+) |
| Dependency automation (Renovate, WUD) | 📋 Planned (Phases 1/10) |
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

Current maturity: **Level 0** (honest baseline, per
[the reproducibility architecture](docs/02-architecture/reproducibility-architecture.md)).
Target: Level 7 (continuously validated reconstruction) — claimed only when
demonstrated. The [reconstruction manifest](docs/15-reproducibility/reconstruction-manifest.md)
lists every component, its source of truth, and its restoration mechanism.

## License & attribution

See [LICENSE](LICENSE).
