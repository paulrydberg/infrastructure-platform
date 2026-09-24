# GitHub Portfolio & Repository Architecture — Phase 0 Discovery

**Status:** Implemented discovery (read-only, 2026-09-24)
**Mandate:** Clarification 1 (15-point investigation) + Amendment 1 §53
**Constraint honored:** no repos created/migrated, no GitHub writes performed

---

## Part A — CURRENT STATE (measured)

### A.1 GitHub account state (Investigation point 1)

| Item | Finding |
|------|---------|
| Account | `paulrydberg`, personal account, **no organizations** |
| Auth | `gh` 2.92.0, SSH protocol, token scopes: repo, workflow, read:org, admin:public_key, gist, user |
| Total repositories | **135** non-fork repositories |
| Public | **2** (`temporal-rag-framework`, `frequency-set-audio-generator`) |
| Private | 133 |
| Profile README repo | **does not exist** (`paulrydberg/paulrydberg` not found) |
| Public repo activity | public repos last updated 2026-05-07 and older |
| Resume-adjacent repo | 1 private resume website repository (name withheld) |

**Honest assessment:** the account is active but effectively invisible —
133/135 repos are private, so a hiring manager sees an essentially empty
profile. The portfolio objective therefore requires a deliberate public
strategy, which is a later decision (see deferred decisions).

### A.2 Existing repositories and purposes (Investigation point 2)

Sampled inventory (all measured via `gh repo list`):

- **Ops/agent-related:** several private ops/agent repositories (names withheld from public record)
- **Web/product work:** numerous private web/application repositories
- **Trading/finance:** several private trading repositories
- **AI/research:** a small number of AI/research repositories, incl. 2 public
- **Personal:** several personal/private repositories (names withheld from public record)

**No repository named `infrastructure-platform` exists** (verified via
`gh repo view` — "Could not resolve to a Repository"). The name is available.

### A.3 Current "infrastructure-platform" contents (Investigation point 3)

The local project directory `~/.hermes/projects/infrastructure-platform/`
contains **documentation only** (7 files: verbatim specs, operating
instructions, prompt log, roadmap, project.json). It is:

- **NOT a git repository** (verified: `git status` → "fatal: not a git repository")
- **NOT on GitHub**
- The only engineering artifact so far is the documentation set itself.

### A.4 Git history / development history (Investigation point 4)

- This project: **no git history exists yet** — nothing to preserve or migrate.
- Host-level: no infrastructure-as-code repositories found on the host for the
  shared platform services (Hermes stack predates this project; its
  reconstruction state is out of scope per constraints.md).
- Implication: **greenfield.** There is no existing repository structure to
  restructure, which removes the Amendment 1 §49 migration path entirely —
  the repo architecture decision is a pure design decision, not a migration.

---

## Part B — ANALYSIS

### B.1 Repository boundary analysis (Investigation points 5–8)

Applying Amendment 1's legitimate-boundary criteria to the components this
platform will actually have, at its actual scale (one operator, one host,
one cluster):

| Candidate repo (Amendment 1 §4) | Independent lifecycle? | Independent deployment? | Security boundary? | Verdict |
|---|---|---|---|---|
| infrastructure-platform (flagship) | n/a — the platform itself | — | — | **CREATE (when authorized)** — everything starts here |
| infrastructure-as-code | Not yet — no cloud infra exists until Phase 8 | No | No | **DO NOT CREATE NOW** — premature; single operator, no state boundaries. Revisit at Phase 8 via ADR |
| platform-engineering | No — charts/manifests evolve with the platform | No | No | **DO NOT CREATE** — belongs in flagship; splitting YAML from its context harms reproducibility |
| operations-automation | No — scripts validate the platform they live with | No | No | **DO NOT CREATE** — keep in flagship; split only if reusable value emerges |
| observability-platform | No | No | No | **DO NOT CREATE** — dashboards/rules are platform-coupled |
| security-platform | No — policies enforce on the same cluster | No | YES (potential) — but policy enforcement (Kyverno) must deploy WITH the cluster; separation would weaken, not strengthen, enforcement | **DO NOT CREATE** — revisit only if a genuine security-boundary need emerges |
| ai-operations | Eventually plausible — AI queue/workflows have a genuinely distinct lifecycle and are deliberately optional | No | No | **DEFER** — the strongest future split candidate; decide at Phase 11 via ADR |
| application-a/b/c | Yes — that is their nature | Yes | Yes | **CREATE WHEN REAL APPLICATIONS EXIST** — never fabricated |

**Rationale (Investigation point 8 — what NOT to create and why):** every
proposed non-flagship repo currently fails the Amendment 1 §31 checklist
(no independent lifecycle, no independent CI, no independent deployment,
no reusable value yet, separation would complicate reconstruction). At
solo-operator scale, multi-repo overhead (cross-repo version locks, multi-PR
atomicity loss, split CI) is pure cost with zero portfolio gain — a single
coherent, well-documented flagship repository demonstrates MORE engineering
maturity than seven half-empty ones.

### B.2 Monorepo vs multi-repo vs hybrid (Investigation point 9 → Amendment 1 §32)

| Option | Pros for this project | Cons | Assessment |
|--------|----------------------|------|------------|
| **Monorepo (flagship only)** | atomic changes; trivially complete reconstruction manifest (one clone = everything); single CI history; simplest fresh-machine bootstrap; honest at current scale | less "organizational" look; mix of concerns as platform grows | **RECOMMENDED for Phases 1–7** |
| Multi-repo (Amendment 1 §4 full set) | realistic org modeling; independent permissions | overhead with zero boundary justification today; reconstruction requires orchestrating 7 clones; risks exactly the artificial fragmentation Clarification 1 forbids | rejected for now |
| **Hybrid** | flagship now; extract ai-operations and/or application repos when real boundaries emerge | requires discipline to keep reconstruction manifest accurate across repos | **RECOMMENDED TARGET STATE** — extraction is an earned, ADR-gated evolution |

**Recommendation:** start monorepo (`infrastructure-platform`), plan for
hybrid extraction at genuine boundaries (first candidate: ai-operations at
Phase 11; then application repos when real applications exist). This is a
recommendation for ADR-0011 — the ADR itself is created when the repo is
authorized, keeping one authorization gate.

### B.3 GitHub Projects & engineering-workflow analysis (Investigation points 9–10)

- **Current:** no projects, no labels, no workflow config anywhere for this
  project (nothing exists yet).
- **Recommendation:** ONE project board ("Infrastructure Platform") tied to
  the flagship repo — not the eight-project structure sketched in Amendment 1
  §16, which presupposes the multi-repo layout we are rejecting. Additional
  boards (if ever) only when their repositories exist.
- Labels: adopt Amendment 1 §29 taxonomy but start minimal (area:*, type:*,
  priority:*) — add only as real work demands.
- Workflow: Issue → branch → PR → CI → merge, per Amendment 1 §17–19, with
  branch protection on main once the repo exists. Issues/PRs/Actions/releases/
  ADRs/incidents/experiments/docs all live in the flagship repo and cross-link.
  Releases: semantic, only at real milestones (v0.1.0 = container foundation,
  per Amendment 1 §30 examples).

### B.4 Source-of-truth matrix (Investigation point 11)

Current truth (everything in one place, once authorized):

| Domain | Owner (Phase 1–7) | Source of truth |
|--------|-------------------|-----------------|
| Platform architecture + docs | infrastructure-platform repo | Git |
| Bootstrap + host config | infrastructure-platform/bootstrap/ | Git |
| K8s/manifests/charts (future) | infrastructure-platform/platform/ | Git |
| CI/CD | infrastructure-platform/.github/ | Git |
| AI operations (future) | infrastructure-platform/ai/ → possibly extracted Phase 11+ | Git |
| IaC/cloud (Phase 8+) | infrastructure-platform/infrastructure/ → possibly extracted | Git + IaC state (state backend TBD with authorization) |
| Secrets | NEVER in any repo | secret manager design (spec §26) — TBD, authorization-gated |
| Container artifacts | registry (GHCR presumptive — TBD Phase 4 ADR) | digest-pinned references |

### B.5 Cross-repository dependency model (Investigation point 11)

With the recommended monorepo start: **no cross-repository dependencies
exist** — the model is trivial and honest. When extraction happens
(ai-operations, applications), the dependency rule will be one-directional:
`applications → platform contracts → flagship`, never circular, with
version-pinned references (image digests, chart versions) per Amendment 1 §14.
The reconstruction manifest (see reconstruction-manifest.md) is structured to
support multi-repo from day one (it has a `repository` field per component)
so a future split does not require a manifest redesign.

### B.6 Reproducibility & DR implications (Investigation points 11–12)

- Monorepo makes fresh-machine reconstruction trivial: clone 1 repo → run
  bootstrap → done. Multi-repo would require the Platform Reconstruction
  Manifest to drive a multi-clone fetch with version locks — supported by the
  manifest design but strictly more failure modes (partial clone, ref drift
  between repos, ordering).
- DR posture today: **this project's own docs exist ONLY on the machine they
  are supposed to make disposable** — the single most urgent reproducibility
  gap found in discovery. (The host does have Time Machine, but its
  destination is 96% full — no reliance should be placed on it.)
- Spec §34's GitHub-outage concern: at monorepo scale, a mirror/cache strategy
  is deferred; recorded as a known external dependency (github.com) in the
  external-dependency register.

### B.7 Portfolio & employment-evidence analysis (Investigation points 13–15)

**What a technically competent hiring manager will be able to inspect once
the roadmap executes (from ONE coherent repo):** architecture docs + ADRs
(decision quality), CI runs + PR history (process quality), issues + releases
(delivery discipline), incidents + experiments (operational maturity),
reconstruction manifest + reports (reproducibility rigor).

**Honest capability matrix at Phase 0 (Investigation point 15 — implemented vs planned):**

| Capability | Status |
|-----------|--------|
| Linux/macOS system administration | Implemented (operator's environment; evidenced by this discovery) |
| Docker operational knowledge | Implemented (host runs 20 production containers) — but NOT yet evidenced by THIS project |
| Git/GitHub | Implemented (tooling verified) |
| Documentation discipline | Implemented (this doc set) |
| Kubernetes | Planned (Phase 2) |
| Helm | Planned (Phase 3) |
| CI/CD (GitHub Actions) | Planned (Phase 4) |
| GitOps (Argo CD) | Planned (Phase 5) |
| Observability stack | Planned (Phase 6) |
| Security (Trivy/Kyverno/SBOM) | Planned (Phase 7) |
| Terraform/OpenTofu + AWS | Planned (Phase 8; requires cloud account — none exists) |
| Renovate/WUD | Planned (Phases 10/1) |
| AI operations layer | Planned (Phases 11–15) |
| Reproducibility/DR | Planned (Phases 17–18) |

**Portfolio gap:** everything portfolio-visible must be BUILT. The fastest
honest wins: put the documentation discipline itself on GitHub first (it is
real, complete work), then let each phase add committed evidence.

---

## Part C — RISKS

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | Portfolio motivation drifts into manufacturing activity | HIGH (objective-level) | Clarification 1 is binding in OPERATING-INSTRUCTIONS.md; every future session re-reads it |
| R2 | Repo sprawl if later phases casually split repos | MEDIUM | ADR-gated extraction only; split checklist in this doc |
| R3 | Public visibility of work exposes host details | MEDIUM | docs must stay environment-honest but never include IPs, hostnames, secrets, or coexisting-project names without explicit decision; default posture: sanitize infrastructure specifics |
| R4 | Monorepo grows unwieldy by Phase 8+ | LOW | hybrid extraction path already defined |
| R5 | No AWS account exists — Phase 8 blocked until created | INFO | external dependency; authorization + credentials gate later |
| R6 | All project state currently only on the Mac Mini | HIGH (until fixed) | first authorized action of Phase 1: git init + push |

---

## Part D — RECOMMENDED ARCHITECTURE (proposed state — REQUIRES AUTHORIZATION)

1. **One flagship repository:** `paulrydberg/infrastructure-platform` —
   name per spec §54, confirmed available; content = the existing project
   directory, `git init`-ed, public or private (visibility = explicit Paul
   decision; recommendation: **public from the start** because rewriting
   history to "go public" later is worse;sanitize per risk R3 before push).
2. Structure per master spec §53/Amendment 1 §5 (bootstrap/, platform/,
   applications/, automation/, ai/, policies/, scripts/, tests/, docs/,
   diagrams/, .github/ — directories created only as they gain real content).
3. Branch protection + CI (even a docs-lint workflow) as the first real
   GitHub Actions evidence.
4. One GitHub Project board; minimal label taxonomy; ADR-0001 onward in-repo.
5. ADR-0011 (repository architecture) records this monorepo→hybrid decision
   with the analysis above as evidence.
6. Deferred: ai-operations extraction (Phase 11), application repos (when
   real apps exist), IaC extraction (Phase 8), profile README (deferred
   decision — useful, but only with honest content worth featuring).

## Part E — DEFERRED DECISIONS (explicitly not decided in Phase 0)

- Repo visibility (public vs private) — Paul's call, gate before push
- aws account + credentials — Phase 8 gate
- registry choice — Phase 4 ADR
- k3s placement/resource allocation — Phase 2 ADR (touches shared Docker VM)
- extraction of ai-operations / applications / IaC — phase-gated ADRs
- profile-level portfolio README — after flagship has demonstrable content

---

*This document is evidence for ADR-0011. It records analysis and
recommendation only; nothing outside the project directory was created,
modified, or written to GitHub during this discovery.*
