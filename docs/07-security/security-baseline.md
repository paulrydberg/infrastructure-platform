# Phase 7 — Security Baseline (Stage 7A: CI Evidence)

**Status: Stage 7A complete — DETECT/BASELINED established. Nothing is
BLOCKED yet by policy; enforcement is a future gate decision.**

Operating principle (per authorization):

```
detect → produce evidence → understand findings → establish baseline
      → define policy → enforce policy
```

## 1. Threat / control scope

| Threat | Control (7A) | Enforcement (future) |
|---|---|---|
| Known CVEs in image | Trivy image scan | severity thresholds (7B) |
| IaC misconfiguration | Trivy config scan of `platform/` | config rules (7B+) |
| Injected secrets | existing grep gate + gitleaks history scan | fail-on-find (candidate 7B) |
| Floating/unpinned images | image-reference policy checks | hard fail (candidate 7B) |
| Supply chain (unknown contents) | SPDX SBOM of built image | provenance/signing (later) |
| Malicious CI tooling | action SHAs pinned; binaries checksum-gated | — (practice established) |

Out of scope for 7A: runtime security, admission enforcement (Kyverno),
image signing/cosign, AWS, AI automation, anything touching the protected
container fleet or the Mac Mini's resident footprint.

## 2. Scanner/tool versions (all pinned)

| Tool | Version | Integrity |
|---|---|---|
| trivy-action | v0.36.0 @ `ed142fd0673e97e23eac54620cfb913e5ce36c25` | commit-SHA pin, annotated tag resolved via GitHub API |
| trivy CLI | v0.70.0 (2026-04-17) | explicit `version:` input; v0.69.4 verified absent upstream |
| gitleaks | v8.30.1 linux_x64 | SHA-256 `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb` verified in-CI |
| kubeconform (existing) | v0.8.0 | SHA-256 pinned (Phase 4) |
| helm (existing) | v3.16.3 | official checksum (Phase 3/4) |

**Supply-chain incident note (2026-03-19):** trivy-action tags ≤ 0.34.2 and
the Trivy v0.69.4 CLI release were compromised (GHSA-69fq-xp46-6x23,
CVE-2026-33634). Our pins post-date and bypass the incident entirely; the
malicious tag was verified absent from the upstream release list before
adoption. This is recorded as evidence the project's pin-and-verify
discipline matters.

## 3. Severity definitions (used consistently)

UNKNOWN < LOW < MEDIUM < HIGH < CRITICAL (Trivy standard). Statuses:
`DETECTED` (scanner reported) · `BASELINED` (present at 7A baseline, triaged)
· `WARNED` (surfaced, not blocking) · `BLOCKED` (enforced — none yet)
· `REMEDIATED` (fixed and re-scanned) · `VERIFIED` (fix confirmed by
rescan). A DETECTED finding is NOT a remediated one.

## 4. CI behavior (evidence mode)

- `security` job runs after `build`, scans the actual built
  `platform-demo:0.1.0` image — not just the source tree
- **exit-code 0 everywhere in 7A**: findings are recorded, never blocking.
  Rationale: policy must come from an observed baseline, not assumed counts
- Artifacts (30-day retention): trivy-report.txt, trivy-config-report.txt,
  sbom-platform-demo.spdx.json, sbom-metadata.txt, gitleaks-report.json
- gitleaks runs with `--redact`: matched secret material never enters CI logs
- image-reference policy check: fails CI only on objective violations
  (floating `:latest`, untagged image refs) — the deterministic rules the
  project already practices; registry-allowlist anomalies are REVIEW-only

## 5. Baseline (first runs — filled from CI evidence)

| Scan | Target | Result | Class |
|---|---|---|---|
| Trivy image | platform-demo:0.1.0 (alpine 3.20.6 base) | **52 CVEs** (LOW 19 / MED 15 / HIGH 16 / CRIT 2 — 2x CVE-2026-31789 openssl heap overflow, fix available 3.3.7-r0; base bump required, no image rebuild blocked) | DETECTED -> BASELINED |
| Trivy config | platform/ manifests | 114+98+125+123 tests; **29 failures total (27 LOW, 4 MEDIUM, 3 HIGH)** — all 3 HIGH are KSV-0118 'default security context allows root' incl. k3s compose + platform-demo chart (chart actually sets non-root 65534 — rule needs triage: possible false positive vs default-namespace render) | DETECTED -> BASELINED (triage in 7B) |
| Gitleaks | full git history | **0 findings** (empty report `[]`) — repo history clean | VERIFIED |
| Image policy | platform/ + applications/ | 0 violations (pinned tags, no latest) | VERIFIED (deterministic) |
| SBOM | platform-demo:0.1.0 | SPDX JSON (76.9 KB) + metadata; digest field empty (`<none>` — locally-built image has no registry digest; digest awareness requires a registry push, out of 7A scope) | BASELINED (digest gap noted) |

## 6. SBOM provenance — what is and is not claimed

```
source (Git, pinned Dockerfile)
  ↓
build (CI, github-hosted runner)
  ↓
image platform-demo:0.1.0 (local digest recorded)
  ↓
SBOM (SPDX JSON, generated FROM the built image)
  ↓
scan (trivy, same image ref)
```

Claimed: SBOM describes the actual built artifact of the pinned source.
NOT claimed: signed provenance, attestation, or byte-reproducible SBOMs
(embed generation timestamps; the identity chain, not file bytes, is the
reproducible claim).

## 7. Accepted-risk / exception process

- An accepted-risk finding requires: documented CVE ID, affected component,
  rationale, review date, and owner (Paul) — recorded in this file's
  baseline table. No exceptions currently claimed.
- Findings may move to WARNED (documented, non-blocking) in 7B once the
  baseline is reviewed. Nothing moves to BLOCKED without a separate
  authorization decision.

## 8. Remediation expectations

- CRITICAL with available fix: remediate or explicitly accept within one
  phase cycle (expectation, not yet enforcement)
- HIGH with fix: remediate within two cycles or document acceptance
- Base-image updates preferred over layer patches (deterministic rebuild)
- Every remediation re-scanned to VERIFIED before the finding is closed

## 9. Controls evaluated and REJECTED (documented, not silently dropped)

- **gitleaks-action v3 (node bundle): REJECTED** — commercial EULA-licensed
  prebuilt bundle; adopting it would trade auditability for convenience.
  Replaced by the checksum-pinned gitleaks binary (same discipline as
  helm/kubeconform). The existing repo grep gate remains the deterministic
  push-blocker; gitleaks adds entropy/ruleset history coverage on top —
  not a redundant duplicate.
- **Kyverno / admission control:** deferred (7B+ decision; would introduce
  resident cluster infrastructure — Phase 6 lessons applied).
- **Cosign/signing:** deferred; SBOM+digest identity chain is the 7A scope.


## 9b. Honest CI failure #1 (preserved)

The first 7A commit placed the scanners in a standalone `security` job.
GitHub-hosted runners are ephemeral per job: the image built in `build`
did not exist on the security job's runner (Trivy FATAL: unable to find
platform-demo:0.1.0; run failed). Correction: scanner steps re-homed into
the build job immediately after the image build/tests — scanners run
against the actual artifact on the same runner. Lesson: scan the artifact
in the job that builds it, or promote via a registry first.


## 9c. Actual baseline findings (first evidence run, 2026-09-24)

**Trivy image scan — platform-demo:0.1.0 (alpine 3.20.6):**
- **52 CVEs total**: LOW 19, MEDIUM 15, HIGH 16, CRITICAL 2
- The 2 CRITICALs are the same OpenSSL vulnerability (CVE-2026-31789,
  heap buffer overflow from large X.509 certificates on 32-bit systems)
  reported once for libcrypto3 and once for libssl3, both fixed in
  3.3.7-r0 — remediation is a base-image bump of alpine 3.20.x, which is
  a deterministic rebuild (tracked for 7B triage; nothing is BLOCKED)
- python-pip findings: 6 (5 MEDIUM, 1 LOW), several with fixes available
  in pip 25.3/26.x — same base-bump remediation path

**Trivy config scan — platform/ manifests:**
- 460 checks across 4 files: 29 failures (27 LOW, 4 MEDIUM, 3 HIGH)
- All 3 HIGH are KSV-0118 ("default security context allows root"):
  k3s compose.yaml, platform-demo chart render, and the metrics-server
  reference in the experiment documentation. Triage note for 7B: the
  platform-demo chart sets runAsUser 65534/non-root/read-only rootfs, so
  the rule firing on it needs verification against the actual rendered
  output — possible rule-context mismatch (false positive) to confirm.

**Gitleaks — full git history:** **0 findings** (empty `[]` report).
Combined with the existing grep gate, the repository's secret hygiene is
VERIFIED clean at 7A.

**SBOM:** SPDX JSON 76.9 KB for platform-demo:0.1.0. Honest gap: the
`digest` metadata field is empty (`<none>`) — a locally-built image inside
CI has no registry digest; digest-level identity requires a registry push
(explicitly out of 7A scope). Source→build→SBOM chain is real; digest
anchoring is a documented gap for 7B.

**Image-reference policy:** 0 violations — no `:latest`, no untagged
references across platform/ and applications/.

## 10. Resource impact

Zero on the Mac Mini: all scanning on GitHub-hosted runners; no resident
security daemons; no k3s/Docker/protected-fleet changes. The platform
remains healthy; the deployment cluster is unchanged.

## 11. Future enforcement stages (NOT authorized yet)

7B candidates: define severity thresholds from observed baseline → flip
exit-codes → fail-on-secret (gitleaks) → digest-pinned base images →
Kyverno audit-mode on k3s. Each is a separate authorization with its own
acceptance criteria.
