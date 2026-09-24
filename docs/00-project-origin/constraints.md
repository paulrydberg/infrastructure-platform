# Constraints — infrastructure-platform

**Status:** Implemented (discovered 2026-09-24, Phase 0)

## Hard hardware constraints

| Constraint | Value | Implication |
|-----------|-------|-------------|
| RAM | 16 GB total; Docker VM holds 7.65 GiB; Docker VM RSS measured 9.8 GB | k3s + observability stack is feasible but tight; Docker VM allocation may need renegotiation in Phase 2 (authorization required — shared with production containers) |
| CPU | 6C/12T Intel i7-8700B, load ~3.5 with existing workloads | moderate headroom; heavy CI builds must be serialized |
| GPU | Intel UHD 630 only; no CUDA | all AI inference = hosted providers; spec §5 VRAM gates map to API cost/latency instead (documented deviation) |
| Architecture | x86_64 | AWS later likely ARM64 Graviton or x86_64 — design for multi-arch images from Phase 1 (spec §12) |
| Disk | 185 Gi free; ~55 GB reclaimable inside Docker | adequate for Phases 1–7 with build-cache discipline |
| Time Machine dest | 96% full | host backup risk — flagged to Paul, outside project scope |

## Environment constraints

1. **Coexistence:** ~20 production containers (several distinct workload
   groups — names withheld from the public record) + ~30 launchd services
   (agent gateway, tunnels, workers) share this host. Nothing in this project
   may restart, reconfigure, or resource-starve them without explicit authorization.
2. **Hermes runs here:** this agent's own gateway is a production service on
   the same machine — self-modification of Hermes infra is out of scope.
3. **No cloud account configured:** no AWS CLI, no ~/.aws. Phase 8 requires
   account creation/credentials — an external dependency and authorization gate.

## Governance constraints (binding, from prompts)

- Phase boundaries require explicit authorization; Phase 0 is read-only.
- No installs, no repo creation/migration, no restructuring without gates.
- Secrets never in source; production services never restarted without OK.
- One authorization gate at a time (Paul's standing ops discipline).
- Portfolio workstream must never manufacture activity (Clarification 1).

## Budget constraints (host context)

Hermes host has daily LLM budget governance (soft $2.50/day). AI-operations
phases must respect it and treat token spend as a governed resource in the
AI queue design (aligns with spec §5).
