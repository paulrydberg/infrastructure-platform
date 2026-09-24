# Phase 7C Shadow-Mode Evaluator — Architecture & Operation

**Status: IMPLEMENTED, observational only.** The evaluator runs in CI but
NEVER changes any exit code. A `WOULD_FAIL` verdict is still a successful
workflow run. Enforcement remains an unauthorized future decision.

```
Trivy JSON (machine-readable, authoritative)
    ↓ normalize (dedupe by identity, flag conflicts)
    ↓ finding identity  = PkgName + "|" + VulnerabilityID
    ↓ previous/current comparison (GitHub Actions artifact of prior successful run)
    ↓ R1 / R2 / R3 / R4 evaluation (deterministic, stdlib-only)
    ↓ exception state (tools/policy/security-exceptions.json — shadow schema)
    ↓ shadow verdict artifact (shadow-policy-verdict, 90-day retention)
```

## Components

| File | Role |
|---|---|
| `tools/policy/shadow_evaluator.py` | The evaluator (stdlib-only + PyYAML for the render; no network, no LLM) |
| `tools/policy/test_shadow_evaluator.py` | 19 unit + historical-regression tests (deterministic, offline) |
| `tools/policy/security-exceptions.json` | Shadow exception ledger (currently empty) |
| `.github/workflows/ci.yml` | Four additive steps: JSON scan → unit tests → previous-run fetch → evaluation + artifact |

## Data-source hierarchy (mandatory)

**Trivy JSON = authoritative machine input. Human-readable `.txt` tables =
presentation only.** The merged-cell counting hazard discovered during the
7B verification is the reason this rule exists.

## Rule semantics (shadow verdict vocabulary)

| Verdict | Meaning |
|---|---|
| `PASS` | rule satisfied; nothing to surface |
| `WARN` | visible finding(s) that do not block under the proposed policy |
| `WOULD_FAIL` | **this finding would block CI under the proposed future policy** — it does NOT mean CI failed; the run stays green |
| `EXCEPTION` | finding covered by an active, unexpired exception (still visible) |
| `UNKNOWN` | evaluator could not determine a result (missing history, malformed input, missing render). **UNKNOWN is never converted to PASS.** |

### R1 — CRITICAL-with-fix
`CRITICAL + FixedVersion non-empty → WOULD_FAIL` (shadow). CRITICAL
without a listed fix stays visible through R3 (`critical_no_fix` list) —
never silently dropped. Historical regression test: the 7A inventory →
`WOULD_FAIL`; the current inventory → `PASS`.

### R2 — Persistence
Identity = `PkgName|CVE-ID` (fix availability is per package+CVE, so
package name alone or CVE alone is insufficient). Compared against the
JSON artifact of the previous successful run's `security-evidence`:
`NEW` (absent previously), `PERSISTENT` (present in both), `RESOLVED`
(present previously, absent now). Severity changes and fix-availability
changes are recorded as **transitions of the same identity**, never
double-counted as new vulnerabilities. Git commit age is never used.
**First run / missing previous artifact → R2 = UNKNOWN with an explicit
`history_available: false` record — missing history is never interpreted
as "no vulnerabilities."**

### R3 — Visibility channel (never blocking)
Surfaces: no-fix CRITICAL/HIGH (`VISIBLE_NO_FIX`), active exceptions,
EXPIRED exceptions (individually; an expired exception never continues to
suppress a finding), malformed previous artifact, malformed current scan,
missing history. Principle: **not blocking ≠ ignored.**

### R4 — Rendered-configuration observation
Scope is explicit: `helm template platform/helm/platform-demo` output,
Deployment document only. Checks: pod-level `runAsNonRoot: true`,
`runAsUser: 65534`, `seccompProfile.type: RuntimeDefault`; container-level
`allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`,
`runAsNonRoot: true`, `runAsUser: 65534`; resources requests+limits
present; image pinned (no `:latest`). The Tier-A metrics-server evidence
manifest is outside R4's scope by design and can never gate anything.

## Exception model (shadow)

`tools/policy/security-exceptions.json`:
`{"exceptions": [{"id": "<pkg>|<CVE>", "scope": "image", "reason": str,
"owner": str, "created": "YYYY-MM-DD", "expires": "YYYY-MM-DD",
"evidence": str, "compensating_controls": [...], "review_required": true}]}`
Missing expiry is rejected (recorded as an EXPIRED_EXCEPTION problem
record — indefinite exceptions are forbidden). **90 days is the proposed
shadow-mode default for expiry, under test — not permanent policy.**
Creation, review, and renewal of real exceptions is a future
authorization decision.

## Fixtures & provenance

Historical regression fixtures are **minimal synthetic copies whose values
are derived from the authoritative artifacts** (CI runs on `aacc256` =
7A: CVE-2026-31789 CRITICAL-with-fix present; run 36033387702 = current:
0 CRITICAL, no-fix HIGHs 53613/53614/76642). They are not full scan
copies; the relationship to the authoritative runs is documented here.
All other fixtures are synthetic (no secrets, no real host data).

## CI integration (additive only)

The four shadow steps execute **after** the existing table scan and
**before** artifact upload; the diff contains zero removed/modified lines
from any existing step (`git diff` shows insertions only). The JSON scan
uses the same pinned action SHA, scanner version, and scan parameters as
the table scan, differing only in `format: json`. `trivy-report.json` is
added to the existing `security-evidence` artifact so the next run can
fetch it as the R2 previous-run source. Previous-run fetch uses
`gh run download` from the last successful run on the branch whose head
SHA differs from the current one; `continue-on-error: true` keeps a
fetch failure from ever failing CI (the evaluator then records UNKNOWN
history).

## Limitations (explicit)

- **First run:** no previous artifact → R2 UNKNOWN; persistence measurement starts at cycle 2
- **CI failure #1 (recorded, preserved in history):** run 36039544280 @ `41ed0e9` — the CLI
  eagerly opened the absent previous-run file (`FileNotFoundError`) instead of letting the
  evaluator record UNKNOWN history. Symptom: build job failed at the shadow step on the very
  first shadow run. Cause: CLI passed an open handle of a nonexistent path. Fix: pass the
  path; `load_prev` resolves file-missing to the documented first-run branch. Verified by
  rerunning the exact first-run scenario locally (verdict UNKNOWN, R2 UNKNOWN,
  history_available=false, R3 carries the missing-history record) plus the full 19-test suite.
- **Artifact retention:** security-evidence is 30-day; runs further apart lose history → UNKNOWN, not zero
- **Unknown fix availability:** empty `FixedVersion` is treated as no-fix; field-absence vs explicit-empty distinction requires scanner confirmation (recorded UNKNOWN only where the input is ambiguous)
- **Exploitability:** never inferred; compensating controls produce risk dispositions, not remediation
- **Identity limits:** (pkg, CVE) identity cannot distinguish two vuln entries differing only in metadata; conflicting duplicates are flagged as issues, first occurrence wins deterministically
- **Differential comparison limits:** only the immediately previous successful run is compared; multi-cycle trends require the accumulated shadow artifacts (90-day retention)

## Resource impact

Mac Mini / Kubernetes / Docker runtime footprint: **0** (GitHub-hosted
CI; evaluator is stdlib Python, runs in <1 s; artifacts are KB-scale).

## Cycle status

- Implementation: **complete** (this commit)
- Cycle 1 (shadow baseline with real JSON): observed at the first CI run of this commit — see shadow-policy-verdict artifact
- Cycle 2 (persistence measurement): **pending** the next natural CI run
- Enforcement decision: **not authorized yet**
