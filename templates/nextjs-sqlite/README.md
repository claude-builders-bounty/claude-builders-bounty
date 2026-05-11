# Next.js + SQLite CLAUDE.md Template

This folder contains an opinionated `CLAUDE.md` for a greenfield SaaS project using Next.js 15 App Router and SQLite through `better-sqlite3` or Turso/libSQL.

## Setup

1. Copy `CLAUDE.md` into the root of a new Next.js + SQLite repository.
2. Make sure the project has the commands named in the template, especially `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and `pnpm db:migrate`.
3. Start Claude Code from the repository root and ask it to plan a small feature; it should identify the route, service, repository, and migration boundaries without more context.

## Included Opinions

- Server components by default, client components only when browser behavior is required.
- SQL access lives behind repositories; product rules live in services.
- Migrations are numbered, immutable after merge, and never run during request handling.
- SQLite constraints are preferred over application-only validation.
- Every rule in the template includes a reason so Claude Code can preserve intent, not just copy structure.
