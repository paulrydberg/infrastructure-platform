# Engineering Evidence Index

A navigation index for technical reviewers. Every claim below is backed
by committed material in this repository — no private history required.

## What this project is
See the repository README (architecture, current maturity, links).

## Architecture
- docs/02-architecture/, docs/00-project-origin/ (verbatim specs)
- Reconstruction architecture: docs/15-reproducibility/

## Reproducibility maturity evidence
- Contract + manifest: docs/15-reproducibility/reproducibility-contract.md,
  reconstruction-manifest.md, reconstruction-manifest.yaml (repo root)
- Runner: bootstrap/reconstruct.sh (deterministic, resource-gated)
- Level 3 (k3s layer): docs/15-reproducibility/level3-completion-record.md,
  reports/level3-final-evidence.json
- Level 4 (GitOps layer): docs/15-reproducibility/level4-completion-record.md,
  reports/level4-final-evidence.json (clean path, 20/20 PASS),
  reports/level4-failure-tests-evidence.txt (failure injection + recovery 9/9)
- Suite: bootstrap/level4-failure-tests.sh

## GitOps
- platform/argocd/ (pinned values v2.13.3, Application manifest, README
  with install/bootstrap/teardown procedures)
- Phase 5A: docs/08-gitops/completion-report-phase5a.md

## Security (Phase 7)
- docs/07-security/ (baseline, triage, remediation report, policy model,
  shadow-cycle records, policy review, hardening, enforcement activation,
  post-enforcement validation)
- Enforcement: .github/workflows/ci.yml (policy evaluation + decision
  gate) and tools/policy/ (evaluator + tests)
- ADRs: docs/decisions/ADR-0004, ADR-0005

## CI/CD
- .github/workflows/ci.yml (validate + build jobs; pinned actions)
- Failure history preserved in phase reports and Git history (e.g. the
  artifact-loss-on-blocking-gate defect: PR #3, run 36075765997,
  corrected in f1043e3 and re-proven in run 36076508779)

## Failure history (deliberately preserved)
- Docker-cp symlink trap + TLS reachability: docs/15-reproducibility/
  level3-completion-record.md + preserved reports
- Level 4 defects L4-1..L4-5, L4-FT-1..3: level4-completion-record.md
  defect table + Git history (cd19397, 339f077, 6c97f6b, fdc8abb,
  575a1cc, 018c1e3, a9e7afd, 72fba1f, da7e31d)
- Scanner incident + policy silent-PASS window: docs/07-security/

## ADRs
- docs/decisions/ (ADR-0001..0006 — foundation, naming, portfolio,
  enforcement deferral, policy simulation, post-Level-3 direction)

## Roadmap
- docs/ROADMAP-STATUS.md (complete/active/next-candidate/deferred
  phases with decision rationale)

## Phase completion records
- docs/05-kubernetes/completion-report.md, docs/08-gitops/,
  docs/07-security/phase7*-*.md, docs/15-reproducibility/*-record.md
