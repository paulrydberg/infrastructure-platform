# Level 6 Readiness Observer — Architecture & Installation Record

**Status:** Observer IMPLEMENTED + TESTED (15/15) · cron entry PREPARED, installation pending
one interactive operator step (macOS TCC) · launchd reconstruction scheduler UNCHANGED

## Architecture (explicit boundary)

```
launchd (com.infrastructure-platform.reproducible-validation)
   → Level 6 RECONSTRUCTION (bootstrap/periodic-validate.sh)   [unchanged]
        ↓ deterministic evidence (docs/15-reproducibility/periodic/)
cron (user-level, daily 09:17)                                  [pending operator install]
   → bootstrap/level6-readiness-check.sh
        → bootstrap/level6-readiness-check.py  (pure stdlib, deterministic)
             ├── NOT_READY → record status / silent
             └── READY → one macOS notification (osascript)
                      → operator returns to the human review thread
```

The observer is a **monitoring/reminder layer**, not part of Level 6
reconstruction, and not an autonomous CTO loop. No LLM, no inference, no
model API, no network; no Docker/Kubernetes/Argo; no Git mutation
(`git rev-parse HEAD` read-only); telemetry written OUTSIDE the repository
so the working tree never dirties (L6-9 lesson applied).

## Readiness contract (deterministic; Level 7 entry criteria as target)

| Criterion | Threshold | Current (2026-09-25) |
|---|---|---|
| Evidence duration | ≥ 4 weeks | 0.0 weeks |
| Pass rate excl. BLOCKED | ≥ 90% | 71% (5/7: 5 PASS, 2 FAIL, 2 BLOCKED not counted) |
| Failure recovery | every FAIL later recovered | verified (FAIL→PASS observed) |
| Fleet incidents | 0 | 0 |
| Comparison stability | stable, non-error | stable |
| Runner-version change | ≥ 1 change in history | not yet (all 1.1.0) — honest NOT_READY |
| Reboot survival | evidence older than last boot | not yet demonstrated |

Guards: unique `run_id` dedup (AUD-1 lesson), required provenance fields,
malformed JSON → ERROR, absence of evidence → NOT_READY (never success).
Anti-spam: state file `~/.infrastructure-platform/level6-readiness-state.json`
— notify once on NOT_READY→READY; re-notify only on material evidence change
(new failure class, regression, expanded window) or operator reset.

## Artifacts

- Evaluator: `bootstrap/level6-readiness-check.py`
- Cron entry point: `bootstrap/level6-readiness-check.sh` (pinned PATH, absolute paths)
- Tests: `bootstrap/level6-readiness-tests.py` — **15/15 PASS**
- Telemetry package (READY, local, never committed):
  `~/.infrastructure-platform/level6-readiness-telemetry/`
  (readiness / run-summary / failure-summary / resource-summary /
  comparison-summary / scheduler-summary .json)
- Notification state: `~/.infrastructure-platform/level6-readiness-state.json`
- Review destination (human only — nothing is ever posted programmatically):
  https://chatgpt.com/share/6ab603e7-fd80-83e9-97d6-b38f2dac2d9d?ogimg=plain

## Cron installation — authentic engineering observation

**Prepared entry** (user-level, macmini):

```
17 9 * * * /Users/macmini/.hermes/projects/infrastructure-platform/bootstrap/level6-readiness-check.sh --notify >> $HOME/.infrastructure-platform/level6-readiness-cron.log 2>&1
```

Daily 09:17 rationale: the observer is a cheap read-only check; daily cadence
detects the readiness threshold crossing promptly without duplicating the
twice-weekly launchd reconstruction.

**Installation blocked non-interactively:** every `crontab` invocation on this
host context hangs — macOS TCC requires Full Disk Access for the executing
application to touch `/usr/lib/cron/tabs` (the `com.vix.cron` daemon exists
but cannot accept the entry from this non-interactive context; `sudo -n` is
also unavailable). Stuck `crontab` processes were terminated; no security
control was weakened; SIP/TCC untouched; no undocumented workarounds used;
no launchd substitution was made (operator explicitly requires real cron).

**Operator manual step (interactive):**

1. System Settings → Privacy & Security → Full Disk Access → enable for the
   terminal application you will use (e.g. Terminal.app).
2. In that terminal:

```
crontab /tmp/l6-crontab.txt        # prepared file; recreate with the line above if /tmp was cleared
crontab -l                          # acceptance test: must print the 17 9 * * * entry
```

3. Then run the exact cron command once by hand to verify end-to-end:

```
/Users/macmini/.hermes/projects/infrastructure-platform/bootstrap/level6-readiness-check.sh --notify
```

Acceptance: `crontab -l` prints the entry; the manual run exits 0, prints the
readiness JSON (currently NOT_READY with the reasons above), writes telemetry
to `~/.infrastructure-platform/level6-readiness-telemetry/`, sends no
notification (NOT_READY ⇒ silent), and leaves `git status` clean.

## Current verified state

Observer implemented: yes · Tests 15/15: yes · Cron installed: **pending
operator FDA step** · Manual observer execution: verified (exit 0, correct
deterministic result, tree clean) · Notification mechanism: verified
(osascript self-test rc 0) · LLM inference: 0 · Git mutation: 0 · Protected
fleet: untouched · Duplicate reconstruction scheduler: no.
