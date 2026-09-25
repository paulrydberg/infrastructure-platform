# Project Engineering Overview

Technical orientation for reviewers. Facts only; every claim maps to
committed evidence (see engineering-evidence-index.md).

**What problem does it solve?** It demonstrates — with executed
evidence — a self-reconstructing deterministic infrastructure platform:
a Mac Mini-hosted Kubernetes environment whose entire definition lives
in Git and can be validated, rebuilt, and governed without manual drift.

**Why deterministic-first?** The platform must function with LLM
inference = 0. AI may assist humans; it is never a prerequisite for
reconstruction, enforcement, or validation. Reconstruction, policy
evaluation, resource gating, and validation are all deterministic
scripts/programs.

**How is Git the source of truth?** All infrastructure definitions
(compose, Helm charts, Argo values/Application, policies, bootstrap,
runner) live in this repo. Changes flow branch → PR → CI (including a
deterministic security-policy gate that blocks FAIL/UNKNOWN verdicts)
→ merge. Argo CD reconciles the cluster from this repo (drift
self-heal demonstrated in Phase 5A).

**How does Kubernetes/Helm/Argo fit?** k3s (single node, 1.5 GiB hard
envelope, in Docker) is the cluster; Helm packages the workload
(platform-demo, pinned image, enforced securityContext); Argo CD
(v2.13.3) provides the control loop.

**How does security enforcement work?** CI builds, scans (Trivy vuln +
config, gitleaks, SPDX SBOM), evaluates a schema-validated Trivy-JSON
policy (R1 critical-with-fix blocks, R4 rendered-manifest posture
blocks, R2/R3 warn, exceptions via a Git-tracked ledger), uploads all
evidence artifacts, and only then decides pass/fail — blocking never
destroys evidence (defect found and fixed in f1043e3; re-proven by
blocking run 36076508779).

**How does reproducibility work?** A machine-readable reconstruction
manifest classifies every component (deterministic / external /
manual / stateful). A resource-gated runner validates prerequisites,
source pin, and manifest, then builds a disposable k3s environment and
(Level 4) drives it through Argo to Synced/Healthy at the exact pinned
commit, then tears it down — producing a JSON report every run,
including on failure.

**How does resource governance affect architecture?** Memory is the
binding constraint (a 16–20 Mi metrics-server probe once induced swap
pressure). Consequences: hard k3s envelope, minimal Argo values, no
resident observability stack, resource gates before any disposable
environment, and refusal to resize Docker to make experiments pass.

**What has been demonstrated?** Phases 0–8: container foundation,
k3s, Helm (install/upgrade/rollback/recovery), CI/CD with controlled
failure evidence, GitOps with drift self-heal, full security program
(baseline → remediation → policy → enforcement, live), reproducibility
Level 3 and Level 4 (GitOps-layer reconstruction with failure testing).

**What failures occurred?** All preserved and documented: scanner
supply-chain incident (pinned + checksummed afterwards), KSV-0118
root-cause experiment, merged-cell report extraction error, silent-PASS
policy window, artifact-loss-on-blocking-gate, docker-cp symlink trap,
TLS reachability issue, Level 4 defects L4-1..L4-5 and L4-FT-1..3
(each: symptom → root cause → fix → re-validation).

**What remains intentionally deferred?** AWS/IaC (ADR-0006: prove local
reconstruction first), observability stack (memory constraint; no
demonstrated need), dependency automation (reassess after base-image
churn), state-restoration DR (no project state exists yet).

**What if the LLM is unavailable?** Nothing in the platform's
build/rebuild/govern path requires it. Inference count across all
reconstruction and enforcement runs: 0.
