# Validation Notes

The issue asks for a template that can be pasted into a fresh Next.js + SQLite
project and let Claude Code understand the project without clarifying questions.

## Static Validation

`tests/validate_nextjs15_sqlite_saas_template.py` checks:

- expected sections: stack, folder structure, migration rules, component
  patterns, anti-patterns, commands, and testing strategy
- required stack terms: Next.js 15, App Router, SQLite, Turso, better-sqlite3,
  Drizzle, Server Components, Server Actions, Zod, Better Auth
- at least 45 explicit `Reason:` entries
- at least 10 anti-pattern rows
- no obvious placeholder markers such as `TODO` or `your-app`

## Smoke-Test Scenario

Fresh app setup:

```bash
pnpm create next-app@latest acme-saas --ts --app
cp templates/nextjs15-sqlite-saas/CLAUDE.md acme-saas/CLAUDE.md
cd acme-saas
claude "Scaffold the project structure, Drizzle config, auth route, env validation, and a dashboard members page."
```

Expected Claude Code behavior:

- Chooses Drizzle and SQLite/Turso without asking which ORM to use.
- Creates `app/(marketing)`, `app/(auth)`, `app/(app)`, `db`, `lib`, `server`,
  `components`, and `tests` folders.
- Adds migrations instead of only editing schema files.
- Uses Server Components for page data and Server Actions for mutations.
- Adds tenant filters with `org_id` for protected data.
- Avoids client-side initial data fetching, raw SQL in pages, and float money.

This was designed as a reproducible checklist rather than a claim that requires
private Claude Code transcript data in the repository.
