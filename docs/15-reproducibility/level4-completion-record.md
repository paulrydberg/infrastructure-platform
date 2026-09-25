# Phase 8 Level 4 Completion Record — GitOps-Layer Reconstruction

## Status

**LEVEL 4: PASS** — all 21 success criteria demonstrated. Evidence:
`docs/15-reproducibility/reports/level4-final-evidence.json` (clean-path
reconstruction: PASS, 20/20 stages, 80 s, LLM 0, source pin `6e5f3a9`)
and `reports/level4-failure-tests-evidence.txt` (failure/recovery suite:
9/9 PASS).

## Executive Summary

The platform can now reconstruct a **disposable Kubernetes environment
through the GitOps control plane**: disposable k3s from the declared
compose machinery → Argo CD installed from source-controlled values
(chart 7.7.11 → v2.13.3) → the source-controlled Application applied →
Argo reconciling the Helm-managed platform-demo **to Synced/Healthy at
exactly the pinned Git commit** → workload validated against the chart's
declared state (image, securityContext, resources, probes, service) →
GitOps teardown → whole-environment teardown → protected fleet verified
untouched. Failure behavior at both the Argo level and the application
level was tested by controlled injection and recovery proven. Zero LLM
inference throughout.

## Starting State

`6e5f3a9` chain origin; branch main; clean; CI green. Level 3 complete
(manifest v1.0.0, runner, disposable k3s validation 12/12 @ `c07a881`,
ADR-0006 identified the GitOps-layer rebuild as the next gap).

## Problem Statement / Hypothesis

Level 3 validated the k3s layer but never proved the platform's central
claim — that Argo CD, installed from the repository's declared source,
reconciles the Git-managed workload to convergence in a disposable
environment. Hypothesis: the declared source of truth (compose, values,
Application manifest, chart) is sufficient to reach and *prove*
convergence with no hidden production state.

## Architecture (actual execution flow)

Git (pinned commit) → reconstruct.sh → resource gate → disposable k3s
(separate compose project, loopback 16443→6443, --tls-san=127.0.0.1) →
helm install argo/argo-cd@7.7.11 with platform/argocd/values.yaml →
Argo Ready → ctr image import (pinned platform-demo:0.1.0) → kubectl
apply platform/argocd/application-platform-demo.yaml → Argo sync poll →
Synced+Healthy (revision == HEAD) → workload validation → GitOps
teardown → environment teardown → fleet check → JSON report.

## Source-of-Truth Integrity

**Repository-controlled:** manifest, runner, k3s compose, Argo values,
Application manifest, Helm chart, failure-test suite, validation logic.
**Explicit external:** argo helm repo (chart 7.7.11; non-OCI, version
pin is the lock — documented limitation), quay.io/ghcr Argocd images,
rancher/k3s:v1.31.2-k3s1, Docker Hub base images, GitHub (public repo —
no credentials), Docker Desktop (host software), helm/kubectl binaries
(checksum-verified Phase 3 installs). **Runtime-generated:** disposable
kubeconfig (temp dir, deleted), cluster state (no volume — dies with
teardown), reports (committed deliberately). **Operator-provided:**
none — reconstruction requires no credentials (public pulls only).
**Hidden-state answer: NO** — three hidden-state dependencies were
found (L4-1 ambient KUBECONFIG, L4-2 ambient PATH, stale disposable
state) and eliminated with guards; the suite additionally proved
recovery without any production reuse.

## Failure Tests (deterministic, disposable working-copy method)

- **B — invalid Application source path:** Argo sync status `Unknown`
  with condition "Failed to load target state: failed to generate
  manifest" — never Synced; runner semantics would FAIL.
- **C — bad image tag (Helm parameter override):** Argo health
  `Progressing` (never Healthy); degraded pods observable.
- **Recovery B:** re-apply of the known-good manifest → Synced+Healthy
  in ~11 s, deployment 1/1.
- **Recovery C:** Helm parameter removal → Synced/Healthy restored.
- **Teardown after failures:** complete; fleet untouched (verified
  pre/post every run).

## Defects Discovered (all preserved with commits)

| ID | Symptom | Root cause | Fix | Commit |
|---|---|---|---|---|
| L4-1 | fast install FAIL | ambient KUBECONFIG targeted production; helm guard refused | disposable stages pin KUBECONFIG | `cd19397` |
| L4-2 | `helm: command not found` | ambient PATH lacking ~/tools/bin | deterministic PATH + stderr capture + bootstrap helm check | `339f077` |
| L4-3 | validator 0/0 race | sampled non-terminal state | bounded readyReplicas wait | `6c97f6b` |
| L4-4 | validator 0/0 false FAIL | `"deploy platform-demo"` as one argv item → rc=1 silently mapped to empty cluster | proper argv splitting | `fdc8abb` |
| L4-5 | successful run wrote NO report | shell-assembled JSON broke on quotes/commas/newlines | TSV + python csv escaping | `575a1cc`, `6e5f3a9` |
| stale-guard | compose reused leftover container/port | no pre-start cleanliness check | stale guard + guard in suite | `018c1e3` |
| L4-FT-1 | suite ran against wrong paths | `dirname $0` without `/..` | repo-root resolution + fatal setup abort | `a9e7afd` |
| L4-FT-2 | 300 s "never Ready" abort | transient k3s cert/kubeconfig mismatch at boot; poll asserted node-line not API success | poll requires successful API round-trip | `72fba1f` |
| L4-FT-3 | compose up raced port release | teardown→create race on 16443 | port-free wait + compose retry | `da7e31d` |

Helm's release-ownership guard deserves note: when L4-1 pointed the
install at production, helm *refused to mutate it* — the failure mode
was safe by design, and the suite proves the disposable environment is
never the production one.

## Resource Impact

Resource gate evaluated before every disposable start (free 73–76%,
swap 1032–1355 MB, requirement ≈1536 MiB; never bypassed). Disposable
cluster lived 80 s (clean run); swap usage *fell* over the session
(1329→1032 MB); production k3s steady ~932 MiB / 1.5 GiB; protected
fleet up and healthy throughout (17 h+ uptimes). No Docker resize, no
new resident services.

## Security Impact

Phase 7 enforcement untouched (`ci.yml` unchanged this phase). No
secrets required or committed (public repo + public pulls; kubeconfig
ephemeral, deleted on teardown). All image references pinned. The
failure tests exercised Argo's own error handling — the GitOps layer
*rejects* invalid source and never fakes health.

## Local vs CI Validation Boundary

- **Local (Mac Mini, required):** everything dynamic — k3s/Argo
  reconstruction, reconciliation, failure injection (privileged
  k3s-in-Docker; GitHub runners cannot host this safely/economically).
- **GitHub CI (hosted):** static validation of all committed artifacts
  (YAML/shell syntax, helm lint/render, kubeconform, image-reference
  policy, security scans, enforcement gate) — run green at each commit.
- **Static:** manifest schema/order, report schema, documentation
  links. This boundary is documented deliberately: CI did not run the
  dynamic reconstruction.

## What Level 4 Does NOT Prove

No physical-host DR; no project-state restoration (none exists —
documented boundary); no cloud/EKS reconstruction; no Level 5–7; no
offline reconstruction (github.com required); no arm64 portability
(untested); k3s privileged-in-Docker remains a documented constraint.

## Future Candidates (not begun)

Dependency automation reassessment (base-image churn now observable via
fresh rebuilds), IaC/AWS (per ADR-0006 sequencing), DR/state-restoration
design (ADR-0013 candidate), Level 5 = tested DR (requires actual state
to restore).

## Final State

HEAD `da7e31d` == origin/main · clean · CI green · enforcement ACTIVE ·
protected fleet healthy · disposable environment torn down · evidence
committed (`level4-final-evidence.json`, `level4-failure-tests-evidence.txt`)
· LLM inference 0.
