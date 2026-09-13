# Next.js 15 + SQLite SaaS CLAUDE.md

Opinionated `CLAUDE.md` for greenfield Next.js 15 App Router + SQLite (better-sqlite3 / Turso) SaaS projects.

## What this covers

- Stack pin and why each choice
- Folder structure with route groups `(marketing)` / `(app)`
- Naming conventions (routes, components, tables, tests)
- SQL / Drizzle migration rules (append-only, IDs, indexes, transactions)
- Server Component / Server Action patterns with code
- Dev commands and definition of done
- Anti-patterns table with reasons
- When Claude should stop and ask

## Usage

```bash
cp templates/nextjs-sqlite/CLAUDE.md ./CLAUDE.md
```

Paste at repo root of a new or existing Next.js 15 + SQLite project. Adjust package manager commands if you are not on pnpm.

No other files required — the document is self-contained.
