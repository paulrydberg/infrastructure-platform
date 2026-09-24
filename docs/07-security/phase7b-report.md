# Phase 7B — Completion Report (Security Finding Triage & Remediation)

**Phase 7B starting SHA:** `1f9965357d06f241817f8ee126a24916bd19b6e6` (Phase
7A completion commit) · branch `main` · tree clean · main == origin/main ·
CI green (run 36030248752).

**Phase 7B commits:** `32cf159` (triage) → `990572e` (remediation) →
`b410810` (SBOM identity) → this documentation commit. No PR used — direct
main commits, consistent with the project's single-operator workflow; CI
validated every commit on main. No history rewritten.

## 1. Executive summary

Every Critical and High finding from the 7A baseline now has an
evidence-backed disposition. The 2 CRITICAL image CVEs were
**REMEDIATED** (base bump; 0 CRITICAL post-remediation, verified by rescan).
The 3 HIGH config findings (KSV-0118) were root-caused via controlled
experiments — the initial false-positive suspicion was **tested and
rejected** — and **REMEDIATED** for both applicable workloads (rescan: 0
HIGH config). Image HIGH CVEs dropped 16 → 10 (measured); the total count
rose 52 → 59 because the refreshed package DB surfaces newer advisories
across the newer base — an expected, honest tradeoff documented below. No
blocking thresholds were enabled. Existing security controls preserved
and re-verified.

## 2–3. Starting state & 7A baseline

See `phase7b-triage.md` (committed first, before any substantive change).
7A baseline referenced, not duplicated: 52 image CVEs (19L/15M/16H/2C),
29 config findings (27L/4M/3H), 0 secrets, 0 policy violations, SBOM with
empty digest field.

## 4–7. Critical findings → disposition

**CVE-2026-31789** (libcrypto3 AND libssl3 — one OpenSSL vulnerability
counted twice), CRITICAL, installed 3.3.3-r0, fixed 3.3.7-r0:
- VALIDATE: affected packages present in runtime image [M]; the app does
  not terminate TLS (loopback HTTP health, cluster-internal traffic), so
  exposed surface is limited — but openssl libs ship in the image and
  applicability is at package level. Runtime reachability: UNKNOWN/low,
  not claimed either way.
- FIX AVAILABLE: yes, and measured present in candidate bases (see
  `phase7b-triage.md` candidate table: alpine3.21 still vulnerable at
  3.3.5-r0 — the "bump one release" instinct would have failed here).
- REMEDIATION: base `python:3.12-alpine3.20` → `python:3.12-alpine3.22`
  (measured openssl 3.5.6-r0, Python 3.12.13). Alternatives documented:
  apk-upgrade in build (rejected: moving-target repo state, breaks the
  deterministic stdlib-only build), alpine3.23 (deferred: newest ≠
  smallest-sufficient; no measured need). Commit `990572e`.
- VALIDATION: post-remediation CI rescan — **CRITICAL 2 → 0 [M]**;
  app health verified locally on the new base (`/health` ok, version
  0.1.0); helm lint/template/kubeconform green in CI.

Disposition: **REMEDIATED + VERIFIED** (rescan-confirmed).

## 6. High findings → dispositions

**KSV-0118 ×3 (config, HIGH).** Root cause established by controlled
experiments (trivy 0.70.0 local binary, checksum-verified):
- pod-level + container-level SC → rule does NOT fire
- container-level only (our chart) → rule FIRES
⇒ rule requires POD-level securityContext. The initial false-positive
suspicion was rejected by evidence. Dispositions:
- platform-demo chart: **REMEDIATED** — pod-level SC added (runAsNonRoot,
  runAsUser 65534, seccompProfile RuntimeDefault), container-level controls
  untouched. Rescan: KSV-0118 gone [M].
- Phase-2 fundamentals fixture: **REMEDIATED** (same treatment).
  Rescan: 0 HIGH [M].
- metrics-server manifest in Tier-A experiment doc: **NOT_APPLICABLE** —
  historical evidence manifest of a component that is not installed in the
  cluster; rewriting it is forbidden. This is the only remaining HIGH, and
  it is documentation, not deployable configuration.

**Image HIGHs (16 → 10).** Post-remediation HIGH set (measured):
- CVE-2026-14456 (libcrypto3+libssl3, QUIC DoS) — fixed 3.5.8-r0 →
  **REQUIRES_BASE_IMAGE_UPDATE** to alpine3.23 (deferred; tracked)
- CVE-2026-45447 (openssl UAF PKCS7_verify) — fixed 3.5.7-r0 → same
- CVE-2026-53612/53613/53614 (util-linux mount TOCTOU/SUID) — 53612 has
  fix in 2.41.6-r0; 53613/53614 **no fix listed** →
  REQUIRES_UPSTREAM_FIX. Applicability note: the image runs as non-root
  with no SUID usage by the app; mount helpers unreachable from the
  Python process. Exploitability: UNKNOWN, compensating control = non-root
  runtime.
- CVE-2026-76642/78408/78410 (util-linux nsenter/bind-mount) — fixes
  available in 2.41.6-rx → REQUIRES_BASE_IMAGE_UPDATE (same alpine3.23
  path). Same non-root compensating context.

The remaining 2 CRITICAL-count and 6 HIGH-count delta: the 7A HIGH count
was against the old package set; the new base's newer packages carry
newer advisories. Count churn ≠ posture regression: CRITICAL went 2 → 0
and every finding now has a disposition.

## 7. Medium/Low

- Image MEDIUMs (17) and LOWs (32): majority are alpine/python packages
  with fixes available in the next base cycle → categorized
  **REQUIRES_BASE_IMAGE_UPDATE (next base review)**; pip CVEs (5 MEDIUM,
  fixes in pip 25.3+/26.x) → **REQUIRES_BASE_IMAGE_UPDATE** (pip is
  upgraded by upstream python images; app installs no packages, so pip
  findings are low-reachability — noted, not claimed as non-exploitable).
- Config 0 HIGH / 2 MEDIUM (KSV-0117 containerPort<1024, KSV-0125
  "untrusted registry" on the metrics-server doc manifest) → both in
  evidence manifests, NOT_APPLICABLE to live posture; the k3s compose
  KSV-0125 is the pinned `rancher/k3s` image — accepted practice
  (official rancher registry), disposition **ACCEPTED_RISK** (registry
  allowlisting is a 7C policy topic).
- Remaining config LOWs (capabilities.drop ALL, default-namespace,
  resourcequota): **DEFERRED** to 7C policy design — they are candidates
  for the future Kyverno-audit stage, not silent suppressions.

## 8. OpenSSL remediation

Covered in §4–5: base bump, alternatives with evidence, before/after
versions (3.3.3-r0 → 3.5.6-r0), local app test on new base, CI green
(run @ `990572e`).

## 9. KSV-0118 analysis

Covered in §6: controlled experiments, rejected false-positive theory,
additive pod-level SC, per-finding dispositions.

## 10. False positives

None declared. One initial false-positive suspicion (KSV-0118) was
investigated and **rejected by experiment** — preserved in triage doc.
No finding was suppressed via .trivyignore or similar (no suppression
config exists in the repo).

## 11. Accepted risks

- k3s image from official rancher registry flagged KSV-0125 "untrusted" —
  accepted (allowlist policy is 7C scope), compensating control: digest
  recorded at deploy time in Phase 2 docs.
- Remaining image HIGHs with fixes: accepted *temporarily* under the
  documented base-review cycle (next base bump evaluates alpine3.23) —
  NOT claimed as safe; tracked as security debt below.

## 12. SBOM and artifact identity

`b410810`: SBOM metadata now records the OCI **config digest** of the
locally built image, explicitly labeled as config-digest — distinct from
a registry manifest digest. Registry publication remains a separate
future decision (not introduced for cosmetics).

## 13–14. Secrets & image policy

Gitleaks rescan: **0 findings [M]** (before and after). Image-reference
policy: **0 violations [M]** (before and after).

## 15. Supply-chain verification

Trivy v0.70.0 retained (no scanner version change in 7B; re-verification
not required by change, advisory re-checked: malicious v0.69.4 remains
absent upstream). Local trivy binary used for controlled experiments was
checksum-verified (`52d53145…`) before use. 7A incident history preserved.

## 16. Before/after (measured, scanner output)

| Control | Before (7A) | After (7B) | Disposition |
|---|---|---|---|
| Image CVEs (total) | 52 | 59 | newer base = newer advisories; dispositions complete |
| CRITICAL | 2 | **0** | REMEDIATED (CVE-2026-31789) |
| HIGH (image) | 16 | 10 | 6 cleared; rest dispositioned (base-update/upstream) |
| Config HIGH | 3 | 1* | 2 REMEDIATED; 1 NOT_APPLICABLE (evidence doc) |
| Config MEDIUM | 4 | 6 | evidence-doc findings (metrics-server) NOT_APPLICABLE |
| Config LOW | 27 | 26 | several cleared by pod-level SC; rest DEFERRED to 7C |
| Secrets | 0 | 0 | VERIFIED both scans |
| Image policy | 0 | 0 | VERIFIED both scans |
| SBOM | present, digest empty | present + config-digest identity | improved, honestly labeled |

*the single remaining HIGH is the metrics-server manifest inside the
Tier-A experiment documentation — historical evidence, not deployed state.

## 17–19. Validation

Application: local build + run + `/health` on the new base OK; CI app
tests green. Kubernetes: helm lint/template/kubeconform green in CI for
both remediation commits. CI: all three 7B commits green — runs at
`32cf159` (docs), `990572e` (remediation), `b410810` (SBOM identity).

## 20. Failures and corrections

No new CI failures occurred in 7B (the 7A ephemeral-runner failure remains
preserved in Actions history). One analysis-level correction preserved:
the KSV-0118 false-positive hypothesis was rejected by controlled test.
One measurement correction preserved: naive table parsing undercounted
HIGHs (merged table cells) — fixed by merged-cell-aware counting; all
numbers in this report use the corrected method.

## 21–23. Git/Actions/PR evidence

Commits: `32cf159`, `990572e`, `b410810`, docs commit. No PR (direct
main, per established single-operator workflow; branch protection and CI
enforced on every push). Actions runs: green on all 7B commits; failed
run 36029393131 (7A) preserved untouched.

## 24. Repository synchronization

main == origin/main at docs commit; tree clean; no new branches; no repo
settings changed; no release/tag (7B is not a release boundary — the
artifact version stays 0.1.0; a release is proposed with 7C policy
enforcement instead).

## 25. Remaining security debt

1. Base cycle: alpine3.23 bump for CVE-2026-14456/45447/76642/78408/78410
   (5 HIGHs with fixes) — next base review.
2. util-linux CVEs without upstream fix (53613/53614) — watch upstream.
3. pip CVEs — resolved when upstream python images refresh pip.
4. Config LOWs (caps-drop, namespace, quota) — 7C policy candidates.
5. Registry-backed digest identity — future phase decision.

## 26. Controls demonstrated

Pinned bases and scanners, SHA/checksum integrity gates, non-root +
read-only rootfs + no-escalation + seccomp preserved and strengthened
(pod-level), evidence-mode scanning, honest before/after, failure and
rejected-hypothesis preservation, Git-first remediation (no live-cluster
mutation anywhere in 7B).

## 27. Controls deferred

Kyverno, signing/cosign, provenance, registry publication, blocking
thresholds, runtime security — all unchanged from 7A boundary.

## 28. Completion assessment

§38 criteria met: every Critical/High finding dispositioned with evidence;
OpenSSL remediated + rescan-verified; KSV-0118 individually validated;
scans rerun; controls intact; SBOM limitation documented and improved;
no secrets; CI reproducible and green; docs/Git/Actions synchronized.

## 29–30. Proposed Phase 7C

Policy stage, on this evidence: (1) registry allowlist policy (resolves
KSV-0125 class), (2) severity thresholds from the dispositioned baseline
(proposal: block CRITICAL-with-fix and HIGH-with-fix older than N days;
warn the rest), (3) digest-pinned deployment references, (4) Kyverno
audit-mode (report-only) for caps-drop/namespace/quota LOWs. Requires
Paul's explicit authorization of threshold numbers and whether CI flips
to blocking; signing/provenance/registry stay deferred until registry
publication is authorized as its own decision.
