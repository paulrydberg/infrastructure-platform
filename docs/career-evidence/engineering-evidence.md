# Engineering Evidence — infrastructure-platform

**Status:** Living record (begun 2026-09-24; every claim below links to a
real artifact — this file must never contain a claim without one)

## The engineering story (honest, per Amendment 2)

«An open-source infrastructure platform developed and operated in a personal
development/validation environment, with a reproducible local-to-cloud
architecture and AWS deployment path.» — the second half of that sentence is
currently aspirational; this file tracks when each claim becomes true.

## Evidence inventory

### Specification & governance (real, complete)
- Verbatim master specification (94 sections) + Amendment 1 + Amendment 2 +
  Clarification 1 — preserved unmodified as project origin records
  (../00-project-origin/)
- Binding operating instructions incl. no-manufactured-activity rule
  (../OPERATING-INSTRUCTIONS.md)
- Prompt log + roadmap tracker maintained from day one

### Discovery (measured, not estimated)
- Hardware/software/resource inventories with live measurements
  (../01-discovery/)
- GitHub account + repository-architecture analysis (15-point investigation,
  ../01-discovery/github-portfolio-and-repository-architecture.md)
- External dependency register with degraded-operation posture

### Architecture & decisions
- ADR-0001 (project foundation), ADR-0002 (naming standard) — with context,
  options, rationale, consequences (../decisions/)
- System/logical/AI/reproducibility architecture docs (../02-architecture/)
- Threat model, resource model (../02-architecture/)

### Reproducibility
- Reproducibility contract v1 + reconstruction manifest v1
  (../15-reproducibility/) — currently Level 0, stated honestly

### Implemented-vs-planned discipline
- Capability matrix (capability-matrix.md) — maturity labels; updated per phase
- Non-goals + constraints docs prevent scope/claim inflation

## Evidence yet to be produced (roadmap)

Git history with meaningful commits · PRs · CI runs · releases · issues ·
incident postmortems · failure-test records · reconstruction reports ·
cloud (AWS) artifacts · AI-operations audit logs. Each will be appended here
as it genuinely exists.

## Rule

Nothing enters this file without a verifiable artifact. Nothing is removed.
History is not rewritten.
