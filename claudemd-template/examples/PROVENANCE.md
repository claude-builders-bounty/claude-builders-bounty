# Test Provenance — CLAUDE.md comprehension test

## Method

1. Created a greenfield Next.js 15 + better-sqlite3 scaffold matching the
   folder structure the template describes (`db/index.ts`, `db/migrations/0001_init.sql`,
   `lib/queries/users.ts`, `lib/auth.ts`, `app/(marketing)/`, `app/(app)/`,
   `components/ui/`, `package.json` with the documented scripts).
2. Dropped `CLAUDE.md` into the project root.
3. Gave a fresh Claude Code session **only** the project path and one task:

   > "add a 'projects' feature: each user can have many projects. Follow the
   > project's CLAUDE.md conventions exactly. Create the database migration
   > and a query module."

   No further instruction about migrations, columns, or conventions — the
   CLAUDE.md was the only context.

## Result — passed, zero clarifying questions

The session completed in ~37 seconds and created exactly two files:

- `db/migrations/0002_projects.sql`
- `lib/queries/projects.ts`

Compliance verified by reading the produced files:

| Rule from CLAUDE.md | Produced |
|---|---|
| Migration named `NNNN_snake_case.sql` | `0002_projects.sql` ✓ |
| Never edit an applied migration | new file, `0001_init.sql` untouched ✓ |
| Wrapped in a transaction | `BEGIN;` … `COMMIT;` ✓ |
| `id TEXT PRIMARY KEY` + `created_at`/`updated_at` ISO defaults | ✓ |
| FK `user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE` | ✓ |
| Queries in `lib/queries/<domain>.ts`, typed in/out | ✓ |
| Bound parameters only, no string building | `db.prepare("… ?").get(id)` ✓ |
| `create*` returns the row via a `find*` helper (users.ts pattern) | ✓ |
| Naming: table plural, columns snake_case, functions camelCase | ✓ |

The session also self-flagged one judgment call (adding
`CREATE INDEX idx_projects_user_id`, justified by the `listProjectsByUserId`
query) and noted — correctly — that `scripts/` was empty, which was out of
scope for the task. Both behaviors are exactly what an understood context
looks like.

## Files in examples/

- `0002_projects.sql` — verbatim output of the test session
- `projects.ts` — verbatim output of the test session
