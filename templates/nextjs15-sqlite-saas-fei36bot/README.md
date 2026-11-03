# Production `CLAUDE.md` Template — Next.js 15 (App Router) + SQLite SaaS

> **Submission for `claude-builders-bounty/claude-builders-bounty#2` (`$75` Bounty)**

## Overview
Drop [`CLAUDE.md`](./CLAUDE.md) into the root of any **Next.js 15 (App Router) + SQLite (`better-sqlite3` / Drizzle ORM / Turso)** SaaS repository to give Claude Code complete, opinionated context on:
- Exact stack & version matrix (`Next.js 15.2`, `React 19`, `better-sqlite3`, `Drizzle ORM`, `Zod`, `Stripe`).
- Clean separation between `src/app/` (routing), `src/db/` (WAL-mode SQLite + schema), and `src/server/` (cached queries + validated Server Actions).
- Mandatory SQLite concurrency PRAGMAs (`WAL`, `busy_timeout = 5000`, `synchronous = NORMAL`, `foreign_keys = ON`) and synchronous transaction rules.
- Explicit anti-patterns table explaining **what we don't do and why**.

