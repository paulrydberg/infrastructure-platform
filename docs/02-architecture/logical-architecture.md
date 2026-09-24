# Logical Architecture — infrastructure-platform

**Status:** Design (Phase 0)

## Component model and responsibilities

| Layer | Components | Source of truth | Determinism |
|-------|-----------|-----------------|-------------|
| Source control | GitHub repos (set TBD by ADR-0011) | Git | deterministic |
| Infrastructure | Terraform/OpenTofu (AWS later) | Git + IaC state | deterministic |
| CI/CD | GitHub Actions | Git (.github/) | deterministic |
| Artifacts | container images, SBOMs, charts | registry, digest-pinned | deterministic |
| GitOps | Argo CD (presumptive) | Git desired-state | deterministic |
| Runtime | k3s (presumptive) → EKS | cluster, reconciled | deterministic |
| Observability | Prometheus, Grafana, Loki, OTel (presumptive) | Git + TSDB (runtime) | deterministic |
| Security | Trivy, Kyverno, SBOM, signing (presumptive) | Git policies | deterministic |
| Automation | scripts, WUD, Renovate (presumptive) | Git | deterministic |
| AI layer | queue, provider abstraction, resource gates | Git + queue state | OPTIONAL |

## Reconciliation layers (spec §70)

Each layer converges: desired state (Git) → controller → actual state →
diff → reconcile. Terraform (cloud), Argo CD (cluster), k8s controllers
(workloads). The AI layer never reconciles directly — it proposes via Git.

## Data flow: event → resolution

```
Event (alert, update, drift, failure)
  → deterministic detection (scanners, exporters, GitOps diff)
  → deterministic classification (rules/policy)
  → deterministic handling where possible (runbooks, rollback)
  → unresolved? → is reasoning actually valuable? (spec §4)
      → no: human notification
      → yes: AI queue → resource/cost check → provider select
        → inference → proposal → branch/PR → CI → policy → staging
        → authorization → GitOps deploy → observe → evidence
```

## Boundaries that must never collapse (spec §4)

Detection ≠ Reasoning ≠ Action ≠ Validation ≠ Authorization ≠ Deployment ≠
Observation. Each remains a distinct, auditable stage.

## State classification (spec §58 preview)

| State type | Current location | Reconstruction source |
|-----------|------------------|----------------------|
| Desired state | (none yet — to be created in Git) | Git |
| Runtime state | Docker Desktop VM | NOT authoritative; to be replaced by declarative definitions |
| Persistent app state | container volumes (71, 10.4 GB) | per-app backup procedures (Phase 17) |
| Secrets | host keychains/env, not in project | secret-manager design (spec §26) |
| Artifacts | local Docker images | registry (digest-pinned) |

## Open architectural questions for later phases (not decided now)

- k3s inside Docker Desktop vs. alternative allocation (Phase 2 ADR;
  touches shared Docker VM resources)
- Registry choice: GHCR vs ECR vs local (Phase 4 ADR)
- Observability sizing given RAM ceiling (Phase 6 ADR)
- Single GitHub repo vs split (ADR-0011, after repo-architecture discovery)
