# Phase 6 Decision Gate Report — Tier A (metrics-server) Go/No-Go

**Status:** DECISION GATE COMPLETE (2026-09-24) — nothing installed; awaiting
authorization. **Recommendation: GO** with the explicit gates below.

---

## 1. Current baseline (re-verified this gate, 5 samples, read-only) [M]

| Check | Result |
|-------|--------|
| Git | `main`, clean tree, HEAD==origin/main (`466161f`), CI **success** |
| Argo CD | **Synced Healthy** (untouched) |
| platform-demo | 1/1 Running, `/health` → `{"status":"ok","version":"0.1.0"}` (uptime 1383 s) |
| Protected fleet | 20/20 running, 0 restarts, 0 OOMs |
| k3s RSS / cap | **1.069–1.074 GiB / 1.5 GiB** (~71%, stable across samples) |
| VM available | **1933–1947 MB** (avg ≈ 1938 — improved vs 1840 at analysis time) |
| Swap | 657.75 MB, **flat across all 5 samples** (no growth) |
| Host load | 3.7–4.3 (one 6.1 spike, transient; 5-min avg 4.18) of 12 threads |
| API `/readyz` | 0.292 s round-trip (healthy) |
| PVCs | 0 (no persistent state) |

No unexpected resource pressure since the checkpoint. Baseline is
known-good and slightly better than the Phase 6 analysis-day numbers.

## 2. Historical measurements used (measurements, not estimates)

From Phase 6 capacity analysis [M]: VM avail 1827–1851 · k3s 1.046–1.05 GiB ·
Argo per-component ~174 MB · swap 495–657 fluctuating · storage 596 GiB free
in VM, 0 PVCs. From Phase 5A [M]: Argo install added ~210 MB VM pressure with
zero protected impact; staged teardown/reinstall cycle worked cleanly.
Metrics-server sizing remains class **[E]** (60–100 MB documented/estimated)
— conversion of [E]→[M] is precisely what the experiment would accomplish.

## 3. Current resource envelope [M]

```
k3s cap                1536 MiB
k3s current            ~1072 MiB   (k3s core ~870 + Argo ~174 + demo ~27)
in-cap headroom          ~464 MiB
VM available            ~1938 MB
```

## 4–5. Tier-A requirements & expected impact

| Aspect | Value [class] |
|--------|---------------|
| Memory | metrics-server pod **60–100 MB [E]**; in-cap headroom remains ~364–404 MiB after |
| CPU | negligible idle [D]; scrape bursts every 60 s [D] |
| Storage | **zero** — in-memory only, no PVC [D] |
| Privileges | **none elevated** — reads kubelet Summary API over in-cluster HTTPS with its own ServiceAccount; no host mounts, no hostNetwork, no privileged [D] |
| Compatibility | metrics-server v0.7.x supports k3s 1.31 [D]; k3s ships it as a deployable addon — no configuration conflict; **note [U]:** k3s embeds its own kubelet metrics paths; validation will confirm scrape paths work as expected |
| Network/API exposure | none new — in-cluster API access only; no new ports, no ingress, loopback posture unchanged [D] |
| Reproducible install | pinned manifest via `platform/metrics-server/` in Git (upstream components.yaml at a pinned release tag, recorded + verified), applied via kubectl — and/or registered as k3s addon config; **not** ad-hoc |
| Clean removal | `kubectl delete -f <pinned manifest>` — stateless, zero PVC cleanup |
| Health validation | `kubectl top nodes/pods` returns real numbers; pod Ready; API latency unchanged |
| Rollback | delete manifest → cluster returns to today's exact state (stateless component) |
| Success | within a 60-min observation window: pod Ready; `kubectl top` functional; k3s RSS stays ≤ 1.25 GiB under normal ops; VM avail ≥ 1800 MB; swap flat; protected fleet 0 restarts/OOMs; API latency within +0.2 s of baseline |
| Abort | k3s RSS > 1.35 GiB sustained; any protected restart/OOM; swap growth > +100 MB sustained > 15 min; API latency > 2× baseline sustained; metrics-server CrashLoop/OOM |
| Unacceptable (hard stop) | any protected-fleet impact attributable to the experiment; any need to raise limits |

## 6–8. Gates defined BEFORE installation (reject/abort if)

- k3s approaches ceiling (>1.35 GiB sustained) → abort
- protected containers restart/OOM/degrade → hard stop
- swap pressure materially and persistently up → abort
- host load sustained >8 with idle workload → abort
- API responsiveness materially degraded → abort
- metrics-server unstable → abort (record honestly)
- remaining headroom insufficient for operations → abort

**Success window:** 60 minutes of observation with periodic sampling (not a
post-startup snapshot), matching the Phase 5A observation discipline.

## 9. Reproducibility / rollback plan

source of truth (pinned manifest in Git) → reproducible install (recorded
command) → validation (top/Ready/latency) → 60-min measured observation
window → documented result ([E]→[M] conversion) → clean rollback (delete
manifest). Identical shape to the Phase 5A staged-experiment discipline.

## 10. Recommendation: **GO**

Rationale: smallest possible component (60–100 MB [E]) against ~464 MiB
measured in-cap headroom [M]; stateless; no privileges; no new exposure;
clean rollback; converts the only remaining estimate into measurement and
unblocks `kubectl top` (operational gain proven needed by the crictl/cgroup
probing used since Phase 2). Risk is bounded and reversible.

## 11. Exact next authorized step (if GO)

1. Fetch metrics-server v0.7.2 components manifest; record SHA-256 in Git
   (`platform/metrics-server/`)
2. Apply to kube-system with the resource limits from this report
3. Validate: pod Ready, `kubectl top nodes`/`pods` functional, API latency
4. 60-min observation window (5-min sampling): k3s RSS, VM avail, swap,
   load, protected fleet
5. Document `docs/09-observability/tier-a-experiment.md` ([E]→[M])
6. Commit evidence → CI green → stop at the next boundary

## 12. Explicitly out of scope

Prometheus, Grafana, Loki, OpenTelemetry, tracing, alerting, WUD, AWS,
AI operations, Docker resize, Argo changes, Ubuntu laptop, Tier B/C —
all remain gated. Metrics-server only; removal plan ready if any gate trips.

---

**Historical note preserved (per instruction):** the Phase 5A source-of-truth
incident remains documented in the repo history as it actually happened —
temporary branch → config stranded → branch deleted → orphaned object
discovered → recovery from `de6de8a` → live-cluster comparison → restore to
main → synchronization. Nothing rewritten.
