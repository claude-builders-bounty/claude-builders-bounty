# Greenfield Test Notes

## Acceptance Mapping

- Project structure: covered in `CLAUDE.md` under `Project Structure`.
- Naming conventions: covered in `Naming Conventions`.
- Database migration rules: covered in `SQL And Migration Rules`.
- Next.js App Router patterns: covered in `Component Patterns`, `Data Access Pattern`, and `Claude Workflow Rules`.
- Opinionated anti-patterns with reasons: covered in `What We Do Not Do, And Why`.
- Setup path: covered in `README.md`.

## Suggested Smoke Test

Prompt:

```text
Read CLAUDE.md and propose the first migration, route structure, and server-action pattern for a tiny B2B todo SaaS. Do not write files yet.
```

Expected response:

- Uses Next.js 15 App Router and SQLite without asking for a stack choice.
- Proposes tenant-scoped tables such as `organizations`, `users`, `memberships`, and `todos`.
- Uses numbered SQL migrations under `migrations/`.
- Places authenticated app routes under `app/(app)/`.
- Uses server actions for form mutations and raw parameterized SQL for reads/writes.
- Calls out validation and authorization checks before implementation.
