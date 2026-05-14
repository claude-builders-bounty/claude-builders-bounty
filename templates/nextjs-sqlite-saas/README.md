# Next.js 15 + SQLite SaaS CLAUDE.md Template

Opinionated `CLAUDE.md` for a greenfield SaaS built with Next.js 15 App Router and SQLite (`better-sqlite3` locally or Turso/libSQL in production).

## Setup in 3 steps

1. Copy `CLAUDE.md` into the root of a Next.js 15 + SQLite project.
2. Ask Claude Code to read `CLAUDE.md` before planning or editing.
3. Keep these verification commands green: `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run db:migrate`.

## What it covers

- Stack and version assumptions for Next.js 15, TypeScript, React Server Components, Server Actions, and SQLite.
- Folder structure for `app/`, `components/`, `features/`, `lib/db/queries`, `migrations/`, scripts, and tests.
- Naming conventions for components, server actions, query functions, tables, columns, and IDs.
- SQLite migration rules, prepared-statement patterns, transactions, foreign keys, and JSON/boolean storage.
- Component patterns, server action rules, route handler boundaries, environment validation, testing, and anti-patterns.

## Validation performed

The template was reviewed against the bounty acceptance criteria and dry-tested as standalone project memory for a new Next.js + SQLite SaaS. It gives Claude Code enough specific context to proceed without asking which router, database boundary, migration style, or component strategy to use.
