# ADR-0006: Post-Level-3 Architecture Direction — Next Phase Selection

**Status:** ACCEPTED (decision recorded; implementation NOT authorized by
this ADR)
**Date:** 2026-09-25
**Deciders:** Paul (authorization gate) with Hermes CTO analysis

## Context

Phase 8 completed Reproducibility Level 3: machine-readable
reconstruction manifest (v1.0.0), deterministic zero-inference runner
(`bootstrap/reconstruct.sh`), resource-gated disposable-cluster
reconstruction (12/12 PASS @ `c07a881`), failure injection with report
preservation, honest classification (DETERMINISTIC /
EXTERNAL_DEPENDENCY / STATEFUL / MANUAL). Security enforcement (Phase
7) is live and artifact-preserving. Memory is the binding local
resource (Phase 6 lesson, re-confirmed every Phase 8 run). The roadmap
numerically places AWS next, but the project's own decision discipline
requires evidence-based selection.

## Problem

What should the project build next: Level 4 reproducibility,
Infrastructure-as-Code/AWS, observability, dependency automation, or
disaster recovery? The roadmap ordering must not decide this by itself.

## Options considered

**A. Level 4 — full from-scratch GitOps rebuild inside the disposable
environment** (disposable k3s + Argo install + platform-demo deploy +
reconciliation validation, all in the ephemeral compose project).
Gap: Phase 8 validated the k3s layer end-to-end but not the GitOps
layer inside a disposable environment. Everything needed already
exists in-repo (values.yaml, application manifest, pinned versions);
the runner already has the disposable-project machinery; the resource
gate is proven. Zero new resident services, zero cloud cost, zero new
credentials (public pulls), and it converts the platform's single
biggest untested claim — "GitOps reconstructs from Git" — into
executed evidence. It also directly exercises the exception/enforcement
interaction with a real fresh rebuild.

**B. IaC/AWS (Terraform/OpenTofu, VPC, IAM, ECR, EKS).** Highest
portfolio novelty for cloud, but: real cost exposure; new credential
and security burden; state management + environment separation are new
problem classes; the local platform's GitOps layer has never been
rebuilt from scratch (so cloud parity would be claimed against an
unproven baseline); and the memory-constrained host gains nothing. The
manifest's DETERMINISTIC concepts map cleanly to IaC later — the
contract work is NOT wasted by waiting, it is strengthened by first
proving the local rebuild.

**C. Observability expansion (Prometheus/Grafana/…).** Tier A already
demonstrated swap-pressure risk from a 16–20 Mi workload; a resident
monitoring stack conflicts with the binding constraint. No current
failure has been attributed to missing observability. CI artifacts +
reconstruction reports already provide evidence-grade observability of
builds and reconstruction. Deferred; cloud-dependent variant preferred
if ever revisited.

**D. Dependency automation (Renovate/Dependabot).** Real value, but
65/65 findings are fix-listed pairs in a base-image cadence; the
exception lifecycle has never been exercised against real update churn;
and a fresh Level 4 rebuild would exercise base-image freshness more
authentically than automation would right now. Reassess after Level 4.

**E. Disaster restoration (state restore, backups).** The platform
currently holds no stateful project data (state boundary documented in
the manifest); the protected fleet's databases are out of scope by
standing constraint. DR-before-cloud is the right *ordering principle*
for later, but there is no project-state data today to restore — the
honest gap is empty by design, not unaddressed.

## Decision

**RECOMMENDED NEXT PHASE: A — Level 4 reproducibility ("full
from-scratch GitOps rebuild inside the disposable environment").**

Factual reasoning: it is the only candidate that (1) closes an
already-identified gap in the platform's own central claim
(self-reconstructing), (2) requires zero new resident services, zero
cloud cost, zero new credentials, (3) reuses proven machinery
(disposable compose project, resource gate, report format), and (4)
every later phase — IaC, cloud promotion, DR — inherits a stronger
baseline from it. "Cloud should demonstrate infrastructure engineering,
not merely add infrastructure": proving the local rebuild first is what
makes a future local→CI→artifact→staging→AWS promotion model
demonstrable rather than aspirational.

**Why not the others yet:** B multiplies managed systems before the
current one is fully proven rebuildable and adds cost/credential
burden; C violates the memory constraint for want of demonstrated need;
D is better exercised after a real fresh rebuild churns the base image;
E has no project state to restore today.

## Consequences

- Level 4, if authorized, must define its acceptance boundary exactly:
  disposable cluster from scratch → Argo CD installed from
  `platform/argocd/values.yaml` (pinned v2.13.3) → Application manifest
  applied → platform-demo Synced+Healthy from Git → validation + report
  + teardown proof, all under the existing resource gate.
- No AWS/Terraform work begins until Level 4 completes and a separate
  authorization happens; reconsideration condition for B: Level 4 done
  OR a cloud-only requirement emerges.
- Roadmap records: Phase 8 COMPLETE; Level 4 = NEXT CANDIDATE;
  AWS/IaC = DEFERRED (dependency order, not cancellation); observability
  = CLOUD-DEPENDENT/DEFERRED; dependency automation = REASSESS AFTER
  LEVEL 4; DR = FUTURE (no project-state data exists today).

## Rejected alternatives

Numerical roadmap ordering ("Phase 8 → AWS next") as a decision basis —
explicitly rejected per the project's evidence-first discipline.

---
*This ADR records an architectural recommendation. It does NOT
authorize implementation of Level 4 or any other phase; a separate
explicit authorization is required.*
