# CLAUDE.md — Next.js 15 + SQLite SaaS Template

A production-ready, opinionated `CLAUDE.md` for SaaS projects built on Next.js 15 App Router and SQLite (`better-sqlite3` locally, Turso in production).

## What's Included

- Stack versions and tooling choices with rationale
- Enforced folder structure with import direction rules
- SQLite connection setup (WAL mode, foreign keys) and migration conventions
- Repository pattern with typed, synchronous DB access
- Server Component / Client Component / Server Action patterns with working code examples
- Naming conventions table
- Anti-patterns table — each one explains *why* it's banned, not just that it is

## Setup (3 steps)

1. Clone or download this repo
2. Copy `CLAUDE.md` to the root of your Next.js project
3. Start Claude Code — it will read the file automatically on launch

## Design Decisions

**Raw SQL over ORM** — ORMs add indirection that makes debugging harder in small teams. Prepared statements via `better-sqlite3` are fast, explicit, and type-safe with minimal wrapper code.

**Synchronous DB access** — `better-sqlite3` is sync by design. Async wrappers add complexity with no benefit at SQLite scale.

**Timestamps as `INTEGER`** — Unix epoch integers sort correctly, compare correctly, and work across every SQLite tool without locale or format issues.

**Co-located Server Actions** — `actions.ts` next to `page.tsx` keeps mutations close to where they're triggered, making the codebase navigable without a global search.
