# Resource-Gate Design Principles (Evidence-Backed)

**Origin:** the Phase 6 Tier-A metrics-server experiment (2026-09-24) and the
read-only swap-driver characterization that followed it. This document
turns that event into a reusable platform principle.

## The core lesson

The original Tier-A gate used a coarse indicator — raw "swap used" bytes —
as a failure trigger. The subsequent characterization showed the host was
healthy (macOS pressure level 1 NORMAL, 76% free, zero swap-in activity at
rest, no degradation anywhere) while swap *used* remained elevated as
cold-page residency. The gate conflated **residency** with **pressure**.

## The distinction chain

Future memory/resource gates must distinguish at minimum:

```
resource allocation
    ≠
resource utilization
    ≠
swap residency (cold pages parked in swap)
    ≠
swap activity (swapin/swapout rates)
    ≠
memory pressure (OS-reported state)
    ≠
performance degradation (observed workload impact)
```

A gate keyed on any single ring of this chain can fire while the system is
actually healthy — or stay silent while it is not.

## Signals available and evidence-backed on this platform

| Signal | Source | Evidence value |
|--------|--------|----------------|
| macOS memory-pressure level | `sysctl kern.memorystatus_vm_pressure_level` | PRIMARY (level 1 = NORMAL) |
| Swap-in/out *rates* | `vm_stat` deltas over time | PRIMARY (0 delta at rest = residency, not pressure) |
| Sustained available memory | repeated samples, not snapshots | PRIMARY (trend over window) |
| Container OOM/restarts | `docker inspect` (RestartCount, OOMKilled) | PRIMARY (per protected fleet) |
| k8s MemoryPressure condition | `kubectl get nodes -o jsonpath` | PRIMARY (in-cluster view) |
| Workload degradation | app health checks / payload checks | PRIMARY |
| Swap *used* bytes | `sysctl vm.swapusage` | SECONDARY ONLY — insufficient alone on macOS/Docker Desktop |
| k3s RSS vs limit | docker stats | contextual (allocation vs utilization) |
| API latency | /readyz timing | contextual |
| Host load | uptime | contextual |
| Pearson-style correlation of driver RSS vs swap | post-hoc attribution | diagnostic, not a gate |

**macOS/Docker Desktop specific:** raw "swap used" is insufficient by
itself to declare memory-pressure failure. macOS parks cold pages in swap
during normal operation (compressor mode 4, hysteresis); elevated used
bytes persist long after the pressure event and decline slowly on idle
(1345.5 → 1281.5 MB over ~25 min observed). A swap-used threshold fired
here while every PRIMARY signal read healthy.

## Gate composition rule (not a universal formula)

Where practical, a resource gate should require **at least one PRIMARY
signal degraded, corroborated by a second**, rather than any single
secondary indicator firing alone. Examples of gate *styles* (to be tailored
per experiment, not standardized prematurely):

- pressure-style gate: `pressure_level > 1` sustained N minutes
- activity-style gate: `swapins_delta > X per interval` sustained N minutes
- degradation-style gate: OOM/restart/health-check failure on any workload
- envelope-style gate: sustained available-memory trend below a floor

Swap-used bytes may still be recorded (it is free telemetry) but should be
treated as context, never as a standalone abort trigger on this host.

## Honest-history rule

When a gate fires and later analysis shows the gate indicator itself was
coarse, the correct sequence is: keep the original result and its
classification verbatim → investigate read-only → document the improved
interpretation as a separate artifact → apply the refined gate to *future*
experiments. Never retroactively reclassify the historical run.

## Where this was applied

- Tier-A experiment: classification preserved unchanged (FUNCTIONAL
  VALIDATION SUCCESSFUL / SWAP GATE TRIGGERED / CAUSALITY UNCERTAIN);
  metrics-server remains experimentally validated, not retained.
- Swap-driver characterization: the evidence artifact that motivated this
  principle (docs/09-observability/swap-driver-characterization.md).
