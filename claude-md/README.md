# CLAUDE.md — Next.js 15 + SQLite SaaS Template

Opinionated, production-ready `CLAUDE.md` for AI-assisted Next.js SaaS development.  
**Bounty: $75** — [#2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

## Usage

```bash
# Create a new Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --app

# Copy the template
cp CLAUDE.md my-saas/CLAUDE.md

# Start building with Claude Code
cd my-saas
claude
```

## What's Covered
- **Stack & versions**: Node.js 22, Next.js 15 App Router, SQLite/Turso, Drizzle, Auth.js, Stripe
- **Folder structure**: Full `src/` layout with conventions
- **Naming rules**: Files, components, functions, DB tables, route params
- **DB conventions**: Migrations, soft deletes, timestamps, IDs, foreign keys
- **Component patterns**: Server-first, Server Actions, Suspense, error boundaries
- **Anti-patterns**: What we explicitly avoid and why
- **Environment variables**: Required and optional with examples
- **Testing strategy**: Unit, integration, and e2e scoping

## Design Philosophy
Every rule in this CLAUDE.md has a specific reason based on production Next.js experience:
- **Server-first** → reduces JS bundle, improves FCP
- **Drizzle over raw SQL** → type-safe queries, migration safety
- **Server Actions over API routes** → simpler auth, no CORS, progressive enhancement
- **Zod at boundary** → catches invalid data before it enters the system
- **Soft deletes** → data recovery without backup gymnastics

## Stack Variants
To adapt for a different stack:
1. Replace DB section for PostgreSQL/MySQL (swap `better-sqlite3` for `pg`/`mysql2`)
2. Replace ORM section for Prisma (adjust migration commands)
3. Keep patterns — they apply regardless of DB choice