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
| CVE-2026-53613 | libuuid | 2.41-r9 | 2.41.6-r0 | Next controlled base cycle (JSON-corrected 2026-09-24; see §4) |
| CVE-2026-53614 | libuuid | 2.41-r9 | 2.41.6-r0 | Next controlled base cycle (JSON-corrected 2026-09-24; see §4) |
| CVE-2026-76642 | libuuid | 2.41-r9 | 2.41.6-r0 | Next controlled base cycle (JSON-corrected 2026-09-24; see §4) |

**Compensating control (applies to all image HIGHs):** application runs
non-root (runAsUser 65534, runAsNonRoot pod+container), read-only rootfs,
no privilege escalation, seccomp RuntimeDefault. A compensating control
reduces exposure; it does **not** eliminate the vulnerability.

## 4. HIGH — awaiting upstream fix (no fix listed by scanner)

**CORRECTED (2026-09-24, shadow cycle-2 audit — this section is now
empty).** The authoritative Trivy JSON (runs 36040098028 and 36040505744,
fields `FixedVersion` + `Status`) shows CVE-2026-53613/53614/76642 ALL
have fix **2.41.6-r0** listed. The earlier "no fix listed" classification
came from merged-cell TABLE extraction (blank Fixed Version cells on
continuation rows) — the exact hazard documented in the policy layer.
JSON is authoritative; all 8 unique HIGH CVEs are fix-listed and tracked
in section 3. Original entries: 53613/53614/76642 → monitor upstream
(obsolete; now base-cycle candidates).

> History note: this register previously carried a reconciliation moving
> 76642 INTO this group; that reconciliation was itself based on table
> extraction and is superseded by the JSON-authoritative correction
> above. Earlier narratives are preserved in their original files.

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
