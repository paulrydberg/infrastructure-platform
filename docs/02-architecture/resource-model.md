# Resource Model — infrastructure-platform

**Status:** Design v1 (Phase 0; from measured baseline in ../01-discovery/resource-baseline.md)

## Shared-host reality (constraints, not aspirations)

The 16 GB host is already carrying: Docker VM (7.65 GiB allocation, ~9.8 GB
RSS observed), Hermes gateway + ~30 launchd services, 20 production
containers. All project workloads must fit in the remainder WITHOUT
renegotiating shared resources — unless a specific phase makes an
authorization case for doing so.

## Phase-by-phase resource plan

| Phase | New workload | Estimated need | Fits without host changes? |
|-------|--------------|----------------|---------------------------|
| 1 | compose app + WUD | < 1 GiB | yes |
| 2 | k3s (single node) | 1–1.5 GiB | **tight** — requires Docker VM allocation review OR k3s outside Docker VM; ADR required |
| 3 | helm (client only) | negligible | yes |
| 4 | CI = GitHub-hosted runners | 0 local | yes (only ghx artifact pulls) |
| 5 | Argo CD | 0.5–1 GiB | tight but feasible after Phase 2 decision |
| 6 | Prometheus+Grafana+Loki | 2–3 GiB | **the binding constraint** — sizing ADR required (retention windows, single-replica, no HA at this scale) |
| 7 | Trivy scans | burst CPU/RAM | scheduled off-peak, serial |
| 8+ | AWS | local: tf/tofu CLI only | yes (cost moves to cloud budget) |
| 11+ | AI layer | API calls; queue overhead < 200 MB | yes — governed by token budget, not hardware |

## Governance thresholds (proposed, validated in Phase 1)

- Do not exceed: 80% Docker VM memory; host free RAM floor 2 GiB; load
  average ceiling 10; Data volume free floor 50 GiB.
- Any workload that would breach a threshold enters WAITING_FOR_RESOURCES
  (this rule becomes the AI resource gate of spec §5/§77).
- Measurements recorded per phase into ../01-discovery/resource-baseline.md
  (spec §78 — measure, don't estimate).

## Cost model (honest)

- Local: electricity only.
- GitHub: free tier sufficient (public repo, Actions minutes free for public).
- AWS (Phase 8+): every resource gets purpose/owner/cost/lifecycle/destruction
  strategy per spec §42; dev environments designed create→use→destroy.
- AI providers: token spend governed by host Hermes daily budget initially;
  per-task budget enforcement designed in Phase 11.
