# Project Overview — infrastructure-platform

**Status:** Defined (master spec, verbatim at
`../00-project-origin/MASTER-SPEC-FULL.md`)

## What this project is

A reproducible, cloud-native infrastructure and platform engineering system:

- begins on a Mac Mini (2018, Intel, 16 GB — see `../01-discovery/hardware-inventory.md`)
- progresses through Docker → Kubernetes (k3s or justified alternative) →
  Helm → CI/CD (GitHub Actions) → GitOps (Argo CD) → observability →
  security → AWS
- has **self-reconstruction as a first-class architectural requirement**:
  "the machine is disposable, the source of truth is persistent"
- is **deterministic-first**: the platform must function with zero LLM
  inference; AI is an optional, resource-governed, event-driven escalation layer
- carries a dual objective (Amendment 1): real engineering system FIRST,
  professional GitHub portfolio SECOND — portfolio value must emerge from
  engineering quality, never be manufactured

## What this project is NOT

- not a homelab-branded toy (spec §54: professional naming; §39: honest scale)
- not a Kubernetes installation for its own sake (spec §20, §81)
- not an AI agent project (spec §3: zero-inference operation is mandatory)
- not a portfolio façade (Amendment 1: no manufactured activity, ever)

## Authoritative documents

| Document | Role |
|----------|------|
| `../00-project-origin/MASTER-SPEC-FULL.md` | master specification (verbatim) |
| `../00-project-origin/AMENDMENT-1-GITHUB-PORTFOLIO-VERBATIM.md` | GitHub/portfolio amendment (verbatim) |
| `../00-project-origin/CLARIFICATION-1-REPO-ARCHITECTURE-VERBATIM.md` | repo-architecture discipline (verbatim) |
| `../../docs/OPERATING-INSTRUCTIONS.md` | binding per-session rules |
| `../../docs/PROMPTS.md` | prompt log |
| `../../docs/ROADMAP-STATUS.md` | living roadmap status |

## Environment context (honest scope statement)

The platform runs on a home Mac Mini that simultaneously hosts ~20 production
containers for other projects and the Hermes agent infrastructure itself.
The project will operate within that reality, documenting shared-resource
constraints rather than pretending to an enterprise environment (Amendment 1 §39).
