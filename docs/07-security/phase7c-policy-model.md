# Phase 7C Policy Model & Historical Simulation (extended) — NOT enforcement

**Status: DESIGN/SIMULATION ARTIFACT.** Extends
`phase7c-policy-simulation.md` (R1–R5 rules selected there remain the
recommendation). This record adds the full policy model dimensions
(fix-availability, age, exceptions, compensating controls, reachability),
the four candidate policy families, the three-state historical matrix,
the exception model/expiry analysis, no-fix and new-CVE handling,
base-image interaction, false-positive lifecycle, shadow-mode design, and
boundary analyses. **CI remains evidence mode; nothing here is wired in.**

## 1. Policy model dimensions

### Severity × fix availability
| | fix listed | no fix listed | unknown |
|---|---|---|---|
| CRITICAL | fail (actionable) | warn + exception required | warn + investigate |
| HIGH | age-dependent fail/warn | warn + tracked monitor | warn + investigate |
| MEDIUM | report | report | report |
| LOW | report | report | report |

"Fix availability unknown" occurs when the Fixed Version cell is empty but
the Status column is inconclusive (merged-cell parsing) — a JSON-based
evaluator must distinguish `FixedVersion: ""` (no fix) from field absence
(parse limitation). This distinction is currently UNKNOWN for our data and
is a mandatory implementation prerequisite.

### Age (candidates analyzed, none selected)
7 / 14 / 30 / 60 / 90 days. **Evidence limitation [U]:** the table scan
artifacts contain no per-finding disclosure dates; the age dimension was
simulated qualitatively (7A findings = aged at scan time; 7B findings =
newly surfaced by the base bump). Honest age gating requires Trivy JSON
(`PublishedDate`) — implementation prerequisite. Observed interaction with
the base bump: every 7B HIGH is "new" under any threshold, so age-based
failing alone would never have fired on the current inventory — age rules
only become meaningful once a finding *persists* across scans (which is
exactly rule R2's persistence design, requiring no dates).

### Exception state
`NO_EXCEPTION` → fail/warn per rule · `ACTIVE_EXCEPTION` → rule suppressed
for that finding id · `EXPIRED_EXCEPTION` → treated exactly as
`NO_EXCEPTION` (fail/warn reactivates) **and** additionally surfaces an
"exception expired" warning so reactivation is never silent.

### Compensating controls
Documented per-finding in exceptions/debt register: `runAsNonRoot`
(pod+container), `readOnlyRootFilesystem`, `seccompProfile=RuntimeDefault`,
`allowPrivilegeEscalation=false`, resource limits, loopback-only exposure.
**Explicit rule: a compensating control produces a documented risk
disposition; it never converts a finding into "no vulnerability."** (The
register's wording already enforces this.)

### Exposure / reachability
Where evidence exists: openssl libs = runtime-present but the app does not
terminate TLS (loopback HTTP) → indirectly included, exposure limited
[observed]; util-linux mount/nsenter tooling = tooling dependency, SUID
paths unreachable from the non-root Python process [reasoned from image
config; exploitability UNKNOWN]; pip = build-time dependency (app installs
nothing at runtime). Where evidence does not establish reachability, the
model records UNKNOWN and does not infer.

## 2. Candidate policy families — historical simulation

States (all [M], extracted from artifacts, not prose):
- **S1 — 7A baseline** (alpine3.20): CRIT 2 pairs (1 unique CVE, fix listed)
  · HIGH 16 pairs = 8 fix-listed pairs / 8 no-fix pairs
- **S2 — post-base-remediation** (alpine3.22 scan): CRIT 0 · HIGH 10 pairs
  = 7 fix / 3 no-fix (inventory *newly surfaced* by the base bump)
- **S3 — current** (same artifact as S2; the eighth unique HIGH is
  explicitly identified: the 8 unique HIGH CVEs are 14456, 45447, 53612,
  53613, 53614, 76642, 78408, 78410 — 5 fix-listed unique / 3 no-fix
  unique; 7 fix-listed pairs because 14456 and 45447 each affect
  libcrypto3+libssl3)

| State | CRIT | HIGH pairs (fix/no-fix) | Policy A | Policy B | Policy C (age) | Policy D (age+exceptions) |
|---|---|---|---|---|---|---|
| 7A baseline | 2 | 8 / 8 | **FAIL** (18 blocking) | **FAIL** (2 actionable; 16 warn) | **FAIL** (8 actionable; 8 warn) | **FAIL** + 8 exceptions |
| post-base remediation | 0 | 7 / 3 | **FAIL** (10 blocking — false regression signal) | WARN (0 fail; 10 warn) | WARN (7 new HIGHs below any 7–90d threshold; 3 warn) | WARN + 3 exceptions |
| current | 0 | 7 / 3 | **FAIL** (10 blocking) | WARN (10 warn) | WARN | WARN + 3 exceptions |

Consequence accounting (not "better/worse"):
- **A:** catches both historical Criticals; but fails CI at every state
  including today — 10 permanent failures, all noise after remediation.
- **B:** catches the historical Criticals (both had fixes); never blocks on
  no-fix debt; 0 failures today; 10 warnings; no exception machinery
  needed yet — but a fix-listed HIGH could sit unaddressed forever.
- **C:** adds aging — at S2/S3 nothing fails (all HIGHs newly surfaced at
  any 7/14/30/60/90-day threshold); failures emerge only when findings
  persist past the threshold; requires date-carrying scan output.
- **D:** adds tracked exceptions — at S1 the 8 no-fix HIGHs would each need
  an exception; at S2/S3 only 3; makes the exception ledger the honest
  measure of accepted debt; highest metadata burden.

**Key discriminator the matrix demonstrates:** only A/B/C-D caught the 7A
Criticals; only C/D avoided reading the 7B advisory-churn as a project
regression; only D gives the no-fix population a bounded, auditable home.

## 3. Exception model (design; no real exceptions created)

Smallest useful Git-tracked schema:

```yaml
exceptions:
  - id: CVE-2026-53613          # what is excepted (CVE id; pair-level optional)
    scope: image                 # image | config | manifest path
    reason: "No upstream fix available in util-linux 2.41.x"
    owner: paul                  # accountable human
    created: "2026-09-24"
    expires: "2026-12-23"        # mandatory — no open-ended exceptions
    evidence: "trivy run 36033387702; security-debt-register.md §4"
    compensating_controls: [runAsNonRoot, readOnlyRootFilesystem, seccompRuntimeDefault]
    review_required: true        # re-authorization before expiry renewal
```

Answers required by the task: what (id+scope) · why (reason+evidence) ·
who (owner) · when (created/expires) · expiry behavior (EXPIRED_EXCEPTION
reactivates the rule + raises an "expired" warning; renewal requires
review_required=true sign-off).

## 4. Exception expiration analysis (candidates, no selection)

30 / 60 / 90 days simulated against project cadence:
- base-image refresh cadence observed: ~1 per security phase (7B bumped
  alpine minor); 30d would expire mid-cycle and churn the ledger;
- upstream advisory timing: util-linux no-fix CVEs have no predictable
  fix date — any duration is arbitrary for them, so the expiry's real
  function is **forced re-review**, not predicted remediation;
- false positives: bounded by the FP lifecycle (§6), not by expiry;
- operational burden: 90d = ~4 ledger touches/year per exception at
  current exception counts (≤3) — low.

**Proposed default for later authorization: 90 days, review_required=true,
renewal requires a fresh evidence citation.** Rationale: aligns with the
observed base-refresh cadence, keeps the ledger honest without churn.
Final choice is Paul's.

## 5. No-fix HIGH handling (design)

`WARN + tracked monitor entry in the debt register + (if it would
otherwise fail) an ACTIVE_EXCEPTION with expiry + periodic review`. Never
an automatic endless failure; never silent. The distinction recorded: no
fix available ≠ harmless (53613/53614 are SUID-mount TOCTOU issues) ≠
immediately blocking (unremediable in-image; blocking only burns green).
The debt register already carries all three with compensating controls.

## 6. Newly disclosed CVE handling

Scenario: existing image, new advisory appears, no project change. The
policy model attributes the finding to **advisory inventory change**, not
project regression — determined by comparing the scan against the
previous run's finding list (R2's persistence artifact): a finding absent
from the previous scan = *newly disclosed* → enters via warn + debt
register review; a finding persisting past its age/persistence limit =
*neglected* → escalates to fail. This is the mechanism that prevents the
7B pattern (52→59 total with CRIT 2→0) from ever being misread as a
regression — the simulation shows raw-count Policy A would have made
exactly that error.

## 7. Base-image refresh interaction

Desired future workflow: new base → build → scan → **differential
comparison vs previous scan** → classify (introduced / eliminated /
severity-changed / fix-availability-changed) → policy evaluation → SBOM →
CI. The policy should consider previous scan, current scan, introduced
findings, eliminated findings, severity changes, and fix-availability
changes. Differential scanning does **not exist yet** — it depends on the
same previous-run artifact as R2 and is listed as an implementation
prerequisite, not implemented here.

## 8. False-positive lifecycle (deterministic)

detected → evidence gathered → experimental validation (the KSV-0118
precedent: suspicion tested by controlled experiment and **rejected** —
the finding was real) → documented disposition → exception only if the
evidence supports it → expiry + review. No permanent "false positive"
exemptions without recorded evidence; the scanner config must not be
edited to hide findings (no .trivyignore exists today).

## 9. Shadow mode design (not implemented)

Lifecycle: policy defined → historical simulation (done) → **shadow mode**
→ observe ≥2 real CI cycles → measure noise → tune → explicit
authorization → enforcement.

Shadow verdicts recorded per run as a CI artifact:
`{verdict: would-pass|would-warn|would-fail|would-exception, finding_id,
policy_rule, reason, timestamp, commit, scan_artifact_ref, exception_state}`.
Metrics that matter: would-fail count per cycle, warning volume,
exception count, FP rate after triage. Unacceptable policy noise
(pre-declared): any would-fail on a no-fix finding; >5 warnings/cycle on
a static codebase; any exception churn without an underlying inventory
change. If a simulation script is created, it stays out of the CI gate
path — none was added to CI in this task.

## 10. Resource & operational cost

Zero Mac Mini runtime footprint — everything runs in existing
GitHub-hosted CI. Estimated adds: JSON output step (~seconds), previous-run
artifact storage (~tens of KB/cycle, 30-day retention), evaluator script
execution (<5 s), no resident services, maintenance = exception ledger
reviews (~quarterly at proposed expiry).

## 11. AI boundary

**LLM inference = 0** in detection, threshold evaluation, exception
validity, or deployment permission — all deterministic, Git-tracked. AI
may later *explain* findings or draft migration plans; it never decides.

## 12. Kyverno boundary (future, not installed)

| Control | CI | Admission | Basis |
|---|---|---|---|
| vuln scanning thresholds | yes | no | scanner lives in CI; admission cannot scan |
| `:latest` prohibition | yes | possible | already deterministic in CI; admission = defense-in-depth later |
| digest requirement | yes (future) | possible | requires registry (deferred) |
| runAsNonRoot / seccomp / resources | yes (chart-level today) | yes | pod-level SC now set; admission covers non-chart workloads |
| approved registry | yes (future) | yes | requires registry decision |
| SBOM presence | yes | possibly | SBOM is a CI artifact |
| signature verification | yes (future) | eventually | requires signing (deferred) |

Evaluated per our architecture: single demo app, chart-rendered, one
cluster — admission adds value only when non-chart or third-party
workloads arrive.

## 13. Registry boundary (future, not introduced)

Publish when a real GitOps deployment consumes images from a non-build
host, or at the AWS/EKS phase — whichever comes first. GHCR = lowest
friction (built-in token); ECR = natural at AWS phase; local-only artifacts
= today's state, config-digest identity only. No publication now; SBOM
continues to record the OCI config digest accurately.

## 14. Implementation prerequisites (future action, not done)

Trivy JSON output step · previous-run finding artifact · in-repo
unit-tested evaluator (test vectors = the S1/S2/S3 inventories recorded
here) · shadow-verdict artifact publisher · exception ledger file + expiry
checker.

## 15. Recommendation for the next authorization gate

Authorize **shadow mode**: implement the prerequisites above with R1+R2+R4
evaluating in shadow (verdict artifacts only, exit-codes untouched), run
≥2 real CI cycles, publish the measured noise report. Threshold numbers,
exception schema/expiry (proposed: 90d), and the enforcement flip each
remain separate explicit decisions for Paul.
