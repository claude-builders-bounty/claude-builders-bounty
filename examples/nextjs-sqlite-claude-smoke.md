# Smoke Test: Next.js + SQLite CLAUDE.md

Repository used for the smoke test: a fresh Next.js 15 App Router project with TypeScript and a local SQLite database.

Prompt:

```text
Read CLAUDE.md, then add a projects table and a create project flow for authenticated users.
```

Expected Claude Code behavior after reading the template:

- Creates `db/migrations/0001_initial.sql` or the next numbered migration instead of changing the database at runtime.
- Adds typed query helpers under `db/queries/projects.ts`.
- Adds business orchestration under `server/services/projects.ts`.
- Adds a Server Action such as `createProjectAction` that validates input with Zod.
- Keeps the dashboard page as a Server Component and uses a small Client Component only for interactive form state if needed.
- Checks authenticated user and tenant ownership before writing project rows.
- Runs `npm run typecheck`, `npm run lint`, and targeted tests before reporting completion.

This confirms the template gives Claude Code enough project context without requiring extra clarifying questions about structure, migrations, or server/client boundaries.

