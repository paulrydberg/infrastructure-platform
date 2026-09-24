# Experiment Record — Option A Abort on Rejection Condition 1

**Status:** ABORTED BEFORE STARTUP (2026-09-24)
**Action taken:** STOP → evidence collected → state verified clean → documented → reported
**Nothing was started; no rollback was required; no resources were increased.**

## What was authorized

Phase 2 implementation, Option A: k3s in a hard-capped container (2.5 GiB /
2 cores) inside the existing Docker Desktop VM, governed by 5 hard rejection
conditions.

## Step 2.1 pre-flight — rejection-condition check

Per the staged plan, the FIRST step was baseline validation before any
component introduction. Rejection condition 1:

> Docker VM free memory falls below 3.0 GiB sustained before k3s startup.

### Measured evidence (direct /proc/meminfo via probe container — the
### measurement method Paul's authorization implicitly requires: "use
### measurements wherever possible")

5 samples, 6 s apart:

| Sample | VM total | VM available |
|--------|----------|--------------|
| 1 | 7838 MB | 2471 MB |
| 2 | 7838 MB | 2427 MB |
| 3 | 7838 MB | 2496 MB |
| 4 | 7838 MB | 2435 MB |
| 5 | 7838 MB | 2497 MB |
| **Average** | | **2465 MB — REJECTION CONDITION 1 TRIGGERED** |

Concurrent host state: load 5.95→7.42 (1-min, of 12 threads; 5-min 4.3–5.2),
swap 680 MB (baseline unchanged).

### Root cause of the wrong earlier estimate

The Phase 2 evaluation derived "≈4.5–5 GiB free" by subtracting the sum of
container memory usage from the VM allocation. That method is invalid: the
VM's kernel, Docker daemon, and page-cache/buffer accounting mean real
*available* memory (reclaimable-cache-adjusted, what new processes can
actually use) is ~2.47 GiB. The direct `/proc/meminfo` probe is the correct
instrument; the derived estimate was the failure. **Recorded as an honest
measurement-methodology lesson: derived capacity estimates must be replaced
by direct instrumentation before gating decisions.**

The top consumer: the protected OLAP database at 2.02 GiB inside its 4 GiB
cap (legitimately using its allocation — protected, untouchable).

## Decision applied (per Paul's explicit rule)

> "If any rejection condition occurs: stop, collect evidence, roll back,
> document the result, report the finding, and do not increase resource
> limits automatically."

- **STOP:** k3s container was never created/started. The k3s image was
  pulled (inert, ~200 MB disk, zero memory impact) and left in place,
  documented.
- **ROLLBACK:** verified no k3s container/volume/network exists; protected
  workload state identical to pre-authorization baseline (no restarts; the
  only RestartCount=1 entries predate this work — verified in the baseline
  capture before startup).
- **DOCUMENT:** this record.
- **NO automatic limit increases, NO cap reduction, NO Docker Desktop
  changes, NO protected-workload changes.**

## Implications (factual, narrow claim per authorization)

The claim actually established by testing is narrower than even the cautious
phrasing suggested:

> "Phase 2 testing established that the Option A starting boundary (2.5 GiB)
> cannot be safely evaluated in the current Docker VM state: sustained
> available VM memory (≈2.47 GiB measured) is below the pre-agreed rejection
> threshold (3.0 GiB) before k3s startup. The experiment was aborted at the
> pre-flight gate by design."

Running k3s under a 2.5 GiB cap in a VM with 2.47 GiB available would place
the VM itself at exhaustion risk even with the cap enforced — the cap bounds
k3s, not the VM. The rejection condition did exactly its job.

## Options now (NOT chosen — Paul decides; none may be self-authorized)

| Option | Description | Trade-off |
|--------|-------------|-----------|
| A′ | Retry Option A when VM available memory recovers above 3.0 GiB (it fluctuates with the protected OLAP db's working set) | may never reliably clear the bar; re-measure first |
| A″ | Reduced k3s envelope (e.g. 1.5 GiB cap) — k3s server class ~700–900 MB could fit | boundary change — requires explicit new authorization; narrows what the cluster can host |
| B | Docker Desktop VM resize (10–12 GiB) | Docker restart impacts all 21 running containers; previously analyzed |
| C | Defer local Kubernetes; proceed Phase 3+ on Docker/compose; revisit k8s at AWS phase | architecture change; portfolio/platform implications |
| D | Hardware/environment separation | out of project scope; host-level decision |

## State after abort

- k3s: image pulled only, no container, no volume, no network
- Protected workloads: 20/20 running, no restarts attributable to this work
- platform-demo: still healthy (untouched)
- Host: no configuration changed
