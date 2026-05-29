# Validation Notes

These notes map the template to issue #2 acceptance criteria.

## Acceptance Criteria Mapping

- Project structure and naming conventions are covered in `Folder Structure` and
  `Naming Conventions`.
- Database migration rules are covered in `Database And Migrations`.
- Dev commands are listed in `Dev Commands`.
- Patterns to follow are covered across `Data Access`, `Server Actions`,
  `Components`, `Forms`, `Routing`, and `Testing`.
- Anti-patterns are listed in `What We Do Not Do`, with reasons.
- The guidance is specific to Next.js 15 App Router plus SQLite through Drizzle,
  with local `better-sqlite3` and hosted Turso/libSQL options.

## Greenfield Smoke Test Prompt

Paste `CLAUDE.md` into a new repository and ask Claude Code:

```text
Create the initial skeleton for this SaaS app: dashboard route, workspace and
project tables, a create-project server action, a health route, and tests for
the project schema. Follow CLAUDE.md exactly.
```

Expected behavior:

- It creates `src/app`, `src/features`, `src/server`, and `src/lib` instead of a
  flat app.
- It places Drizzle schema in `src/server/db/schema.ts`.
- It validates environment variables in `src/lib/env.ts`.
- It validates the create-project input with Zod on the server.
- It does not create a generic `services` folder.
- It adds or updates `package.json` scripts matching the documented workflow.

## Manual Review Checklist

- The file is opinionated rather than generic: it selects Drizzle, SQLite,
  Next.js 15 App Router, server actions, Zod, and clear ownership boundaries.
- Every major rule includes a practical reason.
- The guidance is usable without modifying placeholders.
- The template avoids project-specific secrets, private configuration, and
  personal workflow assumptions.
