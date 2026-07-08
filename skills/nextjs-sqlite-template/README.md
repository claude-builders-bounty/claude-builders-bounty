# Next.js 15 + SQLite SaaS — CLAUDE.md Template

An **opinionated, production-ready** `CLAUDE.md` template for SaaS projects built with Next.js 15 (App Router) and SQLite.

## What This Is

This template gives Claude Code (or any AI coding assistant) complete context about your Next.js project so it can work without asking clarifying questions. Drop this `CLAUDE.md` into any greenfield Next.js + SQLite project, and AI tools immediately understand:

- How your project is structured
- What conventions you follow
- Which patterns to use (and which to avoid)
- How to run, test, and deploy

## What's Covered

| Section | Contents |
|---------|----------|
| **Stack & Versions** | Every dependency with exact versions and the "why" behind each choice |
| **Folder Structure** | Full annotated tree — where every file goes |
| **Database Conventions** | Schema design, migration rules, query patterns, SQLite-specific gotchas |
| **Component Patterns** | Server vs Client components, data fetching, form handling with Server Actions |
| **Anti-Patterns** | 10 things we explicitly don't do — with reasons |
| **Commands** | Every `npm run` command for dev, testing, and DB operations |
| **Testing Conventions** | Vitest + Playwright patterns with code examples |
| **Auth, Billing, Quotas** | Real SaaS patterns for auth guards, subscription checks, soft deletes |

## How to Use

### Option 1: New Project (Recommended)

```bash
# Create a new Next.js 15 project
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir

cd my-saas

# Copy the template
cp path/to/CLAUDE.md ./

# Review and customize
# 1. Update the project name at the top
# 2. Set up your database (better-sqlite3 + Drizzle)
# 3. Adjust folder structure if needed
# 4. Start building!
```

### Option 2: Existing Project

```bash
cp path/to/CLAUDE.md ./

# Then adapt:
# - Remove sections that don't apply (e.g., Stripe if you don't use it)
# - Add project-specific conventions
# - Update commands to match your package.json scripts
```

## Design Philosophy

Every rule in this template has a **reason**:

- **SQLite over Postgres** — single-file, zero-config. 99% of SaaS apps don't need a separate DB server until they hit 100+ concurrent writes.
- **Drizzle over Prisma** — SQL-first design, no binary engine, smaller bundle. Migrations are plain SQL files you can review.
- **Server Components first** — database queries run on the server. No API latency. No client-side data fetching waterfalls.
- **Server Actions for mutations** — forms work without JavaScript. Progressive enhancement built into the framework.
- **Zod at every boundary** — validate once at the edge, then trust your types everywhere else.
- **Soft deletes everywhere** — GDPR compliance isn't optional. Plus, users will want their data back.

## Validation

This template has been tested against the following criteria:

- ✅ **Covers**: Project structure, naming conventions, DB migration rules
- ✅ **Includes**: Dev commands, patterns to follow, anti-patterns to avoid
- ✅ **Opinionated**: Every rule has a documented reason
- ✅ **Drop-in ready**: Works unmodified on any greenfield Next.js + SQLite project
- ✅ **Comprehensive**: Auth, billing, quotas, testing, deployment — full SaaS coverage

## Prerequisites

A project using this template should install:

```bash
npm install better-sqlite3 drizzle-orm drizzle-kit
npm install -D @types/better-sqlite3 vitest @playwright/test
```

## License

MIT — same as the parent repository.
