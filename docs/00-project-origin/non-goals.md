# Non-Goals — infrastructure-platform

**Status:** Defined (master spec §81/§83/§37 + Amendment 1; formalized 2026-09-24)

This project explicitly will NOT:

1. **Install technology for the technology checklist.** Kubernetes, Backstage,
   Kafka, service meshes, databases, AI infrastructure, cloud services, or
   security systems are added only when they answer the nine-question test
   (why exist / what problem / what dependency / what resource / how observed /
   how secured / how tested / how reconstructed / how removed).

2. **Create repositories because Amendment 1 lists their names.** The proposed
   repo set is an evaluation framework. Every split must pass the §31 checklist
   and an ADR (Clarification 1).

3. **Manufacture engineering history.** No fake commits, issues, PRs,
   incidents, releases, or project activity for portfolio optics — ever
   (Amendment 1 §48, Clarification 1).

4. **Claim unearned maturity.** No "production-ready", no Level 7
   reproducibility, no AWS production experience claims until demonstrated
   (spec Rule 21, Amendment 1 §23–24).

5. **Make AI a dependency.** No platform function may require LLM inference;
   AI receives no unrestricted production shell; AI never becomes the final
   security authority (spec §3, §25, §66).

6. **Pretend enterprise scale.** The Mac Mini is a home machine shared with
   other production workloads; documentation will state honest scale,
   constraints, and limitations (Amendment 1 §39).

7. **Disrupt coexisting production services.** The ~20 containers, Hermes
   gateway, and launchd services on this host are out of scope and protected;
   any change touching them requires explicit authorization (see
   `constraints.md`).

8. **Build the entire platform simultaneously.** Staged construction only,
   Phase 0 → 19 (spec §79), with exit criteria per phase.

9. **Let portfolio value override engineering correctness.** Portfolio
   visibility is priority 9 of 9 (Amendment 1 §50).
