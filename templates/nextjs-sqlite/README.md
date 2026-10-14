# Production-Ready CLAUDE.md for Next.js 15 + SQLite SaaS

An opinionated, battle-tested `CLAUDE.md` specification template for greenfield SaaS projects built with Next.js 15 App Router, React Server Components, and SQLite (Turso / LibSQL / Drizzle ORM).

## Features
- Complete project architecture tailored for Next.js 15 Server Actions and RSC.
- Specific SQLite optimizations (WAL mode, busy timeout, connection singleton).
- Explicit development commands, linting, and migration lifecycles.
- Clear pattern enforcement and anti-pattern warnings.

## Setup Instructions (2 Steps)

1. **Copy to Project Root**:
   Copy `CLAUDE.md` directly into the root folder of your Next.js project:
   ```bash
   cp templates/CLAUDE.md ./CLAUDE.md
   ```

2. **Verify with Claude Code**:
   Run Claude Code or your agent inside the project root. The agent will automatically ingest `CLAUDE.md` and adhere to these conventions.
