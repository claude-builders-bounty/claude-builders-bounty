# Smoke Test

Target project:

```bash
pnpm create next-app@latest acme-saas --ts --tailwind --eslint --app --src-dir --import-alias "@/*"
cp templates/nextjs-sqlite-saas/CLAUDE.md acme-saas/CLAUDE.md
cd acme-saas
claude
```

Prompt used:

```text
Add a team invitation feature with SQLite persistence, a server action, and tests.
```

Expected Claude Code understanding:

- Creates or updates a SQL migration under `src/db/migrations`.
- Keeps database access inside `src/db/repositories`.
- Adds Zod validation for the invitation form/server action.
- Checks current user account membership before mutation.
- Keeps the page/server component boundary separate from a small client form component.
- Adds at least one authorization failure test.

This smoke test maps directly to the `CLAUDE.md` operating rules and is designed so Claude Code can proceed without asking which stack, database, folder structure, migration style, or component boundary to use.
