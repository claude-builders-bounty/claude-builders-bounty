# Claude Code Context Check

Use this after copying `templates/nextjs-sqlite-saas/CLAUDE.md` to the root of a new Next.js 15 App Router project.

## Test Setup

Create or use a greenfield project with this shape:

```text
src/app/page.tsx
src/lib/env.ts
src/lib/db/client.ts
src/db/migrations/
package.json
CLAUDE.md
```

The exact app does not need real billing or auth yet. The check is whether Claude Code follows the template without asking broad clarifying questions.

## Prompt 1

```text
Add team billing status support.
```

Expected behavior:

- Proposes a timestamped SQL migration under `src/db/migrations`.
- Uses a `billing_status` column with a SQLite `CHECK` constraint.
- Mentions a rollback note and does not edit existing applied migrations.
- Keeps database access server-only.

## Prompt 2

```text
Create a settings page where team admins can invite a member.
```

Expected behavior:

- Adds route files under `src/app/(app)/team-settings`.
- Creates domain code under `src/features/teams`.
- Uses a Server Component page with a small Client Component only for form interactivity if needed.
- Validates input with Zod before a server action calls a service.
- Checks authorization on the server, not only in the UI.

## Prompt 3

```text
Add a webhook endpoint for subscription updates.
```

Expected behavior:

- Places the route handler under `src/app/api/<provider>/route.ts`.
- Moves signature verification and business logic into a billing service.
- Avoids logging secrets or full provider payloads.
- Updates tests for state transitions or query behavior.

## Pass Criteria

Claude Code passes this check when its first implementation plan references the template's boundaries, names the files it will touch, and does not ask generic questions about project structure, naming, or migration style.
