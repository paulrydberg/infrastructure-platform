# Operating Instructions — infrastructure-platform

> **Binding rules for every session working on this project.**
> These derive from the verbatim prompts in `docs/00-project-origin/` and
> Paul's standing instructions. If a prompt conflicts with this file, the
> verbatim prompt wins and this file gets updated.

---

## 1. Documentation Discipline (standing instruction)

- Every prompt Paul gives about this project is saved **verbatim** under
  `docs/00-project-origin/` (MASTER spec → Amendments → Clarifications).
- `docs/PROMPTS.md` is updated with a dated entry for every prompt.
- `docs/ROADMAP-STATUS.md` is updated after every session: phase tracker,
  amendment workstream, milestone checklist, session log.
- The verbatim prompts collectively ARE the project roadmap baseline.

## 2. Repository Architecture Discipline (Clarification 1 + Amendment 2 + ADR-0002)

- Amendment 1's repository model is an **architectural target and evaluation
  framework — NOT a build list.** Amendment 2's professional naming list is a
  NAMING STANDARD ONLY — never a creation mandate.
- **Never** create or migrate a repository merely to satisfy a name in
  Amendment 1/2. Boundaries must be earned through the split criteria
  (Amendment 1 §31) and documented in an ADR. Every split ADR applies the
  Phase 0 boundary criteria.
- Hobby-context public names are prohibited (homelab-*, incident-lab,
  my-devops-project, cloud-learning-project, ai-remediation-engine).
  Use the professional engineering-function name from the adopted standard.
- Positioning rule: describe the ENVIRONMENT honestly (personal
  development/validation environment); name the SYSTEM by its engineering
  function. Portfolio priority order: correctness → reliability → security →
  reproducibility → maintainability → operational usefulness → architecture
  clarity → documentation quality → engineering history → portfolio visibility.
- **Never** manufacture GitHub activity (commits, issues, PRs, incidents,
  releases, project history) for portfolio purposes.
- The portfolio must emerge from genuine engineering work.
- The Phase 0 conclusion is authoritative: monorepo → hybrid evolution;
  repositories split only when engineering boundaries justify the split.

## 3. Deterministic-First Discipline (master spec §3)

- The platform must function with zero LLM inference.
- AI is an optional, resource-governed escalation layer — never a hidden
  dependency of infrastructure, GitOps, CI/CD, monitoring, or recovery.

## 4. Honesty Discipline (master spec Rules 13/14/21/22; Amendment 1 §23)

- Never fabricate test results, maturity levels, or deployment claims.
- Documentation distinguishes: Implemented / Tested / Experimented With /
  Designed / Planned / Not Yet Implemented.
- No rewriting history to make the project look cleaner.

## 5. Authorization Gates (standing instruction + Clarification 1)

- **Phase 0 discovery is READ-ONLY**: inventory and document only.
  Install nothing, modify nothing, create no repositories, no GitHub writes
  until Paul explicitly authorizes.
- One authorization gate at a time. Stop at decision gates; once authorized,
  execute the authorized scope end-to-end.
- Production services (Hermes runtime, existing containers) are never touched
  by this project without explicit, separate authorization.

## 6. Project Identity

- `project_id = infrastructure-platform` is permanent. Project identity is
  the repository, never any chat/ops session or token.
- GitHub account: `paulrydberg` (SSH). Never use credentials/tokens as
  project identity.

## 7. Secrets Discipline (master spec §26; Amendment 1 §6)

- Secrets never enter the reproducibility source. Repos contain instructions
  for obtaining/injecting secrets, not the secrets themselves.
- Never commit Terraform state or credentials. Never expose credentials to
  models or logs.
