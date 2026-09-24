# Phase 7C Hardening Record — P1–P5 (enforcement NOT enabled)

**Status: hardening complete and tested. Shadow mode remains the CI
default. The `--enforce` mechanism exists in code, is fully unit-tested,
and is NOT passed by CI. Activation remains a separate authorization gate.**

## Problem (from the policy review, verified by probe)

```
structurally-empty scan + available history  →  PASS
```

An eventual enforcement system must never confuse "scanner produced
nothing usable" with "the image is clean."

## Root cause

`normalize()` treated any parseable JSON with a `Results` list as valid
and derived findings from it; a scan with `Results: []`, a missing
`Results` key, `Vulnerabilities` entries lacking identity fields, or
wrong field types normalized to an empty finding dict. With a previous
artifact present, R2 classified the entire prior inventory as RESOLVED
(no PERSISTENT findings → R2 PASS), and the overall verdict became PASS.
Malformed severity (non-string/out-of-vocabulary) took a third path: an
exception mid-normalize, but per-entry problems inside a `Vulnerabilities`
list were appended to a `problems` list that did not flip the
validation result — silently skipped entries.

## Corrections

**P1 — minimum JSON schema validation** (`validate_scan`, derived from
the pinned scanner's real output — trivy v0.70.0 image scan always emits
the alpine OS block plus a Python/library block, each with a
`Vulnerabilities` list):

- Fatal (scan rejected → verdict UNKNOWN, never zero-findings): missing
  or non-list `Results`; non-object result blocks; `Vulnerabilities`
  present but not a list; non-object vulnerability entries; missing or
  empty non-string `VulnerabilityID`/`PkgName` (identity fields);
  non-string `FixedVersion`; zero blocks carrying a `Vulnerabilities`
  collection (never-seen structure — an empty scan is not distinguishable
  from scan insufficiency, and silently deleting the previous inventory
  as "resolved" was the silent-PASS path).
- Legitimate shapes preserved: `Vulnerabilities: null` on a block is
  valid when at least one other block carries a list (real scanner
  behavior for a no-library-vulns target); explicit empty lists are valid.
- The verdict artifact records `scan_identity.schema_validated: true`.

**P2 — severity-absent handling:** missing, empty, malformed
(non-string), or out-of-vocabulary severity is NON-fatal: the finding is
retained with severity `UNKNOWN`, an explicit issue is emitted
("severity absent/malformed … retained as UNKNOWN"), and R3 surfaces an
UNKNOWN visibility record. The finding is never reclassified (never
LOW), never skipped, can never satisfy R1 (so uncertainty cannot
fabricate a block), and can never silently pass. Lowercase severity is
canonicalized (`critical` → `CRITICAL`) with a note.

**P3 — provenance:** every verdict records `provenance: {run_id, image,
scanner_version}` (CI supplies `GITHUB_RUN_ID`, image ref, scanner
version). Absent provenance is recorded as `null` — never fabricated.
Provenance survives even UNKNOWN results.

**P4 — version separation:** `policy_version` (7c-policy-1.0.0 — the R1–
R4 semantics + precedence) is distinct from `evaluator_version`
(7c-shadow-1.1.0 — the implementation) and `schema_version` (2 — verdict
artifact format). Rule changes bump policy_version; code changes bump
evaluator_version; both appear in every artifact.

**P5 — enforcement/rollback tests without enforcement:** the evaluator
accepts `--enforce` with deterministic exit semantics
(`exit_code_for`): shadow → always 0; enforce → FAIL/UNKNOWN exit 1
(UNKNOWN never silently treated as safe, per the policy review),
WARN/PASS exit 0. CI does **not** pass `--enforce`. Tests prove:
shadow+WOULD_FAIL → exit 0; enforce+WOULD_FAIL → exit 1; enforce+PASS →
exit 0; enforce+UNKNOWN → exit 1; shadow+UNKNOWN → exit 0; R4 violation
under enforce → exit 1; rollback (drop `--enforce`) restores shadow exit
0 on the same failing input. Precedence tests cover malformed >
expired-exception > active-exception > R1 > R4 > WARN/UNKNOWN > PASS.

## Silent-PASS closure (the mandatory regression test)

`TestP1SchemaValidation.test_silent_pass_window_closed` asserts the exact
pre-fix failure — `{"Results": []}` **with available history** — now
returns **UNKNOWN**, along with `{}`, missing-`Results`, and wrong-type
variants. Pre-fix, this scenario returned PASS.

## Testing status

- **Unit-tested (synthetic, deterministic):** all 50 tests — P1
  structural acceptance/rejection matrix, P2 severity vocabulary, P3
  provenance presence/absence, P4 version distinction, P5 exit-code
  contract incl. rollback, R1–R4 semantics, precedence, exceptions,
  historical regression fixtures (7A → R1 WOULD_FAIL; current → PASS).
- **Real-CI-artifact validated:** hardened evaluator re-run against the
  actual `trivy-report.json` of Cycles 1/2/3:
  - Cycle 1 (36040098028): verdict UNKNOWN — R1 PASS, R2 UNKNOWN (first
    run), R3 WARN (missing history), R4 PASS — **unchanged** ✓
  - Cycle 2 (36040505744): verdict WARN — 65/65 PERSISTENT — **unchanged** ✓
  - Cycle 3 (36041814661): verdict WARN — 65/65 persistent — **unchanged** ✓
  All three now additionally carry provenance and both version fields;
  `schema_validated: true` on all three.

## Security review of the hardening (§23 checks)

- validator does not reject legitimate trivy output (real artifacts pass;
  null/empty-list block shapes tested explicitly)
- unknown structures do not silently pass (zero-block / all-null → UNKNOWN)
- malformed severity never becomes LOW (becomes UNKNOWN + visible)
- missing FixedVersion never becomes fixed (empty/None → no-fix)
- absent provenance stays `null` (never fabricated)
- policy_version ≠ evaluator_version (asserted)
- `--enforce` is NOT the CI default (workflow grep: zero `--enforce` usage;
  3 comment-only mentions all asserting shadow mode)
- rollback touches only the evaluator invocation flag; scanners/SBOM/
  gitleaks/image-policy steps are byte-identical (diff verified: 0 removed lines)
- exceptions never override malformed evidence (malformed ledger entries
  → expired-equivalent; malformed scan → UNKNOWN regardless of exceptions)
- empty scans cannot pass (regression test)
- test suite includes failure paths, not only happy path (50 tests)

## Final state

P1–P5 implemented · 50/50 tests green · CI integration additive-only ·
**shadow mode active, enforcement OFF** · Mac Mini/Kubernetes/Docker
runtime impact 0 · LLM inference 0.
