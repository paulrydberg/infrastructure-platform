# Post-Level-6 Independent Audit + Architecture Decision Gate

**Status:** AUDIT COMPLETE — Level 6 claim **VALIDATED (with qualification)**; one real defect
found and minimally fixed (AUD-1); longitudinal qualification explicit.
**Date:** 2026-09-25 · Auditor: Hermes CTO (independent of the Level 6 implementation summary)
**Basis:** repository + observable evidence authoritative; prior CTO conclusions treated as claims.

## 1. Executive conclusion

Level 6's **mechanism** is genuinely demonstrated and now stronger than when reported: the audit
found and fixed one real evidence-authority defect (AUD-1 — stale runner-report inheritance),
raising the wrapper test suite to 22/22. The claim «Level 6 = periodically verified
reconstruction» is **correctly scoped but temporally thin**: six retained evidence records from a
single day, of which three are full reconstructions. Mechanism demonstrated ≠ longitudinal
maturity accumulated — the distinction is now documented as the claim's boundary condition. No
further implementation is justified until scheduled history accumulates.

## 2. Baseline (verified, not assumed)

- HEAD `2c6c575` (post-AUD-1-fix) == origin/main, branch main, working tree clean
- CI green (runs @ `631af3b9`, `ddb628a3`, `fdbde213`, `61c1b2d2`, `cc654db7` all success)
- `ci.yml` last changed `f1043e3` (Phase 7) — enforcement untouched; gate present
- launchd job registered: state not-running (idle), runs=5, last exit 0
- Runner 521 lines, wrapper 337, status checker 47, tests 170+102; report-authority 11/11
- AWS/cloud 0; LLM 0; disposable environments 0; protected fleet healthy

## 3. Level-6 claim verification

Chain inspected in source (not docs): launchd plist → wrapper (lock → env snapshot →
`RECONSTRUCT_EXECUTE=1` runner) → resource gate (pressure-level/pageouts/free) → disposable k3s
(:16443, no volume) → ctr image import → Argo 7.7.11/v2.13.3 → Application apply → Synced+Healthy
→ workload validation → report → `report_validate` → L6 evidence record → like-for-like
comparison → teardown → fleet check → classification. **Implementation matches the documented
architecture.** The A. mechanism dimensions all demonstrated (see completion record + 22/22
tests). B. longitudinal: **6 records / 1 day / 3 full reconstructions** — see §5.

## 4–5. Maturity qualification (mechanism vs longitudinal)

| Dimension | Verdict | Basis |
|---|---|---|
| A. Mechanism | **DEMONSTRATED** | full chain executed live repeatedly; taxonomy exercised; 22/22 + 11/11 tests |
| B. Longitudinal | **NOT YET ACCUMULATED** | 6 records, single day, single host; no multi-week history |

**Maturity claim:** Level 6 stands as *mechanism demonstrated*; the record explicitly states
longitudinal confidence requires weeks of scheduled history. This audit makes that boundary
explicit rather than implicit.

## 6. Scheduler audit

- Paths absolute; wrapper sets its own PATH; plist pins PATH; `ExitTimeOut 3600` bounded.
- **Scheduler-fail ≠ reconstruction-fail:** missed-window recorded in evidence; status checker
  classifies never-run (exit 2) and overdue (exit 1) as SCHEDULER_ERROR. A missing run cannot
  disappear silently (evidence gap visible by design).
- **False PASS by scheduler:** impossible — scheduler only launches; PASS requires fresh evidence.
- **Overlap:** portable O_EXCL PID lockfile; concurrent run records "skipped" and exits 0 (T8).
- **Stale lock:** dead-PID detection + reclaim — **live-tested** (reclaimed stale lock from
  nonexistent PID 999999; run proceeded).
- Ambiguity documented: launchd coalesces missed windows to ONE catch-up run (recorded), and
  status-checker currency depends on system clock sanity.

## 7. Evidence-authority audit (probes 1–10)

| Probe | Result |
|---|---|
| valid run + valid evidence | PASS, exit 0 (real run T041255Z) |
| evidence-generation failure | **AUD-1 found here** — fixed; now EVIDENCE_ERROR/FAIL, never PASS |
| malformed evidence | rejected (validate layer) |
| status mismatch | rejected |
| missing required fields | rejected (record validator) |
| **retention failure (unwritable dir)** | **live-probed: exit 2 EVIDENCE_ERROR** — proof not silently lost |
| failed reconstruction + failure evidence | FAIL + evidence preserved (runner failure path) |
| scheduler failure + no evidence | SCHEDULER_ERROR via status checker — never PASS |
| corrupted historical evidence | comparison degrades to "comparison error", never false regression |
| unavailable historical evidence | "no previous validation evidence" — honest, no fabrication |

**One inversion existed (AUD-1) and is now closed with a regression test (T10).**

## 8. Historical-comparison audit

Like-for-like enforced: validate-only machinery records are excluded as baselines (L6-6);
field fallback (`overall_result` → `final_status`) fixed; comparison covers revision,
result transition, duration stability (>50% flagged), gate state. Schema/version changes are not
yet compared (runner_version/manifest_version recorded but not diffed) — documented as a
**known heuristic limit**, acceptable at current maturity; runner version changes are visible in
evidence for manual comparison.

## 9. Drift audit

Drift = unexpected declared-vs-observed difference. Expected change (new commit) never alarms —
comparison records "revision: changed" informationally. Security/image expectations are enforced
in the runner's workload validation (readOnlyRootFilesystem, runAsNonRoot, pinned image tag —
checked per run), which is the strongest deterministic drift control. **Drift detection is
deterministic and currently narrow (duration + revision + result); manifest-content diffing is a
future refinement, not a defect.**

## 10. Resource-governance audit

Post-L6-7/L6-8 gate verified: pressure level (primary), pageouts-only activity (secondary),
free % (context). Cold residency and readback bursts are no longer misclassified — verified by
the audit's standalone measurements (pageins 8 / pageouts 0 / pressure 1 = healthy) vs the two
historic BLOCKED runs. The two BLOCKED outcomes were the gate *working* (safe refusal); the
signals were corrected without bypassing the gate. No Docker resize; no production limit changes.

## 11. Hidden-state audit

- **PATH:** wrapper self-sets; hostile-env (`env -i`) probe executed — wrapper functioned.
- **KUBECONFIG:** L4-1 guard intact — hostile KUBECONFIG honored, prod stage failed honestly
  (FAIL, evidence preserved); disposable stages pin their own kubeconfig.
- **One declared-but-local dependency identified (documented, not eliminable):** the *live
  validation stages* read the production kubeconfig — a gitignored local credential file. This is
  correct secret hygiene (never published) and the disposable reconstruction path does NOT
  require it; but a from-scratch clone on another host would skip live prod checks rather than
  fail. **Classification: KNOWN LIMITATION (declared), not hidden state.**
- Stale containers/volumes/ports: guarded (stale-container guard, :16443 only, no volumes).

## 12. Defect reconciliation — **the correct count is EIGHT, not seven**

L6-2, L6-3, L6-4, L6-5, L6-6, L6-7, L6-8, L6-9 = **eight distinct identifiers** in code and docs.
The completion summary said "seven"; it evidently grouped L6-3/L6-4 (both fixed in the same
pass) as one. Documentation corrected by this audit: **eight defects** (plus audit-found AUD-1 =
nine total corrected defects in the Level 6 layer). All eight verified as *eliminated* (root
causes addressed), not worked around: L6-2 (portable lock, live-tested reclaim), L6-3/4/5
(export + mode-aware semantics), L6-6 (like-for-like + field fallback), L6-7/8 (gate signals
rebuilt per Phase 6 principles), L6-9 (retention/cleanliness conflict resolved by design).

## 13. Failure → recovery audit

Verified from retained evidence (all six records inspected):
`T040106Z PASS (84s, cc654db7)` → `T040310Z BLOCKED (gate)` → `T040629Z BLOCKED (gate)` →
`T040923Z FAIL (dirty-tree WARN, fdbde213)` → `T041255Z PASS (84s, ddb628a3)` —
**recovery without manual repair of the reconstruction system is genuinely demonstrated**; each
run's classification, commit, gate state, teardown, and fleet check verified against its record.
The FAIL→PASS transition happened across a real fix commit (L6-9), which is authentic recovery,
not luck.

## 14. Protected-fleet audit

Disposable environment: loopback **:16443** only (never 6443), no named volumes, ephemeral
kubeconfig, dedicated compose project, per-run teardown + fleet check recorded in every evidence
record (`protected_fleet_check: yes` in all six). Production kubeconfig is used read-only for
live validation stages; the L4-1 helm ownership guard remains. **validation environment ≠
production environment — verified.**

## 15. Security/CI audit

Branch protection ACTIVE (linear history required, force-push/deletion disabled); required
status-check contexts empty and enforce_admins false — **DOCUMENTATION GAP** (protection exists
but is not maximally strict; recording as fact, not changing settings during audit). Secret
scanning + push protection: enabled. Workflow least-privilege permissions present. No new
secrets; no workflow weakening; enforcement untouched since `f1043e3`.

## 16. Git-history authenticity

Commit chain `cc654db` → `61c1b2d` (L6-7) → `fdbde21` (L6-8) → `ddb628a` (L6-9) → `631af3b`
(docs) → `2c6c575` (AUD-1): each fix commit corresponds to an observed failure; messages state
symptom, root cause, correction, and lesson; no squashes; no manufactured activity. The
BLOCKED→BLOCKED→FAIL→PASS sequence is preserved in retained evidence AND reflected in commit
order. **Authentic.**

## 17. Employer/interviewer assessment

An external reviewer can establish: purpose (docs/00-project-origin), deterministic-first design
(no LLM in operations), the reproducibility ladder with honest level distinctions, GitOps +
enforcement + reconstruction, resource governance with a *corrected* gate (two real defects in
the gate itself, preserved), failure engineering (17+ preserved defects across L3/L4/L6), and
explicitly deferred capabilities with reasons. Reproducibility of claims: tests + runner are
executable; scheduled evidence is retained locally (limitation documented).

## 18. Architecture statement

«A deterministic, resource-governed, evidence-driven infrastructure platform that reconstructs
itself from source and periodically verifies that reconstruction, without LLM inference, cloud
infrastructure, or persistent monitoring services.» — **Accurate.** The audit adds one
amendment: *periodic verification is demonstrated as a mechanism; its longitudinal value is
still accumulating.*

## 19–22. Decision gate

**Next capability: Candidate A — accumulate Level 6 history** (passive: scheduled runs continue;
evidence quality reviewed periodically). Rationale: the only remaining gap in the Level 6 claim
is temporal; every other candidate (B–G) either depends on that history or lacks demonstrated
need. Dependency automation (C) is architecturally justified as a *future* consumer of the
periodic machinery — the substrate exists (update → build → scan → disposable reconstruction →
GitOps validation → evidence → PR decision) — but requires weeks of scheduled reliability first.

**Level 7 entry criteria (measurable):** ≥4 consecutive weeks of scheduled runs; ≥90% PASS rate
excluding BLOCKED; ≥2 distinct failure classes detected and recovered automatically-visible;
zero missed-window periods undetected; zero protected-fleet incidents; stable comparison across
≥1 runner-version change; evidence surviving ≥1 host event (reboot). External evidence retention
is *desirable before L7 but not a blocker at L6* — local retention is a documented limitation,
not a violation of "the machine is disposable" (the source of truth is Git; evidence is
historical, not authoritative-state).

## 23. Remaining limitations & defects

- **AUD-1** (found+fixed this audit, commit `2c6c575`, test T10, 22/22)
- Local-only evidence retention (KNOWN LIMITATION)
- Production kubeconfig required for live validation stages on this host (KNOWN LIMITATION,
  declared)
- Branch protection not maximally strict (DOCUMENTATION GAP, recorded)
- Comparison does not yet diff runner/manifest versions (KNOWN LIMITATION)

## 24. Final decision

**Level 6 remains the current demonstrated maturity — mechanism verified, evidence authority
now independently validated, longitudinal accumulation the next (passive) step. No further
implementation authorized. HARD STOP.**

Audit changes: AUD-1 fix + T10 (`2c6c575`); this document; evidence-index note. Nothing else.
