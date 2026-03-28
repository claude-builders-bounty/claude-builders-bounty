# CLAUDE.md — Next.js 15 + SQLite SaaS Template

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## What's included

- **Project structure**: App Router layout with clear separation of concerns
- **Database rules**: Drizzle ORM + SQLite patterns, migration workflow, SQLite-specific constraints
- **Naming conventions**: Files, components, functions, DB columns, env vars
- **Server Actions**: Input validation with Zod, revalidation patterns, domain-based file organization
- **Component patterns**: Server-first architecture, when to use `"use client"`
- **Auth patterns**: Session checks in server components and server actions
- **Anti-patterns**: 12 concrete "do not / do instead" rules with reasons
- **Commands**: dev, build, db:generate, db:migrate, db:studio, db:seed

## Setup

```bash
cp CLAUDE.md /path/to/your/project/CLAUDE.md
```

That's it. Claude Code reads it automatically.

## Opinionated choices (and why)

| Choice | Why |
|--------|-----|
| Drizzle over Prisma | SQL-first, better SQLite support, no binary engine |
| Server Actions over API routes | Less boilerplate, automatic revalidation, type-safe |
| `better-sqlite3` over Turso | Zero config, no network dependency, fast local dev |
| Tailwind only (no CSS files) | Consistency, no context switching, AI-friendly |
| `next-safe-action` | Type-safe error handling without try/catch boilerplate |
| WAL mode by default | Prevents "database is locked" errors in production |

## Customization

Every rule has a reason. If a rule doesn't fit your project, remove it — but read the reason first.
