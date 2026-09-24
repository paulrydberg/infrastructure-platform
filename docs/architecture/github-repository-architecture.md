# GitHub Repository Architecture — infrastructure-platform

**Status:** Adopted (Phase 0 discovery + Amendment 2 naming standard)
**Authoritative sources:** Phase 0 discovery
(`../01-discovery/github-portfolio-and-repository-architecture.md`),
Amendment 2 (verbatim: `../00-project-origin/AMENDMENT-2-NAMING-STANDARD-VERBATIM.md`),
ADR-0001, ADR-0002

## Architectural conclusion (unchanged by Amendment 2)

«Monorepo → hybrid evolution; repositories are split only when engineering
boundaries justify the split.»

## Naming standard (Amendment 2 — adopted)

Professional engineering-system names are the PREFERRED naming standard for
any repositories ultimately justified by the architecture:

- infrastructure-platform
- infrastructure-as-code
- container-platform
- deployment-platform
- observability-platform
- security-platform
- operations-automation
- incident-management
- ai-operations

**Never used** for public repositories (hobby-context names):
homelab-platform, homelab-infrastructure, incident-lab, ai-remediation-engine,
my-devops-project, cloud-learning-project.

## Boundary rule (binding)

A repository may be created ONLY when the Phase 0 boundary criteria are
satisfied (independent lifecycle / deployment / security / ownership,
meaningful reuse, independent release cadence, materially different
operational concerns, independent state management, clear source-of-truth
responsibility, contribution boundary, reproducibility/maintainability
benefits, portfolio clarity without artificial complexity) — and every split
is documented via ADR. **Never create a repository because its name looks
good to an employer.**

## Current state → candidate evolution

```
Now (Phase 1 start, pending authorization):
paulrydberg/
└── infrastructure-platform   ← flagship; ALL platform engineering

Candidate future state (NOT a commitment; ADR-gated extraction only):
paulrydberg/
├── infrastructure-platform
├── infrastructure-as-code    ← if cloud state boundaries justify (Phase 8+)
├── operations-automation     ← if operational lifecycle justifies
└── ai-operations             ← strongest future candidate (Phase 11+)

Available professional names if capabilities become genuinely independent:
container-platform, deployment-platform, observability-platform,
security-platform, incident-management
```

## Flagship repository contents (per Amendment 2)

`infrastructure-platform` remains the primary demonstration of the overall
system and may initially contain: Docker, Kubernetes, Helm, Argo CD, GitHub
Actions, Prometheus, Grafana, Loki, OpenTelemetry, Trivy, Kyverno, WUD,
Renovate, platform configuration, operational documentation,
reproducibility documentation, disaster-recovery procedures, testing
infrastructure. **Do not split technologies into separate repositories merely
to increase repository count.**

## Professional positioning (Amendment 2, adopted)

The project is NOT presented as a "homelab". The environment is documented
honestly as a personal development/validation environment; the SYSTEM is
named and described by its engineering function:

> infrastructure-platform — «A production-oriented infrastructure platform
> implementing Kubernetes, GitOps, observability, security controls,
> reproducibility, and automated operations.»
> (further examples: see verbatim Amendment 2)

Portfolio story (only as implementation substantiates):
«An open-source infrastructure platform developed and operated in a personal
development/validation environment, with a reproducible local-to-cloud
architecture and AWS deployment path.»

## Portfolio quality rule (Amendment 2, priority order — binding)

1. Correctness → 2. Reliability → 3. Security → 4. Reproducibility →
5. Maintainability → 6. Operational usefulness → 7. Architecture clarity →
8. Documentation quality → 9. Demonstrable engineering history →
10. Portfolio visibility.

A smaller number of substantial repositories is preferable to numerous
shallow repositories created for resume keyword coverage.

## Source-of-truth matrix

See `repository-source-of-truth.md` (maintained separately; updated at each
repository creation/extraction).
