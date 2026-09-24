# Repository Source-of-Truth Matrix — infrastructure-platform

**Status:** Adopted v1 (Amendment 2 documentation requirement; will be
re-stated at each repository creation/extraction)

Principle (master spec §7): Git is the ultimate source of truth. Runtime
state is never authoritative. Secrets never live in any repository.

## Current matrix (monorepo stage — one repository, pending creation)

| Domain | Repository | Path | Source of truth | Deployment mechanism | State | Secrets |
|--------|-----------|------|-----------------|---------------------|-------|---------|
| Platform architecture + all docs | infrastructure-platform | docs/ | Git | git clone | stateless | none |
| Bootstrap + host config | infrastructure-platform | bootstrap/ (Phase 1) | Git | bootstrap scripts (idempotent) | host state converges to declared | none |
| Container workloads | infrastructure-platform | applications/ + platform/ (Phase 1–3) | Git | compose → Helm/Argo | cluster reconciles | injected at deploy |
| CI/CD pipelines | infrastructure-platform | .github/ | Git | GitHub Actions | stateless | workflow-scoped tokens |
| Policies (future) | infrastructure-platform | policies/ | Git | admission/deploy | cluster | none |
| AI operations (future) | infrastructure-platform → ai-operations (if extracted) | ai/ | Git + queue state | queue workers | queue state IS stateful → documented per §58 | provider API keys via secret manager |
| Cloud IaC (future, Phase 8+) | infrastructure-platform → infrastructure-as-code (if extracted) | infrastructure/ | Git + IaC state (backend TBD, authorization-gated) | terraform/tofu plan-apply | **remote state — the one Git-adjacent truth store** | provider credentials external |
| Container artifacts | registry (GHCR presumptive, Phase 4 ADR) | — | digest-pinned references | pull by digest | registry | pull/push tokens external |

## Rules that survive any future split

1. One domain = exactly one owning repository (never split a domain's truth).
2. Cross-references use immutable pins (image@sha256, chart version, commit).
3. Dependency direction is acyclic: applications → platform contracts → flagship.
4. The Reconstruction Manifest (../15-reproducibility/reconstruction-manifest.md)
   lists every repository + ref required to rebuild — a fresh machine never
   relies on human memory.
5. Secrets remain external to ALL repositories regardless of count.

## Extraction event procedure (when a split is ADR-approved)

Update this matrix → update the Reconstruction Manifest → update the
external-dependency register → re-run reconstruction validation → record in
ROADMAP-STATUS.md. A split is not complete until the platform can still
reconstruct itself from the new layout.
