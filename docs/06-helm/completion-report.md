# Phase 3 Completion Report — Helm Packaging Fundamentals

**Status:** COMPLETE (2026-09-24) — lint/render/install/upgrade/rollback/
reconstruction all validated. STOPPED at Phase 3 → Phase 4 boundary.

## Helm CLI installation (objective 1–2)

- **Version:** Helm v3.16.3 (GitCommit cfd07493f46efc9debd9cc1b02a0961186df7fdf, go1.22.7)
- **Source:** official get.helm.sh release tarball `helm-v3.16.3-darwin-amd64.tar.gz`
- **Integrity:** SHA-256 verified against the official `.sha256sum` published
  at get.helm.sh — **495d75b404a96fb664f1ca3f8cb01db2210aacc62dbfa1bbab30916abbb20a57**
- **Installed to:** `~/tools/bin/helm` (user-local, outside system paths)
- **Honest failure recorded:** my first checksum was typed from memory and
  FAILED verification. I did not proceed; I fetched the official checksum and
  re-verified. Supply-chain discipline worked as intended — and the failure
  is part of the evidence.
- **Reproducibility:** the bootstrap currently validates helm presence only;
  checksum-pinned install is recorded here as the documented procedure
  (bootstrap installation automation remains Phase 2-classified debt).

## The chart (objectives 3–6)

`platform/helm/platform-demo/` — real chart packaging the existing workload:

- Chart.yaml: v2, chart 0.1.0, appVersion 0.1.0
- values.yaml: pinned `platform-demo:0.1.0` (no floating/latest), resources
  50m/32Mi → 200m/64Mi, probes /health, securityContext (non-root 65534,
  read-only rootfs, no privilege escalation) — behavior-preserving vs Phase 1/2
- templates: _helpers.tpl, _fullname.tpl, deployment.yaml, service.yaml
  (labels/selectors via helpers; immutable selector subset)
- No dependencies introduced → nothing to pin beyond the image tag itself

## Deterministic validation before install (objective 7)

| Gate | Result |
|------|--------|
| `helm lint` | 1 chart linted, 0 failed (1 INFO: icon recommended — cosmetic) |
| `helm template` | rendered 81 lines, labels/selectors/probes correct |
| server-side `kubectl apply --dry-run=server` | service + deployment validated by the API server itself |
| repo CI (secret scan, links, syntax) | green on push |

## Install + verification (objectives 8–9)

- Image mechanics (documented): chart references the Phase 1 local image;
  `docker save` → `ctr -n k8s.io images import` loads it into k3s
  containerd (16.8 MiB, digest sha256:5c69e511…); `IfNotPresent` pull policy
- `helm upgrade --install` → REVISION 1, STATUS deployed, pod 1/1 Running in ~6 s
- securityContext intact (verified via jsonpath), resources intact
- Service discovery: `/health` via `platform-demo.platform-demo.svc.cluster.local`
  returned `{"status":"ok","version":"0.1.0"}` in-cluster
- k3s RSS 460 MiB / VM available 2054–2166 MB — envelope respected
- Quota note (honest): the Phase 2 `test-quota` was a test artifact and was
  correctly deleted with the test namespace; the chart does not create a
  quota in its own namespace. Recorded as a gap to address when the chart
  becomes a real platform workload (not silently ignored).

## Helm lifecycle test (objective 10–11)

| Operation | Result (measured) |
|-----------|-------------------|
| install (rev 1) | deployed, 1/1 Running |
| upgrade → chart 0.2.0, replicas=2 (rev 2) | deployed; rolling replace observed (old + new pods concurrently, then old Terminating) |
| rollback to rev 1 | "Rollback was a success!"; pods converged to 1; history shows rev 3 = Rollback to 1 |
| **bad image via Helm** (tag 9.9.9-does-not-exist, rev 4) | old pod kept Serving; new pod ErrImagePull isolated; `helm rollback` recovered — Phase 2 behavior reproduced through Helm |
| uninstall → install from source | clean release recreation (rev 1) |

## Honest failure + remediation (objective 13)

**Source-of-truth violation (mine):** the release-reconstruction reinstall
used the `/tmp` chart copy that I had mutated during the bad-image test
(tag 9.9.9). The reconstructed release came up ErrImagePull — reconstruction
from a mutated copy is not reconstruction. Root cause: temp-copy drift from
the Git source. Remediation: re-synced the copy from Git (tag 0.1.0),
upgraded → 1/1 Running, health endpoint verified. **Lesson: Helm operations
must always reference the Git-sourced chart path; /tmp copies are working
artifacts, never sources.** CI/DNS/protected workloads unaffected.

## Reproducibility sequence update (objective 14)

```
source → bootstrap → container runtime → k3s → Helm → workload
```

Now explicit: chart in Git + pinned image tag + documented image-import
step (docker save → ctr import) + helm install with kubeconfig from the
k3s volume. Re-verified end-to-end by the uninstall/reinstall cycle.

## Resource discipline (measured before/after)

| Point | k3s RSS | VM available | swap |
|-------|---------|--------------|------|
| Phase 3 start | 419.7 MiB | 2074 MB avg | 552.5 MB |
| after install | 460.3 MiB | 2054 MB | 552.5 MB |
| after full lifecycle | 489.3 MiB | 2077 MB | 520.5 MB |

Envelope 1.5 GiB never approached; Helm itself negligible (client-side);
no protected-container impact at any point (verified 20/20 running, no
restarts, no OOMs at every step). No hard-stop condition occurred. No
Phase 2 k3s configuration changes were required.

## Phase boundary

**STOPPED at Phase 3 → Phase 4 boundary.** Phase 4 (GitHub Actions CI/CD
expansion) NOT begun — requires separate authorization. Argo CD/WUD/
observability/cloud/AI remain gated as before. The Phase 2 evidence stands
unchanged as historical record.
