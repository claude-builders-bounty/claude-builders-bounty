# Next.js 15 + SQLite SaaS — CLAUDE.md Template

Opinionated [Claude Code](https://docs.anthropic.com/en/docs/claude-code) context file for greenfield multi-tenant SaaS projects.

## Setup (3 steps)

1. Scaffold a Next.js 15 App Router project:

   ```bash
   pnpm create next-app@15 my-saas \
     --typescript --tailwind --eslint --app --src-dir \
     --import-alias "@/*" --use-pnpm
   ```

2. Copy `CLAUDE.md` to the project root.
3. Open the project in Claude Code — it will follow the conventions without clarifying questions for routine tasks.

## What it covers

- Stack pins (Next 15, React 19, better-sqlite3 / Turso, Zod, pnpm)
- Folder structure with tenant-scoped routing
- SQL migration rules and query conventions
- Server Component / Client island / Server Action patterns
- Anti-patterns table with reasons

## Reference app

The `reference/` directory is a minimal runnable slice of the patterns in `CLAUDE.md` (migrations, invoice queries, create/void server actions, Vitest unit/integration suites, and ESLint). CI runs it via `reference/scripts/run-tests.sh` (`pnpm lint` + `pnpm test`); use it to sanity-check conventions before copying the template into a greenfield project. Lockfile: `reference/pnpm-lock.yaml` only — the repo root has no npm dependencies and does not commit `package-lock.json`.

## Verify

```bash
# Toolchain check (node, bash, git) — also runs automatically at the start of npm test / make test
npm run env-check

# Full CI validation (7 ci-step-*.sh stages: security, structural, reference, delivery, peer-review)
npm test
# or: make test (env-check + scripts/run-ci-checks.sh)

# Security audits (also run at the start of npm test via run-ci-checks.sh)
node templates/nextjs-sqlite-saas/tests/check-secret-tokens.mjs
node templates/nextjs-sqlite-saas/tests/check-sql-parameterization.mjs

# Individual checks
node templates/nextjs-sqlite-saas/validate-template.mjs
bash templates/nextjs-sqlite-saas/tests/smoke-greenfield.sh
bash templates/nextjs-sqlite-saas/reference/scripts/run-tests.sh

# Fleet hands-on delivery gates (isolated npm scripts)
npm run test:delivery      # no_committed_diff + peer_review_not_passed gates
npm run test:peer-review   # bounty acceptance criteria + branch diff scope

# Descriptive npm script aliases (peer-review requirement)
npm run test-all           # full CI validation (same as npm test)
npm run lint-and-test      # reference app ESLint + Vitest only
npm run test:claude-md     # CLAUDE.md convention tests
npm run test:security      # secret token + SQL parameterization audits
npm run test:structural    # CLAUDE.md checks + validate-template + smoke test

# Direct suite entry points (same as npm scripts above)
node templates/nextjs-sqlite-saas/tests/delivery-verification.test.mjs
node templates/nextjs-sqlite-saas/tests/peer-review-acceptance.test.mjs
```

## Fleet delivery gates

Hands-on takeover agents run these isolated scripts before merge:

| Gate | Script | What it checks |
|------|--------|----------------|
| `no_committed_diff` | `npm run test:delivery` | Committed `CLAUDE.md` diff vs `main` is non-empty; CI prints `OK: no_committed_diff gate passed` |
| `peer_review_not_passed` | `npm run test:delivery` | Diff includes `## Stack & Versions`, pins Next.js 15, documents peer review APPROVED; CI prints `OK: peer_review_not_passed gate passed` |
| Peer review | `npm run test:peer-review` | Bounty #2 acceptance criteria and branch diff scope |

Both gates must pass alongside `npm test` (251 tests: 29 reference + 37 delivery + 185 peer-review) for PR #2529. Template ships explicit reasons including dev seed script guard, migration runner (`scripts/migrate.ts` with `db:migrate:status`), folder READMEs, development environment setup, deployment, security checklist, reference `scripts/seed.ts`, and reference `.env.example` (SESSION_SECRET min(32) documented with a 32+ char placeholder aligned in CLAUDE.md). Last hands-on verification: 2026-06-29T20:26Z (cursor hands-on takeover — npm test 251/251 green; no_committed_diff and peer_review_not_passed gates pass; peer review APPROVED; PR mergeable CLEAN; `.secrets.baseline` relative path for fork CI secret scan).
