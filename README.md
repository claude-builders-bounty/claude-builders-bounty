# CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a typical SaaS project built with Next.js 15 App Router and SQLite.

## Quick Start

```bash
# 1. Copy to your project root
cp CLAUDE.md /path/to/your/project/CLAUDE.md

# 2. Open Claude Code in that project
cd /path/to/your/project && claude
```

That's it. Claude Code will automatically read `CLAUDE.md` and understand your project context.

## What It Covers

| Section | Description |
|---|---|
| **Stack & Versions** | Exact technologies and versions used |
| **Project Structure** | Folder layout with rationale for each directory |
| **Rules We Follow** | SQL conventions, component patterns, data flow, auth, error handling |
| **Anti-Patterns** | Common mistakes with "don't do / do instead" table |
| **Dev Commands** | Copy-paste commands for daily workflows |
| **Architecture Decisions** | Why SQLite? Why Drizzle? Why App Router? — with reasoning |

## Opinionated Choices

This is **not generic**. Every rule has a stated reason:

- **SQLite over Postgres** → zero ops, no Docker, no connection pooling for single-tenant
- **Drizzle over Prisma** → 1:1 SQL mapping, no hidden queries
- **App Router over Pages** → RSC, streaming, nested layouts
- **Server Components by default** → smaller bundle, faster renders

## Verification

To confirm Claude Code understands your project:

```bash
# After placing CLAUDE.md, start a new session and ask:
# "What's our database stack?"
# Expected: "SQLite via better-sqlite3 with Drizzle ORM"
```
