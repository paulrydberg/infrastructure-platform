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
| PI-1 | **Platform-state snapshot collector** | One deterministic script emitting a schema-validated JSON snapshot (host free/swap, Docker VM, k3s RSS+pod set, Argo health, gate status) with provenance (timestamp, tool versions) | Does not exist; inputs measured ad-hoc per session | none (all read-only) | **GREEN** | S | `platform-state schema` validation passes; 2 consecutive runs byte-differ only in timestamps/values; no side effects (read-only probes) |
| PI-2 | **Capacity-forecast model (deterministic)** | Linear/exponential fit over PI-1 snapshot history → free-space and k3s-RSS trend with confidence band; explicit insufficient-data verdict | Evidence exists (19 validation records, daily health) but no model | PI-1 (≥ 2 weeks of snapshots) | **AMBER** (needs snapshot history) | M | Model emits forecast + interval; refuses (INSUFFICIENT_DATA) below threshold; back-test against recorded 2026-10 oscillation reproduces documented 13–36 GiB band |
| PI-3 | **Deployment-readiness evaluator** | Deterministic pre-deploy check consuming PI-1 + policy thresholds (free-mem gate, disk gate, k3s cap margin) → READY/NOT_READY with per-criterion evidence | Logic exists scattered in `bootstrap.sh`/`reconstruct.sh` gates; not reusable standalone | PI-1 | **GREEN** | M | Evaluates current host honestly as NOT_READY (capacity); unit tests cover each criterion's pass/fail branches; reuses gate thresholds from `bootstrap.sh` (import or pinned copy + drift test) |
| PI-4 | **Drift detector (state vs declared)** | Compare live k3s/Argo resources + compose services against Git-declared manifests → DRIFT/CONVERGED evidence record | Argo self-heal already proves the GitOps direction; no standalone detector | PI-1; argo CLI read-only | **AMBER** | M | Detects an injected (test-namespace) drift in a disposable check; zero mutations to protected fleet; evidence record schema-valid |
| PI-5 | **Incident-evidence bundle builder** | One command collecting timestamped, checksummed evidence (logs, docker inspect, k3s events, gate records) into a manifest'd bundle | Partial precedents (validation records, health reports); no bundler | PI-1 | **GREEN** | M | Bundle is reproducible (same inputs → same manifest hashes modulo volatile fields); includes provenance + redaction check (no secrets patterns) |
| PI-6 | **Automated reporting with provenance** | Health/roadmap reports that embed PI-1 evidence + SHA-256 provenance instead of prose-only claims | Daily health check exists (cron, prose); budget report stale (known blocked task) | PI-1, PI-5 | **AMBER** | S–M | Report generator is deterministic; provenance hashes verify; integrates with existing cron |
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
2. PI-5 (evidence bundles) next — reuses PI-1.
3. PI-2/PI-6 once snapshot history accumulates (≥2 weeks).
4. PI-4 when a safe disposable drift-injection test is authorized.
5. PI-7 remains RED behind the capacity gate; PI-8 behind PI-2/PI-3.
