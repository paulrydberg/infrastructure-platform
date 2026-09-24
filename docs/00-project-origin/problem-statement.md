# Problem Statement — infrastructure-platform

**Status:** Defined (master spec; formalized 2026-09-24)

## The problem

Infrastructure built interactively on a long-lived machine accumulates
undocumented state: manual package installs, hidden configuration, snowflake
setup, and "it works but nobody knows why" dependencies. When that machine
dies — or when its owner needs to prove engineering capability to an employer —
the accumulated knowledge is unrecoverable and unevidenced.

## This project addresses four concrete problems

1. **Snowflake infrastructure.** The current Mac Mini hosts valuable systems
   (Hermes ops stack, ~20 containers, launchd services) whose reconstruction
   depends on undocumented machine state. Discovery confirmed: no
   infrastructure-as-code, no cluster declarative state, project docs not even
   under git yet. The project replaces undocumented accumulation with
   Git-versioned, reconstructible definition.

2. **No reproducibility discipline.** There is currently no reconstruction
   manifest, no reproducibility contract, no tested rebuild path for the host
   platform. The project builds these as first-class artifacts with a
   measured maturity model (Level 0 → 7, spec §27).

3. **AI dependence risk.** AI-assisted operations tend to become hidden
   dependencies. This project enforces deterministic-first architecture:
   every core function (deploy, monitor, recover, rebuild) must work with
   AI disabled, verified by an explicit Zero-Inference Test (spec §74).

4. **Unevidenced capability.** Employment evidence requires inspectable,
   honest engineering history — not resume keywords. The project produces
   that evidence as a byproduct of real work (Amendment 1), with explicit
   implemented/tested/planned distinctions (Amendment 1 §23).

## Success condition (spec §93)

The platform is successful when it can reconstruct itself from source with
no hidden dependence on the original machine, operate deterministically
without AI, and present a complete, honest engineering record.
