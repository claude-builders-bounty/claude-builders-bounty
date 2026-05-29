# 📋 CLAUDE.md Template — Next.js + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3 via Drizzle ORM).

**Bounty:** [#2 — $75](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

## What's Included

| Section | Coverage |
|---------|----------|
| Stack & versions | Next.js 15, SQLite (better-sqlite3), Drizzle, Tailwind v4, Zod, shadcn/ui |
| Folder structure | App Router conventions with rationale for every directory |
| SQL / migration rules | Drizzle workflow, schema conventions, transaction patterns with code examples |
| Component patterns | Server vs Client Components, data fetching rules, naming conventions |
| API Route Handlers | Thin handler pattern with Zod validation and service delegation |
| Auth rules | Session protection, rate limiting, cookie security |
| Anti-patterns | 10 explicit "don't do this" rules with reasoning |
| Testing conventions | Vitest, behavior-first, no snapshot tests |
| Dev commands | All pnpm scripts for dev, test, lint, database |
| Environment setup | Required vars with CLI generation hints |
| Deployment | Vercel + SQLite persistence strategy |
| Performance | Bundle analysis, Suspense, image optimization |
| Git conventions | Conventional commits, PR descriptions, branch naming |

## Usage

1. Copy `CLAUDE.md` to your project root
2. Adjust the stack table if you use different tools
3. Claude Code will automatically read it for context — no config needed

## Why This Template

- **Opinionated** — every rule has a reason (explained inline with "Why" column)
- **Production-ready** — covers auth, migrations, testing, deployment
- **SQLite-specific** — Drizzle migration patterns, query conventions, indexing rules
- **Code examples** — real TypeScript snippets for schema, queries, components, routes
- **Anti-patterns included** — tells Claude what NOT to do (critical for good output)

## Acceptance Criteria

- [x] Covers: project structure, naming conventions, DB migration rules
- [x] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated — not generic. Every rule has a reason.
- [x] Usable without modification on a greenfield Next.js + SQLite project
- [x] Tested with Claude Code — zero clarifying questions on first use

## License

MIT
