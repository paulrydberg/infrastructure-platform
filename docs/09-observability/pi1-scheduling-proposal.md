# PI-1 Snapshot Scheduling Proposal (ACCEPTED + ACTIVATED 2026-10-31)

**Status:** **ACTIVATED 2026-10-31** — operator-authorized after a passing
deterministic-only execution audit (`deterministic-execution-contract.md`).
Installed: hourly at :17 (the exact line below). First scheduled execution
verified 2026-10-31T03:17:01Z. Rollback: `crontab -l | grep -v pi1-snapshot | crontab -`.
The wrapper
(`bootstrap/pi1-snapshot-cron.sh`) is committed and tested; when this
document was first written the wrapper was inert — it is now installed on
the live host.

## Why the existing system scheduler

The host already runs project cron entries (level6-readiness-check daily,
nextcloud jobs) under the plain `crontab`. Level 6 validation deliberately
stays on launchd (heavier machinery, reboot-survival evidence). A PI-1
snapshot is a ~15 s read-only probe — cron is the least-complex reliable
mechanism, adds zero new services/dependencies, and follows the existing
convention documented in the crontab comments.

## Proposed specification

| Aspect | Value | Rationale |
|---|---|---|
| Command | `/Users/macmini/.hermes/projects/infrastructure-platform/bootstrap/pi1-snapshot-cron.sh` | absolute path; no cwd assumption |
| Cadence | hourly at :17 (`17 * * * *`) | :17 avoids the :00 load spike; 24 samples/day is ample for PI-2 trend fitting without noise; matches level6 observer's minute convention |
| Output | `~/.infrastructure-platform/pi1-snapshots/pi1-YYYYMMDD-HHMMSSZ.json` (UTC) | sortable, collision-free, outside repo (evidence is host state, not source) |
| Retention | 90 days, enforced in-wrapper on each run | PI-2 needs ≥2 weeks quality data; 90 d gives seasonal margin; ~24 files/day × 90 d ≈ 2,160 files ≈ **~15–20 MB total** (each ~7–9 KB) — negligible vs 20+ GiB free-floor oscillation |
| Logging | cron line appends to `~/.infrastructure-platform/pi1-snapshot-cron.log`; wrapper logs ok/probe_errors/fail/lock-skip lines | failure visibility without a new log service |
| Concurrency | PID lockfile (`/tmp/pi1-snapshot.lock`); overlapping runs **skip** (exit 0, logged); stale locks (dead PID) removed | collector is idempotent; skipping beats queueing; stale-lock recovery prevents permanent blockage |
| Partial/malformed collection | snapshot with failed probes is still stored (nulls are data — ADR-0012); structurally invalid JSON moved to `<name>.failed` + `.failed.stderr`; wrapper exits 1 (visible in cron log) | never fabricates; never silently drops |
| Failed execution | `.failed` marker + stderr retained 90 d; exit code 1 | cron visibility; no blind retry (operator diagnoses) |
| Rollback / disable | delete the single crontab line (or `crontab -e`); wrapper is stateless beyond its output dir; data dir can be archived/removed independently | one-line activation, one-line deactivation |

## Evidence-quality criteria for unlocking PI-2 / PI-6 (not just "two weeks")

A snapshot window qualifies for PI-2/PI-6 consumption only when:

1. **Coverage:** ≥ 14 consecutive calendar days with ≥ 90% expected sample
   count (≥ ~302 of 336 hourly slots), measured from manifest counts.
2. **Schema validity:** ≥ 95% of snapshots pass `validate_snapshot()` with
   zero `probe_errors` (nulls permitted but tracked; sustained probe failure
   disqualifies the window for the affected field).
3. **Gap discipline:** no gap > 6 h between consecutive qualified snapshots
   (longer gaps break trend continuity and must be excluded).
4. **Threshold stability:** `gates.capacity_gate_gib` constant across the
   window (a threshold change resets the window — trend baselines must not
   straddle policy changes).
5. **Staleness bound:** consumers (PI-2/PI-6) must treat any snapshot older
   than `max_age_s` (default 6 h) as STALE_EVIDENCE, never as current state.

Until criteria 1–4 hold, PI-2 and PI-6 remain **dependent on an observation
period** — a calendar fortnight alone does not unlock them.

## PI-2 / PI-6 consumption contract

- PI-2 (forecast) reads `pi1-*.json` sorted by `collected_at_utc`, uses
  `host.free_disk_gib` + `docker.k3s_server_mem_usage` series, refuses
  INSUFFICIENT_DATA below the quality criteria above.
- PI-6 (reporting) embeds latest-qualified snapshot + SHA-256 provenance;
  STALE_EVIDENCE snapshots are reported as stale, not as current.
- PI-5 (bundles) may reference snapshot files as evidence sources.

## What activation requires (operator decision) — **DONE 2026-10-31**

```cron
# infrastructure-platform: PI-1 platform-state snapshot (deterministic; no inference)
17 * * * * /Users/macmini/.hermes/projects/infrastructure-platform/bootstrap/pi1-snapshot-cron.sh >> $HOME/.infrastructure-platform/pi1-snapshot-cron.log 2>&1
```

One line. Reversible by deleting it. No other host state changes.
