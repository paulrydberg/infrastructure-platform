# Roadmap & Architecture Diagnostic — Post-Level-4 (2026-09-25)

**Status:** diagnostic complete; next phase DECIDED-BY-EVIDENCE, not implemented
**Trigger:** report-authority defect (L4-6, audit-discovered) remediated in
`aa4a6ac`; roadmap re-evaluated against the demonstrated system rather than the
original phase ordering.

## Current State

HEAD `aa4a6ac` == origin/main, clean, CI green (run @ `aa4a6ac3`).
Phase 8 Level 4 = PASS, independently audited. Report authority enforced
(11/11 deterministic tests + live poisoned-report regression: runner exits 1
with `evidence_authority FAIL`). Protected fleet untouched; LLM inference 0.

## Level 4 Audit Status

Verified in `docs/history/post-level4-audit.md`: clean-path evidence genuine
(20/20, sync revision == verified HEAD), 9/9 failure tests mapped, 9 defects
confirmed with fixes, hidden-state elimination confirmed (declared
dependencies, not zero dependencies), all 15 runner FAIL sites terminal,
security tree untouched since `f1043e3`.

## Report Authority Defect & Resolution

**Defect (audit):** report-writer exit code unchecked → reconstruction could
print success with missing evidence. **Root cause:** no `set -e`; `emit_report`
rc discarded on both success and gate-blocked paths.
**Resolution (`aa4a6ac`):** `report_validate()` (exists/non-empty, valid JSON,
`final_status` matches verdict, non-empty stages); success/WARN paths require
generated+validated evidence or record `evidence_authority FAIL` and exit 1;
`fail_exit` states evidence-generation failure explicitly; resource-gate WARN
path held to the same standard. Invariant now documented: *a reconstruction
cannot be considered successful unless its evidence artifact is successfully
generated, validated, and preserved* — evidence OF reconstruction is part of
the reconstruction contract. Remaining limitation: preservation beyond the
local repo (off-host retention) is a future concern, not a defect.

## Roadmap Reconstruction (phases ≠ maturity levels)

The master-spec phase numbers (0–19) and the reproducibility maturity model
(Levels 0–7) are **independent numbering systems** that happen to share
integers (roadmap Phase 8 = AWS; maturity Level 4 = GitOps-layer
reconstruction). They must never be conflated. Current true status:

| Roadmap phase | Status (evidence-based) |
|---|---|
| 0 Discovery | DEMONSTRATED |
| 1 Container foundation | DEMONSTRATED |
| 2 Kubernetes | DEMONSTRATED (k3s, 1.5 GiB envelope, Level 2 reconstruction) |
| 3 Helm | DEMONSTRATED (full lifecycle) |
| 4 CI/CD | DEMONSTRATED (failure-mode tested) |
| 5 GitOps | DEMONSTRATED (drift self-heal; Level 4 rebuild) |
| 6 Observability | PARTIAL — capacity analysis + gate principles done; nothing installed; INTENTIONALLY DEFERRED |
| 7 Security | DEMONSTRATED — actually over-delivered (enforcement live; roadmap said "not started") |
| 8 AWS | PLANNED / INTENTIONALLY DEFERRED (ADR-0006) |
| 9 Local-to-cloud promotion | PLANNED (blocked by 8) |
| 10 Dependency automation | PLANNED (newly safer post-Level-4) |
| 11–14 AI phases | PLANNED / PREMATURE (see below) |
| 15 Policy engine | DEMONSTRATED (Phase 7 evaluator exceeded the original concept) |
| 16 Platform engineering (Backstage) | PLANNED, low current value |
| 17 Reproducibility | DEMONSTRATED through Level 4 (roadmap said "not started") |
| 18 Continuous reconstruction | PLANNED — the audit-recommended next phase |
| 19 Final architecture | ongoing synthesis, not a phase |

Maturity model status: Levels 0–4 DEMONSTRATED; Level 5 (tested DR) NOT
APPLICABLE YET (no project-owned state); Level 6 (periodic verification) =
next; Level 7 (continuous validation) after 6.

## Current Capability Map (all evidence-backed)

| Capability | State | Evidence | Known limitation |
|---|---|---|---|
| Source control / GitOps SOT | Demonstrated | repo + Argo reconciliation | branch-tip, not SHA pin |
| Container build/deploy | Demonstrated | v0.1.0, CI-built | no registry publication |
| Kubernetes (k3s) | Demonstrated | Phase 2 + live-state checks | single node |
| Helm | Demonstrated | Phase 3 lifecycle | no chart publication |
| CI/CD | Demonstrated | Phase 4 + failure PRs | no deploy job |
| GitOps | Demonstrated | Phase 5A + Level 4 | single app |
| Security scanning/SBOM | Demonstrated | Phase 7, live enforcement | 65 persistent WARN findings (all fix-listed) |
| Policy enforcement | Demonstrated | blocking path workflow-proven | exception lifecycle fixture-tested only |
| Reproducibility | Level 4 demonstrated | Level 3+4 records, evidence-authority enforced | episodic, not scheduled |
| Failure injection/recovery | Demonstrated | L3 runner + L4 suite | degraded-pod assertion missing |
| Resource gating | Demonstrated | gate before every disposable run | local-only signal |
| Evidence/reporting | Demonstrated + now authoritative | L4-6 fix, 11/11 tests | local retention only |
| Observability | Analysis only | Phase 6 | nothing installed (deliberate) |
| Cloud/IaC | Not implemented | — | no account |
| Dependency automation | Not implemented | — | — |
| Disaster recovery | Not applicable yet | no project-owned state | — |
| AI | Documented only | architecture layer | 0 inference in operations |

## Architecture Center of Gravity

The project has become a **deterministic, resource-gated, evidence-driven
platform-reconstruction system**: GitOps-managed Kubernetes whose defining
loop is *declare → validate → enforce → reconstruct → prove → preserve
evidence*. Not "a Kubernetes cluster with CI" — the reconstruction and
evidence machinery is the product. Central thesis: *the machine is disposable;
the source of truth is persistent; success without evidence is failure.*

## Current Bottleneck

Memory remains the binding local constraint (1.5 GiB envelope, k3s ~1 GiB,
Phase 6 + Phase 8 gate data), but it is now **managed**, not blocking.
The actual next-stage bottleneck is **temporal, not spatial**: reconstruction
correctness is proven only when a human runs it. No scheduled validation, no
evidence retention over time, no drift comparison between runs.

## Candidate Analysis

- **Level 5 (tested DR):** NO project-owned persistent state exists; inventing
  state to justify DR is prohibited. Keep deferred.
- **Level 6 (periodic verification) / continuous reproducibility:** strongest
  candidate — reuses the entire runner/gate/report machinery; converts a
  demonstrated capability into an operating one; smallest new complexity.
- **Level 7 (continuous validation):** after 6 proves the scheduled model.
- **Dependency automation:** newly much safer (disposable reconstruction can
  validate every dependency PR end-to-end), but its safe test loop *is*
  scheduled reconstruction — sequencing it after Level 6 avoids building
  automation on episodic validation.
- **AWS/IaC:** adds a second infrastructure implementation while local one is
  proven but not routinely verified; credentials/state/cost burden; roadmap
  ordering rejected by ADR-0006 and re-rejected here. Premature.
- **Observability:** no unresolved operational problem the deterministic
  evidence cannot diagnose (every Level 4 defect was root-caused without it).
  Ephemerally possible later; resident unjustified. Deferred.
- **AI maintenance:** deterministic limits not yet reached; no concrete first
  workflow with demonstrated need; queued/event-driven remains the correct
  future shape. Premature.

## Dependency Graph (verified against repo)

reproducibility (L4 done) → periodic verification (L6) → evidence retention +
drift comparison → dependency automation (validated by scheduled
reconstruction) → optional AI-assisted maintenance. GitOps (done) →
local/cloud abstraction → AWS/IaC when justified. Enforcement (done) →
automated maintenance gates. Resource gate (done) → any scheduled/disposable
work.

## Premature capabilities (evidence-based)

AI phases 11–14 (no deterministic ceiling reached; no incident corpus);
incident-response AI (no observability, no incidents); AWS before routine
local verification; DR before state; resident observability (memory envelope).

## Newly justified by Level 4

Periodic reconstruction; evidence retention/drift comparison; dependency
automation (as the workflow AFTER scheduled validation exists); local-to-cloud
promotion (design-wise, once 6 is operating).

## Qualitative Decision Matrix

| Candidate | Problem solved | Existing evidence | New complexity | Resource impact | What it proves |
|---|---|---|---|---|---|
| L4-6 fix (DONE) | evidence authority | runner + 11 tests | minimal | none | success ⇒ evidence exists |
| Level 6 periodic reproducibility | episodic-only validation | full runner machinery | scheduler + retention + drift compare | gated, ephemeral | reconstruction works *over time*, not just once |
| Level 5 DR | state loss | none (no state) | — | — | empty abstraction |
| Level 7 continuous | still event-driven validation | needs L6 first | higher | higher | continuously validated |
| Dependency automation | manual churn risk | enforcement + disposable env | bot/PR flow | low | self-maintaining security posture |
| AWS/IaC | cloud gap | reconstruction contract | credentials/state/cost | high | portability (not currently required) |
| Observability | blind spots | Phase 6 analysis | resident memory | conflicts with envelope | nothing currently blocked by its absence |
| AI maintenance | deterministic limits | none reached | provider/safety | — | — |

## Recommended Sequence

```
Current (report authority FIXED)
   ↓  NEXT AUTHORIZATION
Phase A — Level 6 Periodic Reproducibility Validation
   (scheduled resource-gated disposable reconstruction; evidence retention;
    report-to-report drift comparison; failure = visible, never silent)
   ↓  LATER
Phase B — Dependency automation
   (churn PRs validated end-to-end by Phase A machinery before merge)
   ↓  LATER
Phase C — Evidence-based AWS/IaC decision
   (only after A+B are operating; destroyable, budget-capped scope)
   ↓  EVENT-DRIVEN
Observability (ephemeral, on demonstrated need) / AI (on deterministic limits)
```

## Next Authorization Boundary (draft)

- **Objective:** advance reproducibility from Level 4 (demonstrated) to
  Level 6 (periodically verified) via a scheduled, resource-gated disposable
  reconstruction with evidence retention and drift comparison.
- **Why now:** only remaining gap in the core thesis loop is *time*; machinery
  already exists; no new technologies.
- **Reused:** reconstruct.sh (evidence-authority enforced), resource gate,
  report schema, failure-test suite, Argo values/Application.
- **Permitted:** scheduling mechanism (launchd — no new resident daemon),
  retention policy, drift-comparison tooling (deterministic), drift report.
- **Forbidden:** continuous runners, resident monitoring, cloud, AI, new
  services, Docker resize, enforcement changes.
- **Resource budget:** gate unchanged (BLOCKED ⇒ skipped + recorded run;
  scheduled run must never force the gate).
- **Evidence requirements:** every scheduled run leaves a valid report
  (enforced by L4-6 gate); drift report committed or retained per policy;
  failed scheduled runs visible (notification), never auto-remediated.
- **Failure tests:** scheduled run under gate-BLOCKED conditions; stale state;
  report-corruption between runs.
- **Success criteria:** N consecutive scheduled runs with valid evidence;
  drift detection demonstrated on an injected difference; zero protected-fleet
  mutations; LLM 0.
- **Rollback:** remove schedule; machinery unchanged.
- **Hard stop:** no Level 7 automation, no dependency automation, no AWS.

## Long-Term Direction

Capability-oriented: *prove reconstruction → operationalize verification →
automate maintenance on verified foundations → extend to cloud only when the
abstraction is routine → add reasoning only where determinism ends.*

## Known Unknowns

Scheduled-run resource interactions over weeks (swap growth?); long-term
report retention volume; Argo chart-index drift over months; multi-app GitOps
scale (untested, single app only).

## Employer/Interview View

Strongest demonstrated arcs: evidence-authority invariant (audit found the
inversion, minimal fix, tests, live regression); Level 4 GitOps rebuild with
nine root-caused defects; resource-gated disposable methodology; honest
"declared vs hidden" dependency framing; evidence-based roadmap rejection of
its own AWS ordering. The most natural next capability extends the proven
loop (scheduled verification) rather than adding a technology.

## Roadmap / ADR synchronization

- Roadmap: Phase 7/15/17 marked complete (over-delivered vs original notes),
  next authorization = Level 6 periodic validation (decision recorded, not
  implemented), AI/DR/AWS explicitly deferred with reasons.
- ADR-0007 records this re-sequencing decision (decision only).

## Hard Stop

Report-authority fix implemented, tested, documented, committed, CI-validated.
Roadmap diagnostic complete. **No further phase implemented. No cloud. No new
services. No AI. No Level 5/7. Protected fleet untouched. LLM inference = 0.**
