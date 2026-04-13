# CLAUDE.md Template — Next.js 15 + SQLite SaaS

Production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3).

## Setup (3 steps)

1. Copy `CLAUDE.md` to your project root
2. Adjust `DB_PATH` and stack versions if needed
3. Start coding with Claude Code — it understands the context without clarifying questions

## What's Covered

- **Stack & versions** — Next.js 15, TypeScript 5.5+, SQLite, Tailwind CSS 4
- **Folder structure** — App Router, feature-based components, typed DB helpers
- **Database conventions** — WAL mode, ULID primary keys, numbered SQL migrations, no ORM
- **API patterns** — Consistent JSON responses, Zod validation, auth checks
- **Component rules** — Server Components by default, `"use client"` only when needed
- **Anti-patterns** — 13 things we avoid and why
- **Naming conventions** — Files, components, DB tables, env vars, git commits

## Design Decisions

Every rule has a reason:

- **No ORM** — SQLite is simple enough that raw SQL with typed helpers is clearer and faster
- **ULID over auto-increment** — Sortable, unique, doesn't leak record count
- **No serverless** — SQLite needs persistent filesystem. Deploy on VPS with pm2/Docker
- **HTTP-only cookies over localStorage** — XSS protection for auth tokens
- **Vitest over Jest** — Faster, ESM-native, better DX

## Tested On

Created a greenfield Next.js 15 + SQLite project, pasted the CLAUDE.md, and confirmed Claude Code:
- Generates correct folder structure
- Uses raw SQL with typed helpers (no ORM)
- Creates numbered migration files
- Uses ULID for primary keys
- Follows naming conventions
- Uses Server Components by default
- Validates API input with Zod
