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

# Full CI validation (structural checks + greenfield smoke test + delivery + peer-review)
npm test
# or: make test / make ci-validate (env-check + scripts/run-ci-checks.sh)

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

# Direct suite entry points (same as npm scripts above)
node templates/nextjs-sqlite-saas/tests/delivery-verification.test.mjs
node templates/nextjs-sqlite-saas/tests/peer-review-acceptance.test.mjs
```

## Fleet delivery gates

Hands-on takeover agents run these isolated scripts before merge:

| Gate | Script | What it checks |
|------|--------|----------------|
| `no_committed_diff` | `npm run test:delivery` | Committed `CLAUDE.md` diff vs `main` is non-empty |
| `peer_review_not_passed` | `npm run test:delivery` | Diff includes `## Stack & Versions`, pins Next.js 15, and documents peer review APPROVED |
| Peer review | `npm run test:peer-review` | Bounty #2 acceptance criteria and branch diff scope |

Both gates must pass alongside `npm test` (166 tests) for PR #2529.
