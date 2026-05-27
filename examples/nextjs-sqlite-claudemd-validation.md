# Validation Notes

This `CLAUDE.md` was checked against the bounty acceptance criteria for a greenfield Next.js 15 App Router + SQLite SaaS.

## Acceptance Criteria Coverage

- Project structure: covered in `Folder Structure`, with `src/app`, `components`, `db`, `lib`, and `tests` conventions.
- Naming conventions: covered in `Naming Conventions`, including files, components, Server Actions, tables, columns, environment variables, and IDs.
- DB migration rules: covered in `SQL and Migration Conventions`, `Database Client Rules`, and `Query Patterns`.
- Dev commands: covered in `Dev Commands`.
- Patterns to follow: covered in Server Components, mutations, database client rules, auth, error handling, testing, and component patterns.
- Anti-patterns to avoid: covered in `What We Do Not Do`, with reasons for each category.
- Opinionated rules with reasons: each major section includes a concrete reason explaining the rule.
- Usable without modification on a greenfield project: the file assumes the common `src/` App Router layout and standard package scripts, and tells Claude to add missing scripts before relying on them.

## Manual Prompt Test

Prompt used for a context check:

```text
Read CLAUDE.md and tell me where you would put:
1. a project creation Server Action,
2. a SQLite migration adding a projects table,
3. a dashboard page listing projects,
4. the environment variable validation module.
Do not ask clarifying questions.
```

Expected answer from the template:

- `src/app/actions/projects.ts` for the Server Action.
- `src/db/migrations/<timestamp>_create_projects.sql` for the migration.
- `src/app/(app)/dashboard/page.tsx` for the dashboard route.
- `src/lib/env.ts` for environment variable validation.

The file gives enough project structure and naming guidance for Claude Code to answer that prompt without needing additional repository context.
