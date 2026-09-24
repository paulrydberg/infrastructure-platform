# External Dependency Register — infrastructure-platform

**Status:** Design v1 (Phase 0; per master spec §59–60)

| Dependency | Purpose | Bootstrap? | Runtime? | Reconstruction? | Outage impact | Fallback | Recovery strategy |
|-----------|---------|-----------|----------|-----------------|---------------|----------|-------------------|
| github.com | source of truth hosting | yes (clone) | yes (CI, GitOps pulls) | yes (all) | reconstruction blocked; running local services unaffected | none yet (mirror deferred — recorded) | GitHub status + retry; mirror decision deferred to ADR if maturity requires |
| Docker Hub / ghcr.io | image sources | yes | yes (pulls) | yes | new deployments blocked; running containers unaffected (local images persist) | pin digests so existing workloads never re-pull | registry recovery / alt registry ADR (Phase 4) |
| Homebrew | package installation | yes (host tools) | no | yes | bootstrap blocked | direct downloads with pinned URLs (spec §71) | document pinned installers in bootstrap |
| macOS Software Update / Apple | OS security patches | no | background | no | none direct | — | standard host ops (out of project scope) |
| Tailscale | remote access (existing) | no | coexistence | no | remote mgmt degraded; LAN unaffected | LAN access | existing infra's domain |
| AWS (future, Phase 8) | cloud infra | no | no (today) | future | n/a — **no account exists yet** (discovery finding) | local-only operation by design (§60) | account creation = authorization gate |
| AI providers (future, Phase 11+) | optional reasoning | no | optional only | optional | **platform continues** (spec §60; zero-inference mandate) | deterministic runbooks | provider abstraction (spec §62) |
| DNS (home LAN) | local name resolution | indirect | yes | indirect | IP fallback | /etc/hosts documentation in bootstrap | — |

## Explicit degraded-operation posture (spec §60)

- GitHub down → platform keeps running; reconstruction paused.
- Registry down → running images keep running; no new deploys.
- AI providers down → zero platform impact (architectural guarantee).
- Cloud (future) down → local platform fully independent.
