# Phase 7C Shadow Cycle-2 Observation & Reconciliation Record

**Status: observation complete. Two real cycles measured. No enforcement
enabled; no policy redesign; evaluator unchanged (verified correct); one
data-provenance correction applied (documentation + fixtures, with
reconciliation notes — history preserved).**

## 1. Cycles (both real, natural push-triggered CI runs)

| | Cycle 1 | Cycle 2 |
|---|---|---|
| Run ID | 36040098028 | 36040505744 |
| Commit | `07f923f` | `85b950e` |
| Trigger | push (docs commit) | push (docs commit) |
| Conclusion | success | success |
| Artifact | shadow-policy-verdict (downloaded & inspected) | shadow-policy-verdict + security-evidence (downloaded & inspected) |

### Cycle 1 (independently re-verified from artifact)
verdict UNKNOWN · R1 PASS · R2 UNKNOWN (first run, no previous artifact —
history_available=false) · R3 WARN (missing-history record) · R4 PASS ·
65 findings · would_fail 0. **Matches the previous report exactly.**

### Cycle 2 (from artifact)
verdict **WARN** · R1 PASS · R2 WARN (**65 PERSISTENT, 0 new, 0
resolved**) · R3 PASS · R4 PASS · 65 findings · would_fail 0 ·
previous_scan_identity: available, 65 findings.

## 2. Comparison

| Metric | Cycle 1 | Cycle 2 | Delta |
|---|---|---|---|
| Total findings | 65 | 65 | 0 |
| New | n/a (UNKNOWN) | 0 | — |
| Persistent | n/a | 65 | — |
| Resolved | n/a | 0 | — |
| Critical | 0 | 0 | 0 |
| High pairs | 10 | 10 | 0 |
| Would-fail | 0 | 0 | 0 |
| Warnings | 1 (missing history) | 0 | −1 |
| Exceptions | 0 | 0 | 0 |
| Unknown | 2 | 0 | −2 |

Behavioral change: the evaluator transitioned from first-run UNKNOWN to a
fully-determined WARN state — R2 now has history and classified all 65
findings as PERSISTENT, exactly matching an independent reconciliation
performed directly on the two raw `trivy-report.json` artifacts (65/65
identical). R3's missing-history warning correctly disappeared once
history existed.

## 3. R2 persistence verification (primary test)

Independent recomputation from raw JSON (not the evaluator's summary):
PERSISTENT 65 · NEW 0 · RESOLVED 0 · severity transitions 0 · fix-state
transitions 0 · installed-version transitions 0. Evaluator output agrees
with the independent recomputation on every count. No real version/fix/
severity transitions occurred between the cycles (identical scanner DB
window, unchanged image), so those paths remain covered by unit tests
only — documented, not fabricated.

## 4. Identity audit — `PkgName|CVE-ID`

Checked both cycles for duplicate identities across targets, installed
versions, severities, statuses, and sources: **0 duplicate-target
records, 0 conflicting duplicates** in either cycle. One identity =
exactly one (package, CVE) record per scan. The identity is sufficient
for the observed data; unchanged. (Theoretical ambiguities — same CVE in
two distinct targets — do not occur in this single-image scan scope.)

## 5. MATERIAL DATA CORRECTION (discovered by this audit)

The authoritative Trivy **JSON** (both cycles, `FixedVersion` +
`Status='fixed'`) shows **CVE-2026-53613/53614/76642 DO have fix
2.41.6-r0 listed**. The earlier "3 no-fix-listed HIGHs" classification —
recorded in the 7B verification, the debt register, ADR docs, and the
evaluator fixtures — came from **merged-cell table extraction** (the
Fixed Version cell is blank on continuation rows), which is precisely
the table-parsing hazard this policy layer was built to avoid and
document. JSON is authoritative per our own rule; the table-based
extraction was the error.

**Corrected inventory (JSON-authoritative [M]):** 8 unique HIGH CVEs, all
8 fix-listed (unique: 14456, 45447, 53612, 53613, 53614, 76642, 78408,
78410); no no-fix HIGHs in the current image. R3 has nothing to surface
because there is genuinely nothing no-fix — correct behavior, correctly
empty.

Corrections applied (smallest possible, with reconciliation notes, no
history rewriting):
- test fixtures updated to JSON values; no-fix-HIGH R3 path now covered
  by a synthetic fixture (CVE-2026-0001); +1 test (20 total, all green)
- debt register, ADR-0005 note, README fixture provenance: updated below
- evaluator code: **unchanged** (it consumed JSON correctly all along)

Impact on policy selection: none material — Policy A/B/C/D discrimination
depended on severity/fix structure, not on which util-linux CVEs lacked
fixes; the "would raw counts permanently block?" analysis now shifts
from "3 no-fix HIGHs" to "0 no-fix HIGHs today," which strengthens the
fix-availability rule choice (a fix-listed rule would block all 10 HIGH
pairs; the fix-availability + exception model remains the right shape).

## 6. R1 / R3 / R4 verification

- R1: 0 CRITICAL-with-fix in both cycles (JSON) → PASS — matches artifact
- R3: surfaced missing-history at C1, correctly empty at C2; non-blocking
- R4: all 9 checks true, image `platform-demo:0.1.0` pinned; scope remains
  the rendered platform-demo Deployment only; Tier-A metrics-server
  manifest outside scope (verified by scope-by-construction in code)
- Exceptions: ledger empty (no real exceptions fabricated); active/expired
  paths remain covered by unit fixtures; 90-day expiry still proposed-
  under-test, not authorized

## 7. Noise assessment (§18)

- unexpected WOULD_FAILs: none
- excessive WARNs: none (C2 warnings = 0)
- excessive UNKNOWNs: none (C2 unknowns = 0)
- false persistence / false NEW / false RESOLVED: none (65/65 match
  independent reconciliation)
- incorrect exception handling: n/a (no exceptions exist)
- R4 false positives: none
- base-image churn: no inventory change between cycles (identical JSON);
  nothing to misclassify; the C1→C2 delta is pure evaluator state
  maturation (UNKNOWN → determined), not security change
- Classification of the one surprising finding (no-fix discrepancy):
  **data limitation / documentation issue**, not an implementation defect —
  corrected per §5

## 8. Conclusion

Two real cycles observed; evaluator behavior verified correct against
independent raw-JSON reconciliation. The shadow system is ready for a
**policy-review / enforcement decision gate** — which remains a separate,
explicit authorization. "Shadow mode works" is not "policy is authorized."
