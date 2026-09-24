# Project Prompt Log — infrastructure-platform

> Durable record of every prompt Paul has given regarding this project.
> Format: chronological, with date, summary, and pointer to the verbatim copy.
> Verbatim originals live in `docs/00-project-origin/`.

---

## PROMPT 1 — Master Project Specification

- **Date received:** 2026-09-24 (Telegram, DM with Paul)
- **Status:** ✅ Saved verbatim
- **Verbatim copy:** `docs/00-project-origin/MASTER-SPEC-FULL.md`
- **Role:** Canonical high-level overview + baseline roadmap. Sections 0–94.
- **Summary:** Master specification for a reproducible, cloud-native
  infrastructure & platform engineering platform (Mac Mini → AWS). Key
  pillars: self-reconstruction as a first-class requirement, deterministic-first
  architecture (zero-inference operation mandatory), AI as optional
  resource-governed escalation layer, GitOps safety boundary, reproducibility
  maturity model (Level 0→7), staged 19-phase development order (Phase 0
  Discovery first), documentation-as-first-class-system.
- **Project ID inferred from this prompt:** `infrastructure-platform` (§54
  names it as the preferred flagship repository name).
- **First milestone (§92):** documented, version-controlled, reproducible
  engineering foundation — NOT "install Kubernetes".

## PROMPT 2 — GitHub Repository Architecture & Portfolio Amendment

- **Date received:** 2026-09-24 (Telegram, DM with Paul)
- **Status:** ✅ Saved verbatim
- **Verbatim copy:** `docs/00-project-origin/AMENDMENT-1-GITHUB-PORTFOLIO-VERBATIM.md`
- **Role:** Additive amendment to the master spec. Sections 1–53.
- **Summary:** Makes the project serve a dual purpose: real engineering system
  + professional GitHub portfolio (portfolio must never compromise engineering).
  GitHub = first-class engineering surface. Repository architecture is an
  explicit design decision (candidates: infrastructure-platform flagship,
  infrastructure-as-code, platform-engineering, operations-automation,
  observability-platform, security-platform, ai-operations). Requires
  repository source-of-truth matrix, cross-repo dependency model, Platform
  Reconstruction Manifest, GitHub Projects/Actions/labels/releases strategy,
  honest maturity labels, portfolio gap analysis, and ADR-0011 (repository
  architecture). §53 lists the immediate next-step assessment actions.
- **Key constraint:** "Do not build for resume keywords" (§37); monorepo vs
  multi-repo must be an earned ADR decision (§31–32, §46, §49).

## PROMPT 3 — Clarification 1: Repository Architecture & Portfolio Discipline

- **Date received:** 2026-09-24 (Telegram, DM with Paul), pre-Phase 0
- **Status:** ✅ Saved verbatim
- **Verbatim copy:** `docs/00-project-origin/CLARIFICATION-1-REPO-ARCHITECTURE-VERBATIM.md`
- **Role:** Operating clarification on Amendment 1. Binding from now on.
- **Summary:** Amendment 1's repo model is an architectural TARGET and
  evaluation framework, not a requirement to create all proposed repos.
  Portfolio objective is real but must be satisfied by genuine engineering
  work, never artificial repository fragmentation or manufactured activity.
  Adds a 15-point Phase 0 discovery investigation (GitHub account state,
  existing repos, boundary analysis, reproducibility implications, fresh-machine
  reconstruction across repos, demonstrated-vs-planned capabilities) producing
  `docs/01-discovery/github-portfolio-and-repository-architecture.md` with 12
  required sections. Explicit DO-NOTs: no repos for name's sake, no fake
  commits/issues/PRs/incidents/releases. Phase 0 stays read-only until
  authorized.

## PROMPT 4 — Authorization to Proceed into Phase 0

- **Date received:** 2026-09-24 (Telegram, DM with Paul)
- **Status:** ✅ executed within scope
- **Scope granted:** full Phase 0 discovery (15 investigation areas), read-only,
  all constraints (no installs, no repo creation, no GitHub writes).
- **Summary:** "Begin Phase 0… authorized to proceed with the complete Phase 0
  discovery exactly as currently defined… At the end of Phase 0, produce a
  comprehensive discovery report… Do not proceed into implementation merely
  because discovery identifies an obvious next step. Stop at the Phase 0
  authorization boundary and report the findings."
- **Result:** Phase 0 complete — discovery report at
  `docs/01-discovery/discovery-report.md`; full artifact set created;
  stopped at the boundary; awaiting Phase 1 authorization (repo creation +
  visibility decision + Phase 1 implementation scope).

## PROMPT 5 — Amendment 2: Professional Repository Naming Standard & Positioning

- **Date received:** 2026-09-24 (Telegram, DM with Paul), post-Phase 0
- **Status:** ✅ Saved verbatim + fully integrated (documentation-only; no
  repositories created/migrated/renamed/published — boundary preserved)
- **Verbatim copy:** `docs/00-project-origin/AMENDMENT-2-NAMING-STANDARD-VERBATIM.md`
- **Role:** Naming convention + employment-portfolio positioning. Operates
  WITHIN the Phase 0 architecture (monorepo → hybrid; boundary rule intact).
- **Summary:** Preferred professional names (infrastructure-platform,
  infrastructure-as-code, container-platform, deployment-platform,
  observability-platform, security-platform, operations-automation,
  incident-management, ai-operations); hobby-context public names prohibited.
  Candidate evolution (flagship + IaC + ops-automation + ai-operations) is
  NOT a commitment. Positioning: environment = personal dev/validation
  (honest); system = professionally named engineering platform; claims only
  where substantiated. 10-level portfolio quality order.
- **Documentation produced per its Required Documentation section:**
  `docs/architecture/github-repository-architecture.md`,
  `docs/architecture/repository-source-of-truth.md`,
  `docs/career-evidence/capability-matrix.md`,
  `docs/career-evidence/engineering-evidence.md`,
  `docs/decisions/ADR-0002-naming-standard.md`
- **Recorded in:** PROMPTS.md (here), ROADMAP-STATUS.md, project.json,
  docs/00-project-origin/, OPERATING-INSTRUCTIONS.md

## PROMPT 6 — Phase 1 Authorization (Repository Creation + Container Foundation)

- **Date received:** 2026-09-24 (Telegram, DM with Paul)
- **Status:** ✅ executed in full; stopped at Phase 1→2 boundary
- **Scope granted:** create PUBLIC repo `paulrydberg/infrastructure-platform`
  (with pre-push secret/sanitization rules, .gitignore, security boundary,
  honest implemented/planned distinction, no manufactured history); then
  execute Phase 1 per existing scope/exit criteria.
- **Not authorized (respected):** touching production containers, destructive
  host changes, extra repos, AWS, premature Kubernetes, GPU/local-LLM.
- **Result:** repo created public + protected + security features verified
  (ADR-0003); Phase 1 implemented (platform-demo 0.1.0, bootstrap validation,
  CI gates); PR #1 CI-green merged; v0.1.0 tagged + released; completion
  report at `docs/03-foundation/completion-report.md`. Awaiting Phase 2
  authorization.

## PROMPT 7 — Phase 2 Evaluation Authorization

- **Date received:** 2026-09-24 (Telegram, DM with Paul)
- **Status:** ✅ evaluation complete; STOPPED before implementation per stop condition
- **Scope granted:** 19-point read-only/design evaluation; Docker VM change
  explicitly NOT authorized; k3s install NOT authorized; measurements over estimates.
- **Result:** measured protected-workload baseline (21 containers, ~2.4 GiB in
  VM, 17/20 unlimited-cap risk, VM ~4.5–5 GiB free); k3s selection experiment;
  resource-negotiation report with Option A (capped k3s container, NO Docker
  Desktop change — recommended) vs Option B (VM resize — not recommended now);
  5 explicit rejection conditions; rollback = one compose down. Alternatives
  preserved, decision deferred to Paul. Docs: `docs/05-kubernetes/` (4 docs).
  Awaiting authorization for Phase 2 implementation + option choice.

---

## Standing Instructions (from Paul, pre-prompt)

- Save every prompt **verbatim** as the project's high-level overview / goals.
- Maintain markdown documentation of all prompts given for this project.
- After each session/prompt, update where we are on the roadmap (the prompts
  collectively ARE the roadmap) — see `docs/ROADMAP-STATUS.md`.
- Infer the project ID from the prompt itself (done: `infrastructure-platform`).
