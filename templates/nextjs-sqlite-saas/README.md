# Next.js 15 + SQLite SaaS — CLAUDE.md template

An opinionated, production-ready [`CLAUDE.md`](./CLAUDE.md) for a SaaS built with
**Next.js 15 (App Router)** and **SQLite** (better-sqlite3 or Turso/libSQL),
using **Drizzle ORM**, **Zod**, and **Vitest**.

## What makes it opinionated

Every rule states *why* it exists. It encodes the decisions a senior engineer
would otherwise repeat in code review:

- **Migration-first schema** — schema is the single source of truth; migrations
  are generated, forward-only, and never hand-edited.
- **Server-first data flow** — Server Components/Actions, no client `useEffect`
  fetching, validate-then-act ordering in every mutation.
- **Tenant isolation by the authenticated id** — the default control against
  IDOR/broken object-level authorization.
- **SQLite done right** — WAL mode, `foreign_keys = ON`, `busy_timeout`, integer
  cents for money, UTC timestamps, indexed foreign keys.
- **Safe error handling** — log detail server-side, return generic messages;
  never leak stack traces to the client.
- **A real "definition of done"** — `typecheck && lint && build && test` before
  any task is complete, plus a ready-to-use CI workflow.

## Usage

1. Copy [`CLAUDE.md`](./CLAUDE.md) to the root of a new Next.js 15 + SQLite project.
2. Open the project in Claude Code.
3. Ask it to scaffold a feature — it will follow the folder structure, write a
   migration, add a validated Server Action, and a test, without asking for the
   conventions.

## Sections

Stack & versions · Dev commands · Folder structure · Environment & config ·
SQL / migration conventions (with schema + pragma examples) · Component & data
patterns · Auth, security & multi-tenancy · Error handling & observability ·
Testing strategy · Performance · Git & PR workflow · What we DON'T do (and why).
