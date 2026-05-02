# Issue #2 sample validation

This `CLAUDE.md` was drafted for a greenfield SaaS with:

- Next.js 15 App Router
- TypeScript strict mode
- SQLite via `better-sqlite3` locally or Turso/libSQL in production
- Server-first React components

## Prompt used to validate usefulness

```text
You are Claude Code inside a new Next.js 15 + SQLite SaaS repository. Read CLAUDE.md and propose where to put:
1. a workspace creation form,
2. a SQL migration for workspaces,
3. a repository function for fetching workspaces by slug,
4. the auth/authorization check.
Do not ask clarifying questions unless CLAUDE.md is missing required conventions.
```

## Expected behavior

A suitable assistant should answer without clarification and place code in:

- `app/(app)/...` or `features/workspace/` for the workspace creation UI/action
- `migrations/000x_add_workspaces.sql` for schema
- `lib/db/workspace.repo.ts` for SQL access
- `lib/auth/permissions.ts` or feature-level service for tenant authorization

This confirms the file gives concrete structure, naming, migration, data-access, and anti-pattern guidance rather than generic advice.
