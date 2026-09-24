# Threat Model — infrastructure-platform

**Status:** Design v1 (Phase 0; stride-style, refreshed per phase)

## Assets

| Asset | Value | Location today |
|-------|-------|----------------|
| Source of truth (repo) | critical | local only ⚠️ (repo pending) |
| Operator credentials (GitHub token/SSH keys) | critical | host keychain/gh config |
| Future: registry tokens, AWS credentials | critical | TBD |
| Future: cluster + app secrets | critical | TBD (spec §26 design) |
| Shared-host production services | critical (other projects) | Docker/launchd — IN SCOPE TO PROTECT, out of scope to modify |
| Project documentation | high | local + future repo |

## Threats and mitigations (planned/postured)

| Threat | Vector | Mitigation (phase) |
|--------|--------|--------------------|
| Credential leakage into repo | accidental commit | secrets discipline (§26); pre-commit scanning Phase 7; never paste secrets into docs — prompt history reviewed before any push |
| Supply-chain compromise | curl-pipe-sh bootstrap, untrusted images | spec §71: pin/verify all fetched content; digest-pinned images (§15); Trivy Phase 7 |
| Coexistence damage | resource exhaustion by new workloads starves production containers | explicit resource limits (Phase 1+); load tests before Phase 2 cluster; authorization for any Docker config change |
| AI overreach | unauthorized mutation, secret exposure | spec §66 rules binding; GitOps-only deployment path (§56); autonomy ladder starts Level 0–1 |
| Host theft/failure | physical | reconstruction-first design is THE mitigation; stateful data backup separate (§14) |
| GitHub outage | external dependency | documented dependency; mirror strategy deferred (recorded in external-dependency register) |
| Documentation fiction | drift between docs and reality | spec §52 doc validation in CI (Phase 4+) |

## Assumptions

- Single operator; no multi-tenant threats on the host itself.
- Home network behind NAT; Tailscale for remote access (existing).
- No compliance regimes apply at this scale (honest scope).

## Out of scope

Securing the pre-existing Hermes/production stack (other projects' domain);
physical security; host OS hardening beyond project needs (deferred, would
require authorization since it touches shared services).
