# Security Debt Register — infrastructure-platform

**Purpose:** operational decision-making, not a vulnerability dump. Every
entry carries an explicit disposition and next action. Maintained since the
Phase 7B closeout (2026-09-24); evidence source = Trivy v0.70.0 scans
(artifacts of CI runs on `aacc256` [before], `990572e`→`c7af53f` [after]).

**Severity naming convention:** "HIGH pair" = one (package, CVE) entry;
"unique CVE" = one vulnerability. Trivy's totals count pairs; this register
counts both where they differ.

## 1. Critical — eliminated

| Finding | Package | Status | Evidence |
|---|---|---|---|
| CVE-2026-31789 (counted as 2 CRITICAL pairs: libcrypto3+libssl3) | openssl 3.3.3-r0 | **REMEDIATED** — base `python:3.12-alpine3.20` → `python:3.12-alpine3.22` (3.5.6-r0) in commit `990572e` | post-remediation scans: CRITICAL = 0; CVE absent from report |

## 2. HIGH — remediated (config)

| Finding | Status | Evidence |
|---|---|---|
| KSV-0118 ×2 on deployable manifests (platform-demo chart; Phase-2 fundamentals fixture) | **REMEDIATED** — pod-level securityContext (runAsNonRoot, runAsUser 65534, seccompProfile RuntimeDefault) added in `990572e`; container-level controls preserved | independent rescan of HEAD render: KSV-0118 = 0, HIGH = 0, LOW = 5 |

## 3. HIGH — image CVEs awaiting next controlled base cycle (fix listed)

| Finding | Package(s) | Installed | Fixed version | Action |
|---|---|---|---|---|
| CVE-2026-14456 | libcrypto3, libssl3 | 3.5.6-r0 | 3.5.8-r0 | Next controlled base cycle (alpine3.23 candidate) |
| CVE-2026-45447 | libcrypto3, libssl3 | 3.5.6-r0 | 3.5.7-r0 | Next controlled base cycle |
| CVE-2026-53612 | libuuid | 2.41-r9 | 2.41.6-r0 | Next controlled base cycle |
| CVE-2026-78408 | libuuid | 2.41-r9 | 2.41.6-r1 | Next controlled base cycle |
| CVE-2026-78410 | libuuid | 2.41-r9 | 2.41.6-r0 | Next controlled base cycle |

**Compensating control (applies to all image HIGHs):** application runs
non-root (runAsUser 65534, runAsNonRoot pod+container), read-only rootfs,
no privilege escalation, seccomp RuntimeDefault. A compensating control
reduces exposure; it does **not** eliminate the vulnerability.

## 4. HIGH — awaiting upstream fix (no fix listed by scanner)

| Finding | Package(s) | Action |
|---|---|---|
| CVE-2026-53613 | libuuid | Monitor upstream (util-linux); re-check each scan cycle |
| CVE-2026-53614 | libuuid | Monitor upstream |
| CVE-2026-76642 | libuuid | Monitor upstream |

> **Reconciliation note:** the original Phase 7B report grouped 76642 with
> the fix-available set in one section; the verification gate and this
> register re-extracted the final artifact and corrected it here. The
> no-upstream-fix group is **three** unique HIGH CVEs. The original report
> carries an in-place reconciliation note; its narrative is preserved.

## 5. Medium / Low backlog

| Category | Items | Disposition |
|---|---|---|
| pip CVEs (5 MEDIUM pairs, 1 LOW) | e.g. CVE-2025-8869, CVE-2026-13346, CVE-2026-3219 (fixes in pip 25.3–26.2) | Resolved when upstream `python:3.12` images refresh pip; app installs no packages at runtime (low reachability — noted, not proven non-exploitable) |
| Config LOWs | KSV-0003 (capabilities.drop ALL) ×2, KSV-0110 (default namespace), KSV-0040 (per-namespace ResourceQuota) | Deferred → Phase 7C policy candidates (Kyverno audit-mode or CI checks) |
| Config MEDIUMs in evidence docs | KSV-0037/KSV-0125 on the metrics-server experiment manifest | NOT_APPLICABLE (historical evidence, component not installed; rewriting forbidden) |

## 6. Accepted (documented rationale)

| Item | Rationale |
|---|---|
| KSV-0125 "untrusted registry" on `rancher/k3s` (k3s compose) | Official Rancher image, pinned tag, recorded at deploy time; registry allowlist = 7C policy topic |

## 7. False positives

None declared. The one false-positive suspicion (KSV-0118) was
**investigated and rejected** by controlled experiment (Phase 7B).

## 8. Policy gaps (future architectural controls — NOT yet implemented)

| Gap | Future control | Phase |
|---|---|---|
| No CI severity thresholds (evidence mode only) | Block CRITICAL-with-fix / age-based HIGH; warn rest | 7C proposal |
| No digest-pinned deployment refs | Immutable digest in GitOps manifest | 7C proposal / registry decision |
| No admission enforcement | Kyverno audit-mode first | 7C proposal |
| No image signing/provenance | Cosign + SBOM attestation after registry decision | Deferred |
| Registry manifest digest unavailable (SBOM records OCI config digest only) | GHCR or ECR publication — separate decision | Deferred |

## Review cadence

Re-read this register on every security-phase boundary and whenever a base
image or scanner version changes. Owner: Paul (operator); prepared by the
platform CTO agent.
