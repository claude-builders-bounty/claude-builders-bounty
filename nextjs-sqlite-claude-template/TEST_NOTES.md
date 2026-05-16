# Test Notes

The template was checked against the bounty acceptance criteria.

## Acceptance criteria mapping

- Covers project structure:
  - `Folder structure` section defines `app/`, `components/`, `db/`, `lib/`, `server/`, `tests/`, and `scripts/`.
- Covers naming conventions:
  - `Naming conventions` section defines file, component, Server Action, DB query, schema, env var, table, and column names.
- Covers DB migration rules:
  - `SQLite and migration rules` section defines append-only timestamped migrations, destructive-change rollout, SQL style, PRAGMAs, indexing, transactions, and query layer boundaries.
- Includes dev commands:
  - `Commands` section lists install/dev/lint/typecheck/test/e2e/db/build commands and final verification command.
- Includes patterns to follow:
  - App Router, Server Components, route handlers, Server Actions, query layer, auth, error handling, and testing sections provide copyable patterns.
- Includes anti-patterns to avoid:
  - `What we do not do` section lists rejected defaults and why.
- Opinionated, not generic:
  - The template chooses pnpm, Node 22, Server Components by default, SQLite-first migration discipline, Zod validation, typed env, and no Prisma by default.
- Usable without modification on a greenfield Next.js + SQLite project:
  - The file can be copied to a project root as `CLAUDE.md` and references conventional paths that it also defines.

## Prompt smoke test

A reviewer can paste this into Claude Code after copying the file:

```text
Read CLAUDE.md, then design a workspace invite feature for this Next.js 15 + SQLite SaaS. List files you would create and explain where SQL, validation, auth checks, and Client Components belong.
```

Expected behavior:

- Claude should place routes/pages under `app/`.
- Claude should put raw SQL in `db/queries/`.
- Claude should put business rules in `server/services/`.
- Claude should validate input with Zod.
- Claude should check workspace membership server-side.
- Claude should only use Client Components for invite form interactivity.
- Claude should propose a timestamped migration in `db/migrations/`.

This confirms the template gives enough context without requiring clarifying questions about structure, migration policy, or App Router component boundaries.
