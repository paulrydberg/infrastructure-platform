# Reproducibility Architecture — infrastructure-platform

**Status:** Design (Phase 0)

## Core principle (spec §1, §7)

«The machine is disposable. The source of truth is persistent.»

Reconstruction flows from Git → IaC → GitOps desired state → configuration →
artifacts → runtime. Runtime state is never authoritative. Undocumented
manual intervention is technical debt (spec §32) and is recorded whenever it
occurs.

## Self-reconstructing ≠ self-modifying (spec §1)

The platform rebuilds itself from controlled sources. It does not arbitrarily
mutate its own definitions. All changes flow through Git (branch → PR → CI →
policy → merge), whether authored by humans or AI.

## Reconstruction chain (spec §86)

```
PERSISTENT SOURCE (git repos, IaC, manifests, charts, policies,
                   bootstrap scripts, docs, version pins, metadata)
  → BOOTSTRAP → BASE HOST → CONTAINER RUNTIME → KUBERNETES → HELM
  → GITOPS → PLATFORM (networking, storage, observability, security,
             automation, applications) → OPTIONAL AI → VALIDATION
  → RECONSTRUCTION REPORT
```

## Maturity model (spec §27) — current honest position

| Level | Meaning | Status |
|-------|---------|--------|
| 0 | Manual reconstruction possible | ⚠️ PARTIAL — the shared-host services predate this project and lack reconstruction docs (out of scope); THIS project is currently at Level 0 for its own (documentation-only) state |
| 1 | Scripted application deployment | not reached |
| 2 | Automated k8s reconstruction | not reached |
| 3 | Automated platform reconstruction | not reached |
| 4 | IaC infrastructure reconstruction | not reached |
| 5 | Tested disaster recovery | not reached |
| 6 | Periodically verified reconstruction | not reached |
| 7 | Continuous reproducibility validation | not reached |

**Current claimed level for this project: 0.** No level will be claimed
without demonstration (spec Rule 21).

## Environment-specific reconstruction targets

| Target | Feasibility | Notes |
|--------|-------------|-------|
| Fresh Mac Mini (same model) | supported design goal | documented prerequisites + bootstrap |
| Linux VM / machine | design goal (spec §11) | x86_64; bootstrap must be OS-conditional |
| AWS environment | Phase 8+ | IaC-defined |
| Disposable reconstruction env | Phase 17–18 | k3s-in-VM or cloud; enables Level 6–7 |

## Reconstruction diff & reporting (spec §30–31)

Every full reconstruction produces a report: commit, versions, duration,
manual interventions (target: 0 undocumented), deviations classified
EXPECTED/ACCEPTABLE/WARNING/ERROR/UNRESOLVED, final PASS/FAIL. Failed
reconstructions are recorded as evidence, never hidden (spec §31).

## Immediate implication for Phase 0/1 boundary

The project directory is not yet under version control — the FIRST
reproducibility action (pending authorization) is `git init` + first commit +
GitHub remote creation. Until then, this project's own definitions exist only
on the machine it is meant to make disposable — a real, current violation of
the core principle that Phase 1 will fix.
