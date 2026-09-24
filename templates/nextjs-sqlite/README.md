# Production-Ready CLAUDE.md for Next.js 15 + SQLite SaaS Projects

> Bounty Solution for Opire / GitHub Issue #2: `TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project` ($75)

An opinionated, production-grade `CLAUDE.md` template designed specifically for greenfield SaaS web applications powered by **Next.js 15 (App Router with React 19)** and **SQLite (better-sqlite3 / Turso + Drizzle ORM)**.

## Why This Template Is Opinionated

- **Zero Clarifying Questions Needed**: Explicitly dictates library choices, file paths, and pragma parameters so Claude Code never stalls asking architectural questions.
- **SQLite Production Hardening**: Mandates Write-Ahead Logging (`WAL`), `synchronous = NORMAL`, `foreign_keys = ON`, and `busy_timeout = 5000` to prevent database locks.
- **Server Component First**: Enforces data fetching exclusively in Server Components and mutations in Server Actions with Zod schemas.
- **Concrete Anti-Patterns**: Outlines what NOT to do and provides clear engineering rationales.

## Quickstart (2 Steps)

1. Copy `CLAUDE.md` into the root directory of your Next.js + SQLite project.
2. Launch Claude Code (`claude`) — it immediately reads the guidelines and begins developing in alignment with the architecture.
