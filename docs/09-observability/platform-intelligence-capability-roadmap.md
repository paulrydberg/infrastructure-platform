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
| PI-1 | **Platform-state snapshot collector** | One deterministic script emitting a schema-validated JSON snapshot (host free/swap, Docker VM, k3s RSS+pod set, Argo health, gate status) with provenance (timestamp, tool versions) | **Implemented 2026-10-30** (`bootstrap/platform_state_collector.py`, 17/17 tests). **Recurring snapshots ACTIVE 2026-10-31** — hourly cron installed after a deterministic-only execution audit (stdlib-only imports; subprocess allowlist df/sysctl/docker; zero network/inference primitives; structural reproducibility verified). Observation window STARTED 2026-10-31T03:17:01Z | none (all read-only) | **GREEN — DONE; scheduled collection ACTIVE** | S | `platform-state schema` validation passes; 2 consecutive runs byte-differ only in timestamps/values; no side effects (read-only probes) |
| PI-2 | **Capacity-forecast model (deterministic)** | Linear fit over PI-1 snapshot history → free-space trend with confidence band; explicit insufficient-data verdict | **Implemented 2026-11-12, defect-corrected 2026-11-13** (`bootstrap/pi2_capacity_forecast.py`, 20/20 tests; PRs #7/#8/#9 → `a9bbe49`): OLS on free-capacity with residual-scatter band (2σ), slope-stderr significance gate (STABLE vs FORECAST), rolling-origin backtesting, gate-line time projection anchored at evaluation time, consumption reported separately from free capacity. **Discontinuity-first**: rate-normalized threshold (20 GiB/h) + reversal clustering (a cluster whose NET change reverts within 5 GiB is a reported fluctuation, not a segmenting break); trends never extrapolate across a persistent boundary; post-release tails <24 h/8 obs yield INSUFFICIENT_DATA. **M-R1 integrated 2026-11-14** (PR #10 → `3898d16`): advisory `capacity_forecast` block embedded in every L6 evidence record (never gates). Window qualification re-verified via the validator on every invocation | PI-1 window that PASSES evidence_window_validator | **GREEN (mechanism + live)** — first real FORECAST 2026-11-13 (slope −0.45 GiB/h, ttg ≈17 d); backtest 18 evals MAE 2.84/MAPE 1.09%; first scheduled-evidence FORECAST embedded in `l6-20261114T101700Z` (slope −0.297, ttg 623.9 h) | M | Model emits forecast + interval; refuses below threshold; never extrapolates across a persistent discontinuity; advisory integration proven classification-independent (T21–T24) |
| PI-3 | **Deployment-readiness evaluator** | Deterministic pre-deploy check consuming PI-1 + policy thresholds (free-mem gate, disk gate, k3s cap margin) → READY/NOT_READY with per-criterion evidence | **Implemented 2026-10-30** (`bootstrap/deployment_readiness_evaluator.py`, 20/20 tests; live verdict 2026-10-30 NOT_READY — capacity FAIL, honest) | PI-1 | **GREEN — DONE** | M | Evaluates current host honestly as NOT_READY (capacity); unit tests cover each criterion's pass/fail branches; reuses gate thresholds from `bootstrap.sh` (import or pinned copy + drift test) |
| PI-4 | **Drift detector (state vs declared)** | Compare live k3s/Argo resources + compose services against Git-declared manifests → DRIFT/CONVERGED evidence record | **Implemented 2026-10-31, hardened 2026-10-31 (v1.1.0)** (`bootstrap/drift_detector.py`): 6 declared config fields from Helm/Argo sources, runtime-variation exclusion (restarts/status), fail-closed verdicts (DRIFT/CONVERGED/STALE_EVIDENCE/INSUFFICIENT_DATA/SCHEMA_MISMATCH), **content-hashed `baseline_id`** (metadata-independent baseline versioning), **null-vs-absent distinction** (v1.0.0 conflated them — a nullified value now reports DRIFT, absent fields report INCOMPARABLE, never silent MATCH), read-only, zero-inference, verdict-repeatability tested. **Synthetic tests 29/29**. **PI-5 integration: `pi4_drift_verdict` probe in evidence bundles** (explicit `skipped_no_inputs` when no PI4_BASELINE/PI4_OBSERVED — never silent absence). **Live drift-injection validation NOT performed — authorization-gated** | PI-1 (live probe wiring); live injection test | **GREEN — synthetic DONE; live validation BLOCKED on authorization** | M | Synthetic: all 29 pass. Live: detector run against real Argo-managed state + one authorized disposable drift injection; zero mutations otherwise |
| PI-5 | **Incident-evidence bundle builder** | One command collecting timestamped, checksummed evidence (logs, docker inspect, k3s events, gate records) into a manifest'd bundle | **Implemented 2026-10-31** (`bootstrap/evidence_bundle_builder.py`): PI-1 snapshot + fixed probe set, per-file SHA-256, tamper-evident manifest, explicit probe_failed/malformed_output states, no-overwrite rule, fail-closed collection_status (complete / complete_with_failed_probes / degraded). Tests 16/16 incl. incomplete-data, malformed-input, tamper-hash, live E2E | PI-1 | **GREEN — DONE** (2026-10-31) | M | Bundle reproducible; hashes verify (test_17); failed probe ⇒ status ≠ complete (test_11); zero-inference (test_16); live E2E (test_40) | **Implemented; run on demand** (no recurring activation) |
| PI-6 | **Automated reporting with provenance** | Health/roadmap reports that embed PI-1 evidence + SHA-256 provenance instead of prose-only claims | **Report generator implemented 2026-10-31** (`bootstrap/pi6_evidence_report.py`, 10/10 tests): assembles latest-snapshot + window verdict + PI-3 verdict into one schema-valid report with per-input SHA-256, deterministic given fixed clock. **Three-tier authority model**: AUTHORITATIVE (qualified window + fresh snapshot + resolved verdicts) / ADVISORY_ONLY (unqualified window or stale snapshot — explicit, never upgraded by elapsed time) / INSUFFICIENT_DATA (missing/unparseable inputs — fail-closed). **Live output today: ADVISORY_ONLY** (window unqualified) — correct behavior. PI-2/PI-6 unlock still gated on a QUALIFIED window; report generator does not bypass it | PI-1 (qualified window via validator), PI-5 | **AMBER** (generator DONE; authoritative output blocked on qualified window) | S–M | Report generator is deterministic; provenance hashes verify; integrates with existing cron |
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
3. PI-2/PI-6 once snapshot history accumulates (≥2 weeks). **PI-1 hourly
   cron ACTIVATED 2026-10-31 (operator-authorized after a passing
   deterministic-only execution audit). Observation window STARTED
   2026-10-31T03:17:01Z. Quality criteria are MACHINE-CHECKABLE:
   `bootstrap/evidence_window_validator.py` (19/19 tests) measures coverage
   ≥90%, schema validity ≥95%, gap discipline ≤6 h, and threshold
   stability — PI-2/PI-6 unlock only on a QUALIFIED verdict, never on
   elapsed time. PI-2/PI-6 remain BLOCKED until then.**
4. ~~PI-4 when a safe disposable drift-injection test is authorized.~~
   **Detector implemented + synthetically validated 2026-10-31**
   (`bootstrap/drift_detector.py`, 29/29 tests after v1.1.0 hardening:
   baseline_id content-hash versioning, null-vs-absent fix, PI-5 bundle
   integration). **Live drift-injection validation remains blocked on
   authorization** and is tracked separately.
5. PI-7 remains RED behind the capacity gate; PI-8 behind PI-2/PI-3.
