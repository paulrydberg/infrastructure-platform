# k3s Resource Profile — Measured Reference Data

**Status:** Evidence appendix (2026-09-24) — measured/observed data supporting
the Phase 2 evaluation; generic estimates explicitly labeled.

## Measured on THIS host (2026-09-24)

| Measurement | Value |
|-------------|-------|
| Docker Desktop VM memory | 7.654 GiB (8,218,742,784 bytes via docker system info) |
| VM CPUs | 12 |
| Container memory sum (21 containers) | ≈ 2.4 GiB |
| Largest protected consumer | olap db: 1.996 GiB / 4 GiB cap, ~100% of 1 core in bursts |
| Hard-capped protected containers | 4 of 20 (4G, 4G, 256M, 1G) |
| Unlimited protected containers | 17 of 20 (balloon risk noted) |
| Host load average | 3.32 / 3.44 / 3.64 (of 12 threads) |
| Host CPU idle | ~80% |
| Host swap | 680 MB used / 2 GB |
| VM free memory (derived) | ≈ 4.5–5 GiB |
| Disk free (Data volume) | 184 GiB |
| Docker reclaimable disk | ≈ 56 GB (36.3 images + 13.9 build cache + 5.4 volumes) |

## k3s footprint class (observed class from k3s project documentation and
## community deployments; will be MEASURED during Phase 2 implementation and
## this table updated with real numbers)

| Component | Expected RSS |
|-----------|--------------|
| k3s server (agent embedded, sqlite, Traefik+servicelb disabled) | 512–900 MB |
| kubelet/containerd overhead (inside k3s container) | included above |
| metrics-server | 60–100 MB |
| test workload pod | ≤ 64 MB |
| **Phase 2 envelope** | **≤ 1.2 GiB expected, capped at 2.5 GiB hard** |

⚠️ These k3s numbers are the ONLY estimates in this report set. Everything
else is measured on this host. Phase 2 step 2.3 replaces them with real
measurements before the reconstruction test is attempted.

## Rejection conditions (verbatim from resource-negotiation-report.md)

1. VM free memory < 3.0 GiB sustained before k3s start
2. k3s hits its 2.5 GiB cap during normal Phase 2 workloads
3. Any protected container restarts/OOMs attributable to k3s
4. Host swap doubles from 680 MB baseline and stays elevated
5. Sustained host load > 8 for > 5 minutes with k3s idle
