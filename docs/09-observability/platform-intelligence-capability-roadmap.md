# Platform-Intelligence Capability Roadmap (2026-10-30)

**Purpose:** define the deterministic, evidence-driven capabilities the
platform should build next, with dependency relationships, resource
classification (GREEN/AMBER/RED per the 2026-10-30 capacity-gate scope
decision), and verification criteria. Foundation documents:
`observability-architecture-assessment-2026-10-30.md`,
`resource-gate-principles.md`, `phase6-completion-record.md`.

**Design rule:** deterministic evaluation first; heuristic/AI-assisted
interpretation only where a deterministic boundary is proven insufficient
(master-spec Phase 11–15 doctrine, unchanged).

## Capability backlog

| # | Capability | Objective | Current state | Depends on | Class | Effort | Verification criteria |
|---|---|---|---|---|---|---|---|
| PI-1 | **Platform-state snapshot collector** | One deterministic script emitting a schema-validated JSON snapshot (host free/swap, Docker VM, k3s RSS+pod set, Argo health, gate status) with provenance (timestamp, tool versions) | **Implemented 2026-10-30** (`bootstrap/platform_state_collector.py`, 17/17 tests). **Recurring snapshots NOT active** — scheduling proposed (`pi1-scheduling-proposal.md`), activation authorization-gated | none (all read-only) | **GREEN — DONE (implementation); operational activation PENDING authorization** | S | `platform-state schema` validation passes; 2 consecutive runs byte-differ only in timestamps/values; no side effects (read-only probes) |
| PI-2 | **Capacity-forecast model (deterministic)** | Linear/exponential fit over PI-1 snapshot history → free-space and k3s-RSS trend with confidence band; explicit insufficient-data verdict | **Prerequisite tooling done 2026-10-31, hardened v1.1.0**: `bootstrap/evidence_window_validator.py` (19/19 tests) measures window qualification (C1 slot-aligned coverage ≥90% — cannot exceed 1.0, C2 schema-valid ≥95% with parseable-but-keyless counted against validity, C3 gaps ≤6 h from actual timestamps, C4 threshold stability) + explicit anomaly handling (duplicates counted once + flagged, future-dated rejected as clock anomalies beyond a 5-min skew tolerance, DST-proof epoch math, deterministic via injectable clock). Non-qualifying window reports WHICH criterion failed and why. **Model itself NOT implemented — blocked on a qualifying recurring-snapshot window** (cron not authorized). 14-day window is a qualification MINIMUM, not a reliability proof | PI-1 window that PASSES evidence_window_validator | **AMBER** (validator DONE; model blocked on evidence window) | M | Model emits forecast + interval; refuses (INSUFFICIENT_DATA) below threshold; back-test against recorded 2026-10 oscillation reproduces documented 13–36 GiB band |
| PI-3 | **Deployment-readiness evaluator** | Deterministic pre-deploy check consuming PI-1 + policy thresholds (free-mem gate, disk gate, k3s cap margin) → READY/NOT_READY with per-criterion evidence | **Implemented 2026-10-30** (`bootstrap/deployment_readiness_evaluator.py`, 20/20 tests; live verdict 2026-10-30 NOT_READY — capacity FAIL, honest) | PI-1 | **GREEN — DONE** | M | Evaluates current host honestly as NOT_READY (capacity); unit tests cover each criterion's pass/fail branches; reuses gate thresholds from `bootstrap.sh` (import or pinned copy + drift test) |
| PI-4 | **Drift detector (state vs declared)** | Compare live k3s/Argo resources + compose services against Git-declared manifests → DRIFT/CONVERGED evidence record | **Implemented 2026-10-31, hardened 2026-10-31 (v1.1.0)** (`bootstrap/drift_detector.py`): 6 declared config fields from Helm/Argo sources, runtime-variation exclusion (restarts/status), fail-closed verdicts (DRIFT/CONVERGED/STALE_EVIDENCE/INSUFFICIENT_DATA/SCHEMA_MISMATCH), **content-hashed `baseline_id`** (metadata-independent baseline versioning), **null-vs-absent distinction** (v1.0.0 conflated them — a nullified value now reports DRIFT, absent fields report INCOMPARABLE, never silent MATCH), read-only, zero-inference, verdict-repeatability tested. **Synthetic tests 29/29**. **PI-5 integration: `pi4_drift_verdict` probe in evidence bundles** (explicit `skipped_no_inputs` when no PI4_BASELINE/PI4_OBSERVED — never silent absence). **Live drift-injection validation NOT performed — authorization-gated** | PI-1 (live probe wiring); live injection test | **GREEN — synthetic DONE; live validation BLOCKED on authorization** | M | Synthetic: all 29 pass. Live: detector run against real Argo-managed state + one authorized disposable drift injection; zero mutations otherwise |
| PI-5 | **Incident-evidence bundle builder** | One command collecting timestamped, checksummed evidence (logs, docker inspect, k3s events, gate records) into a manifest'd bundle | **Implemented 2026-10-31** (`bootstrap/evidence_bundle_builder.py`): PI-1 snapshot + fixed probe set, per-file SHA-256, tamper-evident manifest, explicit probe_failed/malformed_output states, no-overwrite rule, fail-closed collection_status (complete / complete_with_failed_probes / degraded). Tests 16/16 incl. incomplete-data, malformed-input, tamper-hash, live E2E | PI-1 | **GREEN — DONE** (2026-10-31) | M | Bundle reproducible; hashes verify (test_17); failed probe ⇒ status ≠ complete (test_11); zero-inference (test_16); live E2E (test_40) | **Implemented; run on demand** (no recurring activation) |
| PI-6 | **Automated reporting with provenance** | Health/roadmap reports that embed PI-1 evidence + SHA-256 provenance instead of prose-only claims | Daily health check exists (cron, prose); budget report stale (known blocked task). **Window-qualification gate now measurable** (`evidence_window_validator.py`, 11/11 tests) — reports must cite a QUALIFIED window or state INSUFFICIENT_DATA | PI-1 (qualified window via validator), PI-5 | **AMBER** | S–M | Report generator is deterministic; provenance hashes verify; integrates with existing cron |
| PI-7 | **Tier-B observation-window runner** | Staged deploy→measure→teardown of the minimal stack with pre-defined gates (Phase-5A pattern) | Designed (Sep-24, posture 2); not authorized | 50 GiB gate pass + operator authorization | **RED** | L | Window produces [E]→[M] table update; VM returns to baseline (measured); zero protected-fleet impact |
| PI-8 | **Capacity-aware deployment recommender** | Consumes PI-2/PI-3 outputs → GO/NO-GO per candidate workload with explicit thresholds | Not started | PI-2, PI-3 | **AMBER→RED** | M | Recommender verdict matches hand-computed result on recorded data; never overrides operator authorization gates |

## Dependency graph

```
PI-1 (snapshot collector)  ──┬─→ PI-2 (forecast)  ──┐
                             ├─→ PI-3 (readiness)   ├─→ PI-8 (recommender)
                             ├─→ PI-4 (drift)       │
                             └─→ PI-5 (evidence) ───┴─→ PI-6 (reporting)
PI-7 (Tier-B windows) — independent authorization gate (RED: capacity + operator)
```

## Deterministic vs AI-assisted boundary

- **Deterministic (all PI-1…PI-6 collection/evaluation):** thresholds,
  schema validation, trend fitting with explicit models, hash verification,
  gate logic. No inference. LLM count stays 0 — consistent with the
  platform's `llm_inference_required: 0` evidence contract.
- **AI-assisted (later, separately justified):** narrative summaries of
  already-computed evidence; anomaly-explanation drafts. Never the verdict
  source; verdicts stay deterministic (spec Phase 11 boundary, unchanged).

## Sequencing (recommended)

1. **PI-1 + PI-3 now (GREEN, repo-only):** collector + readiness evaluator
   with tests — converts ad-hoc measurement practice into reproducible
   machinery; immediately useful to the Level 6/7 program.
   **Status 2026-10-31: DONE** (commit `42993cf`). PI-5 also DONE
   (evidence-bundle builder, 16/16 tests).
2. ~~PI-5 (evidence bundles) next — reuses PI-1.~~ **DONE 2026-10-31.**
3. PI-2/PI-6 once snapshot history accumulates (≥2 weeks). **PI-1
   scheduling proposed (`pi1-scheduling-proposal.md`); activation is an
   operator decision. Quality criteria are now MACHINE-CHECKABLE:
   `bootstrap/evidence_window_validator.py` (11/11 tests) measures coverage
   ≥90%, schema validity ≥95%, gap discipline ≤6 h, and threshold
   stability — PI-2/PI-6 unlock only on a QUALIFIED verdict, never on
   elapsed time.**
4. ~~PI-4 when a safe disposable drift-injection test is authorized.~~
   **Detector implemented + synthetically validated 2026-10-31**
   (`bootstrap/drift_detector.py`, 29/29 tests after v1.1.0 hardening:
   baseline_id content-hash versioning, null-vs-absent fix, PI-5 bundle
   integration). **Live drift-injection validation remains blocked on
   authorization** and is tracked separately.
5. PI-7 remains RED behind the capacity gate; PI-8 behind PI-2/PI-3.
