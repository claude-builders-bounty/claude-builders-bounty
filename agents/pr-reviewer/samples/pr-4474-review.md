## Summary
This PR adds an opinionated `CLAUDE.md` template for a Next.js 15 App Router + SQLite (better-sqlite3) SaaS stack. It pins the toolchain, defines a folder structure, documents dev commands, SQL/migration rules and component patterns, and lists explicit anti-patterns — each with a stated reason.

## Identified risks
- The template pins better-sqlite3 + Drizzle, which is opinionated; a project already on Turso/Prisma would need edits. This matches the bounty's "usable without modification on a greenfield project" scope, but is not drop-in for existing stacks.
- The "no N+1 queries" rule is documented but not enforced by any lint or test.

## Improvement suggestions
- Add an explicit secrets/.env convention (never commit `.env`, validate env with Zod) — currently implied by "No client-side secrets" but not stated as a setup step.
- Add a short "getting started" sequence that ties the dev commands together (db:generate → db:migrate → dev → build).

## Confidence
High — the document is self-consistent, covers every acceptance section, and each rule carries a reason.
