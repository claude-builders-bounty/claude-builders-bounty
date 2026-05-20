# Next.js SQLite SaaS CLAUDE.md Template

This directory contains an opinionated `CLAUDE.md` template for a greenfield
SaaS project using Next.js 15 App Router and SQLite.

## Use In A New Project

1. Create a Next.js 15 project.
2. Choose SQLite through `better-sqlite3` or Turso/libSQL.
3. Copy `CLAUDE.md` from this directory into the new project's repository root.
4. Update only the stack version lines if the project intentionally differs.
5. Ask Claude Code to implement a small feature and verify that it follows the
   database, component, and testing rules without needing extra context.

## Design Choices

- The template is server-first because SQLite and SaaS authorization logic
  should stay out of client bundles.
- The structure separates URL routes from feature logic so App Router folders
  do not become the whole architecture.
- Every rule includes a reason so future agents can preserve intent instead of
  only matching formatting.
- The database guidance works for local `better-sqlite3` and hosted Turso/libSQL
  deployments without forcing an ORM.

## Validation Prompts

Use these prompts after copying the file into a new project:

```text
Create a workspace settings page that lets an owner rename a workspace.
Use the existing conventions from CLAUDE.md and include the tests you would add.
```

```text
Add a database migration for subscription status history and explain the
rollback risk.
```

```text
Review this PR for auth, billing, and SQLite migration risks using the project
rules in CLAUDE.md.
```

Expected behavior: Claude Code should identify `app/`, `features/`, `db/`, and
`lib/auth/` ownership boundaries; it should avoid client-side secrets, direct SQL
in components, and unvalidated server inputs.
