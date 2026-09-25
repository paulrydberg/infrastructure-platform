# Phase 7C Post-Enforcement Validation & Next-Phase Decision Analysis

**Status: validation complete. Enforcement remains ACTIVE. One concrete
CI-integration defect was discovered and fixed by this validation
(`f1043e3`). Next-phase decision recorded at the end — nothing
implemented.**

## 1. Starting state

`578cbc4` == origin/main · branch main · tree clean · CI green.
Enforcement live since `eb451e2`, validated run 36074112719.

## 2. Enforcement audit (from source, not summaries)

Verified in-repo: `ci.yml` gate step (end of build job, after uploads);
evaluator `tools/policy/shadow_evaluator.py` (policy 7c-policy-1.0.0,
evaluator 7c-shadow-1.1.0, schema 2); activation record
`phase7c-enforcement-activation.md`; README/matrix/roadmap/project.json
all state scanning/evaluation/**enforcement** ACTIVE with shadow
rollback. No contradictions found.

## 3. Clean-path validation (real run 36074112719, from artifact)

commit `eb451e2` · image platform-demo:0.1.0 · scanner 0.70.0 ·
schema_validated true · verdict **WARN**: 65 findings / 65 persistent /
0 critical / 0 unknown / R1 PASS / R2 WARN / R3 PASS / R4 PASS · gate
step **success** · all 3 artifacts present and unexpired.

**Distinction made explicit:** CI PASS ≠ zero vulnerabilities. The
policy deliberately keeps non-blocking persistent findings at WARN —
the gate blocks only CRITICAL-with-fix (unexcepted), R4 violations,
expired exceptions, and UNKNOWN evidence.

## 4. Blocking-path validation at the workflow level (PROVEN)

Mechanism: isolated branch + PR (no main contamination, no real
vulnerability — a deterministic R4 violation via
`values.yaml readOnlyRootFilesystem: false` on branch
`test/policy-block-validation`, PR #3, never to be merged).

- **Run 36075765997: CI FAILURE.** Gate read `WOULD_FAIL` → exited
  non-zero; build job failed; R4 correctly identified the violation.
- **Defect discovered (authentic evidence, preserved):** the gate sat
  BEFORE the artifact-upload steps → on the blocking run, all three
  artifact steps were SKIPPED. The invariant «policy failure MUST NOT
  destroy security evidence» was violated at workflow level.
- **Fix `f1043e3`:** relocated the enforcement-decision step to the end
  of the build job (16/16 lines, pure relocation, zero semantic
  change). Main CI re-validated green (run 36076172841).
- **Re-test run 36076508779 (PR #3 with fixed ordering): CI FAILURE
  with full evidence preservation** — uploads all `success`, then gate
  `failure`. Verdict artifact downloaded from the FAILED run:
  WOULD_FAIL / R4 WOULD_FAIL / `ctr_readOnlyRootFilesystem: false` —
  exactly the injected violation.

## 5–6. Clean path & evidence preservation

Clean path re-proven on main (run 36076172841: scan → evaluate →
upload → enforcement → green). Evidence-preservation invariant now
proven on BOTH paths: green run (artifacts present) and blocking run
(artifacts present before gate failure).

## 7. Operational semantics

Already documented in `tools/policy/README.md` + activation + hardening
records: blocking definition, WARN/UNKNOWN meaning, exception lifecycle
(schema, 90-day proposed expiry, EXPIRED → reactivates rule), rollback
(delete gate step), artifact locations, failed-gate investigation
(verdict artifact `rules` + `summary`). No additions required.

## 8. Security-control inventory (Phase 7 closeout)

| Control | Implementation | Behavior | Evidence | Status |
|---|---|---|---|---|
| Trivy vulnerability scan | pinned action@SHA + v0.70.0 | evidence | security-evidence artifact | implemented, verified |
| Trivy config scan (kubeconform-adjacent) | pinned | evidence | trivy-config-report | implemented, verified |
| Gitleaks | pinned v8.30.1 + checksum, evidence mode | evidence | gitleaks-report | implemented, verified |
| SPDX SBOM | syft-generated from built image | evidence | sbom artifact | implemented, verified |
| Image-reference policy | deterministic CI check | blocking (pre-existing validate job) | job step | implemented, verified |
| Policy evaluator | stdlib-only, JSON-only input, schema-validated | verdict artifact | shadow-policy-verdict | implemented, verified |
| Enforcement | gate step, artifact-preserving | blocking (CRIT+fix/R4/expired-exc/UNKNOWN) | gate step + run history | implemented, **workflow-verified both paths** |
| Exception handling | Git-tracked ledger schema | blocking on expiry/malformed | tests + empty ledger | implemented (fixture-verified; no real exception ever exercised) |
| Provenance | run/commit/image/scanner/versions in every verdict | metadata | verdict artifact | implemented, verified |
| Artifact retention | 90d verdict / 30d evidence / 7d manifest | — | artifacts API | implemented, verified |

**Known debt (classification, not remediation backlog):** all 65
current findings are fix-listed pairs (0 no-fix): libcrypto3/libssl3 50
pairs (25 unique × 2 pkgs), libuuid 8, pip 6, xz-libs 1. Classes: **fix
requires base-image refresh** (openssl/busybox-family — next natural
base cycle, evidence-gated); **upstream/python-image cadence** (pip —
fixed by periodic base refresh, not urgent); **policy disposition**
(remaining MEDIUM/LOW — intentionally WARN-only). No no-fix population;
no compensating-control dependencies active.

## 10–13. Next-phase decision analysis (factual, not scored)

**Candidate A — Observability (Prometheus/Grafana/…):** prerequisites
(metrics-server) validated in Tier A, but Tier A itself demonstrated
swap pressure from a 16–20 Mi workload and was rolled back. A resident
Prometheus stack (~250–400+ Mi) materially conflicts with the binding
constraint (memory) and the protected-fleet envelope. High operational
cost, low reproducibility value. *Premature on this host.*

**Candidate B — Reproducibility/DR:** current level 2 demonstrated
(source → bootstrap → runtime → k3s → Helm → workload). Gaps assessed
from evidence: reconstruction manifest is a documented placeholder
("not yet built — entries per phase"); host assumptions (Docker Desktop
allocation, k3s envelope) are documented but not machine-validated;
GitHub configuration (branch protection) is live state outside Git;
persistent data/credentials are out-of-contract by design. Highest
alignment with the north star («the machine is disposable») and zero
memory cost. Validates and hardens everything already built.

**Candidate C — AWS/IaC:** large scope, real billing exposure, and it
inherits every unreconstructed local gap — cloud reconstruction of a
platform whose local reconstruction manifest is still a placeholder
amplifies drift instead of reducing it.

**Candidate D — Dependency automation (Renovate/WUD):** genuine value
but wrong sequencing: automation without the enforcement/exception
lifecycle being exercised against real update churn would generate
noise; also WUD is a resident service (memory constraint).

**Candidate E — other:** Phase 7 closeout artifacts are done; nothing
else shows higher leverage than B.

**Reproducibility-vs-cloud question answered:** evidence supports
strengthening reproducibility BEFORE cloud expansion — the Level 2→3
step (manifest instantiation + automated reconstruction validation) is
memory-free, CI-hostable, and directly deepens the project's core
claim.

**NEXT PHASE JUSTIFIED: Candidate B — Reproducibility / Disaster
Recovery (Level 2 → 3: instantiate the reconstruction manifest and add
automated reconstruction validation).** This is a decision analysis,
NOT authorization to begin.

## Resource observations

All validation ran on GitHub-hosted CI. Mac Mini/Kubernetes/Docker
impact 0. LLM inference 0.

## Final state

HEAD `f1043e3` == origin/main · tree clean · CI green (main run
36076172841) · enforcement ACTIVE with artifact-preserving ordering ·
PR #3 preserved open as authentic blocking-path evidence (never
merged) · branch `test/policy-block-validation` preserved.
