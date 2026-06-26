# CLAUDE.md Template for Next.js + SQLite SaaS

An opinionated, production-ready CLAUDE.md for greenfield Next.js 15 projects with SQLite.

## Usage

```bash
# 1. Copy to your project root
cp CLAUDE.md /path/to/your/project/CLAUDE.md

# 2. Done. Claude Code reads it automatically.
```

## What's covered

- **Stack**: Next.js 15 (App Router), SQLite via Drizzle, Lucia auth, Tailwind + shadcn/ui
- **Folder structure**: where what lives and why
- **SQL conventions**: migrations, full-text search, transactions
- **Component patterns**: server-first, Server Actions, loading/error boundaries
- **What we don't do**: Prisma, Redux, cron inside Next.js, N+1 queries — and why
- **Dev commands**: build, migrate, lint, typecheck, test
