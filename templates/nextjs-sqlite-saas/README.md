# Next.js 15 + SQLite SaaS `CLAUDE.md` Template (Bounty Issue #2)

Opinionated, production-ready `CLAUDE.md` engineered for greenfield and production Next.js 15 App Router + SQLite (`better-sqlite3` / LibSQL Turso) + Drizzle ORM SaaS projects.

## Quick Setup (2 Steps)

1. Copy `CLAUDE.md` to the root of your Next.js 15 + SQLite repository:
   ```bash
   cp CLAUDE.md /path/to/your-saas-repo/CLAUDE.md
   ```
2. Launch Claude Code in your repository root (`claude`). Claude Code automatically loads `CLAUDE.md` and enforces WAL-mode PRAGMAs, ULID keys, tenant-scoped DAL queries, and Next.js 15 async request APIs without asking clarifying questions.
