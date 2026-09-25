# Level 6 Readiness Observer — Architecture & Installation Record

**Status:** Observer IMPLEMENTED + TESTED (15/15) · **cron entry INSTALLED + VERIFIED via
crontab -l** (2026-09-25, after operator granted Full Disk Access to Terminal) · launchd
reconstruction scheduler UNCHANGED

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

**Installation history (authentic engineering observation):** initially every
`crontab` invocation hung — macOS TCC requires Full Disk Access for the
executing application to touch `/usr/lib/cron/tabs`. No security control was
weakened; SIP/TCC untouched; no launchd substitution made (operator requires
real cron). The operator granted Full Disk Access to Terminal; installation
then succeeded non-interactively:

- `crontab /tmp/l6-crontab.txt` → rc 0
- `crontab -l` → prints exactly the observer entry (acceptance test PASSED)

**Installed schedule (verified via `crontab -l`):**

```
17 9 * * * /Users/macmini/.hermes/projects/infrastructure-platform/bootstrap/level6-readiness-check.sh --notify >> $HOME/.infrastructure-platform/level6-readiness-cron.log 2>&1
```

Daily 09:17. The entry invokes only `level6-readiness-check.sh` (pinned PATH,
absolute paths). Proven properties of the execution path: pure local
computation (AST-verified: only `git rev-parse HEAD` read-only, `sysctl
kern.boottime`, `osascript` notification — no network, no GitHub API, no
Docker/Kubernetes/Argo, no model API, no reconstruction trigger), no Git
mutation, telemetry written outside the repository.

**Manual verification of the exact cron command** (minimal cron-like env:
`PATH=/usr/bin:/bin:/usr/sbin:/sbin`): exit 0, deterministic result
`NOT_READY` (0.0 weeks history < 4; pass rate 71% < 90%; runner-version
change not yet available; reboot survival not yet demonstrated — all honest
NOT_READY reasons, expected for a young evidence window), telemetry refreshed
(all 6 artifacts 0s-old at execution, attributable to that run via matching
`evaluated_at`), notification correctly silent (NOT_READY ⇒ no notify; state
file untouched), `git status` clean, protected fleet untouched (the running
k3s-server/platform-demo are the PROTECTED fleet — the observer contains no
docker invocation at all). Scheduler separation verified: launchd
(`com.infrastructure-platform.reproducible-validation`, twice-weekly,
reconstruction + authoritative evidence) vs cron (daily 09:17, observation
only). Tests re-run post-install: 15/15 OK.

**Current readiness: NOT_READY — expected.** Level 6 longitudinal evidence
is accumulating on the launchd cadence; the observer will notify once when
the documented Level 7 entry criteria are met by real history.

## Current verified state

Observer implemented: yes · Tests 15/15: yes (re-run post-install) · Cron
installed: **YES** · Verified via `crontab -l`: **YES** · Manual observer
execution: verified (exit 0, NOT_READY, telemetry fresh, tree clean) ·
Notification path: verified (silent on NOT_READY; READY path covered by
tests) · LLM inference: 0 · Network dependency for evaluation: 0 · Git
mutation: 0 · Protected fleet: untouched · Duplicate reconstruction
scheduler: none — launchd remains the only reconstruction scheduler.
