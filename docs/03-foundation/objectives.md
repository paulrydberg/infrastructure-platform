# Phase 1 — Local Container Foundation

**Status:** In progress (authorized 2026-09-24)
**Scope:** master spec §79 Phase 1 + initial-roadmap.md Phase 1 entry
**Boundary:** coexisting production containers/launchd services remain OUT OF SCOPE; no Kubernetes in Phase 1; no AWS; no new repositories

## Objectives

1. Establish the reproducible container foundation: a first versioned
   container application with compose orchestration, health checks, logging,
   and documented lifecycle (build/start/stop/restart/recovery).
2. Establish the idempotent bootstrap skeleton that will grow per phase.
3. Establish CI (docs + config validation) as the first GitHub Actions evidence.
4. Update detection: evaluate WUD (read-only monitoring posture first).

## Deliverables

- [ ] `bootstrap/bootstrap.sh` — idempotent prerequisite validation
- [ ] `applications/platform-demo/` — first versioned container app
      (Dockerfile + compose + healthcheck + resource limits)
- [ ] Lifecycle test evidence (build/start/stop/restart/recovery recorded)
- [ ] CI workflow (docs lint + compose config validation)
- [ ] docs/03-foundation/ + docs/04-containers/ phase documentation
- [ ] WUD evaluation note (read-only findings)
- [ ] Completion report with intended vs actual state

## Exit criteria (from initial-roadmap.md)

- Fresh clone → bootstrap → demo app healthy, with **zero undocumented
  manual steps** (measured, reported honestly)
- App lifecycle: build/start/stop/restart/recovery all pass, recorded
- CI green on main
- Reproducibility Level 0 → 1 transition recorded
- Resource limits in place; coexisting workloads untouched (verified)
