# Next.js 15 SQLite SaaS CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` for a greenfield SaaS app
using Next.js 15 App Router and SQLite through Drizzle.

## Use In 3 Steps

1. Create a new Next.js app: `pnpm create next-app@latest acme-saas --ts --app`.
2. Copy `templates/nextjs15-sqlite-saas/CLAUDE.md` into the new project root.
3. Start Claude Code in that root and ask it to scaffold the folder structure.

## What It Decides

- Next.js 15 App Router with Server Components by default.
- SQLite locally and Turso/libSQL for hosted deployments.
- Drizzle schema and append-only migration rules.
- Better Auth, Zod validation, Tailwind, shadcn/ui, Vitest, and Playwright.
- Naming conventions, component patterns, Server Actions, route handlers, env
  validation, authz, multi-tenancy, and anti-patterns with reasons.

## Validation

Run from the repository root:

```bash
python3 tests/validate_nextjs15_sqlite_saas_template.py
```

The validator checks that the template covers the issue acceptance criteria,
contains explicit reasons for rules, and avoids placeholder text that would make
the file unusable as a greenfield template.
