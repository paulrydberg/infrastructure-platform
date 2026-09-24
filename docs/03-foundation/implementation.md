# Phase 1 Implementation — Local Container Foundation

**Status:** Implemented (2026-09-24)

## What was built

### 1. platform-demo 0.1.0 (applications/platform-demo/)

The project's first versioned container application — deliberately minimal,
existing to prove the platform lifecycle deterministically:

- Base image pinned: `python:3.12-alpine3.20` (immutable-artifact principle, spec §15)
- Non-root user (`app`), stdlib-only Python (no dependencies to drift)
- Endpoints: `/health` (container healthcheck), `/ready`, `/` (metadata)
- Compose orchestration (`compose.yaml`): project `infrastructure-platform-demo`,
  port 8081→8080, restart policy `unless-stopped`, log rotation (5m×3),
  `no-new-privileges`, **explicit limits: 0.5 CPU / 128 MB** (coexistence
  discipline — cannot starve protected workloads)

### 2. Bootstrap validation (bootstrap/bootstrap.sh)

Idempotent 10-check validation: host/arch, git/docker/compose/jq/gh presence,
engine reachability (+ protected-container count report), disk floor,
secret-pattern scan. **Validates, never mutates** — installation remains an
authorization-gated human step (spec §32 posture). Run twice → identical
results (idempotence demonstrated).

### 3. CI (.github/workflows/ci.yml)

Deterministic gates on every push/PR: secret-pattern scan, shell syntax,
python compile, compose config validation, relative doc-link resolution.
Dry-run locally first; two real bugs caught and fixed before push
(self-matching scan pattern; non-portable realpath). CI green on PR #1.

### 4. Repository establishment (per Phase 1 authorization)

- `paulrydberg/infrastructure-platform` created PUBLIC (ADR-0003)
- Pre-push sanitization verified (no IPs/emails/private names/secret patterns)
- Branch protection: linear history, no force-push, no deletion
- Secret scanning + push protection + Dependabot enabled (API-verified)
- Real workflow exercised: branch → PR #1 → CI green → merge → tag → release

## Test evidence (all executed, all passing)

| Test | Result |
|------|--------|
| compose config validation | PASS |
| build | PASS |
| start + healthcheck wait | PASS (healthy) |
| /health, / endpoints | PASS (200 + correct JSON) |
| docker logs capture | PASS |
| restart | PASS |
| kill PID 1 → self-recovery (12s) | PASS — restart policy healed it |
| stop / start-again | PASS |
| **destroy (image+network) → rebuild from source only** | **PASS** |
| bootstrap idempotence (×2) | PASS |
| coexistence count before/after | 20 protected untouched (total 21 with ours) |
| CI on PR | PASS (run 35979401280) |

## Deviations from plan

None material. One recorded learning: CI gates were dry-run locally and two
defects were found and fixed BEFORE the first remote run — the first green
CI run was earned, not lucky.

## Manual interventions required for a fresh machine

`git clone`, then `bootstrap/bootstrap.sh` (validate), then
`docker compose up -d --build --wait`. If prerequisites are missing, the
bootstrap reports exactly what — installation itself is deliberately not yet
automated (documented technical debt, spec §32 classification: missing
automation feature, deferred to Phase 2+ bootstrap work).
