# AMENDMENT 2 — Professional Repository Naming Standard & Positioning

> **CANONICAL VERBATIM RECORD — AMENDMENT 2**
> Received via Telegram 2026-09-24, after Phase 0 completion.
> Amendment to the GitHub repository architecture and employment-portfolio
> strategy. Naming convention, NOT a requirement to create repositories.
> Phase 0 architectural conclusion (monorepo → hybrid) remains authoritative.
> Telegram line-wrap artifact rejoined: "Terr↔aform". No other edits.
> Prompt log: `../PROMPTS.md` · Roadmap: `../ROADMAP-STATUS.md`

---

Integrate the following as an explicit amendment to the project's GitHub repository architecture and employment-portfolio strategy.

The repository naming convention below should be treated as the preferred professional naming standard for any repositories that are ultimately justified by the architecture.

This is a NAMING CONVENTION, not a requirement to create all of these repositories.

The architectural decision from Phase 0 remains authoritative: begin with the flagship "infrastructure-platform" repository and allow additional repositories to emerge only when actual engineering boundaries justify them.

## Professional Repository Naming Standard

Preferred repository names:

- "infrastructure-platform"
- "infrastructure-as-code"
- "container-platform"
- "deployment-platform"
- "observability-platform"
- "security-platform"
- "operations-automation"
- "incident-management"
- "ai-operations"

These names should be evaluated as professional engineering-system names rather than portfolio-project names.

Avoid public repository names that primarily describe the hobby context or the reason the project was created, such as:

- "homelab-platform"
- "homelab-infrastructure"
- "incident-lab"
- "ai-remediation-engine"
- "my-devops-project"
- "cloud-learning-project"

The environment may accurately be described as a home/development/validation environment in documentation. The software and repositories should instead be named according to their engineering function.

## Repository Boundary Rule

Do NOT create repositories merely because a name appears in the preferred naming list.

A repository may be created only when Phase 0's repository-boundary criteria are satisfied, including where appropriate:

- independent lifecycle
- independent deployment lifecycle
- distinct security boundary
- distinct ownership boundary
- meaningful reuse
- independent release cadence
- materially different operational concerns
- independent state management
- clear source-of-truth responsibility
- meaningful contribution boundary
- reproducibility/reconstruction benefits
- maintainability benefits
- portfolio clarity that does not introduce artificial complexity

Every repository split must be documented through the project's normal architectural decision process.

## Current Architectural Direction

The current Phase 0 conclusion remains:

"infrastructure-platform"

is the flagship repository and initial engineering surface.

Additional repositories should emerge only when justified.

The current preferred potential evolution is therefore:

paulrydberg/
│
├── infrastructure-platform
├── infrastructure-as-code
├── operations-automation
└── ai-operations

However, this is a candidate future state, NOT a commitment to create these four repositories.

Other names from the professional naming standard may become appropriate if the actual architecture eventually justifies them.

For example:

container-platform
deployment-platform
observability-platform
security-platform
incident-management

should remain available as professional naming options if those capabilities eventually become sufficiently independent to warrant separate repositories.

## Flagship Repository

"infrastructure-platform" should remain the primary demonstration of the overall engineering system.

Where technically appropriate, it may initially contain:

- Docker
- Kubernetes
- Helm
- Argo CD
- GitHub Actions
- Prometheus
- Grafana
- Loki
- OpenTelemetry
- Trivy
- Kyverno
- WUD
- Renovate
- platform configuration
- operational documentation
- reproducibility documentation
- disaster-recovery procedures
- testing infrastructure

Do not split these technologies into separate repositories merely to increase repository count.

The architecture should optimize for actual engineering quality first and portfolio visibility second.

## Professional Positioning

The project should not be presented primarily as a "homelab."

The environment can be documented honestly as:

- Development environment: Mac Mini
- Local infrastructure: Docker / Kubernetes
- Cloud environment: AWS
- Infrastructure as code: Terraform/OpenTofu
- Deployment model: GitOps
- Repository hosting/CI: GitHub
- Validation environment: local and cloud environments as implemented

The software itself should be described according to its engineering function.

For example:

infrastructure-platform

«A production-oriented infrastructure platform implementing Kubernetes, GitOps, observability, security controls, reproducibility, and automated operations.»

infrastructure-as-code

«Reproducible AWS and local infrastructure using Terraform/OpenTofu.»

deployment-platform

«CI/CD and GitOps deployment infrastructure using GitHub Actions, Helm, and Argo CD.»

observability-platform

«Centralized metrics, logs, traces, dashboards, alerting, and infrastructure health monitoring.»

operations-automation

«Event-driven infrastructure maintenance, remediation, dependency management, container updates, recovery, and operational automation.»

ai-operations

«Controlled AI-assisted engineering operations for infrastructure analysis, remediation, migration, and maintenance.»

These descriptions are examples of the intended professional positioning. Do not claim capabilities until they actually exist.

## Employment Portfolio Principle

The GitHub presence should communicate engineering capability without misrepresenting the origin or maturity of the project.

The distinction is:

«Environment: personal development/validation environment.»

versus:

«System: professionally structured infrastructure engineering platform.»

The repository names should describe the second.

Do not conceal that the system was developed and operated in a personal environment.

Instead, make the environment part of the engineering story:

«An open-source infrastructure platform developed and operated in a personal development/validation environment, with a reproducible local-to-cloud architecture and AWS deployment path.»

Only use claims that are demonstrably supported by the implementation.

## GitHub Profile Positioning

The eventual GitHub profile may use professional positioning such as:

«Systems / Infrastructure Engineer | Cloud | Kubernetes | DevOps | Automation»

Do not add this merely as branding.

The repositories, implementation history, documentation, CI/CD pipelines, incidents, architecture decisions, tests, deployments, and operational evidence must substantiate the capabilities represented by the profile.

## Portfolio Quality Rule

Do not optimize for repository count.

Optimize in this order:

1. Correctness
2. Reliability
3. Security
4. Reproducibility
5. Maintainability
6. Operational usefulness
7. Architecture clarity
8. Documentation quality
9. Demonstrable engineering history
10. Portfolio visibility

A smaller number of substantial repositories is preferable to numerous shallow repositories created primarily for resume keyword coverage.

## Required Documentation

Integrate this convention into the existing repository architecture documentation.

Update or create, as appropriate:

"docs/architecture/github-repository-architecture.md"

"docs/architecture/repository-source-of-truth.md"

"docs/career-evidence/capability-matrix.md"

"docs/career-evidence/engineering-evidence.md"

Also update the relevant ADR or create the next appropriate ADR if the naming convention itself constitutes an architectural decision.

Do not modify the Phase 0 architectural conclusion merely to accommodate these names.

The existing Phase 0 finding remains:

«Monorepo → hybrid evolution; repositories are split only when engineering boundaries justify the split.»

The naming convention should now operate within that architecture.

## Critical Rule

Never create a repository simply because its name looks good to an employer.

Create the repository because the engineering system has earned the boundary.

Then use the professional name that accurately describes what that repository does.

The portfolio should therefore emerge naturally from real engineering work rather than being constructed as a collection of resume keywords.

## Record-keeping instructions

Record this amendment in:

- "docs/00-project-origin/"
- "docs/PROMPTS.md"
- "docs/ROADMAP-STATUS.md"
- "project.json"

Preserve the existing authorization boundary.

Do not create, migrate, rename, or publish any repositories as part of this amendment.

After documentation is complete, stop and report what was changed.
