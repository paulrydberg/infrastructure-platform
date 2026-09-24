# Software / Environment Inventory — infrastructure-platform

**Status:** Implemented (measured 2026-09-24, Phase 0 read-only discovery)

## Toolchain present

| Tool | Version | Notes |
|------|---------|-------|
| Docker | 29.2.1 (Docker Desktop) | 12 CPUs, 7.654 GiB allocated to VM |
| git | 2.52.0 | identity configured (see git config) |
| GitHub CLI (gh) | 2.92.0 | authenticated as `paulrydberg`, SSH protocol, scopes: repo, workflow, read:org, admin:public_key, gist, user |
| kubectl | installed | **version string empty at discovery — no cluster, no ~/.kube directory** |
| Homebrew | 6.0.20 | Intel (/usr/local) |
| Python | 3.14.4 (system brew) | plus 3.11.14 in some project venvs |
| Node.js | 20.20.0 | npm 10.8.2 |
| Go | installed | version did not report in discovery — re-verify later (recorded uncertainty) |

## Toolchain NOT installed (roadmap gaps)

| Tool | Phase where needed |
|------|--------------------|
| helm | Phase 3 |
| k3s / kind / k3d (any local cluster) | Phase 2 |
| terraform / tofu | Phase 8 |
| argocd CLI | Phase 5 |
| trivy | Phase 7 |
| aws CLI | Phase 8 |
| k9s (optional) | — |

## Running container workloads (20 containers — DO NOT DISTURB)

These are **production services belonging to other projects**. This project's
Phase 1+ work must coexist or be explicitly scheduled around them.

| Group | Containers |
|-------|-----------|
| Observability stack (coexisting project) | 7 containers (server, worker, db, cache, object store, olap, coordinator) |
| Agent/UI stack (coexisting project) | 3 containers (gateway, web UI, search) |
| App platform (coexisting project) | 2 containers (proxy, ops API) |
| Data services (coexisting project) | 2 containers (cache, vector db) |
| Relay stack (coexisting project) | 4 containers (relay, cache, db, object store) |
| Trading terminal (coexisting project) | 1 container |

## Host services (launchd) relevant to coexistence

- `ai.hermes.gateway` — the agent gateway this project's CTO agent runs in
  (the "Hermes" agent platform; the name appears throughout the verbatim
  specification by design and is retained there unmodified)
- Additional launchd services: cloudflare tunnel, tailscale proxy, plus
  ~27 more workers/agents (names withheld from the public record)

## Kubernetes state

- **No cluster exists.** No k3s/kind/k3d, no ~/.kube, no k8s containers.
- kubectl binary present but idle. Phase 2 will be a true greenfield decision
  (spec §20 requires the "why Kubernetes" documentation BEFORE install).

## Git state of this project

- Project directory `~/.hermes/projects/infrastructure-platform/` exists with
  documentation only — **it is NOT yet a git repository**. Initializing git
  and creating the GitHub repo is a Phase 0/1 boundary decision requiring
  authorization (see github-portfolio-and-repository-architecture.md).
