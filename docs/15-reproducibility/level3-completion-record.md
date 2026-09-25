# Level 3 Reconstruction Completion Record — infrastructure-platform

**Status: LEVEL 3 ACHIEVED (evidence-backed).** Automated platform
reconstruction is now executable, validated, failure-tested, and
resource-gated. Final evidence:
`docs/15-reproducibility/reports/level3-final-evidence.json`
(final_status PASS, 12/12 stages, source pin `c07a881`).

## Objective & maturity transition

- Starting maturity: **Level 2** — automated Kubernetes reconstruction
  (Phase 2 `down -v → up` evidence: container foundation, k3s, Helm,
  GitOps, platform-demo rebuildable from source).
- Target: **Level 3** — automated *platform* reconstruction: a declared,
  executable, validated reconstruction contract covering the platform's
  deterministic components.
- Achieved: **LEVEL 3** (see Success Criteria at the end; every criterion
  mapped to evidence).

## What was added

1. **`reconstruction-manifest.yaml`** (manifest_version 1.0.0) —
   machine-readable contract. Components: source, prerequisites,
   container_runtime, kubernetes, gitops, platform_workload,
   validation. Classifications honest: k3s/Helm/Argo/platform-demo =
   DETERMINISTIC (with EXTERNAL image/helm-repo dependencies recorded);
   Docker Desktop = EXTERNAL_DEPENDENCY (host software, not
   reconstructable from this repo); prerequisite *installation* =
   MANUAL (bootstrap validates, operator authorizes installs);
   cluster state in the `k3s-data` volume = STATEFUL boundary.
2. **`bootstrap/reconstruct.sh`** — deterministic, zero-inference
   runner: prerequisite validation (reuses `bootstrap/bootstrap.sh` —
   no duplicate implementation), source-pin + clean-tree check,
   manifest schema + order-completeness validation, live-state diff
   (node Ready / Argo Synced+Healthy / deployment 1/1), optional
   resource-gated disposable-cluster mode, machine-readable report,
   report preserved on failure, exit codes 0/1/2.
3. **State boundary (§6, mandatory):** reconstructed from source =
   source, bootstrap, k3s container+config, charts, Argo install +
   Application, manifests, policies, scripts. Requires
   restoration/operator = `k3s-data` volume contents (empty-on-recreate
   is the proven Phase 2 behavior), GitHub credential, Docker Desktop
   allocation, any future app data. Model: *infrastructure
   reconstruction + state restoration = full DR* — no "fully
   recoverable" claim is made.
4. **External-dependency inventory (§7)** — in-manifest: github.com
   (blocks everything), Docker Hub (k3s image), ghcr.io (Argo +
   platform-demo images), argoproj helm repo, Docker Desktop, GitHub
   Actions (image rebuild). Each with auth, version sensitivity,
   offline behavior. No invented alternatives.
5. **Secrets boundaries (§8)** — reconstruction needs an operator
   GitHub read credential (never in repo); no cluster secrets required
   for platform-demo today; manifest describes dependencies, never
   values.
6. **Host assumptions (§9)** — portable (charts/manifests/YAML/logic)
   vs macOS-specific (host checks, resource commands) vs
   Docker-Desktop-specific (VM allocation, privileged k3s-in-docker —
   documented constraint) vs x86_64-specific (envelope sizing; arm64
   untested). No Linux/cloud portability claimed.
7. **Reports** — every run emits JSON (timestamp, commit, manifest
   version, environment, architecture, LLM=0, duration, per-stage
   PASS/WARN/FAIL/SKIPPED, final status) to
   `docs/15-reproducibility/reports/` (gitignored run output; the final
   evidence report committed deliberately).

## Testing evidence (all real executions on this host)

- **Validation-only runs** (clean tree `9e66091` → PASS 8/8; earlier
  dirty-tree run honestly WARNed on the source pin).
- **Disposable reconstruction (the §15 core test):**
  - Intermediate defect #1 (docker cp of a symlink → empty kubeconfig)
    — WARN honestly reported; root-caused (`/etc/rancher/k3s/k3s.yaml`
    is a symlink to `/output/kubeconfig.yaml`).
  - Intermediate defect #2 (EOF on host→container `16443:16443` with
    `--https-listen-port=16443`) — WARN honestly reported; root-caused
    by controlled experiment.
  - Fix `c07a881`: use the bind-mounted kubeconfig directly; keep k3s
    on 6443, map host `16443→6443`, `--tls-san=127.0.0.1`.
  - **Final run @ `c07a881`: 12/12 PASS** — disposable k3s Ready in
    ~5 s, host-side kubectl Ready, full teardown verified, production
    fleet untouched (post-run: k3s-server up 15 h, platform-demo
    healthy, protected containers undisturbed).
- **Failure injection (§18):** (a) manifest with order referencing an
  undefined component → detected ("MISSING:bogus_stage"), FAIL, exit 1,
  report preserved; (b) unreachable cluster (bogus KUBECONFIG) →
  kubernetes_live FAIL, report final_status FAIL preserved. Both
  restored cleanly afterward.
- **Idempotence (§11):** repeated validation runs are read-only and
  stable (PASS → PASS → PASS); disposable mode tears down and rebuilds
  from scratch each run (stateless by design — no named volume).
  Full-cluster idempotence on the *production* cluster is deliberately
  NOT claimed: Argo CD reconciliation provides declarative convergence
  (drift self-heal ≤10 s, Phase 5A), which is the platform's idempotence
  mechanism; a destructive idempotence test against production was
  rejected by the resource-gate principle.
- **Resume (§19):** validation stages are read-only and re-runnable;
  disposable stages restart cleanly. No transactional claim made.

## Resource impact (§16 resource gate)

Gate evaluated BEFORE any second cluster: free 75%, swap used
1297–1329 MB (< 1600 MB threshold), required ≈1536 MiB. Disposable
cluster lived ~10 s per run, peak impact small and bounded; production
k3s steady at ~955 MiB / 1.5 GiB throughout. Protected workloads never
touched (validated after every run). Swap used did not increase across
runs. Mac Mini resident-service additions: 0. LLM inference: 0.

## CI integration (§22)

Existing CI untouched (enforcement gate intact and unchanged). Safe
deterministic subset already covered by existing validate job (bootstrap
syntax, helm lint/render/kubeconform, image-reference policy); manifest
validation is local-runnable via the runner (stdlib PyYAML check) and
is exercised in CI's YAML-valid gates. No new resident CI machinery.

## Known limitations (honest)

- GitOps/platform stages were validated as *live-state equivalence*
  plus the Phase 2 `down -v → up` reconstruction evidence; a full
  from-scratch rebuild including Argo + platform-demo *inside the
  disposable environment* (image pulls, helm install) was not executed
  in this phase — the disposable test validated the k3s layer
  end-to-end (start → Ready → host validation → teardown). This keeps
  the achieved level honestly at Level 3 (platform reconstruction
  contract + automated validation + executed k3s reconstruction)
  rather than claiming more.
- k3s-in-Docker privileged mode remains a documented constraint.
- arm64/Windows/Linux host portability untested (documented, not
  claimed).
- State restoration (DR beyond infrastructure) remains future work.

## Success criteria mapping

manifest exists ✓ · source-of-truth boundaries ✓ (manifest) ·
reconstruction order ✓ · deterministic runner ✓ · stages self-validate ✓
· report ✓ (JSON, statuses) · external dependencies ✓ · secret
boundaries ✓ · state/data boundary ✓ · host assumptions ✓ ·
zero-inference ✓ (all runs LLM=0) · idempotence tested where practical ✓
(validation runs; Argo convergence documented) · controlled failure
behavior tested ✓ (2 injections) · resource safety demonstrated ✓ (gate
+ post-run fleet checks) · Git contains all deterministic logic ✓ ·
no hidden manual steps (documented MANUAL class) ✓ · actual
reconstruction executed ✓ (disposable k3s 12/12 + Phase 2 history) ·
results recorded ✓ (this record + evidence report).

## Next candidate (not begun)

Level 4 (infrastructure reconstruction / full disposable GitOps rebuild
including Argo + platform-demo inside the disposable environment) or AWS
per roadmap — separate authorization required.
