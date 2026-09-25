# Roadmap Status — infrastructure-platform

> **How this works:** The verbatim prompts are the roadmap baseline.
> This file tracks WHERE WE ARE against that roadmap and is updated after
> every session or work item. The master spec's §79 defines Phases 0–19;
> Amendment 1 adds the GitHub/portfolio workstream.

**Last updated:** 2026-09-24 (Phase 1 complete; released v0.1.0)
**Current phase:** Phase 1 — Local Container Foundation ✅ COMPLETE
**Current status:** Repo live (public, protected, security-verified);
platform-demo 0.1.0 tested incl. destroy→rebuild reconstruction; CI green;
v0.1.0 released. Stopped at Phase 1→2 authorization boundary.
**Next gate:** Paul's authorization for Phase 2 — Kubernetes (incl. the
Docker-VM resource-negotiation decision, which requires a separate explicit OK).

---

## Phase Tracker (master spec §79)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 0 | Discovery | ✅ complete | Read-only; discovery report delivered; stopped at boundary |
| 1 | Local Container Foundation | ✅ complete | platform-demo 0.1.0 + bootstrap + CI + v0.1.0; PR #1 CI-green; reconstruction demonstrated (Level 1) |
| 2 | Kubernetes | ✅ complete (A″ 1.5 GiB envelope) | k3s v1.31.2 steady 450-475 MiB/cap 1536; fundamentals+quota+self-heal+rollout-undo demonstrated; reconstruction Level 2 (Ready in ~8s); 20/20 protected untouched; stopped at Phase 2→3 gate |
| 3 | Helm | ✅ complete | helm v3.16.3 (checksum-verified); platform-demo chart lint/render/dry-run green; install+upgrade+rollback+bad-image-recovery+reconstruction demonstrated; envelope respected (k3s 489 MiB max); stopped at Phase 3→4 gate |
| 4 | CI/CD | ✅ complete | 2-job pipeline (validate+build) w/ pinned SHAs, checksum-gated tools, chart/image consistency, kubeconform; both controlled failure modes demonstrated (PR #2); protection API-verified; stopped at Phase 4→5 gate |
| 5 | GitOps | ✅ Phase 5A complete | Argo CD v2.13.3 measured ~209 MB pod memory; control loop + drift self-heal + failure/recovery demonstrated; staged teardown AND permanent residency both verified within 1.5 GiB envelope; stopped at Phase 5 boundary |
| 6 | Observability | 🔄 capacity analysis complete (READ-ONLY) | Tier A (metrics-server) FITS envelope; Tier B tight; Tier B+ requires VM resize or staging; nothing installed; awaiting Paul's architecture choice |
| 7 | Security | 🔲 not started | Trivy/Kyverno/SBOM |
| 8 | AWS | 🔲 not started | Terraform/OpenTofu |
| 9 | Local-to-Cloud Promotion | 🔲 not started | |
| 10 | Dependency Automation | 🔲 not started | Renovate |
| 11 | AI Maintenance Engine | 🔲 not started | AI stays optional |
| 12 | AI Dependency Migration | 🔲 not started | |
| 13 | AI Container Updates | 🔲 not started | WUD → policy → AI → PR |
| 14 | AI Incident Response | 🔲 not started | |
| 15 | Policy Engine | 🔲 not started | |
| 16 | Platform Engineering | 🔲 not started | Backstage evaluation |
| 17 | Reproducibility | 🔲 not started | NOT optional |
| 18 | Continuous Reconstruction | 🔲 not started | |
| 19 | Final Architecture | 🔲 not started | |

Legend: 🔲 not started · 🔄 in progress · ✅ complete · ⏸️ blocked · ❌ failed/rolled back

## Amendment Workstream (Amendment 1 + Clarification 1)

| Item | Status | Notes |
|------|--------|-------|
| Clarification 1 documented + binding | ✅ done | `docs/00-project-origin/CLARIFICATION-1-REPO-ARCHITECTURE-VERBATIM.md` + `docs/OPERATING-INSTRUCTIONS.md` |
| GitHub Portfolio & Repo Architecture Gap Analysis | ✅ done | Folded into 15-point discovery below |
| 15-point repository/portfolio discovery | ✅ done | `docs/01-discovery/github-portfolio-and-repository-architecture.md` (READ-ONLY, honored) |
| ADR-0011 repository architecture | 🔄 analysis complete, ADR pending | Monorepo→hybrid recommended; ADR written at repo-creation authorization |
| Repository source-of-truth matrix | ✅ done v1 | `docs/architecture/repository-source-of-truth.md` (Amendment 2) |
| Cross-repo dependency model | ✅ done v1 | In same doc (monorepo stage: none; rules defined for future splits) |
| Platform Reconstruction Manifest | 🔲 not started | §15 |
| GitHub Projects setup | 🔲 not started | §16 — only as work becomes real |
| Portfolio docs tree (docs/portfolio/) | 🔲 not started | §28 — only with real content |

## Spec Intake Status

| Document | Status |
|----------|--------|
| Master spec (94 sections) | ✅ saved verbatim |
| Amendment 1 — GitHub Portfolio (53 sections) | ✅ saved verbatim |
| Prompt log (docs/PROMPTS.md) | ✅ current |
| project.json | ✅ created |

## First Milestone Checklist (master spec §92)

The first milestone is a **documented, version-controlled, reproducible
engineering foundation** — not Kubernetes. Deliverables:

- [x] 1. Discovery report — `docs/01-discovery/discovery-report.md`
- [x] 2. Hardware/software inventory — `docs/01-discovery/hardware-inventory.md` + `software-inventory.md`
- [x] 3. Resource baseline — `docs/01-discovery/resource-baseline.md` (snapshot; steady-state re-measure Phase 1)
- [x] 4. Architecture document — `docs/02-architecture/system-overview.md` + `logical-architecture.md`
- [x] 5. Reproducibility architecture — `docs/02-architecture/reproducibility-architecture.md`
- [x] 6. Reproducibility contract — `docs/15-reproducibility/reproducibility-contract.md`
- [x] 7. Reconstruction manifest — `docs/15-reproducibility/reconstruction-manifest.md`
- [x] 8. Initial roadmap — `docs/01-discovery/initial-roadmap.md` + this tracker
- [x] 9. Threat model — `docs/02-architecture/threat-model.md`
- [x] 10. Resource model — `docs/02-architecture/resource-model.md`
- [x] 11. Initial ADRs — ADR-0001 (foundation); ADR-0011 analysis done, ADR at repo creation
- [x] 12. Repository structure — recommended (monorepo→hybrid); creation authorized-gated
- [x] 13. Bootstrap design — Phase 1 scoped in initial-roadmap.md
- [x] 14. Initial validation strategy — per-phase exit criteria + contract validation
- [x] 15. Phase 1 exit criteria — `docs/01-discovery/initial-roadmap.md`

## Session Log

- **2026-09-24** — Project initialized. GitHub access verified (paulrydberg).
  Master spec + Amendment 1 received from the operator and saved verbatim.
  Prompt log + roadmap tracker created. No platform work performed yet.
- **2026-09-24** — Clarification 1 received and saved verbatim; operating
  instructions created (`docs/OPERATING-INSTRUCTIONS.md`) binding the
  repo-architecture discipline + read-only Phase 0 gate. Awaiting explicit
  authorization to begin Phase 0 discovery.
- **2026-09-24** — Phase 0 EXECUTED (read-only) on Paul's explicit
  authorization. Measured: host/hardware/software/resource baseline, GitHub
  account state (135 repos, no infrastructure-platform repo, no orgs), toolchain
  gaps. Created full §92 milestone artifact set (24 docs incl. ADR-0001,
  threat model, resource model, reproducibility contract, reconstruction
  manifest, 15-point repo/portfolio discovery). NOTHING installed/modified;
  no GitHub writes; stopped at Phase 0→1 boundary. Findings reported.
- **2026-09-24** — Amendment 2 (naming standard + positioning) received,
  saved verbatim, integrated. ADR-0002 created; 4 required docs produced
  (architecture/github-repository-architecture.md,
  architecture/repository-source-of-truth.md, career-evidence/capability-matrix.md,
  career-evidence/engineering-evidence.md); OPERATING-INSTRUCTIONS updated.
  Phase 0 conclusion unchanged (monorepo → hybrid). Documentation-only — no
  repositories touched. Authorization boundary intact.
- **2026-09-24** — Phase 1 EXECUTED on Paul's authorization. Repository
  `paulrydberg/infrastructure-platform` created PUBLIC after verified
  sanitization (IPs/email/private names redacted); branch protection +
  secret scanning + push protection + Dependabot enabled (ADR-0003).
  Phase 1: platform-demo 0.1.0 (pinned/non-root/healthcheck/limits),
  bootstrap.sh (10 checks, idempotent), CI (5 gates). All lifecycle tests
  passed incl. kill-PID1 self-recovery and destroy→rebuild-from-source
  (Reproducibility Level 0→1). Real workflow: branch → PR #1 → CI green →
  merge → tag v0.1.0 → GitHub release. WUD evaluated → deferred to Phase 4+
  (needs registry). Coexisting production containers untouched (count
  verified). STOPPED at Phase 1→2 boundary.
- **2026-09-24** — Phase 2: evaluation + RC-1 abort of 2.5 GiB Option A
  (direct measurement superseded derived estimate); reduced-envelope analysis;
  A″ authorized and executed — k3s v1.31.2 on 1.5 GiB/2-core envelope,
  fundamentals demonstrated, Level 2 reconstruction. STOPPED at Phase 2→3 gate.
- **2026-09-24** — Phase 3 EXECUTED on Paul's authorization. Helm v3.16.3
  (checksum-verified after honest from-memory-checksum failure); real chart
  for platform-demo (pinned 0.1.0, security-preserving); lint/template/
  server-dry-run green; install → upgrade → rollback → bad-image-via-Helm →
  rollback → release reconstruction all demonstrated. Honest failure:
  /tmp chart drift caused ErrImagePull on first reconstruction; remediated
  from Git source; lesson recorded (Git path is the only Helm source).
  Envelope respected (k3s max 489 MiB); protected workloads clean. Report:
  docs/06-helm/completion-report.md. STOPPED at Phase 3→4 boundary.
- **2026-09-24** — Phase 3 artifact-integrity verification PASSED (blob-hash
  worktree==HEAD for all chart files; lint/template re-validated against
  committed tree). Phase 3 FORMALLY CLOSED.
- **2026-09-24** — Phase 4 EXECUTED on Paul's authorization. 2-job CI
  (validate→build) on GitHub-hosted runners: helm lint/render, chart↔compose
  consistency, kubeconform schema validation, container build + app tests,
  manifest artifact. Actions pinned to SHAs, tools checksum-gated,
  least-privilege, zero secrets. Controlled failure modes demonstrated via
  PR #2 (helm lint fail; app-assertion fail; build skipped/fail correctly);
  restored green. 3 CI-development failures honestly recorded (wrong
  hardcoded checksum; .sha256sum filename mismatch; kubectl dry-run needs
  API server → kubeconform). Protection API-verified. Report:
  docs/07-ci-cd/completion-report.md. STOPPED at Phase 4→5 boundary.
- **2026-09-24** — Phase 5A EXECUTED on Paul's authorization. Argo CD v2.13.3
  (chart 7.7.11) demonstrated the full GitOps control loop on the 1.5 GiB
  envelope: measured ~209 MB pod memory, drift self-heal ≤10 s, invalid-image
  failure isolated zero-downtime, restore ~12 s, staged teardown AND permanent
  residency both verified. 4 honest failures + remediations documented.
  Report: docs/08-gitops/completion-report-phase5a.md. STOPPED at Phase 5
  boundary. (Also: one git-state slip by the agent — Phase 5A commit initially
  landed on a leftover test branch, cherry-picked to main, branch removed.)
- **2026-09-24** — Phase 6 READ-ONLY capacity analysis EXECUTED. Nothing
  installed; Argo preserved (Synced Healthy). Baseline: VM avail ~1840 MB,
  k3s 1.05 GiB/cap, Argo ~174 MB, storage not binding (596 GiB free in VM).
  Decision matrix: Tier A FITS; Tier B tight; Tier B+ VM-resize-or-staged;
  Tier C not justified. Recommendation: Tier A experiment. Choice deferred
  to Paul. Artifact: docs/09-observability/capacity-analysis.md.
- **2026-09-24** — GitHub source-of-truth checkpoint (Paul-authorized, Phase 6
  paused). Verified: clean tree, main==origin/main, all Phase 1-6 artifacts in
  Git, repo settings (public/protected/scanning) API-verified, branch incident
  resolved, security sweep clean. One defect found+fixed: platform/argocd/
  config files lost in failure-test branch cleanup — recovered bit-identical
  from orphaned commit de6de8a (commit 99c787e). README status table +
  capability matrix synced to actual phase progress. Resource note from Paul:
  Ubuntu laptop (Tailscale SSH) may be evaluated as future memory resource —
  measure-only first, no migration without separate authorization.
- **2026-09-24** — Phase 6 Tier-A metrics-server v0.7.2 EXECUTED (Paul-authorized).
  Pinned manifest under Git (upstream SHA-256 verified, image pinned, one delta:
  resource limits). Functional validation successful: Ready in ~31 s, kubectl
  top nodes/pods working, measured 16-20 Mi (vs 60-100 MB estimated). 12-sample
  55-min window: k3s 1.005-1.058 GiB (cap 1.5), API within baseline, load within
  baseline, Argo Synced Healthy, platform-demo healthy, protected fleet
  0 restarts/OOMs. SWAP GATE TRIGGERED: 625.75 -> 1260 MB during window, never
  reverted. Attribution: k3s RSS shrank at the event, Pearson r(k3s,swap)=0.131
  over 27 samples, no k8s/docker OOM events, node MemoryPressure=False,
  metrics-server constant — evidence does not support metrics-server as cause
  but causality unproven. Classified CORRELATED_BUT_CAUSALITY_UNCERTAIN;
  closed conservatively via documented rollback (control comparison: swap did
  not revert after removal, did not keep growing either). Classification:
  FUNCTIONAL VALIDATION SUCCESSFUL / SWAP GATE TRIGGERED / CAUSALITY UNCERTAIN.
  metrics-server = experimentally validated, NOT implemented. Full report:
  docs/09-observability/tier-a-experiment.md; raw log:
  docs/09-observability/tier-a-observation.log. STOPPED at Phase 6 boundary.
- **2026-09-24** — Phase 6 READ-ONLY host swap-driver characterization (Paul-authorized,
  post-Tier-A). Findings: macOS pressure level 1 (NORMAL), 76% free, zero
  throttled pages; swap 1281.5 MB of 2048 MB and DECLINING on an idle host
  (1345.5 -> 1281.5 over ~25 min); swapins delta 0 over 30 s at rest — current
  swap is cold-page residency, NOT active pressure. Docker VM process = 10.53 GB
  of 16 GB host physical (dominant consumer); container set inside VM ~4.3-4.5 GiB.
  The 07:11 swap step correlates with NO monitored container change (clickhouse
  +/-8.3% normal variation; k3s RSS fell at the step; r=0.131); driver outside
  monitored set — causality not established. Gate-design lesson recorded:
  swap-used thresholds conflate residency with pressure; future gates should
  use swap-activity rate + pressure level. Tier-B not cleared by this evidence.
  Report: docs/09-observability/swap-driver-characterization.md. STOPPED.
- **2026-09-24** — Phase 6 CLOSED (Paul-accepted). Resource-gating lesson
  formalized as a platform principle (docs/09-observability/resource-gate-principles.md):
  allocation ≠ utilization ≠ swap residency ≠ swap activity ≠ pressure ≠
  degradation; raw swap-used insufficient alone on macOS/Docker Desktop;
  future gates combine pressure level + swap activity + OOM/restarts +
  MemoryPressure + API latency + load + workload degradation. Tier-A
  classification preserved verbatim with an appended (not rewritten)
  addendum pointing to the characterization. Phase 6 completion record
  created (docs/09-observability/phase6-completion-record.md) tying the
  full chain: capacity analysis -> decision gate -> experiment -> swap
  event -> rollback -> characterization -> gate refinement -> decision.
  Roadmap decision memo produced (docs/roadmap-decision-memo.md):
  RECOMMENDATION = Phase 7 Security, CI-first staging (Trivy + SBOM +
  gitleaks + image-policy codification; Kyverno deferred to separate gate).
  Tier B NOT cleared; AWS deferred by dependency order. Awaiting explicit
  Phase 7 authorization. STOPPED at Phase 6 boundary.
- **2026-09-24** — Phase 7A CI security evidence EXECUTED (Paul-authorized;
  CI-only staging per roadmap memo). Controls: Trivy image+config scans
  (action v0.36.0 @ SHA ed142fd0, scanner v0.70.0 — supply-chain incident
  GHSA-69fq-xp46-6x23/CVE-2026-33634 documented and bypassed: malicious
  v0.69.4 verified absent upstream); gitleaks v8.30.1 binary + checksum
  551f6fc8... (gitleaks-action v3 REJECTED: commercial EULA bundle;
  existing grep gate retained as the deterministic blocker, gitleaks adds
  entropy/history coverage with --redact); SPDX SBOM generated FROM the
  built platform-demo:0.1.0 image with digest metadata; deterministic
  image-reference policy step (no :latest, no untagged refs — fails CI on
  objective violations only). Evidence mode throughout: exit-code 0, 30-day
  artifact retention. New security job runs on GitHub-hosted runners AFTER
  build — zero Mac Mini footprint, zero cluster changes. Security baseline
  doc: docs/07-security/security-baseline.md (DETECTED/BASELINED/WARNED/
  BLOCKED/REMEDIATED/VERIFIED distinctions established; nothing BLOCKED).
  STOPPED at 7A boundary. 7B (policy from baseline -> enforcement) requires
  separate authorization.
  7A honest failure #1 (preserved): the first 7A push placed scanners in a
  standalone security job; GitHub-hosted runners are ephemeral per job, so
  the image built in the build job did not exist there (trivy FATAL: image
  not found; run failed). Correction: scanner steps re-homed INTO the build
  job right after image build/tests. Lesson: scan the artifact in the job
  that builds it, or promote the image via a registry.
  7A baseline established (CI run, all evidence mode): Trivy image scan of
  platform-demo:0.1.0 (alpine 3.20.6) = 52 CVEs (19 LOW/15 MED/16 HIGH/
  2 CRIT; the 2 CRITs are CVE-2026-31789 openssl on libcrypto3+libssl3,
  fixed in 3.3.7-r0 -> base-bump remediation path, nothing BLOCKED);
  Trivy config scan = 460 checks, 29 failures (27 LOW/4 MED/3 HIGH; all 3
  HIGH are KSV-0118 default-security-context, incl. one likely rule-context
  false positive on the non-root chart -> 7B triage); gitleaks full-history
  = 0 findings (VERIFIED clean); SPDX SBOM 76.9 KB generated from the built
  image (digest field empty: local CI build has no registry digest ->
  documented 7B gap); image-reference policy 0 violations. Evidence
  artifact (30-day retention) published with the run.
- **2026-09-24** — Phase 7B (triage & remediation) COMPLETE (Paul-authorized;
  evidence mode maintained, no blocking thresholds enabled). Starting SHA
  1f99653. Commits: 32cf159 (triage: candidate-base measurement table,
  KSV-0118 controlled experiments), 990572e (remediation: base
  python:3.12-alpine3.20 -> alpine3.22 — smallest supported base resolving
  CVE-2026-31789, measured 3.5.6-r0 vs still-vulnerable alpine3.21 tag at
  3.5.5; pod-level securityContext added to chart + fundamentals fixture
  after controlled tests PROVED the rule requires pod-level SC, rejecting
  the initial false-positive hypothesis), b410810 (SBOM records OCI config
  digest, labeled as such; registry manifest digest = future decision).
  Results [M]: CRITICAL 2 -> 0 (rescan-verified); config HIGH 3 -> 1 (the
  remainder is the metrics-server manifest inside the Tier-A experiment
  doc = historical evidence, NOT_APPLICABLE); image HIGH 16 -> 10 (newer
  base surfaces newer advisories; each dispositioned — 5 fixable via next
  base cycle, 2 awaiting upstream fix); secrets 0; image policy 0;
  helm/kubeconform/app tests green throughout; gitleaks 0 both scans.
  Security controls preserved & strengthened (non-root, read-only rootfs,
  no-escalation, seccomp now pod+container). No live-cluster mutation; all
  remediation via Git -> CI. Full report:
  docs/07-security/phase7b-report.md. STOPPED at 7B boundary; 7C (policy
  thresholds, registry allowlist, Kyverno audit) proposed, unauthorized.
- **2026-09-24** — Phase 7B CLOSEOUT + 7C DESIGN PREPARATION (Paul-authorized
  documentation-only pass). Corrections: 7B report reconciled in place —
  CVE-2026-76642 re-verified against the final artifact as having NO listed
  fix, so the no-upstream-fix group is THREE unique HIGH CVEs (53613/53614/
  76642) and the fix-listed base-cycle group is FOUR (14456/45447/53612/
  78408/78410 minus 76642 = 4 unique + their pairs); original narrative
  preserved with an explicit reconciliation note. NEW:
  docs/07-security/security-debt-register.md (dispositions: remediated /
  base-cycle / upstream / accepted / false-positive-check / policy gaps)
  and docs/07-security/phase7c-proposal.md + ADR-0004 (CI-first thresholds
  with expiring exceptions proposed; registry-dependent controls deferred;
  Kyverno audit-mode staged later; signing/provenance deferred; enforcement
  deterministic, LLM=0). **Phase 7C is PROPOSED, NOT IMPLEMENTED** — no
  thresholds flipped, no Kyverno, no registry, no signing. Verified 7B
  state unchanged: CRITICAL 0, KSV-0118 0 on deployable manifests, gitleaks
  0, image-policy 0.
- **2026-09-24** — Phase 7C POLICY SIMULATION & DESIGN GATE complete
  (Paul-authorized; still NOT implemented, CI untouched). Candidate
  policies simulated against the two authoritative historical scan
  inventories (7A: CRIT 2/HIGH 16; 7B: CRIT 0/HIGH 10): raw-count rules
  (P1/P3) REJECTED — they permanently block on the three no-fix upstream
  CVEs (53613/53614/76642); the 30-day age rule (P4) REJECTED AS DESIGNED
  — table output has no per-finding dates, JSON required; SELECTED:
  R1 CRITICAL-with-fix blocks (simulated FAIL@7A -> PASS@7B, zero
  exceptions, catches regression), R2 persistence rule for recurring
  fix-listed HIGHs (needs previous-run artifact), R4 HIGH config gate
  scoped to RENDERED deployable manifests only (protects the Tier-A
  evidence manifest from blocking), R3 non-blocking warning channel.
  Edge cases recorded: CRITICAL-no-fix blind spot (mitigated by R3),
  merged-cell counting hazard (JSON parsing mandated), evidence-doc
  scoping, exception-expiry requirement carried over. Enforcement gated
  behind >=2 shadow-mode cycles with recorded verdicts + explicit Paul
  authorization. Deliverables: phase7c-policy-simulation.md, ADR-0005.
  CI remains evidence mode; nothing wired in.
  7C policy-model extension (same day, Paul-authorized): full model
  dimensions (fix-availability incl. unknown, age candidates 7-90d,
  exception states, compensating controls, reachability where evidenced)
  + four policy families simulated across THREE historical states (7A
  baseline CRIT 2/HIGH 16; post-base-remediation CRIT 0/HIGH 10 with
  inventory newly surfaced; current identical artifact). Consequences:
  Policy A fails at every state incl. today; B catches historical
  Criticals, 0 failures today; C cannot be honest without JSON dates;
  D bounds the no-fix population via expiring Git-tracked exceptions.
  Eighth unique HIGH explicitly identified from artifact (14456/45447/
  53612/53613/53614/76642/78408/78410; 5 fix-listed unique / 3 no-fix;
  7 fix pairs — 14456+45447 dual-package). Exception model + 90d expiry
  proposal, no-fix handling, new-CVE vs project-change discrimination
  (via previous-run diff), base-refresh differential design, FP
  lifecycle (KSV-0118 precedent), shadow-mode record schema and noise
  thresholds, Kyverno/registry boundary tables: all documented in
  phase7c-policy-model.md; ADR-0005 refined. STILL NOT IMPLEMENTED —
  CI untouched, enforcement unauthorized.
- **2026-09-24** — Phase 7C SHADOW EVALUATOR IMPLEMENTED (observational
  only; CI green). tools/policy/: shadow_evaluator.py (stdlib-only,
  deterministic, LLM=0; JSON-only policy input; identity=PkgName|CVE;
  R1 CRIT+fix WOULD_FAIL, R2 NEW/PERSISTENT/RESOLVED with severity/fix
  transitions, R3 visibility incl. expired exceptions + missing history,
  R4 rendered-platform-demo-only config observation), 19 offline unit +
  historical-regression tests (7A fixture -> R1 WOULD_FAIL; current ->
  PASS), shadow exception ledger (empty; 90d expiry = proposed default
  under test). CI: 4 additive steps (JSON scan same pins, unit tests,
  previous-run fetch w/ continue-on-error, shadow-policy-verdict artifact
  90d). **CI failure #1 recorded + fixed** (run 36039544280: eager open
  of absent previous file -> FileNotFoundError; fix 07f923f passes the
  path and resolves file-missing to the first-run UNKNOWN branch;
  failure documented in tools/policy/README.md). **Cycle 1 observed
  (real artifact, run 36040098028 @ 07f923f): verdict UNKNOWN — R1 PASS,
  R2 UNKNOWN (first run, no previous artifact — expected per design),
  R3 WARN (missing-history visibility record), R4 PASS.** Cycle 2
  (persistence measurement) PENDING the next natural CI run. Enforcement
  NOT enabled; scanner exit behavior unchanged (ci.yml diff = insertions
  only, zero removed lines).
  **CYCLE 2 OBSERVED & VERIFIED (run 36040505744 @ 85b950e, real push CI):**
  verdict WARN — R1 PASS, R2 WARN with 65/65 PERSISTENT (0 new/0 resolved),
  R3 PASS, R4 PASS. Independent raw-JSON reconciliation matches evaluator
  exactly; no version/severity/fix transitions between cycles; identity
  PkgName|CVE audited (0 duplicates/0 conflicts) and retained. **MATERIAL
  DATA CORRECTION:** authoritative JSON shows CVE-2026-53613/53614/76642
  ARE fix-listed (2.41.6-r0) — the earlier "3 no-fix HIGHs" came from
  merged-cell TABLE extraction (the documented hazard). All 8 unique HIGH
  CVEs are fix-listed; debt register/ADR-0005/fixtures/README corrected
  with reconciliation notes (history preserved, evaluator code unchanged
  — it used JSON correctly). 20 tests green. Two real cycles complete;
  shadow system ready for the separate policy-review/enforcement gate.
  Enforcement NOT enabled.
  **POLICY REVIEW GATE COMPLETE (docs-only; enforcement NOT enabled):**
  full 7C policy review from 3 real shadow-cycle artifacts + evaluator
  probes. Verdict: READY WITH REQUIRED PRECONDITIONS — proposed
  enforcement contract defined (FAIL = R1 crit+fix unexcepted OR R4
  failure OR expired-exception; WARN = R3/R2 records; UNKNOWN never
  PASS; deterministic precedence). Probes found one silent-PASS window
  (structurally-empty scan + history) and missing-field permissiveness
  -> preconditions P1 (minimum JSON schema validation), P2 (severity-
  absent visibility), P3 (run-id/image/scanner-version in artifact),
  P4 (policy_version), P5 (enforcement + rollback unit tests) — all
  documented with evidence in phase7c-policy-review.md; single-flag
  rollback design recorded. Skill audit: infrastructure-platform-security
  = supplemental, consistent with source-controlled docs, repo remains
  reconstructible without it. CI untouched (run 36041814661 green @
  dc92979); 20/20 tests green; NO enforcement change applied.
  **P1-P5 HARDENING IMPLEMENTED & VERIFIED (enforcement NOT enabled):**
  policy-review preconditions closed. P1 minimum Trivy-JSON schema
  validation (derived from pinned scanner's real output; fatal =
  missing/non-list Results, non-list vulns, missing identity fields,
  wrong types, zero blocks carrying a Vulnerabilities collection —
  closes the verified silent-PASS window); P2 severity handling
  (missing/malformed -> retained as UNKNOWN + R3-visible, never LOW,
  never skipped, never satisfies R1; lowercase canonicalized); P3
  provenance (run_id/image/scanner_version in every verdict, null when
  absent, survives UNKNOWN); P4 policy_version (7c-policy-1.0.0)
  distinct from evaluator_version (7c-shadow-1.1.0) + schema_version 2;
  P5 enforcement/rollback exit-code contract unit-tested (--enforce:
  FAIL/UNKNOWN exit 1, WARN/PASS exit 0; shadow always 0; rollback
  restores shadow) — CI does NOT pass --enforce. 50/50 tests green.
  Real-artifact compatibility: hardened evaluator re-run on Cycles 1/2/3
  scan JSONs — substantive verdicts unchanged (UNKNOWN/WARN/WARN,
  65/65 persistent) + provenance + schema_validated on all three. CI
  diff additive-only (provenance env/args; zero --enforce usage). No
  runtime infrastructure changes; LLM inference 0.
  **POLICY ENFORCEMENT ACTIVATED (2026-09-24, Paul-authorized final gate;
  commit eb451e2; verified run 36074112719):** preflight passed (P1-P5
  source probes, silent-PASS regression, cycle replays, branch-protection
  review — no new required check needed, gate lives in existing build
  job). Activation = one new final CI step AFTER all artifact uploads:
  WOULD_FAIL/UNKNOWN verdicts exit non-zero; WARN/EXCEPTION/PASS green.
  Real run: gate step success, verdict WARN (65 persistent, 0 critical,
  R4 PASS), all three artifacts present. Blocking path proven via unit
  suite (Critical+fix, R4, UNKNOWN -> exit 1) + real-artifact gate
  simulation; rollback = delete the single gate step. Security scanning
  ACTIVE, policy evaluator ACTIVE, policy enforcement ACTIVE, shadow
  semantics retained for rollback. No history rewritten.

## Phase 8 — Reproducibility Level 2 -> 3 (COMPLETE 2026-09-25)
Authorized Level 2->3 phase executed. reconstruction-manifest.yaml
(manifest_version 1.0.0: components source/prerequisites/container_
runtime/kubernetes/gitops/platform_workload/validation; honest
DETERMINISTIC/EXTERNAL_DEPENDENCY/STATEFUL/MANUAL classification;
external-dependency inventory; secret boundaries; state boundary —
infrastructure reconstruction vs state restoration; host-assumption
classes). bootstrap/reconstruct.sh: deterministic zero-inference
runner (prereq validation reusing bootstrap.sh, source-pin check,
manifest schema+order validation, live-state diff, resource-gated
disposable-cluster mode, JSON reports preserved on failure). Executed
evidence: disposable k3s start->Ready(~5s)->host-side kubectl Ready->
teardown proof, 12/12 PASS @ c07a881 (level3-final-evidence.json);
two intermediate integration defects honestly reported + root-caused +
fixed (docker-cp symlink; nonstandard listen port EOF -> 16443:6443
mapping + tls-san). Failure injection: manifest order violation ->
FAIL+report preserved; unreachable cluster -> FAIL+preserved.
Idempotence: read-only validation runs stable; Argo convergence =
platform idempotence mechanism; destructive production test rejected
by resource gate. Resource gate enforced before every disposable run
(free>=35%, swap<1600M); protected fleet untouched post-run. CI and
enforcement untouched. LEVEL 3 ACHIEVED; Level 4/AWS not begun.

## Post-Level-3 Architecture Decision Gate (2026-09-25, ADR-0006)
Decision-gate analysis completed (no implementation). Options compared:
Level 4 GitOps-rebuild / IaC-AWS / observability / dependency
automation / DR. **NEXT CANDIDATE: Level 4 reproducibility — full
from-scratch GitOps rebuild inside the disposable environment**
(ADR-0006). Roadmap state after this gate:
- Phase 8 (Reproducibility L3): COMPLETE
- Level 4 (disposable GitOps rebuild): NEXT CANDIDATE — not authorized
- AWS / IaC (Terraform/OpenTofu, VPC, IAM, ECR, EKS): DEFERRED
  (dependency order per ADR-0006 — not cancelled; reconsider after L4)
- Observability (Prometheus/Grafana/...): DEFERRED, cloud-dependent
  variant preferred (memory constraint; no demonstrated need)
- Dependency automation (Renovate/Dependabot): REASSESS AFTER LEVEL 4
- Disaster recovery (state restore): FUTURE — no project-state data
  exists today (state boundary documented in manifest v1.0.0)
Numerical roadmap ordering explicitly rejected as a decision basis.

## Phase 8 Level 4 — GitOps-Layer Reconstruction (COMPLETE 2026-09-25)
Authorized Level 4 executed. bootstrap/reconstruct.sh extended: Argo CD
installed from declared values (chart 7.7.11 -> v2.13.3) in the
disposable cluster, Application applied from source-controlled manifest,
platform-demo reconciled by Argo to Synced/Healthy at the exact pinned
commit, workload validated against chart-declared state (pinned image,
securityContext, resources, probes, service), GitOps teardown +
whole-environment teardown. Clean-path evidence: 20/20 PASS, 80s, LLM 0
(reports/level4-final-evidence.json @ 6e5f3a9). Failure injection suite
(bootstrap/level4-failure-tests.sh): invalid Application source path ->
Argo Unknown/error (never Synced); bad image tag -> health Progressing
(never Healthy); recovery to Synced/Healthy (~11s) + 1/1 workload;
9/9 PASS (reports/level4-failure-tests-evidence.txt). Nine defects
discovered and fixed with preserved evidence: L4-1 ambient KUBECONFIG
(helm ownership guard protected production), L4-2 ambient PATH,
L4-3/L4-4 validator races/argv, L4-5 report serialization, stale-state
guard, L4-FT-1..3 suite path/cert-race/port-release. Resource gate
enforced before every disposable run; protected fleet untouched
throughout. Zero inference; no cloud; no new resident services.
LEVEL 4 COMPLETE. Level 5+ / AWS / dependency automation remain
separate future decisions per ADR-0006 sequencing.

## Post-Level-4 Audit (2026-09-25)
Independent audit verified the Level 4 evidence, defect history,
hidden-state elimination, and failure semantics
(docs/history/post-level4-audit.md). One follow-up defect recorded
(report-writer failure is non-fatal; fix requires separate
authorization). NEXT PHASE: DECISION PENDING — audit recommends
report-authority fix followed by continuous reproducibility
validation (Candidate E); nothing implemented.
