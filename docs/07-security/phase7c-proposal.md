# Phase 7C Proposal — Security Policy Design (NOT implemented)

**Status: PROPOSED.** This document is a design/preparation deliverable
authorized by the Phase 7B closeout task. Nothing in it is implemented.
Phase 7C execution requires Paul's explicit authorization of the specific
increments and threshold numbers below.

## 1. Objectives

Move the platform from evidence-only security (7A) and verified
remediation (7B) toward **deterministic, minimal policy enforcement** —
without adding resident infrastructure or dependencies the current
single-cluster, single-app platform does not justify.

## 2. Current-state baseline (evidence, all [M])

- Scanner: Trivy v0.70.0 (action pinned by commit SHA), gitleaks v8.30.1
  (checksummed binary), SPDX SBOM of the built image, deterministic
  image-reference policy step — all in CI on GitHub-hosted runners
- Verified 7B state: CRITICAL 0; KSV-0118 remediated (0 HIGH on deployable
  manifests); remaining image HIGHs = 8 unique CVEs / 10 (package,CVE)
  pairs — 5 pairs (4 unique CVEs) fix-listed for the next base cycle,
  3 unique CVEs awaiting upstream; gitleaks 0; policy violations 0
- CI currently runs scanners in **evidence mode** (exit-code 0 everywhere);
  the only deterministic gates are helm/kubeconform/tests/image-policy
- SBOM records the OCI **config digest** of the local build; no registry
  manifest digest exists (no registry is used)

## 3. Candidate control A — severity thresholds (recommended first increment)

**What the scanner actually reports today:** 0 CRITICAL, 3 HIGH pairs
with fixes + 5 HIGH pairs without fixes listed, 4 MEDIUM pairs (+22
fix-listed pairs in the inherited block), LOWs. Any threshold that counted
raw HIGH totals would have blocked this pipeline on day one — that result
would be noise, not signal.

**Analysis of threshold bases:**

| Basis | Fit for this platform |
|---|---|
| Severity count alone | Poor — counts no-fix upstream items the project cannot act on; would block indefinitely |
| Fixable severity | **Good** — actionable findings only; aligns with the debt register's "next base cycle" model |
| Runtime relevance / reachability | Directionally right but not deterministic from scanner output alone; would require manual inventory — deferred until a real deployment workload exists |
| Exploitability | Not established by scanner evidence; cannot be automated honestly — excluded from CI logic |
| Environment (dev vs prod) | Single small cluster; premature |
| Exception expiration | Necessary companion to any threshold (else exceptions become permanent suppressions) |

**Recommended design (for authorization, not yet implemented):**
- **Fail CI when:** CRITICAL-with-fix > 0, or HIGH-with-fix older than a
  defined age (proposal: 30 days) without an unexpired exception
- **Warn (report) on:** CRITICAL/HIGH without listed fix; all MEDIUM/LOW
- **Exception mechanism:** `.trivyignore`-style entries only with CVE id,
  rationale, owner, and **expiry date**; CI fails on an expired exception
  (deterministic, auditable, in Git)
- Rationale: on the current baseline this policy is **green today**
  (0 CRITICAL; all fix-listed HIGHs are younger than any reasonable age
  limit and tracked in the debt register) while it would have caught the
  7A baseline's 2 CRITICALs immediately — that is the correct sensitivity

**Sequencing:** thresholds ship with report-mode shadow output for one CI
cycle before flipping exit-codes, so the policy is validated against real
finding flow first.

## 4. Registry strategy (decision analysis — decision deferred)

| | A: no registry (current) | B: GitHub Container Registry | C: AWS ECR | D: other |
|---|---|---|---|---|
| Immutable digest identity | ✗ (config digest only) | ✓ manifest digest | ✓ | ✓ |
| GitOps digest-pinning | impossible | possible | possible | possible |
| SBOM↔image binding | loose (config digest) | strong | strong | strong |
| Signing/provenance | not possible | cosign-ready | cosign-ready | varies |
| CI credentials | none needed | GITHUB_TOKEN (built-in) | AWS creds | varies |
| Cost | zero | free tier sufficient | pay-per-store | varies |
| Complexity | none | low | medium (+AWS dependency, out of order) | varies |
| Reproducibility | unchanged | improved | improved | improved |
| AWS/EKS path | N/A | acceptable | natural | acceptable |

**Recommendation:** **stay on Option A for 7C.** No current control
requires a registry: thresholds and exception policy work on scan output;
digest-pinning and signing require a registry and are therefore sequenced
AFTER the registry decision. The natural trigger for Option B (GHCR) is
the first deployment that consumes images from somewhere other than the
build host, or the AWS/EKS phase. SBOM metadata must keep describing the
config digest accurately until a manifest digest actually exists.

## 5. Digest-pinned deployment design (proposed, not implemented)

```
build → image digest (registry manifest) → SBOM → vuln scan → signing/provenance
      → GitOps manifest references digest → Argo CD → Kubernetes
```

- **Why digests matter:** tags are mutable pointers; digests are
  content-addressed — the cluster then provably runs the scanned artifact
- **Digest origin:** registry push (a manifest digest does not exist for a
  local-only build; this is the technical reason the registry decision
  gates this design)
- **Git recording:** the Argo Application/helm values carry
  `image: ghcr.io/owner/platform-demo@sha256:…` — a CI job updates the
  digest via PR, keeping a human-visible diff per promotion
- **Argo CD consumption:** unchanged architecture; k8s pulls by digest;
  drift self-heal (demonstrated ≤10 s in Phase 5A) then restores the
  exact digest
- **CI prevention of mutable tags:** extend the existing image-reference
  policy step to require `@sha256:` for deployment manifests (CI-level,
  deterministic)
- **Reproducibility:** closes the last gap between "scanned artifact" and
  "deployed artifact"
- **Required infrastructure:** registry (§4) — none of this is implementable
  today, which is why it is sequenced after the registry decision

## 6. Kyverno evaluation (proposed, not implemented)

| Check | Right home |
|---|---|
| no `:latest`, pinned/digest refs | **CI** (already enforced deterministically; admission adds defense-in-depth later) |
| required securityContext / runAsNonRoot / seccomp / no-escalation | **Admission (Kyverno audit-mode first)** — CI validates charts we write; admission covers anything that reaches the API server |
| resource requests/limits | Admission (audit-mode) |
| approved registries | Admission after the registry decision; CI lint meanwhile |
| required labels/namespace rules | CI (project convention) + admission later |

**Recommendation:** Kyverno **audit-mode only**, staged after thresholds,
on the k3s cluster, with a resource footprint measured before/after per
the Phase 6 resource-gate principles (pressure/activity, not just
residency). Enforcement mode is a separate later gate. Kyverno is
**not installed**; nothing in this proposal changes the cluster.

## 7. Signing & provenance (evaluated, deferred)

Future chain, with honest status labels:

| Chain stage | Status |
|---|---|
| source → CI → build | **implemented** (Phase 1/4) |
| SBOM of built image | **implemented** (7A) |
| vulnerability scan | **implemented** (7A), thresholds **proposed** (7C) |
| image digest (manifest) | **deferred** (requires registry) |
| signing (cosign) / SBOM attestation / SLSA provenance | **deferred** (requires registry + signing keys) |
| admission verification of signatures | **deferred** (requires Kyverno enforce + registry) |

Nothing may be described as signed or provenance-verified today; the SBOM
records a config digest, not a registry manifest digest.

## 8. Proposed minimal 7C scope (smallest useful increment)

1. **First:** severity thresholds + expiring exceptions, shadow-mode →
   enforced (CI-only, zero runtime footprint, reversible by reverting one
   workflow commit)
2. **CI-only, same increment or next:** extend image-policy step to
   explicitly reject mutable deployment references in rendered output
3. **Later, separate gate:** Kyverno audit-mode on k3s (requires cluster
   change authorization + measured resource envelope)
4. **Requires registry (deferred):** digest-pinning, signing, provenance
5. **Deferred until AWS/EKS:** ECR, cloud-native policy tooling
6. **Deferred until a real deployment workload exists:** reachability- and
   exploitability-based gating (no honest automation is possible today)
7. **Unnecessary complexity now:** multi-registry support, key management
   infrastructure, admission enforcement before audit evidence, AI-assisted
   policy decisions (see §9)

## 9. Deterministic-first principle (unchanged)

```
deterministic detection (trivy/gitleaks, pinned)
  ↓ deterministic policy (thresholds + exceptions in Git)
  ↓ deterministic validation (CI exit-codes)
  ↓ human/policy authorization (Paul gates each increment)
  ↓ Git/GitOps → deployment
```

No LLM anywhere in detection, policy, or enforcement. The platform remains
fully functional with **LLM inference = 0**; AI may later *explain*
findings but must never *decide* them.

## 10. Resource / rollback / testing impact

- Thresholds + exceptions: **zero** runtime footprint (CI-only); rollback =
  revert the workflow commit; testing = shadow-mode run over ≥1 real PR
  cycle before enforcement
- Kyverno audit-mode (later): small resident footprint on k3s — must pass
  a pre-defined resource gate (Phase 6 principles) before install; rollback
  = delete namespace/manifests via Argo
- Registry/signing (deferred): adds CI credentials surface — threat-model
  before adoption

## 11. Authorization gate

Phase 7C execution requires Paul's explicit authorization of: (1) threshold
numbers and the age rule, (2) the exception format + expiry policy, (3)
whether shadow-mode duration is acceptable, and separately (4) Kyverno
audit-mode with its resource envelope, and (5) the registry decision
(GHCR vs defer). Each is independently gateable; nothing is authorized by
this document.
