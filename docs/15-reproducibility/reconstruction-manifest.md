# Reconstruction Manifest — infrastructure-platform

**Status:** Design v1 (Phase 0) — one registered component; grows per phase

Schema fields per master spec §9. A component is listed here only when it
exists or is being built; entries carry honest status.

---

## Component 1: Project Source & Documentation

| Field | Value |
|-------|-------|
| Component name | infrastructure-platform (source + docs) |
| Purpose | canonical source of truth for the platform's definitions |
| Source of truth | Git (GitHub, repo pending authorization) |
| Version | git commit pin (manifest updated at each tagged release) |
| Configuration source | repository itself |
| Deployment mechanism | git clone (docs-only today; bootstrap Phase 1+) |
| Dependencies | github.com, git, SSH/token auth |
| Secret requirements | GitHub read credential (operator-provided) |
| State requirements | none (stateless) |
| Artifact requirements | none |
| Restoration mechanism | fresh clone at pinned ref |
| Validation method | file manifest + SHA-256 verification |
| Expected location | any machine, `~/projects/infrastructure-platform/` (or equivalent) |
| Failure behavior | clone failure blocks reconstruction of everything downstream |
| Reconstruction order | **1st** — everything depends on this |
| Deterministic | yes |
| Requires external services | github.com |
| Status | **DOCUMENTED BUT NOT RECONSTRUCTIBLE YET** — repo does not exist; Phase 1 gate |

## Component 2: Host Prerequisites (planned — Phase 1)

Bootstrap must install/verify: git, docker (or engine per Phase 1 ADR), jq.
Detailed entry added when bootstrap exists.

## Components 3+: Container Runtime, Kubernetes, Helm, GitOps, Observability,
Security, Registry, Applications, Automation, Backups, AI, Secrets, Cloud,
DNS, Stateful Data

**Not yet built — entries will be added per phase.** This manifest is
deliberately seeded with one honest component rather than aspirational stubs
(master spec Rule 23: document what was actually built).
