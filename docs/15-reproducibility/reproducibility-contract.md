# Reproducibility Contract — infrastructure-platform

**Status:** Design v1 (Phase 0)

## Contract statement

Every subsystem added to this platform MUST be documented against the
following template BEFORE it is considered operational (master spec §8).
Any reconstruction requiring undocumented manual intervention is technical
debt and must be recorded in the Reconstruction Manifest (spec §32).

## Contract template (per subsystem)

- **Inputs:** what must exist before reconstruction (repos, OS, architecture,
  network, credentials, registries, DNS, secrets provider, package repos)
- **Preconditions:** what must be true
- **Bootstrap procedure:** how reconstruction is initiated
- **Outputs:** what exists after success
- **Postconditions:** how success is determined
- **Validation:** which tests prove equivalence
- **External dependencies:** what cannot be reconstructed locally
- **Known exceptions:** what still requires human intervention

## Subsystem 1: Project documentation (current state)

| Field | Entry |
|-------|-------|
| Inputs | GitHub repo `paulrydberg/infrastructure-platform` (**CREATED 2026-09-24, public**) |
| Preconditions | network + GitHub auth (SSH key or gh token) |
| Bootstrap | `git clone git@github.com:paulrydberg/infrastructure-platform.git` |
| Outputs | full documentation set (verbatim specs, discovery, ADRs, roadmap) |
| Postconditions | all docs present at pinned commit |
| Validation | file count + SHA-256 spot check vs manifest |
| External dependencies | github.com availability |
| Known exceptions | none — docs are fully self-contained |
| **Current status** | ✅ **SATISFIED (2026-09-24)** — repo live, initial commit pushed; contract now testable |

## Subsystem 2–N: (empty by design)

Subsystems will be appended as they are built (container runtime → Phase 1,
Kubernetes → Phase 2, GitOps → Phase 5, ...). No subsystem may be declared
operational with an incomplete contract entry.

## Manual-intervention policy (spec §32, adopted)

Every intervention found during any reconstruction is recorded and classified:
(1) intentional human authorization step, (2) external dependency,
(3) unavoidable operational action, (4) technical debt, (5) missing automation.
Objective: zero UNDOCUMENTED reconstruction work — not zero authorization.
