# CLAUDE.md Template: Next.js 15 + SQLite SaaS

A production-ready, opinionated `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## What This Is

Drop this file into the root of a new Next.js + SQLite project. Claude Code will immediately understand your stack, conventions, and constraints without asking clarifying questions.

## Installation (1 step)

```bash
# Copy CLAUDE.md to your project root
cp CLAUDE.md /path/to/your/project/
```

## What's Inside

| Section | What It Covers |
|---------|---------------|
| **Stack & Versions** | Next.js 15, React 19, SQLite (better-sqlite3/Turso), Drizzle ORM, Tailwind 4 |
| **Folder Structure** | App Router layout, db/schema convention, feature-scoped components |
| **SQL & Migration Rules** | Hand-written SQL migrations, integer PKs, epoch timestamps, no SELECT * |
| **Component Patterns** | Server Components by default, Server Actions for forms, Zod validation |
| **Dev Commands** | dev, build, lint, typecheck, db:migrate, db:seed |
| **Anti-patterns** | No Prisma, no NextAuth, no UUIDs, no auto-migrations, no barrel files |

## Why Opinionated

Every rule has a reason. This isn't a generic template — it makes specific technology choices and explains why alternatives were rejected.

## Quick Start

```bash
# 1. Create a new Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --app

# 2. Install SQLite + Drizzle
cd my-saas && npm install better-sqlite3 drizzle-orm

# 3. Copy CLAUDE.md
cp /path/to/CLAUDE.md .

# 4. Start building — Claude Code knows your stack
```
