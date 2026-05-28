# 📋 CLAUDE.md Template — Next.js + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

**Bounty:** [#2 — $75](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

## What's Included

| Section | Coverage |
|---------|----------|
| Stack & versions | Next.js 15, SQLite (better-sqlite3), Drizzle, Tailwind, Zod, Better Auth |
| Folder structure | App Router conventions, feature-first organization |
| SQL / migration rules | Drizzle workflow, schema conventions, transaction patterns |
| Component patterns | Server vs Client components, data fetching rules |
| Anti-patterns | 8 explicit "don't do this" rules with reasoning |
| Dev commands | All pnpm scripts for dev, test, lint, DB |
| Testing conventions | Vitest, behavior-first, colocated test files |
| Git conventions | Conventional commits, PR descriptions |
| Deployment | Vercel + SQLite persistence strategy |

## Usage

1. Copy `CLAUDE.md` to your project root
2. Adjust the stack table if you use different tools
3. Claude Code will automatically read it for context

## Why This Template

- **Opinionated** — every rule has a reason (explained inline)
- **Production-ready** — covers auth, migrations, testing, deployment
- **SQLite-specific** — migration patterns, query conventions, Drizzle idioms
- **Anti-patterns included** — tells Claude what NOT to do (critical for good output)

## Acceptance Criteria

- [x] Covers: project structure, naming conventions, DB migration rules
- [x] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated — not generic. Every rule has a reason.
- [x] Usable without modification on a greenfield Next.js + SQLite project
- [x] Tested with Claude Code

## License

MIT
