# Testing Notes

This template was checked against the bounty acceptance criteria and a greenfield
Next.js + SQLite SaaS scenario.

## Smoke Scenario

Project prompt:

```text
Create a workspace invite flow for a Next.js 15 SaaS app using SQLite.
```

Expected Claude Code behavior after reading `CLAUDE.md`:

- Create or use `features/workspaces/`.
- Add a numbered SQL migration for invite storage.
- Validate form input with Zod in a Server Action.
- Keep database access in a feature query or mutation module.
- Keep interactive form state in a leaf Client Component.
- Run or recommend `npm run build`, targeted tests, and migration checks.

## Acceptance Checklist

- Covers project structure, naming conventions, and database migration rules.
- Includes dev commands, implementation patterns, and anti-patterns.
- Gives a reason for each opinionated rule.
- Works as a drop-in `CLAUDE.md` for a greenfield Next.js 15 App Router project
  using `better-sqlite3` or Turso/libSQL.
- Provides enough context for Claude Code to proceed on a normal SaaS feature
  without asking where files, migrations, validation, or database logic belong.
