# WUD Evaluation — Phase 1 (read-only findings)

**Status:** Evaluated (Phase 1); deployment decision deferred
**Scope note (master spec §18):** WUD = container image update DETECTOR. It
is not an AI migration engine and must not duplicate Renovate/CI/GitOps roles.

## What WUD would provide here

Detection of newer image versions for compose-managed containers, exposed
via API/notifications — the first stage of the spec's update workflow:
`WUD → update event → policy → (safe automation | AI queue)`.

## Phase 1 findings (read-only analysis; WUD not deployed yet)

1. **Local-build reality:** platform-demo is built locally, not pulled from
   a registry — WUD detects updates for REGISTRY images. Until artifacts are
   pushed to a registry (Phase 4 decision), WUD has nothing to watch for this
   project's containers. Recorded honestly: **WUD provides no value yet.**
2. **Coexistence constraint:** the host Docker instance is shared with 20
   protected production containers. WUD would see ALL of them. Read-only
   watching is harmless, but any future notification/webhook wiring must
   never trigger actions against containers this project does not own.
   Deployment requires: dedicated compose project, read-only docker socket
   access pattern evaluation, and explicit authorization (socket sharing is
   the main risk surface).
3. **Deterministic-fit check (spec §2/§81):** WUD is deterministic detection
   — architecturally approved in principle. The nine-question test answers:
   exists to detect drift between running image and latest available; solves
   silent image staleness; adds one small container (~50 MB); observed via
   its API; secured by least-privilege socket access; tested by simulated
   update event; removed by compose down. Verdict: **defer to Phase 4+**
   (registry existence is the prerequisite), revisit with the registry ADR.
4. **Alternative already active:** GitHub's Dependabot (enabled at repo
   creation) covers the repository-dependency side; Renovate (Phase 10) will
   consolidate. WUD covers only the runtime-image side.

## Decision

DEFER WUD deployment to Phase 4+ (requires registry). The update-detection
CONCEPT is validated and the workflow position (deterministic detector →
policy → optional AI) is reserved in the architecture. No tools were
installed during Phase 1 for this evaluation.
