# Bounty #2: CLAUDE.md for Next.js 15 + SQLite SaaS

> **Bounty**: $75 — [Issue #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

## What This Is

An opinionated, production-ready `CLAUDE.md` for a SaaS project built with **Next.js 15 App Router** and **SQLite** (better-sqlite3).

Every rule has a reason. This isn't generic boilerplate — it's battle-tested guidance for Claude Code (or any AI assistant) to work effectively on this stack.

## Sections Covered

- ✅ **Stack & Versions** — exact packages and why each was chosen
- ✅ **Folder Structure** — App Router layout with route groups, conventions
- ✅ **SQL / Migration Conventions** — Drizzle ORM, snake_case columns, migration workflow
- ✅ **Component Patterns** — Server vs Client Components, Server Actions
- ✅ **API Routes** — when to use Route Handlers vs Server Actions
- ✅ **What We Don't Do** — anti-patterns with explanations (no Prisma, no tRPC, no `any`)
- ✅ **Dev Commands** — complete list with `pnpm` scripts
- ✅ **Git Conventions** — branch naming, commit format
- ✅ **Anti-Patterns** — 7 specific "don't do this" rules
- ✅ **Testing Patterns** — Vitest examples with rules
- ✅ **Environment Setup** — required env vars with Zod validation

## Testing This

1. Create a new Next.js 15 project: `npx create-next-app@latest my-saas --typescript --tailwind --app`
2. Install better-sqlite3 and Drizzle: `pnpm add better-sqlite3 drizzle-orm`
3. Copy `CLAUDE.md` to the project root
4. Open Claude Code in the project directory
5. Ask Claude Code to create a new feature (e.g., "Add a users table and a /users page")
6. Claude Code should understand the conventions without asking clarifying questions ✅

## Why Every Rule Exists

| Rule | Reason |
|---|---|
| No Prisma/TypeORM | Drizzle is lighter, generates readable SQL, no engine binary needed |
| No tRPC | REST + Server Actions cover SaaS needs without extra complexity |
| Synchronous SQLite | No async mental model, no connection pool bugs, simpler code |
| No barrel files | They break tree-shaking and slow down builds |
| No `moment.js` | It's 300KB. Native `Intl` or `date-fns` do the same job |
| Validate env vars | Missing env vars should fail at startup, not at runtime |
| No `getServerSideProps` | Pages Router pattern — we use App Router's async components |

## Author

**Qiu-Difeng** — claimed via `/opire try` on Issue #2
