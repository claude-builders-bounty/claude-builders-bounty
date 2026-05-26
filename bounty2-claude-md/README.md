# CLAUDE.md Template — Next.js 15 + SQLite SaaS

> **Bounty #2** — $75 | [claude-builders-bounty#2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

An opinionated, production-ready `CLAUDE.md` for greenfield SaaS projects built with Next.js 15 App Router and SQLite.

## What's Included

| Section | Content |
|---------|---------|
| **Stack & Versions** | Every dependency with version + rationale |
| **Project Structure** | Complete folder tree with naming rules |
| **Naming Conventions** | Tables, files, components, env vars — all patterns |
| **Database Rules** | Migration discipline, query patterns, WAL mode config |
| **Component Patterns** | RSC vs Client Components, Server Actions |
| **Anti-Patterns** | 5 common mistakes with correct alternatives |
| **Dev Commands** | All daily-use commands (dev, DB, test, build) |
| **Testing Strategy** | Unit / Integration / E2E layer definitions |
| **Performance Rules** | Caching, dynamic imports, bundle analysis |

## Design Philosophy

- **Opinionated**: Every rule has a reason. No generic advice.
- **Zero-abstraction**: Drizzle ORM over Prisma, Server Actions over tRPC
- **SQLite-aware**: WAL mode, connection limits, index strategy
- **Ready to paste**: Works on any new project without modification

## Install

Copy `CLAUDE.md` to your project root:

```bash
curl -fsSL https://raw.githubusercontent.com/jiangyj545/claude-builders-bounty/main/bounty2-claude-md/CLAUDE.md -o ./CLAUDE.md
```

## Verification

1. Create a new Next.js 15 project: `npx create-next-app@latest my-saas --typescript --tailwind --app`
2. Paste this `CLAUDE.md` into the root
3. Open Claude Code in the project directory
4. Ask: "Set up SQLite with Drizzle ORM and a users table"
5. Expected: Claude follows all conventions from this file without asking clarifying questions
