# Resource Baseline — infrastructure-platform

**Status:** Implemented (snapshot measured 2026-09-24 ~03:35–03:40 CDT; Time
Machine was mid-backup, so treat as a plausible-load snapshot, not idle baseline)

## Measured snapshot

| Metric | Value |
|--------|-------|
| CPU load avg (1/5/15m) | 3.55 / 3.56 / 3.47 |
| CPU usage | ~6.9% user, ~15.2% sys, ~78% idle |
| RAM free (system-wide) | ~70% per memory_pressure, BUT: |
| Largest process | Docker VM (com.apple.Virtualization) — 9.83 GB RSS, 58.6% of physical RAM, 97.7% of one CPU avg over 3.5 days |
| Swap | 2 GB total, 872 MB used (encrypted) |
| Disk (Data volume) | 497 Gi used / 185 Gi free (73%) |
| Docker images | 44.72 GB (36.13 GB reclaimable, 80%) |
| Docker containers | 22 defined / 20 running / 1.92 GB |
| Docker volumes | 71 defined / 22 active / 10.41 GB (5.38 GB reclaimable) |
| Docker build cache | 17.1 GB (13.87 GB reclaimable) |
| **Total reclaimable Docker disk** | **≈ 55 GB** |
| Time Machine dest | 221/233 Gi (96% full) ⚠️ |

## Capacity planning implications (Design status)

- **Available headroom for k3s + observability:** with Docker Desktop's VM
  capped at 7.65 GiB, adding k3s (likely in Docker or as a lightweight
  alternative allocation) requires a resource budget decision. Prometheus +
  Grafana + Loki typically want 2–3 GB. This fits ONLY if Docker's VM
  allocation is revisited in Phase 2 — a decision requiring authorization
  because it can impact the 20 production containers.
- **AI inference:** zero local GPU. All AI = hosted APIs (spec §62 aligns).
  Local AI resource governance reduces to: don't saturate CPU with
  orchestration, and treat token spend as the governed resource (spec §5's
  CPU/RAM/VRAM gates mostly map to API cost/latency here — record as an
  environment-specific deviation).
- **Disk:** ~55 GB reclaimable inside Docker is the first lever if disk
  pressure appears; cleanup would require authorization since it touches
  shared Docker state.
- **Measurement gap:** this is ONE snapshot. Spec §78 requires actual
  measurements — a follow-up steady-state measurement (post-Time-Machine,
  with Docker quiet) should be taken during Phase 1 and recorded here.

## Planned steady-state budget (PROPOSED, needs Phase 1 validation)

| Workload | Target ceiling |
|----------|---------------|
| Docker VM total | ≤ 10 GiB (requires config change + authorization) |
| k3s control plane | ≤ 1.5 GiB |
| Observability stack | ≤ 2.5 GiB |
| Platform apps | ≤ 2 GiB |
| Host reserve (Hermes + macOS) | remaining |
