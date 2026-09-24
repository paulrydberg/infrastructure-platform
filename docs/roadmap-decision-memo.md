# Roadmap Decision Memo — Post-Phase-6 (2026-09-24)

**Purpose:** identify the highest-leverage next engineering phase after the
Phase 6 closeout, on engineering value and dependency order — not on
technology novelty. **No work has begun; this is a recommendation only.**

## 1. Current demonstrated capabilities (all evidence-linked)

| Capability | Level | Evidence |
|---|---|---|
| Container foundation | Tested | Phase 1, v0.1.0, kill-PID-1 recovery |
| Kubernetes (k3s, 1.5 GiB envelope) | Tested | Phase 2 A″, Level 2 reconstruction |
| Helm chart lifecycle | Tested | Phase 3 + integrity verification |
| CI/CD (deterministic, 2-job, failure-mode tested) | Tested | Phase 4, PR #2 failure demos |
| GitOps (Argo CD, drift/self-heal) | Tested | Phase 5A, permanent resident |
| Observability analysis & gating methodology | Tested (analysis + principle) | Phase 6 chain |
| metrics-server | Experimental, not retained | Tier-A experiment |
| Security tooling (Trivy/Kyverno/SBOM) | Not started | — |
| AWS/cloud | Not started | — |
| Dependency automation (WUD/Renovate) | Evaluated only | docs/04-containers |
| AI maintenance engine | Not started | Phases 11–15 prerequisite |

## 2. Phase 6 final state

CLOSED. Capacity analysis ✓, decision gate ✓, Tier-A experiment ✓ (closed
on the swap gate, classification preserved verbatim), swap-driver
characterization ✓ (residency ≠ pressure established), resource-gate
principles codified ✓. Nothing installed. See
`docs/09-observability/phase6-completion-record.md`.

## 3. What Phase 6 taught us

1. In-cluster memory was never the constraint — k3s peaked at 1.058 GiB of
   1.5 GiB with Tier A resident; ~442 MiB headroom remained.
2. Gate design matters as much as measurement: a swap-used threshold fired
   on a healthy host (cold-page residency). Resource governance must
   measure pressure and degradation, not residency
   (`resource-gate-principles.md`).
3. Estimates can be conservative: metrics-server [E] 60–100 MB vs [M]
   16–20 MiB — but Tier-B's +500–900 MB [E] is a different order of
   magnitude and must NOT inherit that comfort.
4. The honest-failure arc (estimate → gate → rollback → investigation →
   principle) is itself portfolio-grade engineering evidence.

## 4. What remains unimplemented

Phases 5B (if any), 7 (security: Trivy/Kyverno/SBOM/image policy/secret
discipline), 8–9 (AWS + local-to-cloud promotion), 10 (dependency
automation), 11–15 (AI maintenance engine, policy), 16 (platform
engineering), 17–19 (reproducibility hardening, continuous reconstruction,
final architecture). Tier B/C observability remains optional, gated.

## 5–7. Candidate next phases, dependencies, resource implications

| Candidate | Depends on | Resource impact | Fit |
|---|---|---|---|
| **Phase 7 — Security** | k3s + Helm + CI (all present) | **Minimal**: Trivy scans run in CI (GitHub-hosted) + local scan-on-demand; Kyverno policy evaluation is control-plane-light; SBOM generation is a build step | **Strong** — no resident memory cost; strengthens what exists |
| Phase 10 — Dependency automation | CI + registry discipline | Small resident (WUD/Renovate ~100–200 MB [E]) | Moderate — useful but adds a resident component |
| Tier B observability | Phase 6 analysis | +500–900 MB [E] on a shared host | Weak now — the measured environment argues against |
| Phase 8–9 — AWS | Phase 7 by dependency order (security before cloud) | External, but premature | Deferred |
| Phases 17–18 — Reproducibility/reconstruction | Broad platform maturity | Labor-heavy, not memory-heavy | Valuable later |

## 8. Risk / rollback implications

Phase 7 is naturally low-risk: CI-side scanning changes nothing resident in
the cluster; admission policy (Kyverno) can be introduced in audit mode
first with a documented rollback (delete policies); SBOM generation is an
added CI job. The protected fleet is untouched. Every element is
source-controlled and removable by manifest deletion — matching the
reproducibility principles already established.

## 9. Recommendation

**Phase 7 — Security, staged in CI-first order:**

1. **Trivy** vulnerability scanning of platform-demo images in CI
   (GitHub-hosted runners; zero local resident cost; failure thresholds
   defined before enabling)
2. **SBOM** generation (syft or Trivy's native SBOM) attached as a CI
   artifact
3. **Secret discipline** formalization (the repo already has scanning +
   push protection; document policy, add gitleaks to CI)
4. **Image policy** documentation (pinned-digest rule already practiced —
   codify it)
5. **Kyverno** admission policies on k3s — LAST, audit mode first, only
   after 1–4 are green, with the refined resource-gate principles applied
   to any measurement window

This strengthens CI/CD, security, and supply-chain discipline — the
dependency predecessor for AWS (Phase 8) — without expanding the resident
envelope, without touching the protected fleet, and with every component
reproducible from Git and removable cleanly.

**Explicitly NOT recommended now:** Tier B observability (environment
evidence against), AWS (dependency order), dependency automation (adds a
resident component before security discipline exists).

## 10. Exact authorization required to begin

Paul's explicit go-ahead for **Phase 7 — Security (CI-first staging:
Trivy + SBOM + gitleaks + image-policy codification, Kyverno deferred to a
separate gate)**, including:

- confirmation that CI-side scanning (GitHub-hosted runners) is in scope
- confirmation that Kyverno is excluded from the first authorization
- resource gates: none required for CI-side work; any in-cluster component
  later uses the refined pressure-based gate design
- hard stops: no protected-workload changes, no Docker resize, no Tier B,
  no AWS, no Ubuntu-laptop use
