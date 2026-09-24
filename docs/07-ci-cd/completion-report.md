# Phase 4 Completion Report — Deterministic CI/CD

**Status:** COMPLETE (2026-09-24) — CI green on main, both controlled failure
modes demonstrated, branch protection API-verified. STOPPED at Phase 4 → 5
boundary.

## CI architecture & execution flow (objective 12)

**Provider:** GitHub-hosted `ubuntu-latest` runners — deterministic, pinned
tool versions, zero CI load on the resource-constrained Mac Mini (the Mini
hosts only the repository; its k3s/compose stack is never a CI dependency).

```
push to main / PR opened / tag v*
        ↓
checkout (actions/checkout @ pinned SHA 11bd7190… v4.2.2)
        ↓
validate job (parallel-safe, ~30–60s):
  secret-pattern scan → shell syntax → python compile →
  compose config validation → doc-link resolution →
  helm install (checksum-gated) → helm lint (committed chart) →
  helm template render + YAML/kind assertion →
  chart/image consistency (chart tag == compose tag; no floating refs) →
  kubeconform strict schema validation (pinned v0.8.0, checksum-gated)
        ↓ (only if validate passes)
build job:
  docker build platform-demo:0.1.0 from repo source →
  application tests: /health payload assertions (status ok, version 0.1.0)
  + stop/start lifecycle → rendered-manifest artifact (7-day retention)
```

**Check matrix (objective 13):**

| Trigger | What runs |
|---------|-----------|
| pull request | full validate + build (PR #2 exercised this path) |
| push to main | full validate + build |
| tag `v*` | full validate + build (release tagging triggers the same gates; no deploy) |

## Which failures were demonstrated (objectives under Testing requirements)

| # | Injected failure | Observed CI behavior |
|---|------------------|---------------------|
| 1 | Invalid Helm template (nonexistent helper) on PR #2 | `helm lint` FAILED with precise template error; `build` job correctly SKIPPED (run 35985620959) |
| 2 | Broken application health assertion (expects NOT-OK) | validate passed; **build** failed at `health payload wrong` with the actual JSON printed — proving the test tests the app (run 35985792757) |
| 3 | Restored valid state | CI returned green (final state on main) |

Evidence preserved: PR #2 (closed, unmerged — state verified via API:
`CLOSED, merged=never`) + immutable Actions run logs. No history rewriting;
test branch deleted only after closure (evidence lives in PR + run records).

## Security & supply-chain (objectives 14–16)

- Third-party actions pinned to **immutable commit SHAs**: checkout
  (11bd7190…, v4.2.2), upload-artifact (6f51ac03…, v4.5.0) — documented inline
- helm + kubeconform binaries **checksum-gated** at install (official
  project checksums; kubeconform v0.8.0 SHA256 pinned in workflow)
- Least-privilege: workflow `permissions: contents: read` only
- **Zero secrets used** — nothing to store in GitHub secret storage
- No floating images anywhere; platform-demo pinned strategy enforced by CI
  itself (chart tag == compose tag check; floating-ref grep gate)

## Honest failures during CI development (recorded, fixed via normal commits)

1. **Wrong hardcoded checksum:** I initially pasted the darwin-arm64 checksum
   for the linux tarball — caught by reasoning about the runner platform
   before push, but the deeper fix was: fetch the official `.sha256sum` for
   the exact pinned version instead of hardcoding (single source of truth).
2. **Checksum verification filename mismatch (CI run failure):** `.sha256sum`
   names the original tarball, CI saved it as `/tmp/helm.tgz` → `shasum -c`
   failed "No such file or directory". Fixed by direct digest comparison.
   (Commit d17482f)
3. **kubectl dry-run rejected:** `--dry-run=client --validate=strict` still
   requires API-server OpenAPI (connection refused on runner). Replaced with
   **kubeconform v0.8.0** (checksum-pinned) validating offline against
   upstream Kubernetes schemas — verified locally first (2 resources, 0
   invalid). (Commit ab97a4c)

## Branch protection / enforcement (objectives 10–11)

- Protection verified **via GitHub API, not assumed**:
  `required_linear_history=true, allow_force_pushes=false,
  allow_deletions=false`
- PR #2 demonstrated the PR path executes identical validation before merge
- Architectural boundary honored: CI validates and builds; **nothing deploys
  automatically** — `Git commit → CI validation → artifact/build validation`
  only. GitOps = Phase 5.

## Resource discipline

Zero Mac Mini resources consumed by CI (GitHub-hosted runners); local k3s
untouched (k3s still running at ~460 MiB, envelope intact); protected
workloads unaffected (no restarts/OOMs at any point during Phase 4).

## Remaining notes

- Release/tag runs use the same validation+build pipeline; image publishing
  to a registry is deliberately absent (Phase 4 scope; registry = Phase 4+
  follow-on per master spec §23 publish step, to be proposed at the next gate)
- The rendered-manifest artifact provides inspectable evidence of exactly
  what the chart produces per commit

**STOPPED at the Phase 4 → Phase 5 boundary.** GitOps/Argo CD not begun —
requires separate authorization.
