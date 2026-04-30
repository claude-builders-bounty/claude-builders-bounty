# Next.js 15 + SQLite SaaS CLAUDE.md Template

This directory contains a production-ready `CLAUDE.md` template for greenfield SaaS projects built with Next.js 15 App Router and SQLite.

## Usage

Copy `CLAUDE.md` to the root of a new project:

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your-saas/CLAUDE.md
```

The template is intentionally opinionated around:

- Next.js 15 App Router and React 19
- TypeScript strict mode
- SQLite through `better-sqlite3` or Turso/libSQL
- Drizzle ORM and SQL migrations
- Zod validation
- Server Components by default
- Server Actions for app form mutations
- Route Handlers for webhooks and public APIs

It is designed to give Claude Code enough context to work without asking basic stack, folder structure, database, migration, or component-boundary questions.
