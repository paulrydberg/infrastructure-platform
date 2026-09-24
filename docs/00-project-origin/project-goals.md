# Project Goals — infrastructure-platform

**Status:** Defined (master spec + Amendment 1; formalized 2026-09-24)

## Primary goals

1. **Self-reconstruction** — the platform can rebuild itself from
   source-controlled definitions. Target: reproducibility Level 7
   (continuous reconstruction validation), claimed only when demonstrated.
2. **Deterministic-first operation** — core infrastructure functions with
   zero LLM inference (spec §3), verified by explicit testing (spec §74).
3. **Real engineering system** — Docker → k3s → Helm → CI/CD → GitOps →
   observability → security → AWS, each component justified by the
   nine-question test (spec §81), never installed for resume value.
4. **AI as optional escalation layer** — event-driven, resource-governed,
   provider-neutral, safety-constrained (spec §4–6, §66); autonomy earned
   through demonstrated reliability (spec §39).
5. **Professional GitHub portfolio** (Amendment 1) — publicly demonstrable
   evidence of infrastructure/platform/DevOps/SRE capability, emerging from
   genuine work; repository architecture earned via ADR, never name-driven.
6. **Complete engineering record** — ADRs, runbooks, incidents, experiments,
   honest history (spec §45–52); documentation validated against reality.

## Non-goals

See `non-goals.md`.

## Priority order (spec §2 — do not invert)

1. Working software → 2. Observable behavior → 3. Deterministic operation →
4. Reproducibility → 5. Security → 6. Validation → 7. Automation →
8. Intelligence → 9. Optimization → 10. Documentation and historical evidence.

(Amendment 1 §50 adds the portfolio hierarchy: Correctness > Reliability >
Security > Reproducibility > Maintainability > Operational usefulness >
Architectural clarity > Documentation > Portfolio visibility.)
