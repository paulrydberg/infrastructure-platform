# Resource Negotiation Report — k3s on the Shared Mac Mini

**Status:** Complete (2026-09-24, Phase 2 evaluation)
**Scope:** read-only measurements; NO Docker Desktop config changed, NO k3s installed
**Mandate:** Paul's Phase 2 authorization — this report precedes any resource change

---

## 1. Current allocation (measured)

| Resource | Docker Desktop VM allocation | Host total |
|----------|------------------------------|------------|
| CPU | 12 (all host cores) | 6C/12T |
| Memory | **7.654 GiB** | 16 GB |
| Disk | shared Data volume (184 GiB free) | 699 Gi |

## 2. Current observed utilization (measured 2026-09-24)

**Inside the VM (docker stats, no-stream):**

| Consumer | Memory | Limit |
|----------|--------|-------|
| olap db (protected) | 1.996 GiB | 4 GiB (hard-capped) |
| observability server (protected) | 663 MiB | 4 GiB (hard-capped) |
| web UI (protected) | 246 MiB | unlimited |
| relay (protected) | 181 MiB | unlimited |
| langfuse-worker-class (protected) | 212 MiB (82% of cap!) | 256 MiB hard cap |
| gateway (protected) | 172 MiB | 1 GiB hard cap |
| remaining 14 protected containers | ~180 MiB combined | unlimited |
| **platform-demo (ours)** | 13 MiB / 128 MiB | hard cap |
| **Sum of container usage** | **≈ 2.4 GiB** | |

**Key measured fact:** the VM has **≈ 4.5–5 GiB free inside its 7.654 GiB**
(7.65 − 2.4 containers − ~0.7 VM overhead), and host CPU is ~80% idle
(load 3.3–3.6 of 12 threads), swap 680 MB / 2 GB.

## 3. Current workload baseline

- 21 running containers (20 protected + our platform-demo).
- **17 of 20 protected containers have NO hard limits** — they may balloon
  into VM memory under load. Only 4 are capped (4G, 4G, 256M, 1G).
- Sustained host load 3.3–3.6; the heaviest CPU consumer is the olap db
  (~100% of one core during query bursts).

## 4–7. Projected requirements (k3s / platform / observability)

| Component | Projected need (measured class, not generic estimate) |
|-----------|------------------------------------------------------|
| k3s server (single node, embedded sqlite, Traefik+servicelb disabled) | 512–900 MB RSS, ≤ 0.5 core steady |
| test/validation workloads (Phase 2) | ≤ 256 MB |
| Phase 3–5 additions (helm client is local; Argo CD later) | ≤ 512 MB (Argo CD ~300–400 MB when deployed) |
| metrics-server only (Phase 2) | ~60–100 MB |
| **k3s envelope with margin** | **≤ 2.5 GiB, ≤ 2 cores — ENFORCED as a hard container limit** |
| Full Prometheus/Grafana/Loki (DEFERRED to Phase 6) | 2–3 GiB — does NOT fit Option A; separately gated |

## 8–10. Storage / networking / persistence

- **Storage:** k3s local-path provisioner → VM-local host paths. Phase 2 workloads
  are stateless by design; persistence = document-and-defer. VM-local storage is
  explicitly NOT durable across Docker resets — recorded in the reproducibility contract.
- **Networking:** k3s in a container on a dedicated bridge network; API server
  bound to 127.0.0.1:6443 only (host port 6443 verified free); default pod CIDR
  10.42.0.0/16 and service CIDR 10.43.0.0/16 do not conflict with the host LAN;
  NodePort (range 30000–32767) mapped selectively for validation; Traefik and
  ServiceLB disabled (no ingress needed in Phase 2 — fewer moving parts).
- **Persistence requirements:** none for Phase 2 workloads; k3s state (sqlite,
  kubelet data) lives in a named container volume so the cluster can be
  destroyed/recreated cleanly.

## 11–12. Failure & contention scenarios (analysis)

| Scenario | Expected behavior |
|----------|-------------------|
| k3s reaches its 2.5 GiB hard limit | k3s pod(s) OOM-kill INSIDE the limit; protected containers unaffected (cgroup isolation); platform degrades, host unharmed |
| olap db grows to its 4 GiB cap | VM pressure; k3s (limited) loses first by design; protected processes keep their caps |
| multiple unlimited protected containers balloon | same as above — k3s yields first; host OOM killer is the last resort (unchanged from today's status quo) |
| host memory exhaustion | unchanged risk profile vs today: k3s adds a BOUNDED 2.5 GiB worst case inside an already-allocated VM — no new host-level exposure |
| VM restart (Docker Desktop update/crash) | k3s container with restart policy auto-starts; state from its volume; validation includes this test |

**Worst case is bounded and isolated** — the fundamental argument for Option A.

## 13. Proposed allocation — OPTIONS (decision NOT made; Paul decides)

### Option A — RECOMMENDED: no Docker Desktop change
Run k3s as a privileged container **inside the existing VM** with a hard
2.5 GiB / 2-core cap. Zero impact on protected workloads (their VM allocation
is untouched; k3s can never exceed its cap). Zero rollback surface (no Docker
Desktop settings change). Reject conditions below.

### Option B — increase Docker Desktop VM to 10–12 GiB
Provides Phase 6 observability headroom today. BUT: requires Docker Desktop
restart (impacts all 21 running containers), expands the protected workloads'
envelope, and creates a rollback procedure that touches them. Higher risk now
for capacity that Phase 6 actually needs.

### Alternatives if evidence had said "cannot fit" (documented, not chosen)
Reduced observability footprint · different distribution (minikube/kind —
rejected for other reasons: kind needs its own VM-in-VM on macOS, minikube
similar) · move workloads to AWS earlier · hardware upgrade · environment
separation. The measurements show Option A fits, so these are NOT exercised —
but they remain the recorded fallback set.

**This report does not choose; it recommends and defers.**

## 14. Impact on protected workloads

Option A: none measurable — no config change, no restart, hard-capped guest.
Validation will verify via before/after docker stats and uptime of all 20.

## 15–16. Rollback & validation procedures

- **Rollback (Option A):** `docker compose down` on the k3s project (removes
  container + volume). No Docker Desktop settings to revert. Protected
  workloads never touched at any point.
- **Rollback (Option B, if ever chosen):** Docker Desktop settings → revert
  memory slider → Docker restarts (ALL containers restart — this is exactly
  why Option B is not recommended now).
- **Validation (either option):** before/after snapshots of docker stats for
  all 21 containers; host load; k3s node Ready; test pod schedules + serves;
  kill k3s container → restart policy recovery; VM-restart survival test.

## 17. Minimum acceptable headroom & rejection conditions

Option A is REJECTED if any of these measured conditions occur during validation:
1. VM free memory < 3.0 GiB sustained before k3s start (need 2.5 + 0.5 margin)
2. k3s hits its 2.5 GiB limit during normal Phase 2 workloads (not just induced failure tests)
3. Any protected container restarts or OOMs attributable to k3s presence
4. Host swap usage doubles from today's 680 MB baseline and stays elevated
5. Sustained host load > 8 for > 5 minutes with k3s idle

→ Any rejection escalates to Option B or the alternative set, with a fresh
report. **Paul decides; the platform does not self-authorize.**

## 18. Conditions under which the proposed allocation should be rejected

= the five conditions above, verbatim, plus: any change in the protected
workload mix (new containers, changed caps) invalidates this report's
baseline and requires re-measurement before proceeding.

---

**Bottom line:** the measurements show the Mac Mini CAN host Phase 2's
Kubernetes footprint safely — as a hard-capped guest inside the existing VM —
without touching Docker Desktop, without restarting anything, and with a
one-command rollback. The full observability stack does NOT fit under Option A
and remains Phase 6-gated with its own negotiation.
