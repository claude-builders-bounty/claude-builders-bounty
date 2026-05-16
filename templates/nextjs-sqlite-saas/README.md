# Next.js + SQLite SaaS — CLAUDE.md Template

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## Setup (3 steps)

1. Copy `CLAUDE.md` to your project root
2. Adjust the stack versions if needed (Node, TypeScript, etc.)
3. Start coding — Claude Code will follow the conventions without asking clarifying questions

## What's Covered

- **Stack & versions** — pinned, no ambiguity
- **Folder structure** — where everything goes
- **Naming conventions** — files, components, DB tables, env vars
- **SQL/migration rules** — 10 opinionated rules for Drizzle + SQLite
- **Component patterns** — Server vs Client components, when to use each
- **Validation** — Zod schemas shared between client/server
- **Auth** — Session-based with Lucia (no JWTs)
- **Error handling** — consistent patterns for routes and actions
- **Security** — input validation, parameterized queries, rate limiting
- **Testing** — Vitest + Playwright, real SQLite (no mocks)
- **Anti-patterns** — what we don't do, and why
- **PR workflow** — branch naming, commit messages, merge strategy

## Design Principles

Every rule has a **reason**. This isn't a generic template — it's opinionated so Claude Code can make decisions without asking "which approach do you prefer?"

## Test It

1. Create a new Next.js project: `pnpm create next-app@latest my-saas --typescript --app --tailwind`
2. Paste `CLAUDE.md` in the root
3. Ask Claude Code: "Add a users table with email login"
4. Claude should follow the conventions (Drizzle schema, Lucia auth, Zod validation) without asking clarifying questions
