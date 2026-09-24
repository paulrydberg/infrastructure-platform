# Phase 2 — Kubernetes (planned, authorization-gated)

**Status:** Evaluation complete; implementation awaiting authorization
**Authorization state:** evaluation/design authorized and complete (2026-09-24);
implementation (k3s install, workloads, any VM change) NOT authorized yet

## Documents in this phase

| Document | Content |
|----------|---------|
| [phase2-evaluation.md](phase2-evaluation.md) | 19-point evaluation: architecture, k3s suitability, resources, storage, networking, security baseline, implementation plan, validation/rollback |
| [resource-negotiation-report.md](resource-negotiation-report.md) | measured baseline, projected requirements, Option A (recommended) vs Option B, rejection conditions, rollback/validation procedures |
| [resource-profile.md](resource-profile.md) | measured host data + labeled estimates |
| [experiment-k3s-selection.md](experiment-k3s-selection.md) | k3s vs kind/minikube/microk8s experiment record |

## Recommendation (not a decision)

**Option A:** k3s as a hard-capped container (2.5 GiB / 2 cores) inside the
existing Docker Desktop VM — no Docker Desktop change, no restarts, one-command
rollback, protected workloads untouched. Full observability stack explicitly
does NOT fit under Option A and stays Phase 6-gated.

## What happens after authorization (staged)

2.1 commit pinned k3s compose → 2.2 start + validate → 2.3 measure real
footprint + check 5 rejection conditions → 2.4 failure tests → 2.5
reconstruction test (Level 2) → 2.6 completion report. Any rejection condition
met → stop, escalate, re-report.
