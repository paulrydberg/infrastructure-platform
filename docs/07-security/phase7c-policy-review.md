# Phase 7C Policy Review & Enforcement-Readiness Gate

**Status: REVIEW COMPLETE. Enforcement NOT enabled and NOT authorized by
this document.** This is the readiness review and the proposed enforcement
contract; the shadow→enforcement transition remains a separate explicit
authorization by Paul.

## 1. Evidence base (all real artifacts, inspected this review)

| Item | Value | Source |
|---|---|---|
| Git HEAD | `dc92979` == origin/main, tree clean | git at review start |
| Cycle 1 | run 36040098028 @ `07f923f`: UNKNOWN (R2 first-run) | artifact |
| Cycle 2 | run 36040505744 @ `85b950e`: 65/65 PERSISTENT | artifact |
| Cycle 3 (natural, post-review-commit) | run 36041814661 @ `dc92979`: WARN, 65/65 persistent, 0 new/resolved, R1/R3/R4 PASS | artifact |
| Independent reconciliation | raw-JSON counts == evaluator counts | cycle record |
| Fix-availability correction | 53613/53614/76642 ARE fix-listed (JSON); 8/8 unique HIGHs fix-listed; no-fix population = 0 | cycle record §5 |
| Tests | 20/20 green | local run |
| Identity | `PkgName\|CVE-ID`: 0 duplicates/conflicts across 3 cycles | cycle record §4 |

## 2. Policy review findings

### R1 — CRITICAL-with-fix → FAIL (proposed enforcement)
Deterministic: severity + non-empty `FixedVersion` from JSON. Reviews:
(1) deterministic ✓ (2) counts pairs; the FAIL condition is existential
(≥1 pair), with pair lists recorded per-identity (3) one CVE affecting
two packages = two records, one rule evaluation — recorded in
`critical_with_fix[]` (4) installed version NOT part of the condition
(correct: any vulnerable installed version with an available fix counts)
(5) "fix available" = non-empty `FixedVersion` string in JSON — concrete
and checkable (6) malformed FixedVersion (non-string) currently raises
inside normalize → caught by evaluate() → verdict UNKNOWN with error —
**no silent PASS** (verified by probe) (7) missing severity → `UNKNOWN`
class, cannot match CRITICAL, surfaced only via counts — **gap: logged
below as precondition P2** (8) severity change between scans = R2
transition of same identity, R1 re-evaluated on current severity (9)
Critical-no-fix → R3 `VISIBLE_NO_FIX`, never blocking, never silent
(10) cannot silently pass: R1-PASS with zero criticals is only reachable
with a structurally valid scan; see UNKNOWN semantics (§4).

### R2 — persistence
Identity retained: 3 real cycles × 65 findings, zero ambiguity. Verified
against real evidence: NEW/PERSISTENT/RESOLVED classification, missing
history → UNKNOWN. Unit-test-only (synthetic coverage, honestly labeled):
severity transitions, fix-state transitions, version changes. **Blocking
role: none proposed.** R2 stays observational/contextual — its fail
semantics (N-cycle escalation) were explicitly deferred until measured
data justifies them. Under enforcement, R2 remains WARN-only.

### R3 — visibility (non-blocking; stays non-blocking)
Real-world validated: missing-history surfacing (cycle 1), clean-empty
state (cycles 2–3). Fixture-validated only: no-fix HIGH/CRITICAL, active
exception, expired exception, malformed ledger — no real no-fix
vulnerability exists to exercise them (none manufactured). R3 remains
non-blocking under enforcement; its contribution is the audit record.

### R4 — rendered-configuration gate
Deterministic key/value comparisons on the rendered platform-demo
Deployment; scope explicitly excludes the Tier-A evidence manifest
(scope-by-construction, re-verified in code). All 9 checks true in all 3
cycles. Suitable as a blocking gate: inputs are fully deterministic,
zero flakiness observed, failure = an actual missing control.

## 3. Proposed enforcement contract (NOT activated)

Verdict semantics under enforcement:
- **FAIL (CI fails):** R1 ≥1 CRITICAL pair with non-empty `FixedVersion`
  in the authoritative JSON **without** an active exception covering its
  identity; OR R4 ≥1 unchecked/failed control on the rendered platform-demo
  Deployment; OR an **expired exception** covering a finding that would
  otherwise FAIL (expired ≠ tolerated).
- **EXCEPTION:** identity covered by an active, unexpired, well-formed
  exception (id, scope, reason, owner, created, expires, evidence,
  review_required all present). Still listed in the verdict artifact.
- **WARN (visible, non-blocking):** all R3 records (no-fix CRITICAL/HIGH,
  malformed ledger entries); R2 transitions and persistence classifications.
- **UNKNOWN (non-blocking, loudly visible):** missing/invalid previous
  artifact (R2), malformed current scan, structural schema anomalies,
  evaluator internal errors. Recorded in the artifact with reasons.
  UNKNOWN never implies safety.
- **PASS:** none of the above conditions.

**Precedence (deterministic, first match wins):**
1. malformed/unusable current scan → UNKNOWN (over everything)
2. expired exception covering an otherwise-FAIL finding → FAIL
3. active exception → EXCEPTION
4. R1 match → FAIL
5. R4 failure → FAIL
6. any WARN/UNKNOWN records → WARN/UNKNOWN
7. otherwise → PASS

### UNKNOWN-under-enforcement decision (explicit, not implicit)
- R2 UNKNOWN (no history): **non-blocking** — blocking would make every
  30-day artifact-gap a red build; the gap is operational, not a security
  signal. Compensating visibility: UNKNOWN record + warnings summary.
- Current-scan UNKNOWN (malformed/empty/unusable): **non-blocking as a
  verdict, but flagged as precondition P1** — under enforcement a
  scanner-producing-garbage scenario must not read as PASS. Resolution:
  the enforcement step treats `verdict == UNKNOWN` as a **required
  visible warning plus artifact check**, and the contract adds: a scan
  with zero findings AND structurally absent `Results` data ⇒ UNKNOWN
  (implemented) — plus precondition P1's minimum schema validation.

## 4. Failure modes (intended behavior table)

| Failure | Behavior today (verified by probe where noted) | Enforcement behavior (proposed) |
|---|---|---|
| Scanner unavailable | CI step fails at the existing scan step (unchanged) | same — evidence layer still owns that |
| Malformed JSON | evaluator → UNKNOWN + error record ✓ (probed) | UNKNOWN + WARN, never PASS |
| Structurally-valid-but-empty scan | findings=0; with history ⇒ PASS — **the one genuine silent-PASS window** | P1 schema check closes it |
| Previous artifact missing | R2 UNKNOWN + R3 record ✓ (real, cycle 1) | UNKNOWN + WARN |
| Evaluator crashes | CI step fails (happened once: failure #1) | step failure = red CI — acceptable, never silent |
| Exception ledger malformed | recorded via R3 issues | malformed entries treated as EXPIRED-equivalent (no silent tolerance) |
| Trivy JSON structure change | type errors → UNKNOWN; missing fields → permissive skip | P1 minimum schema validation |
| GitHub artifact API unavailable | continue-on-error → missing history → UNKNOWN | UNKNOWN + WARN |

## 5. Provenance & versioning (§13/§14)

Present in every artifact: `schema_version`, `evaluator_version`, commit
SHA, UTC timestamp, current/previous scan identities. **Missing and
material under enforcement (preconditions):** P3 = workflow run ID +
image reference in the verdict; P4 = `policy_version` distinct from
`evaluator_version` (policy text lives in Git; the version string pins
which rule set produced a verdict). Trivy version is already recorded in
the scan metadata step; referencing it in the verdict is part of P3.
Minimum implementation: 3 fields in `evaluate()` + env passthrough —
documented, not applied.

## 6. Rollback concept (§15 — designed, not implemented)

Enforcement must be a **single-line flip**: the shadow step's evaluator
invocation gains an `--enforce` flag; enforcement = failing the step when
verdict ∈ {FAIL} (exit 1) after artifact upload. Rollback = remove the
flag (or set `POLICY_ENFORCE=0`) → evaluator returns to shadow verdicts;
all scanning steps untouched. Because the evaluator is additive, rollback
cannot disable Trivy/gitleaks/SBOM/config/image-policy evidence. This
design is what makes the future change coherent and one-commit reversible.

## 7. Future enforcement delta (§18 — conceptual, NOT applied)

```diff
       - name: shadow policy evaluation (R1/R2/R3/R4 — never blocking)
         run: |
           ...
           python3 tools/policy/shadow_evaluator.py \
             --current trivy-report.json \
             ...
             --out shadow-verdict.json
+          # ENFORCEMENT GATE — activate only by separate authorization
+          # (revert this single block to return to shadow mode):
+          python3 - <<'PY'
+          import json, sys
+          d = json.load(open('shadow-verdict.json'))
+          if d['verdict'] == 'FAIL':
+              sys.exit('policy FAIL (see shadow-verdict.json)')
+          PY
       - name: upload shadow policy artifact   # unchanged, uploads BEFORE the gate
```
- Only the shadow step changes; no scanner step changes; artifact upload
  order guarantees the verdict survives a FAIL.
- Branch protection: **no new required check needed** — the gate lives
  inside the existing `build` job, so the existing required CI status
  already covers it. Enforcement is independent of the scanner itself.
- Precondition P5 (below) is applied in the same change.

## 8. Enforcement readiness

**READY WITH REQUIRED PRECONDITIONS.**

Evidence-backed preconditions (each small, each necessary):
- **P1 — minimum JSON schema validation:** reject/UNKNOWN when `Results`
  is absent-not-as-empty, a Vulnerabilities entry lacks
  VulnerabilityID/PkgName, or a non-string FixedVersion appears. Closes
  the verified silent-PASS window (empty scan + history ⇒ PASS today).
- **P2 — severity-absent findings must be visible:** currently a missing
  Severity silently skips R1. Under enforcement they must appear as
  UNKNOWN records.
- **P3 — provenance fields in the artifact:** run ID + image reference +
  scanner version (material once verdicts gate merges).
- **P4 — `policy_version` in the artifact:** distinguish same-scan/
  different-policy from different-scan/same-policy.
- **P5 — enforcement unit tests:** FAIL-path exit-code test + rollback
  (shadow) test, so the flip itself is test-covered before activation.

Not preconditions (explicitly rejected as invented work): Kyverno,
registry, signing, reachability analysis, new severity thresholds,
multi-cycle R2 escalation.

## 9. Skill audit (§24)

`infrastructure-platform-security` found at
`~/.hermes/skills/devops/infrastructure-platform-security/SKILL.md`
(21 lines, created 2026-09-24):
1. Stored in the Hermes skill directory (`devops/` category).
2. **Not source-controlled** — lives outside the repository.
3. Contains: the JSON-authority rule (incl. the 53613/53614/76642
   correction), identity algorithm, missing-history semantics, shadow
   architecture summary, verdict vocabulary, exception model state,
   operating conventions (measure-first, VERIFIED-labels, reconciliation
   notes, independent recomputation).
4. Repository-specific: yes — it names this repo's paths and history.
5. Duplication/conflict: **no conflicts found**; every rule in the skill
   is also present in source-controlled `tools/policy/README.md`,
   `docs/07-security/phase7c-shadow-cycles.md`, and the debt register
   (verified by grep). The skill is a condensed copy, not a divergent
   authority.
6. Hidden state: it is outside Git, but it contains no rule that is not
   in Git — the project remains reconstructible from the repository
   alone (verified: all skill content traces to committed docs).
7. Needed: useful as a session-bootstrap index for future CTO sessions;
   not load-bearing for the platform.
8. Verdict: **supplemental, not authoritative; consistent with the
   source-controlled policy; no action required.** The repository remains
   the single source of truth (self-reconstructing principle upheld).

## 10. Final readiness matrix

| Area | Status | Evidence | Enforcement impact |
|---|---|---|---|
| Git integrity | PASS | `dc92979` == origin/main, clean, full 7A→7C ancestry | none |
| Cycle 1 evidence | PASS | artifact re-verified | none |
| Cycle 2 evidence | PASS | artifact + raw-JSON reconciliation | none |
| Cycle 3 evidence | PASS | artifact (natural run) | none |
| R1 | PASS | probes: deterministic; malformed → UNKNOWN | gate per contract |
| R2 | PASS | 3 cycles real; transitions unit-only (labeled) | stays WARN-only |
| R3 | PASS | real missing-history + clean states; no-fix fixture-only | stays non-blocking |
| R4 | PASS | deterministic; 3×9 checks true; Tier-A excluded | gate per contract |
| JSON authority | PASS | rule + the demonstrated correction | formalized in contract |
| Finding identity | PASS | 0 duplicates/conflicts ×3 cycles | unchanged |
| Transition handling | PASS (unit-labeled) | synthetic coverage only | WARN-only |
| Exception model | PASS w/ P5 note | ledger empty; semantics unit-tested | expired → FAIL |
| UNKNOWN semantics | PASS | explicitly defined, never PASS | per contract §3 |
| Artifact provenance | PARTIAL → P3 | run-id/image/scanner-version missing | precondition |
| Policy versioning | PARTIAL → P4 | policy_version absent | precondition |
| Failure handling | PASS w/ P1 note | probed; one silent-PASS window | precondition |
| Rollback design | PASS (concept) | single-flag flip; evidence untouched | enables safe flip |
| Existing CI controls | PASS | byte-identical diffs verified previously | untouched |
| Skill/source-of-truth | PASS | supplemental, consistent, reconstructible | none |
| Tests | PASS | 20/20 (+P5 pending) | P5 before flip |
| CI | PASS | run 36041814661 green @ HEAD | gate lives in build job |
| **Enforcement readiness** | **READY WITH REQUIRED PRECONDITIONS** | P1–P5 | flip after P1–P5 + authorization |

## 11. Boundary statement

**CI enforcement = NOT ENABLED.** No exit-code, branch-protection, or
workflow behavior was changed in this review. The contract above is a
proposal. Activation requires Paul's explicit authorization AND
completion of P1–P5 in a single reviewed change, with rollback verified.
