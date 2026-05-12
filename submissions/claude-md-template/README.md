# CLAUDE.md Template — Next.js 15 + SQLite SaaS

> **Bounty: $75** — [Issue #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

An opinionated, production-ready `CLAUDE.md` for a typical SaaS project built with Next.js 15 App Router and SQLite (better-sqlite3 via Drizzle ORM).

## What's Included

- **Stack decisions** — Framework, ORM, UI library, auth, forms — with reasons
- **Project structure** — Flat route hierarchy, domain-separated business logic
- **Naming conventions** — Files, components, functions, DB tables, types
- **Database & migration rules** — Drizzle Kit workflow, one migration per feature
- **Component patterns** — Server Components first, client only when needed
- **Anti-patterns we avoid** — 8 concrete "don't do this" rules with explanations
- **Dev commands** — Complete npm script reference
- **PR standards** — Branch naming, commit messages, review requirements

## Usage

1. Copy `CLAUDE.md` to the root of your Next.js + SQLite project
2. Claude Code reads it automatically and follows the conventions
3. No modifications needed — works on any greenfield project

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Drizzle ORM over Prisma | SQLite-native, sync API, smaller bundle |
| SQLite over Postgres | Zero infrastructure for 99% of SaaS apps |
| Server Actions over tRPC | Built into Next.js, no extra dependency |
| Tailwind v4 + shadcn/ui | Composable, accessible, actively maintained |
| No global state library | RSC + URL params replace 90% of use cases |
