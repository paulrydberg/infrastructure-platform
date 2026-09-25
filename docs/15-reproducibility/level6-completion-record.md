# Level 6 Completion Record — Periodically Verified Reconstruction

**Status: LEVEL 6 DEMONSTRATED** · implementation `cc654db` → `ddb628a` ·
real scheduled-run evidence committed under `docs/15-reproducibility/periodic/`
(retained locally; representative records referenced below) · LLM inference 0 ·
protected fleet untouched.

## What changed from Level 4 to Level 6

- **Level 4:** "I can reconstruct the platform" — proven, but only when a
  human ran it.
- **Level 6:** "I periodically prove that the reconstruction contract still
  works" — the same deterministic machinery now runs on a schedule, produces
  an indexed evidence record every run, compares each run against prior
  validated runs, and makes *absence* of validation visible.

## Why Level 6, why not L5/L7

Level 5 (tested DR) is **not applicable**: the project has no meaningful
project-owned persistent state requiring restoration. The introduction of
such state is the condition that would make L5 applicable. Level 7
(continuous validation) remains deliberately deferred — the periodic model
must first operate reliably (see Future Boundary).

## Architecture

```
launchd StartCalendarInterval (Tue/Sat 04:17 local, ExitTimeOut 3600)
        ↓
bootstrap/periodic-validate.sh        (deterministic wrapper)
        ↓  portable PID lockfile (one validation at a time; stale reclaim)
bootstrap/reconstruct.sh              (the proven Level 4 runner — reused, not reimplemented)
        ↓  resource gate (pressure-level primary · pageout-activity secondary · free % context)
full disposable reconstruction        (RECONSTRUCT_EXECUTE=1: k3s → Argo → GitOps → Synced/Healthy)
        ↓  evidence authority (generate → validate → preserve; inherited L4-6 invariant)
evidence record validation-l6-<ts>.json
        ↓  historical comparison (like-for-like, deterministic)
periodic validation result (taxonomy below)
```

No new resident daemon: launchd is the host's existing scheduler. No cloud,
no credentials, no LLM.

## Scheduling Model & Failure Visibility

- Cadence: twice weekly — conservative; full reconstruction ~85 s, so the
  cadence is bounded by evidence value and host availability, not runtime.
- `bootstrap/periodic-status.sh` answers "did validation actually happen?":
  - no evidence at all → `SCHEDULER_ERROR` (exit 2): a missing run is never a PASS
  - evidence older than 10 days → `SCHEDULER_ERROR` OVERDUE (exit 1)
  - last outcome FAIL/EVIDENCE_ERROR → visible (exit 3)
- launchd coalesces missed windows (host asleep); the wrapper records
  `scheduler_missed_window` in the evidence record — demonstrated with a real
  simulated missed window (`validation-l6-20260925T035957Z.json`).

## Evidence Contract (per record)

`run_id · trigger · scheduler (+ missed window) · repository · branch ·
source_commit (exact SHA) · runner_version · manifest_version ·
runner_exit_code · start/end/duration · resource_gate · reconstruction ·
kubernetes/helm/argocd (versions) · gitops · workload_validation ·
evidence_generation · evidence_validation · evidence_retention ·
historical_comparison · drift_result · teardown · protected_fleet_check ·
failure_classification · overall_result · llm_inference_required`

## Failure Taxonomy (non-collapsing)

| Status | Meaning | Demonstrated by |
|---|---|---|
| PASS | reconstruction + evidence gen/validate/preserve all succeeded | real scheduled run `T041255Z` |
| FAIL | reconstruction or validation failure | wrapper classification tests T2/T3 |
| EVIDENCE_ERROR | reconstruction OK but evidence failed — never PASS | T4 + wrapper path |
| BLOCKED | resource-gate rejection — not a reconstruction failure | real scheduled runs `T040310Z`, `T040629Z` |
| SCHEDULER_ERROR | missed window / no evidence — never a PASS | status-checker tests (overdue + never-run) |

## Real Defects Found by Real Scheduled Runs (the reason Level 6 matters)

| ID | Symptom | Root cause | Fix | Commit |
|---|---|---|---|---|
| L6-2 | wrapper dead on macOS (`flock: command not found`) | macOS ships no flock | portable O_EXCL PID lockfile + stale reclaim | `cc654db` |
| L6-3/L6-4 | RECORD KeyError; WARN misclassified in validate-only mode | env not exported; mode-blind classification | export; mode-aware WARN semantics | `cc654db` |
| L6-5 | machinery test recorded fake reconstruction results | fields not mode-aware | validate-only runs record `NOT_EXECUTED` | `cc654db` |
| L6-6 | false "duration REGRESSION" across run classes | compare mixed baselines; field mismatch | like-for-like comparison + field fallback | `ddb628a` |
| L6-7 | **gate BLOCKED at 76% free memory** | raw swap-used threshold conflated residency with pressure (the Phase 6 mistake) | pressure-level primary, swap-activity secondary | `61c1b2d` |
| L6-8 | still BLOCKED: cold-page readback counted | pageins+pageouts summed | pageouts-only activity signal | `fdbde21` |
| L6-9 | every scheduled run dirtied the tree → next run's clean-pin WARN | evidence written inside repo, untracked | evidence dir gitignored (retained local evidence) | `ddb628a` |

Six of seven defects were invisible until validation actually ran on a
schedule — the strongest argument for Level 6 itself.

## Historical Comparison & Drift Semantics

Each run compares against the most recent **like-for-like** record: revision
changed/same, result transition, duration stability (>50% change flagged),
resource-gate state. **Drift = unexpected difference between declared and
observed state** (image, security properties, GitOps convergence). A new Git
commit is *expected change*, never drift; `NO_UNEXPECTED_DRIFT` vs
`DURATION_REGRESSION` are the current deterministic drift outcomes.

## Test Results

- `bootstrap/periodic-validate-tests.sh`: **21/21 PASS** (T1 happy path
  end-to-end; T2/T3 reconstruction & GitOps failure → FAIL; T4 evidence →
  EVIDENCE_ERROR; T5 gate → BLOCKED incl. PASS-cannot-override; T6 scheduler
  visibility; T7 teardown residue never silent; T8 concurrency skip; T9
  idempotence after failure + comparison executed).
- `bootstrap/report-authority-tests.sh`: 11/11 PASS (invariant intact).
- Real scheduled runs via `launchctl kickstart`: PASS → BLOCKED → BLOCKED →
  FAIL(WARN) → **PASS** — the full failure taxonomy exercised live, with a
  clean run after failures (S12) and evidence retained for every run.

## Success Criteria

S1–S17: all demonstrated (S4/S5/S13/S14 from the real PASS run: disposable
k3s Ready, Argo Synced+Healthy @ exact commit `ddb628a3…`, teardown complete,
fleet unchanged; S15 zero new resident daemons; S16 LLM 0; S17 enforcement
untouched — `ci.yml` unchanged since Phase 7).

## Resource Model

Gate now measures what Phase 6 said to measure: pressure level (primary),
pageout activity (secondary), free % (context). The two live BLOCKED runs
were the gate working as designed (safe refusal) while its signal choice was
wrong — both corrected without bypassing the gate.

## Limitations

Local-only (single host); evidence retained on the same host it validates
(off-host retention = future); branch-tip reconstruction (SHA-pin = future
hardening); comparison is heuristic (no statistical baseline, by design).

## Future Boundaries

- **Level 7** requires: the periodic model operating reliably across weeks,
  demonstrated evidence retention/drift value, and a concrete need for
  event-driven validation.
- **Dependency automation** integrates cleanly: dependency PR → scheduled/
  disposable validation → evidence → merge gate (explicitly NOT authorized).
- **L5 DR** becomes applicable only with meaningful project-owned persistent
  state.
