# System Overview — infrastructure-platform

**Status:** Design (Phase 0; grounded in measured discovery)

## Current state (measured 2026-09-24)

```
Mac Mini 2018 (Intel i7-8700B, 16GB, x86_64, macOS 15.7.9)
│
├── macOS host
│   ├── agent gateway + ~30 launchd services (PRODUCTION, out of scope)
│   ├── Time Machine backup (destination 96% full ⚠️)
│   └── Docker Desktop 29.2.1 (VM: 12 CPU / 7.65 GiB)
│       └── 20 containers — coexisting production workload groups
│           (names withheld from the public record)
│
├── Tools present: docker, git, gh, kubectl (no cluster), python, node, go
├── Tools absent: helm, k3s/*, terraform/tofu, argocd, trivy, aws
│
└── THIS PROJECT: ~/.hermes/projects/infrastructure-platform/
    └── documentation only — NOT yet a git repository, no GitHub repo
```

## Target state (spec §85–86, condensed)

```
Git/GitHub (source of truth)
   ├─→ IaC (Terraform/OpenTofu) ──→ AWS (VPC/IAM/ECR/EKS)
   └─→ App/platform code ──→ CI/CD (GitHub Actions) ──→ Artifacts
                                    ↓
              GitOps (Argo CD) ──→ Kubernetes (k3s local → EKS cloud)
                                    ↓
        Applications | Observability (Prom/Grafana/Loki/OTel) | Security
                                    ↓
                    Events → deterministic handling → AI queue (optional)
                                    ↓
                    Validation ← Reconstruction ← Bootstrap
```

## Architecture principles (binding)

1. Self-reconstructing, not self-modifying (spec §1)
2. Deterministic-first; zero-inference operation mandatory (spec §3)
3. AI = optional, resource-governed, event-driven escalation layer (spec §4–6)
4. Git is the source of truth; runtime state is not (spec §7)
5. GitOps as the AI safety boundary (spec §56)
6. The machine is not the platform (spec §87)

## Environment layers (spec §12)

| Layer | This project's instantiation |
|-------|------------------------------|
| Local development environment | macOS host + existing toolchain |
| Local Kubernetes environment | TBD Phase 2 (k3s presumptive, needs ADR + Docker resource renegotiation) |
| Cloud environment | AWS, Phase 8+ (no account today) |
| Disposable reconstruction environment | TBD Phase 17–18 |

## Key architectural tension discovered

The host is shared with production workloads that this project must not
disturb. Every compute decision (cluster placement, resource limits, CI
concurrency) must be evaluated against coexistence constraints
(see ../00-project-origin/constraints.md). This is the central operational
risk of the whole platform and will drive Phase 2's ADR.
