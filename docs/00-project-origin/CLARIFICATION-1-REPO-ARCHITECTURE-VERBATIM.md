# CLARIFICATION 1 — Repository Architecture & Portfolio Discipline

> **CANONICAL VERBATIM RECORD — CLARIFICATION 1**
> Received via Telegram 2026-09-24, before Phase 0 begins.
> Applies to: master spec (MASTER-SPEC-FULL.md) + Amendment 1
> (AMENDMENT-1-GITHUB-PORTFOLIO-VERBATIM.md).
> Saved verbatim; no edits to prompt text. Prompt log: `../PROMPTS.md`.

---

Before you begin Phase 0, add one additional clarification to the project documentation and operating instructions:

The GitHub repository architecture described in Amendment 1 is an architectural target and evaluation framework, NOT a predetermined requirement to immediately create all of the proposed repositories.

The employment/portfolio objective is a genuine project requirement, but it must be satisfied through real engineering work rather than artificial repository fragmentation.

During Phase 0 discovery, explicitly investigate and document:

1. The current GitHub account/organization state relevant to this project.
2. Existing repositories and their current purposes.
3. The current contents and structure of "infrastructure-platform".
4. Existing Git history and development history.
5. Which components have legitimate independent lifecycle, deployment, security, ownership, reuse, or release boundaries.
6. Which components should remain in the flagship repository.
7. Which components may eventually warrant independent repositories.
8. Which proposed repositories from Amendment 1 should NOT be created, and why.
9. The proposed GitHub Projects structure and what engineering work each project would represent.
10. How issues, PRs, Actions, releases, ADRs, incidents, experiments, and documentation should relate to the repositories.
11. How a multi-repository architecture would affect reproducibility and disaster recovery.
12. How a fresh machine would discover, clone, version-lock, and reconstruct every required repository.
13. How repository boundaries should support the employment objective without creating artificial complexity.
14. What capabilities the final GitHub portfolio should visibly demonstrate to a technically competent hiring manager.
15. Which capabilities are actually demonstrated versus merely planned.

Create a formal discovery artifact such as:

"docs/01-discovery/github-portfolio-and-repository-architecture.md"

This should include:

- current state
- desired state
- repository-boundary analysis
- monorepo vs multi-repo vs hybrid analysis
- GitHub Projects strategy
- source-of-truth matrix
- cross-repository dependency model
- reconstruction implications
- portfolio/job-market considerations
- risks
- recommended architecture
- deferred decisions

Do NOT create or migrate repositories merely to satisfy the names in Amendment 1.

Do NOT manufacture GitHub activity, commits, issues, PRs, incidents, releases, or project history for portfolio purposes.

The portfolio must emerge from genuine engineering work.

The final objective is not to maximize the number of repositories. The objective is to create a GitHub presence that makes the project's actual engineering capabilities easy to inspect and understand.

Also preserve the existing authorization gate: Phase 0 discovery should remain read-only and should install or modify nothing until the appropriate authorization is given.

Once this clarification is documented, proceed with Phase 0 only when authorized.
