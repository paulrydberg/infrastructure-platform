# ADR-0003 — Flagship Repository Creation

**Status:** Accepted
**Date:** 2026-09-24
**Deciders:** Paul Rydberg (authorizer), Hermes CTO (author)
**Implements:** ADR-0001 (deferred repo decision), ADR-0002 (naming)

## Context

Phase 1 authorization received: create `paulrydberg/infrastructure-platform`,
public, containing the existing Phase 0 documentation foundation, with
pre-push security sweep, .gitignore, public-information boundary, and
protected main branch. No other repositories, no orgs, no migrations.

## Decision

1. Repository created **public**: `paulrydberg/infrastructure-platform`
   (name per ADR-0002 standard; visibility per Paul's explicit authorization).
2. Initial content = real Phase 0 engineering record (39 files, 1 commit,
   genuine chronology — nothing manufactured, nothing backdated).
3. **Pre-push sanitization performed and verified** (grep-verified across repo):
   - host IPs (LAN + Tailscale) → redacted
   - personal email → removed from doc body
   - names of unrelated private repositories → withheld (counts/categories kept)
   - names of coexisting production container groups → genericized
   - secret-pattern scan: CLEAN
   - Verbatim specification files retained unmodified (they contain no such data).
4. `.gitignore` established (secrets/state/artifacts/hygiene patterns).
5. **Branch protection on `main`:** linear history required, force-push
   denied, deletion denied (verified via API).
6. **Security boundary:** secret scanning ENABLED, push protection ENABLED,
   Dependabot security updates ENABLED, vulnerability alerts subscribed
   (all verified via API).
7. Public README carries the honest implemented/planned table and the
   environment statement (personal development/validation environment).
8. Monorepo conclusion of Phase 0/ADR-0001 stands; no additional repositories.

## Rationale

The repository is the platform's source of truth and the beginning of its
public engineering history. Security posture must exist from commit #1, not
be retrofitted. Public visibility was Paul's explicit decision (recommends
against late-publicization history rewrites).

## Consequences

- Positive: real, inspectable engineering record begins now; reconstruction
  contract Component 1 becomes satisfiable (clone → docs present).
- Cost/risk: public surface requires permanent sanitization discipline —
  encoded in OPERATING-INSTRUCTIONS.md and .gitignore; secret-scanning push
  protection provides a technical backstop.
- Neutral: GitHub-free-tier CI minutes apply when Actions land.

## Verification

- Repo visibility PUBLIC, default branch main (API-verified)
- 1 commit on remote, contents match local (API-verified)
- Branch protection + scanning settings (API-verified)
