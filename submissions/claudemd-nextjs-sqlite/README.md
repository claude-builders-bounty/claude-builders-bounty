# CLAUDE.md Template: Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for greenfield SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3 for local dev, Turso for production).

## What This Is

A single file you drop into a new Next.js + SQLite project. Claude Code reads it and immediately understands your stack, conventions, and boundaries without asking clarifying questions.

## Design Decisions

**No ORM.** The template prescribes raw SQL with typed helper functions. ORMs add cold start penalty and fight SQLite's embedded architecture. Fifty lines of typed query functions replace thousands of lines of ORM configuration.

**Server Components by default.** Every rule reinforces Next.js 15's model: Server Components for reads, Server Actions for writes, API routes only for external webhooks. The anti-patterns section explicitly calls out common mistakes like `useEffect` data fetching and internal API routes.

**SQLite-specific conventions.** WAL mode, `PRAGMA foreign_keys = ON`, text primary keys (ULID/nanoid) for Turso compatibility, ISO 8601 text dates, and the rename-and-recreate pattern for schema changes. These aren't generic database rules --- they're SQLite rules.

**Anti-patterns with reasons.** Every "don't do this" has a concrete "because." Developers (and Claude) follow rules better when they understand the tradeoff.

## Usage

```bash
cp CLAUDE.md /path/to/your-nextjs-project/CLAUDE.md
```

Then open Claude Code in that project. It will pick up the conventions automatically.

## Bounty

Submitted for [Issue #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) --- TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project ($75).
