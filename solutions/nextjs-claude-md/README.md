# CLAUDE.md for Next.js 15 + SQLite SaaS

Opinionated, production-ready `CLAUDE.md` for a SaaS project built with
Next.js 15 App Router and SQLite (better-sqlite3).

## What's covered

- **Project structure** — file organization with route groups
- **Naming conventions** — table with examples for every entity type
- **Database rules** — WAL mode, migrations, prepared statements, singleton pattern
- **API conventions** — versioning, response format, validation, status codes
- **Component architecture** — UI primitives vs feature components, Server vs Client
- **Error handling** — per-layer strategy
- **Environment variables** — validation, naming, security
- **Dev commands** — full command reference
- **Anti-patterns** — 8 specific things to never do (with reasons)
- **Patterns** — 5 specific things to always do

## Design decisions

Every rule has a reason. Examples:

- "Always use WAL mode" → Without it, readers block writers in SQLite
- "Never use Prisma with SQLite in production" → Known WAL/concurrency issues
- "Store dates as ISO 8601 TEXT" → SQLite has no native date type
- "Version your API from day one" → You'll need v2 sooner than you think

## Usage

Drop `CLAUDE.md` into your project root. Claude Code reads it automatically.
