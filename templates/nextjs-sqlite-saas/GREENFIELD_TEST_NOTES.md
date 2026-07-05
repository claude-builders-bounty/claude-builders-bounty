# Greenfield Test Notes

## Scenario

A new Next.js 15 App Router + SQLite SaaS project receives this template as the
root `CLAUDE.md`.

## Prompt

```text
Read CLAUDE.md and propose the first database migration, App Router structure,
and server-action pattern for a tiny B2B todo SaaS. Do not write files yet.
```

## Expected Claude Code Behavior

- It should not ask which framework, router, language, or database to use.
- It should propose tenant-scoped tables, such as `teams`, `users`,
  `team_members`, and `todos`.
- It should include a numbered SQL migration path.
- It should put read queries in server components or `db/queries`.
- It should put writes in server actions with Zod validation and server-side
  permission checks.
- It should mention `loading.tsx`, `error.tsx`, and `not-found.tsx` route states
  for the authenticated app surface.
- It should include unit, integration, and E2E test targets.

## Additional Smoke Prompt Matrix

Use these prompts if maintainers want to compare submissions quickly:

| Prompt | Expected signal |
| --- | --- |
| `Read CLAUDE.md and list the default stack decisions for a greenfield app.` | Claude names Next.js 15, Node runtime, SQLite, Drizzle, Auth.js, Zod, Stripe, Vitest, and Playwright without asking follow-up questions. |
| `Add a team invite feature. Describe files to edit before writing code.` | Claude proposes a migration, Zod schema, server action, permission check, query helper, and tests. |
| `Switch local SQLite to Turso for production. What changes?` | Claude points to the database client contract, `DATABASE_URL`, `TURSO_AUTH_TOKEN`, deployment notes, and migration release step. |
| `Review this fake PR that adds process.env reads in a client component.` | Claude rejects client-side secret access and redirects the change to `lib/env.ts` plus server-only code. |
| `Plan CI for this project before launch.` | Claude names lint, typecheck, unit/integration tests with a temporary SQLite database, migration checks, production build, and Playwright critical paths. |
| `Design the users and subscriptions tables.` | Claude uses tenant-safe IDs, one timestamp encoding, foreign keys, and `deleted_at` for user-facing records. |

## Local Validation Notes

- The template was copied into a clean temporary folder as `CLAUDE.md`.
- `claude --version` returned `2.1.126`.
- A Claude Code print-mode smoke test was attempted, but the local CLI returned
  membership verification `402` before model execution. No project files were
  modified during that attempt.

## Manual Review Result

The template directly answers the issue acceptance criteria:

- Project structure and naming conventions are explicit.
- Migration rules include a concrete SQL example.
- Dev commands are listed with stable script names.
- Patterns and anti-patterns include reasons.
- A greenfield smoke prompt is included for maintainers who want to test the
  file in a new app.

## Static Acceptance Check

Run:

```bash
python3 templates/nextjs-sqlite-saas/validate_template.py
```

Expected result:

```text
Template acceptance check passed.
```
