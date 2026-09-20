# Next.js 15 + SQLite Production CLAUDE.md Template

Opinionated, production-ready `CLAUDE.md` template designed for SaaS projects built with **Next.js 15 (App Router)** and **SQLite** (`better-sqlite3` or Turso).

## Features
- **Strict Next.js 15 App Router Patterns**: Server Components by default, Server Actions for mutations, Zod validation.
- **SQLite Concurrency & WAL Configuration**: Single-writer safety, connection singleton for HMR, transaction wrapping.
- **Drizzle ORM Integration**: Type-safe schema definitions and migration workflows.
- **Explicit Anti-Patterns**: Guardrails preventing client-side SQL leakage, un-parameterized queries, and connection deadlocks.

## Setup Instructions (3 Steps)
1. Copy `CLAUDE.md` to the root directory of your Next.js project.
2. Ensure your `.gitignore` includes:
   ```gitignore
   *.db
   *.db-journal
   *.db-wal
   *.db-shm
   sqlite.db
   ```
3. Run Claude Code in your project:
   ```bash
   claude
   ```
   Claude Code will automatically detect `CLAUDE.md` and enforce all architecture, naming, and SQLite safety conventions.
