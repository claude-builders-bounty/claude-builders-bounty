# CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for SaaS projects using Next.js 15 App Router and SQLite (better-sqlite3 / Turso).

## Install

Copy into your project root:

```bash
cp CLAUDE.md /path/to/your/project/CLAUDE.md
```

Claude Code reads it automatically on session start.

## What's Included

| Section | Purpose |
|---------|---------|
| **Stack & Versions** | Pinned tech choices with rationale |
| **Dev Commands** | Every command your team runs daily |
| **Folder Structure** | Where files go and why |
| **SQL & Migrations** | Drizzle ORM conventions, naming, ID strategy |
| **Component Patterns** | Server vs Client components, forms, validation |
| **Anti-Patterns** | 10 explicit "don't do this" rules with reasoning |

## Opinionated Choices (with reasons)

- **Drizzle over Prisma** — Prisma's SQLite support is second-class, no edge runtime
- **CUID2 over autoincrement** — URL-safe, sortable, doesn't leak row counts
- **Server Actions over API routes** — No unnecessary network hop for internal CRUD
- **Soft deletes** — `deleted_at` column instead of `DELETE` — data is recoverable
- **Single schema file** — Until 20+ tables, one file is easier to navigate

## Tested

Claude Code understands the context immediately — no follow-up questions needed for standard operations (creating pages, adding tables, building forms, writing tests).
