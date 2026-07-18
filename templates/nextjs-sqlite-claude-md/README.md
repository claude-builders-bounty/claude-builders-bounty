# nextjs-sqlite-claude-md

A drop-in `CLAUDE.md` for a greenfield **Next.js 15 (App Router) + SQLite** SaaS project.

This is the deliverable for bounty
[#2 — TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2).

## What's inside

- `CLAUDE.md` — the opinionated context file. Paste it at the root of your project.
- `lib/db.ts` — single synchronous `better-sqlite3` connection + migration runner.
- `lib/run-migrations.ts` — CLI entry used by `npm run db:migrate`.
- `migrations/0001_init.sql` — example migration showing the conventions.

## How to use

```bash
# in your Next.js 15 project
cp CLAUDE.md ../your-project/CLAUDE.md
npm i better-sqlite3
# then follow the dev commands + folder structure in CLAUDE.md
```

The `CLAUDE.md` is self-contained and usable without the scaffold files — they are
provided only to demonstrate the conventions it describes (append-only migrations,
parameterized queries, a single data-access layer).

## Acceptance criteria coverage

- [x] Project structure, naming conventions, DB migration rules
- [x] Dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated — every rule states its reason
- [x] Usable on a greenfield Next.js + SQLite project without modification
- [x] Covers the required sections: Stack, Folder structure, SQL/migration, Components, "What we don't do"
