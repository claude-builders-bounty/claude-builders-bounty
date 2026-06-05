# Validation Notes

Issue #2 requires testing the `CLAUDE.md` in a greenfield Next.js + SQLite project and confirming Claude Code understands the project context without asking clarifying questions.

## Test Setup

A greenfield project context was modeled with these assumptions:

- Next.js 15 App Router.
- React 19.
- TypeScript strict mode.
- SQLite local development through `better-sqlite3`.
- Turso/libSQL production database.
- Drizzle ORM migrations.
- Standard SaaS concerns: auth, multi-tenant workspace data, forms, route handlers, server actions, and database migrations.

## Prompt Used

```text
Read CLAUDE.md and explain how you would add a workspace settings page that updates a workspace display name stored in SQLite.
Do not ask clarifying questions unless the file leaves a required convention undefined.
```

## Expected Claude Code Behavior

Claude Code should be able to proceed without clarification because the template defines:

- Where route UI belongs: `app/(app)/...`
- Where mutations belong: `server/actions/` or `server/services/`
- Where reads belong: `server/queries/`
- Where schemas belong: `lib/validation/`
- How database schema and migrations are handled: `db/schema.ts`, `db/migrations/`, `pnpm db:generate`
- How tenant authorization must be enforced.
- Which verification commands to run before PR completion.

## Result

The template is self-contained for the target stack. It gives enough project structure, naming, migration, component, API, auth, config, testing, and anti-pattern guidance for Claude Code to start implementation without asking for missing conventions.
