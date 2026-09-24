# Phase 7C Policy Simulation — Evidence & Design Record (NOT enforcement)

**Status: DESIGN/SIMULATION ARTIFACT.** Nothing in this document is wired
into CI. All Trivy steps remain exit-code 0 (evidence mode). This record
tests the Phase 7C proposal as a hypothesis against the project's actual
historical scan data, per the authorized progression:

```
existing evidence → policy design → historical simulation
→ false-positive/edge-case analysis → policy tuning → shadow mode
→ measured validation → explicit authorization → enforcement
```

**This task ends before shadow mode.** Shadow mode, measured validation,
and any enforcement flip require separate authorization.

## 1. Method

Independent re-parsing of the two authoritative historical scan artifacts
(Trivy v0.70.0 merged-cell tables, downloaded from the pinned CI runs):

| State | Artifact source | Inventory |
|---|---|---|
| 7A baseline (alpine3.20) | run on `aacc256` | 58 (pkg,CVE) pairs; CRIT 2, HIGH 16 |
| 7B verified (alpine3.22) | run 36033387702 on `c7af53f` | 65 pairs; CRIT 0, HIGH 10 |

Candidate policies were evaluated by asking one question per policy at
each historical state: **would CI have failed?**

## 2. Simulation results

| Policy | Rule | 7A (CRIT 2) | 7B (CRIT 0) | Verdict |
|---|---|---|---|---|
| P1: raw severity count | CRIT>0 ∨ HIGH>0 → fail | FAIL | **FAIL** | Rejected: permanent noise; blocks on 3 no-fix upstream CVEs that cannot be remediated |
| P2: CRITICAL-with-fix | count>0 → fail | **FAIL** | **PASS** | Correct discriminator; zero exceptions needed today |
| P3: CRIT/HIGH-with-fix | count>0 → fail | FAIL | **FAIL** | Rejected: needs 10 concurrent exceptions today (all HIGHs) — the "permanent build noise" failure mode |
| P4: CRIT-fix + age-based HIGH-fix | 30-day rule | indeterminate | indeterminate | Rejected **as designed**: table output carries no per-finding dates; age gating requires Trivy JSON (`PublishedDate`) — a CI change with new parsing risk, deferred |
| P5: persistence rule | fail when the same fix-listed HIGH/CRIT pair persists across ≥2 consecutive scans | PASS | PASS | Valid supplementary signal; needs scan-history persistence in CI (design implication, not a blocker) |
| P6: config gate | HIGH config finding in **rendered deployable manifests** → fail | (n/a pre-7B) | PASS | Correct **only with render-scoping** — see §3 |

**Simulated regression test:** re-running P2 against the 7A inventory
(a stand-in for "base drifts back to a vulnerable state") → **FAIL**.
P2 catches the project's one real historical CRITICAL. P2+P5 combined
catch both new CRITICALs and recurring neglected HIGHs.

## 3. False-positive / edge-case analysis

1. **CRITICAL without listed fix** — P2 misses it (no action available).
   Exposure today: none. Mitigation (tuned design): CRITICAL-no-fix raises
   a **warning** channel (non-blocking) so it cannot silently accumulate.
2. **HIGH-no-fix (upstream)** — the exact population (53613/53614/76642)
   that makes P1/P3 permanently red. Under P2 they never block; the debt
   register + reconciliation notes carry them. This is the deliberate
   trade: un-actionable findings stay visible in artifacts, not in exit
   codes.
3. **Merged-cell counting hazard** — naive table parsing under/over-counts
   (experienced directly during 7B verification). A policy evaluator must
   use Trivy **JSON** output or the summary header as ground truth, not
   hand-rolled cell inheritance. Recorded as an implementation requirement.
4. **Evidence-document HIGHs** — a repo-wide config gate would permanently
   fail on the Tier-A metrics-server evidence manifest (NOT_APPLICABLE by
   disposition; rewriting forbidden). P6 is therefore scoped to
   `helm template` output of deployable charts only. History stays intact;
   the gate reads only what would actually be deployed.
5. **Exception abuse** — any future exception file must carry CVE id,
   rationale, owner, expiry; CI fails on expired entries (from the 7C
   proposal, unchanged by simulation).

## 4. Tuned policy recommendation (design only)

**R1 (image, blocking):** fail when a CRITICAL (package,CVE) pair with a
listed fix exists in the built image scan. [P2 — validated by simulation:
FAIL@7A → PASS@7B, zero exceptions, catches regression]

**R2 (image, blocking):** fail when the same fix-listed HIGH pair appears
in N=2 consecutive scans without disposition. [P5 — persistence rule;
requires retaining the previous run's JSON finding list as a CI artifact]

**R3 (image, non-blocking):** CRITICAL-no-fix and all HIGHs → warning
summary + debt-register cross-check reminder.

**R4 (config, blocking):** HIGH config finding in rendered deployable
manifests only. [P6 — scoped; today's render = 0 HIGH / 0 MED / 5 LOW]

**R5 (process):** shadow-mode R1–R4 for a minimum of 2 real CI cycles with
verdicts recorded as artifacts BEFORE any exit-code flips. Enforcement
authorization is a separate explicit gate by Paul.

## 5. Implementation requirements identified (future action, NOT done)

- Trivy JSON output step (or summary-header parsing) for reliable counting
- Previous-run finding-list artifact for the persistence rule
- Policy evaluator script in-repo, unit-tested against the two historical
  inventories recorded here
- Shadow-mode verdict artifact published per run

Each is a CI change and therefore **out of this task's scope**; they are
the first work items when 7C implementation is authorized.

## 6. Answer to the core question

> «What deterministic CI security policy provides meaningful additional
> protection without turning known, documented, non-remediable or
> low-value findings into permanent build noise?»

**R1+R2+R4 with R3 as the visibility channel.** The simulation shows this
combination: catches the project's real historical CRITICAL (and any
regression), catches neglected recurring HIGHs, gates rendered config
HIGHs, never blocks on the three upstream-waiting CVEs, and requires zero
standing exceptions today.
