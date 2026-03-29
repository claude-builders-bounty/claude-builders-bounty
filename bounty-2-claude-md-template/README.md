# Template: CLAUDE.md for Next.js + SQLite SaaS (Bounty #2)

An opinionated, production-ready `CLAUDE.md` template for Next.js 15 (App Router) and SQLite (Turso / better-sqlite3) using Drizzle ORM.

## Features
- **Strict Architecture Rules**: Enforces feature-driven folders, Server Actions for mutations, and Data Access Layers (DAL) for queries.
- **SQLite / Drizzle Best Practices**: Mandates integer UNIX timestamps (due to SQLite limitations) and text UUIDs over auto-incrementing integers for security.
- **Anti-Patterns Defined**: Explicitly bans Prisma, `useEffect` data fetching, barrel files, and default exports (outside of Next.js constraints).
- **Usable Instantly**: Can be dropped directly into the root of any greenfield Next.js SaaS project to guide Claude Code effectively.

## Usage
Simply copy the provided `CLAUDE.md` into the root of your project directory.
