# Post-Level-4 Independent Audit + Architecture Decision Gate

**Status:** AUDIT PASS — one follow-up defect recorded, no implementation performed
**Date:** 2026-09-25 · **Auditor:** Hermes CTO (independent re-inspection; prior CTO summary not trusted)

## Audit Scope

Verification of the completed Phase 8 Level 4 state from repository
artifacts only: evidence integrity, defect history, hidden-state and
source-of-truth claims, report authority, failure semantics, resource
governance, security preservation, documentation accuracy, Git/GitHub
record, and an evidence-based next-phase recommendation.

## Starting Git State

- branch `main`, HEAD `7e7d1beb…` == origin/main, working tree clean
- 12 Level 4 commits since ADR-0006 (`7dec488` → `7e7d1be`), CI green at every one (verified via `gh run list`: 6/6 success on main)
- No history rewrites (`git fsck` clean; reflog linear)

## Level 4 Evidence Verification

`docs/15-reproducibility/reports/level4-final-evidence.json` inspected
field-by-field: `final_status PASS`, source_commit `6e5f3a9443…`,
`llm_inference_required 0`, duration 80 s, 20 stages all PASS with
per-stage details (prereqs → source pin + clean tree → manifest →
live-state checks → stale guard → k3s start/ready ~5 s → kubeconfig →
argo install 7.7.11/v2.13.3 → argo ready ~49 s → image import →
app apply → **sync @ revision 6e5f3a9443…** → workload validation →
GitOps teardown → teardown). Mechanism verified in
`bootstrap/reconstruct.sh`: the reported sync revision is read from
Argo's own `status.sync.revision` and equals the report's
`source_commit` because both derive from the same verified HEAD at run
start — not an accidental or stale value.

### Revision semantics (precise wording)

`targetRevision: main` — the Application tracks the **declared branch
tip**, not a SHA pin. The `revision == HEAD` match is genuine in
mechanism (Argo polls origin/main; the runner requires a clean tree
synced with origin before building), and is documented here so it is
never over-read as SHA-level pinning. SHA-pinned reconstruction is a
possible future hardening (Deferred).

## Clean-Path Verification

Every transition in the §4 chain has a corresponding PASS stage with
concrete detail (versions, timings, revision, replica counts, security
flags). Workload validation asserts Git = Argo = Kubernetes on image,
securityContext, resources, probes, and service presence.

## Failure-Test Verification

`level4-failure-tests-evidence.txt` maps to 9 assertions, all script
assertions against **live observed behavior** (observed values are
printed alongside, e.g. `sync=Unknown condition='Failed to load target
state…'`, `health=Progressing`):

| Test | Expected | Observed | Nature |
|---|---|---|---|
| disposable k3s Ready | Ready | 1 node Ready | live assert |
| Argo core ready | 1/1 | 1/1 | live assert |
| B: invalid source path | never Synced | `Unknown` + ComparisonError | live assert |
| recovery B | Synced+Healthy | ~11 s | live assert |
| recovery B workload | 1/1 | 1/1 | live assert |
| C: bad image tag | never Healthy | `Progressing` | live assert |
| recovery C | Synced/Healthy | restored | live assert |
| teardown | container gone | 0 | live assert |
| protected fleet | k3s-server present | 1 | live assert |

Coverage honesty: the suite does **not** assert `degraded_pods` (an
observation only), and does not drive the runner itself to FAIL —
Argo-level behavior is directly evidenced; runner-level FAIL semantics
are established by code inspection (below), not by an executed
runner-failure drill in this suite.

## Defect History Verification

All nine defects confirmed in Git with diffs inspected:

| Defect | Root cause (confirmed) | Fix | Validation | Architectural lesson |
|---|---|---|---|---|
| L4-1 `cd19397` | inherited `KUBECONFIG` targeted production; helm refused (guard worked) | disposable stages pin KUBECONFIG | subsequent run reached Argo install | ambient env is hidden state; pin everything |
| L4-2 `339f077` | `helm` absent from default non-interactive PATH | deterministic PATH + error capture + bootstrap helm check | install succeeded | environment self-sufficiency |
| L4-3 `6c97f6b` | validator sampled non-terminal replica state | bounded readyReplicas wait | 1/1 then validation | assert terminal states |
| L4-4 `fdc8abb` | `"deploy platform-demo"` as single argv → kubectl rc=1 silently mapped to empty cluster | proper argv + rc surfaced | live validator returns real state | argv construction is contract; never substitute defaults on rc≠0 |
| stale state `018c1e3` | leftover disposable container owned name/port → "cannot re-use a name" | pre-start stale guard (runner + suite) | clean starts thereafter | disposable envs must start from nothing |
| L4-5 `575a1cc`+`6e5f3a9` | shell-assembled JSON broke on quotes/commas then newlines → successful run wrote NO report | TSV + python csv escaping; defensive row guard | report written on PASS | serialization boundary owns escaping |
| L4-FT-1 `a9e7afd` | suite cd'ed into `bootstrap/`, wrong relative paths | repo-root resolution + fatal setup abort | suite ran against real inputs | harnesses need env discipline too |
| L4-FT-2 `72fba1f` | transient k3s cert/kubeconfig mismatch at boot; poll asserted node-line, not API success | poll requires successful API round-trip | setup reliable | readiness = working API call, not object presence |
| L4-FT-3 `da7e31d` | compose up raced Docker port release | port-free wait + compose retry | suite passed 9/9 | teardown→create needs settling |

## Hidden-State Audit

- **Eliminated:** ambient `KUBECONFIG` (L4-1; now pinned per stage),
  ambient `PATH` (L4-2; runner exports deterministic PATH), stale
  container/port state (guard).
- **Ambient residue (declared, controlled):** runner still reads
  `KUBECONFIG` from the environment *if set* (production live-state
  stages only — intentional, documented default path exists); Docker
  Desktop VM allocation; host tools (`helm`, `kubectl`, `gh`,
  `python3`, `docker`).
- **External, declared:** github.com (repo + App source, public),
  argo helm repo + ghcr images (chart 7.7.11 version-pinned; the
  upstream repo index itself is not digest-pinned — documented
  limitation), rancher/k3s v1.31.2-k3s1, Docker Hub base images,
  GitHub Actions.
- **Runtime-generated:** disposable kubeconfig/state (no volume, dies
  with teardown), reports (committed deliberately).
- **Operator-provided:** none — public pulls only; no credentials in
  the reconstruction path.
- Correct framing: **declared dependencies, not zero dependencies.**

## Source-of-Truth Audit

Manifest classifications (DETERMINISTIC / DETERMINISTIC_VALIDATION /
EXTERNAL_DEPENDENCY / MANUAL / STATEFUL) are consistent with runner
behavior and documentation. Argo/Kubernetes state: disposable by
construction (no named volume). No category blurring found. Note:
`docs/16-disaster-recovery/` does not exist — Level 4 correctly does
not claim DR.

## Report Generation Audit — FOLLOW-UP DEFECT RECORDED (not fixed here)

`emit_report` python failure is **not** fatal: the runner has no
`set -e`, does not check the emit exit code, and the success path ends
`emit_report "$FINAL_STATUS"` → `exit 0`. Verified live: a poisoned
input/path makes the report writer exit 1 while the runner would still
print `complete: PASS`. Probability is low (L4-5 closed the known
serialization causes; guards added) but the **evidence-authority
inversion** remains: reconstruction could complete without its report.
**Proposed follow-up (implementation, requires authorization):** check
emit_report's exit code; on writer failure emit a minimal
reserved-character-safe report or exit non-zero. Report status today:
**authoritative when present** (machine-generated from live state at
run time), not yet *guaranteed* to exist on every success.

## Failure Semantics Audit

All 15 `stage … FAIL` call sites are terminal (`fail_exit` within
their block; `fail_exit` emits a FAIL report and exits 1) —
infrastructure/Argo/application/validation failures cannot become
PASS. Teardown failure is an explicit FAIL stage. Final status derives
from counters (any FAIL ⇒ FAIL). Resource-gate BLOCKED ⇒ report WARN +
SKIPPED stage (never PASS). No silent failure modes found beyond the
report-writer case above.

## Resource Audit

Gate executed pre-disposable in every run (inputs: free-memory
percentage ≥ 35 and swap < 1600 MB; bypass impossible — BLOCKED skips
disposable stages and reports WARN). Observed across Level 4 runs:
free 73–76%, swap 1032–1355 MB, disposable lifetime ~80 s, production
k3s ~932–975 MiB of 1.5 GiB, swap did not grow. Conclusion unchanged:
**memory remains the binding constraint.**

## Security Audit

`.github/workflows/ci.yml` and `tools/policy/` untouched since Phase 7
(`git diff f1043e3..HEAD` empty). Enforcement gate, scanners, SBOM,
image-reference policy all active. No new secrets (sweep hits were the
project's own detection patterns). Enforcement placement remains
artifact-preserving.

## Documentation / Employer-Review Audit

An external reviewer can determine: project purpose, architecture,
deterministic-first rationale (LLM inference = 0 throughout), why
Level 4 (ADR-0006), why AWS/observability deferred, how reconstruction
works, what failed and how it was corrected (defect tables, preserved
reports), what remains unproven (explicit non-claims), and the
local-vs-CI validation boundary. Minor gaps: roadmap next-phase entry
says "separate future decisions" — updated below to decision-pending
after this audit; evidence index references are valid (0 broken links
repo-wide).

## Git/GitHub Audit

History reads as authentic engineering: feature → defect → diagnosis →
fix → validation → documentation, with test-suite failures preserved
(`a9e7afd` includes the failed first execution). Six consecutive green
main runs verified. No manufactured activity; no history rewriting.

## Current Architecture Maturity (qualitative)

- Containers/K8s/Helm/GitOps: **demonstrated** (deployed + reconstructable to Synced/Healthy)
- CI/CD + security enforcement: **demonstrated** (live gate, blocking path proven in Phase 7)
- Reproducibility: **Level 4 demonstrated** (this audit confirms)
- Resource governance: **demonstrated** (gate + enforcement discipline)
- Failure testing: **demonstrated** (Level 3 injection, Level 4 Argo/app injection + recovery)
- Disaster recovery / state restoration: **not applicable yet** (no project-owned state; no DR docs)
- Observability: **intentionally deferred** (Phase 6 memory evidence)
- Cloud/IaC: **planned, intentionally deferred** (ADR-0006)
- AI architecture: **documented only** (zero inference in platform operations)

## What Level 4 Changed

Before: the platform could rebuild the **Kubernetes layer** in a
disposable environment (Level 3). Now: it can rebuild the
**GitOps-managed application platform from Git** — control plane,
Application reconciliation, workload convergence at the declared
revision, with failure detection and recovery. This is the
"reconstruct the platform from its source of truth" claim, executed.

## Remaining Gaps (evidence-backed)

1. Report-writer failure is non-fatal (above) — smallest real defect.
2. Application tracks `main`, not a SHA (accepted semantics; SHA-pin
   would tighten reconstruction determinism).
3. No scheduled/continuous reconstruction validation (Level 6
   direction; currently evidence exists only for run-time executions).
4. Security debt (65 persistent findings, all fix-listed) is monitored
   but its lifecycle is exercised only when base images change.
5. No project-owned state ⇒ DR remains an empty abstraction (honest).

## Next-Phase Candidates (qualitative)

| Candidate | Builds on | Adds | New complexity | Risk | What it proves |
|---|---|---|---|---|---|
| A. AWS/IaC | reconstruction contract | second infra implementation | credentials, state mgmt, cost, drift | high | cloud parity (not yet needed) |
| B. Observability | Phase 6 evidence | operational signals | resident memory vs 1.5 GiB envelope | medium | nothing currently demanded by failures |
| C. Dependency automation | enforcement + disposable env | safer base-image churn lifecycle | bot config, PR flow | low-medium | policy exercised against real churn |
| D. Deeper DR | — | state restoration | **no state exists** | — | empty abstraction today |
| E. Continuous reproducibility | runner + gate + reports | scheduled validation, drift detection, evidence retention | scheduler, retention policy | low | Level 6-style verified reconstruction over time |
| F. AI maintenance | deterministic workflows | reasoning in the loop | provider/resource/safety | — | no concrete demonstrated need yet |

## Recommended Next Move

**Close the report-authority gap, then adopt Candidate E (Continuous
Reproducibility Validation) as the next architectural phase.**
Reasoning: the current architecture's weakest evidenced point is that
reconstruction correctness is proven *episodically* (only when a human
runs it); the runner, gate, reports, and teardown machinery already
exist, so scheduled disposable validation with report retention and
drift comparison is the smallest implementation that converts Level 4
from a demonstrated capability into an *operating* one — advancing
toward the maturity model's "periodically verified reconstruction"
without new technologies, credentials, or resident memory pressure
(ephemeral, resource-gated, runs only when the gate passes).
Dependency automation (C) becomes materially safer *after* E exists
(churn is then validated by scheduled reconstruction automatically);
AWS (A) remains premature until local reconstruction is routinely
verified. Precondition for E: fix the report-authority defect first so
automated evidence can be trusted unattended.

## Deferred / Follow-Up

- Report-writer exit-code enforcement (proposed, needs authorization)
- Optional SHA-pinned reconstruction mode
- `degraded_pods` assertion in the failure suite
- ADR-0006 addendum: recorded as adequate in existing completion
  records; no redundant volume added

## Final State

- Starting HEAD `7e7d1beb` → ending HEAD: docs commit below (see final report)
- Infrastructure changes: **0** · resident services added: **0** · cloud changes: **0** · LLM inference: **0**
- Protected fleet untouched; no disposable environment created during this audit
- **NEXT PHASE = DECISION ONLY — IMPLEMENTATION NOT AUTHORIZED — HARD STOP**
