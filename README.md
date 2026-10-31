# infrastructure-platform

> A production-oriented infrastructure platform implementing Kubernetes,
> GitOps, observability, security controls, reproducibility, and automated
> operations — developed and operated in a personal development/validation
> environment, with a reproducible local-to-cloud architecture and an AWS
> deployment path on the roadmap.

![CI](https://github.com/paulrydberg/infrastructure-platform/actions/workflows/ci.yml/badge.svg)

**CI/CD:** deterministic two-job pipeline (`validate` → `build`) running on
every pull request and push to `main` — secret scan, shell/Python syntax,
Compose validation, documentation links, Helm lint/template, chart↔Compose
consistency, Kubernetes schema validation (kubeconform), container build,
real application tests, and a deterministic security policy
evaluator + enforcement gate (see [tools/policy/README.md](tools/policy/README.md) —
a `WARN` verdict is a passing run with visible findings, not a clean bill).
Controlled failure modes demonstrated via
[PR #2](https://github.com/paulrydberg/infrastructure-platform/pull/2).

## What this is

An infrastructure and platform engineering system built as a real,
operable platform — designed so it can **reconstruct itself from source**
(the machine is disposable; the source of truth is persistent) and operate
**deterministically with zero AI inference** in its core.

| Principle | Meaning here |
|-----------|--------------|
| Self-reconstructing, not self-modifying | all changes flow through Git: branch → PR → CI → policy → merge |
| Deterministic-first | the platform functions with AI disabled entirely |
| GitOps safety boundary | deployment authority lives in Git, never in ad-hoc shell access |
| Honest maturity labels | every subsystem carries Implemented/Tested/Planned status — no unearned claims |

## Environment (stated honestly)

This platform is developed and operated in a **personal
development/validation environment** on constrained shared hardware that
also runs unrelated workloads. That constraint is part of the engineering
story: resource governance, coexistence discipline, and reproducibility are
first-class concerns, not afterthoughts. Hardware/software/resource
baselines are measured and documented in
[`docs/01-discovery/`](docs/01-discovery/).

## Current status — implemented vs planned (honest)

| Capability | Status |
|-----------|--------|
| Phase 0 — Discovery and architecture baseline | ✅ Complete |
| Phase 1 — Local container foundation | ✅ Complete — v0.1.0 |
| Phase 2 — Kubernetes | ✅ Complete — k3s v1.31.2, 1.5 GiB envelope, Level 2 reconstruction |
| Phase 3 — Helm | ✅ Complete — install/upgrade/rollback/reconstruction validated |
| Phase 4 — CI/CD | ✅ Complete — deterministic GitHub Actions validation/build pipeline |
| Phase 5A — GitOps | ✅ Complete — Argo CD control loop, drift self-heal, failure/recovery |
| Phase 6 — Observability | 🔬 Capacity analysis + Tier-A metrics-server experiment completed; rolled back after a conservative resource gate; no persistent observability stack retained |
| Platform intelligence (PI-1/3/4/5) | ✅ Deterministic collector, readiness evaluator, drift detector, and evidence-bundle builder implemented and tested (ADR-0012 **ACCEPTED 2026-10-31**). PI-1 hourly snapshots **ACTIVE since 2026-10-31T03:17:01Z** (deterministic-only execution audited: stdlib-only, local read-only commands, zero inference/network). **No resident monitoring stack; no live drift detection** — scheduling and live validation remain authorization-gated where applicable. PI-2/PI-6 unlock is gated on a machine-checkable evidence-window verdict (`bootstrap/evidence_window_validator.py`), not elapsed time |
| Phase 7 — Security | ✅ Complete — CI scanning, SBOM, deterministic policy evaluation and enforcement |
| Phase 8 / Maturity Level 3 | ✅ Complete — deterministic platform reconstruction |
| Phase 8 / Maturity Level 4 | ✅ Complete — GitOps-layer reconstruction with failure injection and recovery |
| Phase 8 / Maturity Level 6 | ✅ Demonstrated — periodic resource-gated reconstruction validation; longitudinal history still accumulating |
| Phase 8 / Level 5 DR | ⏸️ Not applicable yet — no meaningful project-owned persistent state exists |
| Level 7 — Continuous reconstruction validation | 📋 Deferred — requires longitudinal Level 6 history and additional entry criteria |
| Dependency automation | 📋 Deferred — architecturally justified as a future consumer of the validation machinery; not currently authorized |
| AWS / Terraform/OpenTofu / local-to-cloud promotion | 📋 Deferred — no current demonstrated requirement |
| Persistent observability stack | 📋 Deferred — no demonstrated diagnostic need and memory remains the binding constraint |
| AI operations | 📋 Deferred — deterministic boundaries have not yet required LLM inference |
| PI-1 recurring snapshots | ✅ **ACTIVE** — hourly at :17, installed 2026-10-31 after deterministic-only execution audit; first scheduled run verified 2026-10-31T03:17:01Z; observation window started (see `docs/09-observability/pi1-scheduling-proposal.md` for contract + rollback) |
| PI-2 / PI-6 (forecast, reporting) | ⏸️ Blocked pending qualification — requires the 14-day minimum window AND machine-checked criteria (coverage ≥90%, schema-valid ≥95%, gaps ≤6 h, threshold stability) via `evidence_window_validator.py`; snapshots alone do not qualify them |
| PI-4 live drift-injection validation | ⏸️ Synthetic validation complete (29/29); live injection requires authorization |

### Recent progress (verified 2026-10-26/27 — see [docs/ROADMAP-STATUS.md](docs/ROADMAP-STATUS.md) for the evidence trail)

- **Reproducibility hardening:** historical validation comparison now diffs runner/manifest versions (tests T18/T19 — makes the Level 7 "stable comparison across a runner-version change" criterion *measurable*); evidence-freshness race fixed (AUD-2, test T20); test suite fully green (29/29) with disk-gate-aware T1/T9 assertions. Commits `1ab407f`, `cb045e6`, `3734101`.
- **CI security-gate repair:** the R2 persistence baseline could deadlock after any enforcement-gate failure; baseline selection now keys on evidence existence + re-validation via the evaluator's own validator (`39f9113` + `71cfc8b`, verified on run 40359054233: verdict WARN, 68 persistent / 0 new / 0 resolved).
- **Disk-capacity root cause identified by experiment:** the unexplained 19–31 GiB free-space swings — and the 8 consecutive scheduled-validation failures they caused — were Time Machine hourly local snapshots pinning deleted data (`2b9beac`). The 2026-10-26 cleanup restored ~57 GiB, but the Oct 28 window failed the 50 GiB gate again (13 GiB at gate time): snapshots re-pinned freed blocks and data growth re-consumed capacity. The gate was never modified. 2026-10-29 reclamation (Docker build cache 3.9 GB + 21 image tags, VM-internal ~11 GB) recovered VM-internal space; host free space remained snapshot-pinned at ~27–28 GiB pending snapshot thinning. Durable remediation not yet claimed.
- **Backup recoverability proven in isolation:** the 2026-08-03 snapshot restored into a temporary directory — 987/987 manifest checksums verified, `state.db` passes full SQLite `integrity_check`/`quick_check`, memory archive extracts cleanly. Automated backups remain **disabled** (deliberate, post-incident); reactivation awaits owner approval plus a protected `state.db` path (the SQLite online-backup `.backup` API was validated for consistent live capture).
- **Latest checkpoint:** `66e9e7e` — CI green (run 40426262572). Scheduled validation window 2026-10-28 04:17 CDT: **executed; 50 GiB capacity gate FAILED (13 GiB free); evidence record retained and verified; reboot survival NOT VERIFIED.** Next scheduled validation window: **2026-11-01 04:17 CDT**; its result will be reported as four independent facts (execution, gate result, evidence retention, reboot survival).

The roadmap's numbered phases and reproducibility maturity levels are **separate axes**. Phase 8 in the original roadmap is AWS; the current workstream also uses Phase 8 for the later reproducibility program because the roadmap evolved. See [docs/ROADMAP-STATUS.md](docs/ROADMAP-STATUS.md) and [docs/15-reproducibility/](docs/15-reproducibility/).

The authoritative capability matrix is [docs/career-evidence/capability-matrix.md](docs/career-evidence/capability-matrix.md).

## Documentation map

| Area | Path |
|------|------|
| Project origin (vision, goals, constraints) | [`docs/00-project-origin/`](docs/00-project-origin/) |
| Discovery (hardware, software, resources, GitHub analysis) | [`docs/01-discovery/`](docs/01-discovery/) |
| Architecture (system, logical, AI, reproducibility, threat model) | [`docs/02-architecture/`](docs/02-architecture/) |
| Architecture decision records | [`docs/decisions/`](docs/decisions/) |
| Repository architecture & source-of-truth | [`docs/architecture/`](docs/architecture/) |
| Career evidence (capability matrix, engineering evidence) | [`docs/career-evidence/`](docs/career-evidence/) |
| Reproducibility (contract, reconstruction manifest) | [`docs/15-reproducibility/`](docs/15-reproducibility/) |
| Roadmap status & session log | [`docs/ROADMAP-STATUS.md`](docs/ROADMAP-STATUS.md) |
| Operating instructions (per-session rules) | [`docs/OPERATING-INSTRUCTIONS.md`](docs/OPERATING-INSTRUCTIONS.md) |
| Platform-intelligence capability roadmap (PI-1…PI-8) | [`docs/09-observability/platform-intelligence-capability-roadmap.md`](docs/09-observability/platform-intelligence-capability-roadmap.md) |
| Observability architecture assessment (Phase 6) | [`docs/09-observability/observability-architecture-assessment-2026-10-30.md`](docs/09-observability/observability-architecture-assessment-2026-10-30.md) |
| PI-1 snapshot scheduling proposal (ACTIVATED 2026-10-31) | [`docs/09-observability/pi1-scheduling-proposal.md`](docs/09-observability/pi1-scheduling-proposal.md) |
| ADR-0012 platform-intelligence foundation (**ACCEPTED 2026-10-31**) | [`docs/decisions/ADR-0012-platform-intelligence-foundation.md`](docs/decisions/ADR-0012-platform-intelligence-foundation.md) |
| ADR-0012 technical review (recommendation ACCEPT, executed) | [`docs/decisions/adr0012-review-2026-10-31.md`](docs/decisions/adr0012-review-2026-10-31.md) |
| Deterministic-only execution contract (binding for scheduled paths) | [`docs/09-observability/deterministic-execution-contract.md`](docs/09-observability/deterministic-execution-contract.md) |

## Repository architecture

Single flagship repository by deliberate decision ([ADR-0001](docs/decisions/ADR-0001-project-foundation.md),
[ADR-0002](docs/decisions/ADR-0002-naming-standard.md)): additional
repositories emerge only when genuine engineering boundaries justify them
(independent lifecycle, deployment, security or state boundaries). Platform
components live here until then:

```
infrastructure-platform/
├── bootstrap/          # (Phase 1) idempotent environment bootstrap
├── applications/       # (Phase 1+) versioned container workloads
├── platform/           # (Phase 2+) kubernetes/helm/gitops definitions
├── automation/         # operational automation (deterministic-first)
├── ai/                 # (Phase 11+) OPTIONAL AI operations layer
├── policies/           # policy-as-code
├── tests/              # validation, reconstruction tests
├── scripts/            # operational scripts
├── docs/               # the engineering record
└── .github/            # CI/CD
```

(Directories appear as they gain real content — no empty scaffolding.)

## Reproducibility

Current demonstrated maturity: **Level 6 — periodically verified reconstruction (mechanism demonstrated; longitudinal history still accumulating).**

The project has demonstrated:

- **Level 1:** application/container destroy → rebuild from source.
- **Level 2:** Kubernetes reconstruction.
- **Level 3:** deterministic platform reconstruction.
- **Level 4:** GitOps-layer reconstruction from declared source through Argo CD to Synced/Healthy, with failure injection, recovery, evidence generation, validation, and teardown.
- **Level 6:** the Level 4 machinery now runs through the host's existing launchd scheduler, with resource gating, non-collapsing failure classification, evidence authority, historical comparison, drift checks, and teardown.

The post-Level-6 independent audit found and fixed **AUD-1**, a stale runner-report inheritance defect that could have allowed an old report to influence a run that did not produce its own report. The periodic-validation test suite is now **22/22**, alongside **11/11** report-authority tests.

Level 6 is deliberately qualified: the **mechanism is demonstrated**, but longitudinal confidence is still being earned. As of the day-29 review (2026-10-26) the evidence window covers **4.17 weeks / 18 scheduled-window records (6 PASS / 10 FAIL / 2 BLOCKED; 37.5% PASS excluding BLOCKED)** — including 8 consecutive FAILs (Sep 30–Oct 24) caused by the host's own 50 GiB free-disk prerequisite gate tripping on real disk pressure. The gate functioned correctly throughout; the threshold was never modified. The host disk was recovered on 2026-10-26 and qualifying history accumulation resumes at the next scheduled window (2026-10-31 04:17 CDT), which also provides the natural post-reboot evidence-survival test. The next step is therefore to let the existing validation mechanism accumulate qualifying history rather than immediately adding Level 7 or another platform subsystem.

Level 5 disaster recovery is currently **not applicable** because the project has no meaningful project-owned persistent state requiring restoration. Level 7 continuous validation remains deferred pending measurable entry criteria.

The machine is disposable; the source of truth is persistent. Validation evidence is historical evidence rather than authoritative infrastructure state. Current limitations include local-only evidence retention, a declared local production-kubeconfig dependency for live fleet checks, and heuristic historical comparison.

See:
- [docs/15-reproducibility/level6-completion-record.md](docs/15-reproducibility/level6-completion-record.md)
- [docs/history/post-level6-audit.md](docs/history/post-level6-audit.md)
- [docs/history/engineering-evidence-index.md](docs/history/engineering-evidence-index.md)
- [docs/15-reproducibility/reconstruction-manifest.md](docs/15-reproducibility/reconstruction-manifest.md)

## License & attribution

See [LICENSE](LICENSE).
