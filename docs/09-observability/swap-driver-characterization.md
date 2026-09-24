# Host Swap-Driver Characterization — Read-Only Investigation (2026-09-24)

**Objective:** understand the environmental condition that prevented the
Tier-A metrics-server experiment from receiving a clean resource-gate pass
(swap 625.75 MB → ~1260 MB during the observation window; classification:
FUNCTIONAL VALIDATION SUCCESSFUL / SWAP GATE TRIGGERED / CAUSALITY
UNCERTAIN — that experiment and its evidence remain preserved as-is).

**Method:** read-only host/Docker/Kubernetes telemetry only. No containers
stopped/restarted/resized, no k3s/Argo/protected-workload changes, no swap
reconfiguration, no pruning. One bounded 5-sample idle window (declared
before running: hypothesis H1 swap flat-or-declining on an idle host;
metric swapused; interval 60 s; stop on +100 MB growth or window end).

## 1. Current environment (measured 11:05–11:20 local)

- Host: Mac Mini, 16 GB physical (`hw.memsize` 17,179,869,184), uptime 3 d 19 h
- Docker Desktop VM: 7.654 GiB allocation; VM process RSS **10.53 GB** on host
- k3s: 1.5 GiB hard cap; measured 1.000–1.023 GiB after metrics-server removal
- macOS swap: **total 2048 MB, used 1281.5 MB and declining** (was 1345.5 at
  10:46 — see §6)
- macOS memory-pressure level: `kern.memorystatus_vm_pressure_level = 1`
  (NORMAL), `vm.page_free_wanted = 0`, **76% free** system-wide
- Compressor mode 4 (default), pages throttled 0
- Load: 2.49–4.16 on 12 threads (normal)

## 2. What is consuming physical memory (observed)

| Consumer | Footprint | Share of 16 GB |
|---|---|---|
| Docker VM (Virtualization.framework process) | **10.53 GB RSS** | ~64% |
| openclaw-gateway | 641 MB | 4% |
| Docker Desktop backend + app | ~374 MB | 2.3% |
| Python (agent runtime) | ~297 MB | 1.8% |
| WindowServer + UI | ~64 MB | <1% |
| Everything else (observed top-15) | <350 MB combined | ~2% |

The Docker VM is by far the dominant physical-memory consumer on the host.
Inside the VM, container usage sums to roughly 4.3–4.5 GiB
(largest: clickhouse 1.80–1.95 GiB, k3s ~1.0 GiB, langfuse-server ~0.6 GiB,
plus ~20 smaller containers), i.e. the VM holds substantial memory beyond
container working sets (page cache/buffers).

## 3. What is in swap

Per-process swap attribution on macOS is not exposed through unprivileged
telemetry (`ps`/`top` do not provide a per-process swap column; the
Virtualization VM is opaque to it by design). What can be said [M]:

- Swap used 1281.5 MB of 2048 MB, **declining on an idle host**
- **Swapins delta = 0 over a 30 s idle window** (14,000,861 → 14,000,861);
  swapouts likewise static — **no active swapping occurring at rest**
- Historical totals: pageins 222 M vs pageouts 2.3 M over 3 d 19 h uptime —
  most paging is file-back/cache activity, not swap churn

Conclusion: the current swap level is **cold-page residency, not active
memory pressure**. Swap allocated ≠ swap in use ≠ pressure ≠ degradation;
the evidence distinguishes all four at present.

## 4. Is macOS under meaningful memory pressure?

**No [M].** Pressure level 1 (NORMAL), 76% free, zero wanted pages, zero
throttled pages, swap inactive at rest, load normal. The host is healthy.

## 5. Largest container footprints (observed, 11:05–11:20)

| Container | Memory | Notes |
|---|---|---|
| langfuse-clickhouse (protected OLAP) | 1.798–1.953 GiB of 4 GiB cap | varies ±8.3% |
| k3s-server | 1.000–1.023 GiB of 1.5 GiB cap | post-experiment |
| langfuse-server | ~613 MiB | |
| open-webui | ~210 MiB | |
| langfuse-worker | ~205 MiB of 256 MiB | 80% of its small cap |
| remaining ~18 containers | each <155 MiB | |

## 6. Temporal evidence on the swap event (correlation assessment)

Measured trajectory across the whole day [M]:

| Time | Swap | Event |
|---|---|---|
| 06:19–06:50 | 625.75 flat | baseline, metrics-server installed 06:19 |
| 06:55 | 716 | first drift |
| 07:11 | **1239** | step change; k3s RSS simultaneously fell 1.058→1.01 GiB |
| 07:16–08:51 | 1143–1260 | plateau w/ small drift |
| 09:01–10:46 | 1196→1345 | slow rise, then decline begins |
| 10:55–11:20 (post-removal idle) | **1345.5 → 1281.5, declining** | metrics-server absent |

- clickhouse memory varied only 1.80–1.95 GiB (±8.3%) through the entire
  event — **temporally associated with normal operation, no step change**;
  plausible background contributor but no correlating step observed
- k3s RSS fell at the swap step (inverse direction) — evidence against the
  k3s/metrics-server side driving it
- Pearson r(k3s RSS, swap) = 0.131 over 27 samples (near zero)
- The single step change at ~07:11 correlates with **no observable change
  in any monitored container** — the driver was **outside the monitored
  set** (uninstrumented host processes, VM-internal kernel/page-cache
  reclamation, or macOS compressor dynamics are candidates)

## 7. Answers to the ten questions

1. Physical memory: Docker VM dominates (10.53 GB of 16 GB).
2. Swap: 1281.5 MB cold pages; per-process attribution unavailable
   unprivileged on macOS (stated as unknown, not guessed).
3. Docker VM as pressure source: it is the dominant memory *consumer*;
   no evidence it is under internal pressure (k3s comfortable, no OOMs).
4. macOS pressure: none — level 1 NORMAL, 76% free, swap inactive.
5. Largest workloads: clickhouse > k3s > langfuse-server (table §5).
6. ClickHouse–swap correlation: none observed at the event (±8.3% normal
   variation, no step); plausible slow contributor over hours at most.
7. Swap after metrics-server removal: yes, remained elevated, then began
   **declining** (1345.5 → 1281.5 over ~25 idle minutes).
8. Natural decline: **observed** — the idle window showed monotonic decline,
   supporting the cold-page-residency interpretation.
9. Performance degradation: **none measurable** — swapins 0/30 s at rest,
   API 247 ms, load normal, no k8s/docker OOMs. Current swap is residency,
   not thrashing.
10. Repeatable driver identified? **No.** The evidence bounds the question
    (not k3s, not metrics-server, not a clickhouse step) but cannot name the
    driver with available unprivileged telemetry. Causality NOT established.

## 8. Attribution assessment (language discipline)

- **Observed:** swap step at ~07:11; decline on idle host; zero swap
  activity at rest; Docker VM dominance of physical memory.
- **Correlated/temporally associated:** nothing in the monitored container
  set correlates with the swap step.
- **Plausible contributors:** host-side processes outside the monitored set;
  VM-internal page-cache dynamics; macOS compressor/swap hysteresis.
- **Supported by evidence:** k3s/metrics-server side did NOT drive the step
  (inverse RSS movement, r=0.131, constant pod footprint).
- **Causality not established** for any named driver.

## 9. Remaining uncertainty

- Per-process swap owners on macOS require elevated or instrumented
  telemetry not available read-only/unprivileged (recorded as UNKNOWN, not
  guessed).
- The 07:11 driver was outside the monitored set; identifying it would
  require either broadened host instrumentation or a re-run with host-level
  paging counters sampled at 1-minute resolution around a fresh event.

## 10. Implications

- **Kubernetes capacity:** the 1.5 GiB envelope remains sound; the Tier-A
  gate failure was a host-environment telemetry artifact of swap residency,
  not in-cluster exhaustion. In-cluster headroom at experiment peak: ~442 MiB.
- **Tier B (Prometheus/Loki +500–900 MB):** would still be the dominant
  incremental consumer and would likely re-trigger the same coarse swap
  gate on this shared host. Evidence does not clear Tier B.
- **Docker VM resize:** unchanged decision — available as a separate
  authorization; the host has physical room (16 GB, VM 7.65 GiB) but no
  measured necessity for k3s workloads to date.
- **Gate design lesson:** a swap-*used* threshold conflates cold residency
  with pressure. Future gates should key on swap *activity* (swapins/outs
  rate) plus pressure level, not raw used bytes.

## 11. Recommended next decision (for Paul)

(a) Re-run Tier A with an activity-based gate (swap rate + pressure level)
now that residency vs pressure is distinguished; (b) extend host telemetry
first; (c) leave observability at current state and proceed elsewhere on
the roadmap; (d) VM resize decision. No option executed without explicit
authorization.

---

*All measurements read-only; timestamps local; no protected workload was
modified, stopped, or restarted during this investigation.*
