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

The `reference/` directory is a minimal runnable slice of the patterns in `CLAUDE.md` (migrations, invoice queries, create/void server actions, and Vitest suites). CI runs it via `reference/scripts/run-tests.sh`; use it to sanity-check conventions before copying the template into a greenfield project.

## Verify

```bash
# Toolchain check (node, bash, git) — also runs automatically at the start of npm test / make test
npm run env-check

# Full CI validation (structural checks + greenfield smoke test + delivery + peer-review)
npm test
# or: make test / make ci-validate (env-check + scripts/run-ci-checks.sh)

# Individual checks
node templates/nextjs-sqlite-saas/validate-template.mjs
bash templates/nextjs-sqlite-saas/tests/smoke-greenfield.sh
bash templates/nextjs-sqlite-saas/reference/scripts/run-tests.sh
node templates/nextjs-sqlite-saas/tests/delivery-verification.test.mjs
node templates/nextjs-sqlite-saas/tests/peer-review-acceptance.test.mjs
```
