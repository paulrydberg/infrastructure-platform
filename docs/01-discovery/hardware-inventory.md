# Hardware Inventory — infrastructure-platform

**Status:** Implemented (measured 2026-09-24, Phase 0 read-only discovery)
**Method:** live measurement via `sysctl`, `df`, `system_profiler`, `top`, `ps`

## Host

| Item | Value |
|------|-------|
| Model | Macmini8,1 (Mac Mini 2018) |
| CPU | Intel Core i7-8700B @ 3.20GHz (6 cores / 12 threads) |
| Architecture | x86_64 (IMPORTANT: not ARM64 — affects image base selection) |
| RAM | 16 GB (17,179,869,184 bytes) |
| GPU | Intel UHD Graphics 630, 1536 MB dynamic VRAM, Metal 3 — **no discrete GPU, no CUDA, no usable local model acceleration** |
| Virtualization | Intel HVM supported (`kern.hv_support = 1`) |
| OS | macOS 15.7.9 (Build 24G830) |
| Uptime at discovery | 3 days 11 hours |
| LAN IP | *(redacted — RFC1918 private LAN address)* |
| Tailscale | present (IP redacted) |

## Storage

| Volume | Size | Used | Avail | Notes |
|--------|------|------|-------|-------|
| Macintosh HD (Data) | 699 Gi | 497 Gi (73%) | **185 Gi** | primary working disk |
| TimeMachine volume | 233 Gi | **221 Gi (96%)** | **12 Gi** | ⚠️ nearly full; active backup in progress during discovery (1.85M changed items) |

## Resource-relevant observations

- **Docker Desktop VM** is allocated 7.65 GiB of the 16 GB and was consuming
  ~9.8 GB RSS (58.6% of physical RAM) at discovery time — the single largest
  memory consumer on the host.
- 20 containers running (see software-inventory.md) — these are **production
  services for other projects** (several distinct workload groups, names
  withheld from the public record). This project MUST NOT disrupt them.
- Load average ~3.5 with CPU ~78% idle; Time Machine was mid-backup during
  measurement (29% CPU from `backupd`), so numbers are a snapshot, not steady-state.
- Swap: 2 GB total, 872 MB used — mild pressure, not critical.

## Architecture constraints derived from this hardware

1. **x86_64 only locally.** Any AWS EKS work later will likely be ARM64
   (Graviton) or x86_64 — multi-arch images should be a design goal from Phase 1.
2. **16 GB RAM total, ~7.6 GB already committed to Docker.** A local k3s
   cluster + observability stack (Prometheus/Grafana/Loki) is feasible but
   tight; the AI layer must be API-based, not local-GPU.
3. **No discrete GPU.** Local LLM inference is effectively impractical;
   AI operations will rely on hosted providers (matches spec §62 provider
   abstraction).
4. **~185 GB free disk** is adequate for Phase 1–7 but Docker build cache
   discipline will be required (17 GB build cache already accumulated).
5. **Time Machine volume at 96%** — full backup disk will stall host backups;
   this is an existing host risk to flag to Paul (outside project scope to fix
   without authorization).
