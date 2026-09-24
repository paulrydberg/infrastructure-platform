# Phase 7B — Security Finding Triage & Remediation (working notes)

**Starting SHA:** `1f9965357d06f241817f8ee126a24916bd19b6e6` (Phase 7A
completion commit; branch `main`, tree clean, main == origin/main, CI green
run 36030248752).

## 1. OpenSSL / CVE-2026-31789 triage (the 2 CRITICALs)

Finding: CVE-2026-31789 reported for libcrypto3 AND libssl3 (same underlying
OpenSSL issue — heap buffer overflow from large X.509 certificates on
32-bit systems; the doubled count is one vulnerability in two packages).

Evidence collected (direct instrumentation, per RC-1 discipline):

| Base image | openssl in image | CVE-2026-31789 | Tag last rebuilt |
|---|---|---|---|
| `python:3.12-alpine3.20` (current) | 3.3.3-r0 | **PRESENT** | 2025-05-10 |
| `python:3.12-alpine3.21` | 3.3.5-r0 | **STILL PRESENT** (tag not rebuilt with fix) | 2025-10-13 |
| `python:3.12-alpine3.22` | **3.5.6-r0** | RESOLVED (≥ 3.3.7-r0) | 2026-04-19 |
| `python:3.12-alpine3.23` | 3.5.8-r0 | RESOLVED (newest) | 2026-09-21 |

Alpine package repos (authoritative APKINDEX, fetched directly):
- v3.20 main: libcrypto3 **3.3.7-r0** (the fix EXISTS in 3.20's repo — the
  pinned image just predates it)
- v3.21 main: 3.3.7-r1
- v3.22 main: 3.5.8-r0

Key insight: the fix exists for the CURRENT base's repo, but the current
pinned tag was last rebuilt 2025-05-10 and contains 3.3.3-r0. Options:

a) `apk upgrade`/pin openssl packages in Dockerfile — introduces package
   installs into a deliberately stdlib-only deterministic build; adds a
   moving target (repo state at build time) without pinning
b) Bump base to `python:3.12-alpine3.21` — does NOT fix (measured: image
   contains 3.3.5-r0)
c) Bump base to `python:3.12-alpine3.22` — fixes (3.5.6-r0 measured),
   smallest supported base that actually resolves the CVE
d) Bump to `python:3.12-alpine3.23` — fixes, but newest-available rather
   than smallest-needed; 3.23 rebuilt 2026-09-21

**Selected: (c) python:3.12-alpine3.22.** Reason: smallest supported version
that resolves the issue (per §19 discipline), official upstream build
(guaranteed Python↔OpenSSL ABI compatibility, Python 3.12.13 measured),
alpine 3.22 within supported window. alpine 3.23 deferred: no additional
security need measured; will be evaluated at the next base-review cycle.

Compatibility checks performed: Python 3.12.13 confirmed in candidate;
application is stdlib-only (urllib HTTP server); app runs as non-root user
created in-image (unchanged); healthcheck unchanged; no other packages.

## 2. KSV-0118 (3 HIGH config findings) — root cause established via controlled tests

Hypothesis 1 (raw helm-template parsing) — TESTED AND REJECTED: scanning a
fully rendered manifest still fires KSV-0118 on platform-demo.

Controlled experiments (trivy v0.70.0 local, checksum-verified):
- Test A (pod-level + container-level securityContext): KSV-0118 **NOT fired**
- Test B (container-level only — exactly our chart): KSV-0118 **FIRED**

Root cause: **KSV-0118 requires POD-level `spec.securityContext`**; it fires
when pod-level SC is absent even when every container has a complete
non-root securityContext.

Classification: **legitimate hardening finding, NOT a false positive**
(initial suspicion was wrong and is preserved here). Defense-in-depth value:
pod-level SC governs all current and future containers/ephemerals in the
pod. Remediation: add pod-level securityContext (runAsNonRoot + runAsUser
+ seccompProfile RuntimeDefault) to the chart — additive, preserves all
existing container-level controls.

Per-finding applicability:
- `platform-demo` (chart): APPLICABLE → remediated via pod-level SC
- `demo` in platform-test (Phase 2 fundamentals test fixture,
  `kubernetes/k3s/test/fundamentals.yaml`): APPLICABLE to that test
  artifact → same pod-level SC treatment for consistency
- `metrics-server` reference in Tier-A experiment doc: the doc's manifest
  is historical evidence (metrics-server upstream default config, not
  retained in cluster) — NOT_APPLICABLE to live posture; documented, not
  "fixed" (rewriting evidence manifests is forbidden)

## 3. Medium/Low config findings (27+4)

Categories observed in artifact: default-namespace usage (KSV-0110, LOW —
platform-demo deploys to `default` by chart values; acceptable for the
single-app demo cluster, tracked), capabilities.drop missing ALL (KSV-0003,
LOW), seccomp profile unset (KSV-0300-ish, MEDIUM/LOW — being addressed by
the pod-level seccompProfile in the KSV-0118 remediation), service-account
token automount (LOW). Each is static-config hardening; batch disposition:
REMEDIATED where the pod-level SC fix covers them, otherwise DEFERRED with
the inventory listing.

## 4. Image CVEs (52 total: 19L/15M/16H/2C)

Base bump to alpine3.22 expected to clear most/全部 of the alpine-package
CVEs (busybox, openssl, zlib etc. all refresh) and pip CVEs partially
(pip 25.x in image; fixes in 25.3+/26.x — some pip findings may persist
until python:3.12 image updates pip). Post-remediation scan is
authoritative; inventory updated from actual scan output only.

## 5. SBOM digest

Local CI build produces no registry digest (docker images --digests shows
<none> for untagged-digest local images). Options: (a) registry push — new
infrastructure dependency, out of 7B scope by authorization; (b) use the
OCI image ID (config digest) as the immutable local identity — this IS an
immutable content digest of the image config, obtainable via
`docker images --no-trunc --format '{{.ID}}'` and `docker inspect`. It is
NOT the registry manifest digest and must not be labeled as one. Decision:
record the **image ID (config digest)** clearly labeled as such; keep
registry-manifest-digest as the documented future step.

## 6. Commit plan (natural boundaries only)

1. phase7b: finding inventory + triage docs (evidence of investigation)
2. phase7b: bump base to python:3.12-alpine3.22 (OpenSSL CVE-2026-31789)
   — with version-bump of app tag 0.1.0 → 0.1.1 (chart↔compose consistency)
   IF tests pass; else preserve failure first
3. phase7b: pod-level securityContext in chart (KSV-0118)
4. phase7b: SBOM image-ID identity (labeled, not misrepresented)
5. docs: 7B report + baseline update + matrix/README/roadmap
(adjusted to reality as work proceeds — no forced structure)
