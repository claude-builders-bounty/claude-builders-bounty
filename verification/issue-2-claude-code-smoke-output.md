# Claude Code smoke-test output

- Run time: 2026-09-25T11:52:37+08:00 (Asia/Shanghai)
- Claude Code: 2.1.282 (Claude Code)
- Fixture: fresh `create-next-app@15.5.26` project, with the template copied to its root and six placeholder files
- Mode: plan/read-only; only project/local settings loaded; API and gateway credential variables removed for this process; no session persistence
- Result: Claude Code inspected the manifest and source files, proposed tenant-scoped authorization and an append-only migration, identified missing scripts and test infrastructure, and did not ask for task clarification.

The generated plan-file destination is omitted from this public copy. The captured plan follows.

---

# Plan: Server Action to archive a project (workspace-scoped)

## Context

The repo is a greenfield Next.js 15 + SQLite scaffold. Every piece needed for this feature exists only as a stub or is entirely absent:

- `src/features/projects/server/mutations.ts` → `archiveProject()` is a no-op stub (no params, no `'use server'`, no logic).
- `src/features/projects/server/queries.ts` → `getProject()` is a no-op stub.
- `src/server/db/client.ts` → `getDb()` just `throw`s; no `better-sqlite3` (or any driver) is installed.
- `src/server/auth/session.ts` → only a `Session` **type**, no function to read the actual session.
- `src/server/db/migrations/0001_create_projects.sql` → `projects` table has only `id, workspace_id, name`; no `archived_at`, no unique/index on `workspace_id`, no migrations-tracking table, no migration runner file exists.
- No validation library (Zod etc.) is installed; `features/projects/schemas.ts` doesn't exist.
- No test framework is installed (no Jest/Vitest/node:test); no test files exist anywhere.
- No lockfile, `.env.example`, `.nvmrc` exist.

`package.json` scripts are only `dev`, `build`, `start`, `lint` — **no `typecheck`, `test`, or `db:migrate` script exists today.** Per CLAUDE.md ("Discover commands from `package.json`"), I will not claim these run; I list them as scripts to add only because the task requires them.

Because almost nothing is wired up, this plan necessarily includes the minimal supporting pieces (db driver, connection helper, session reader, migration runner, validation) needed to make the Server Action real — not speculative extras. Everything is scoped to exactly what archiving a project touches, per CLAUDE.md's "don't add dependencies for a one-off helper" — but a driver, a session getter, and a migration runner are prerequisites for this one-off, not extras.

## 1. Files to inspect/change

Already inspected (facts above are from direct reads, not assumptions):
- `package.json`, `tsconfig.json`, `next.config.ts`, `.gitignore`
- `src/server/db/client.ts`, `src/server/db/migrations/0001_create_projects.sql`
- `src/server/auth/session.ts`
- `src/features/projects/server/{mutations.ts,queries.ts}`
- `src/app/(app)/projects/[projectId]/page.tsx`

To change/create:
- `package.json` — add `better-sqlite3` (+ `@types/better-sqlite3`), a validation lib (`zod`), and the `typecheck`/`db:migrate` scripts (and a test runner + `test` script if tests are required — see §4).
- `src/server/db/client.ts` — real singleton connection: open the file from a server-only env var (e.g. `DATABASE_PATH`, default `./data/dev.sqlite3` for local dev), `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL` (guarded for durable local storage), bounded `PRAGMA busy_timeout`. Must not be imported by any Client Component; add `import 'server-only'`.
- `src/server/db/migrations/0002_add_projects_archived_at.sql` — new append-only migration (see §3). Do **not** edit `0001_create_projects.sql`.
- `src/server/db/migrate.ts` — a migration runner does not exist; one is needed to apply `0001` and `0002` in order and record applied IDs in a tracking table, since `db:migrate` has nothing to run today.
- `src/server/auth/session.ts` — add the actual session-reading function (e.g. `getSession(): Promise<Session>` or similar, reading from cookies) — this repo has no auth mechanism wired yet, so the exact source (cookie/JWT/etc.) is a call the implementer must make based on how auth is later added; the Server Action must depend on this function's return value, never on a client-submitted workspace/user id.
- `src/features/projects/schemas.ts` — new file: input validation for the archive action (e.g. `{ projectId: string }` non-empty).
- `src/features/projects/server/mutations.ts` — implement `archiveProject`.
- `src/features/projects/server/queries.ts` — optionally add a workspace-scoped `getProject` used to confirm the row before/after archiving, following the same predicate pattern.
- `src/app/(app)/projects/[projectId]/page.tsx` — wire the page to call the mutation from a form (out of scope to fully build the UI, but the plan should note the action needs a caller; keep this Server Component thin).

## 2. Authorization and SQL predicates

- Never accept `workspace_id` from the client. The Server Action's only untrusted input is `projectId` (validated via the new schema).
- Derive `workspaceId` server-side from the session: `const { workspaceId } = await getSession()`.
- Mark the mutation file/function server-only: `'use server'` at the top of the action, and route/runtime declared `export const runtime = 'nodejs'` wherever `better-sqlite3` is touched (Server Actions run on Node by default, but any Route Handler equivalent must declare this explicitly per CLAUDE.md).
- Scope the update by **both** the primary key and the tenant key in the same statement, and check the affected row count:

```ts
const stmt = db.prepare(
  `UPDATE projects
   SET archived_at = ?
   WHERE id = ? AND workspace_id = ? AND archived_at IS NULL`
);
const result = stmt.run(new Date().toISOString(), projectId, workspaceId);
if (result.changes === 0) {
  // either the project doesn't exist, belongs to another workspace,
  // or is already archived — treat all three as "not found" to the caller
  throw new Error("Project not found");
}
```

- This predicate means a leaked/guessed `projectId` belonging to another workspace updates zero rows instead of leaking existence or succeeding cross-tenant.
- Add a composite index to support this predicate efficiently: `CREATE INDEX idx_projects_workspace_id ON projects(workspace_id);` (add in the same or a follow-up migration).
- After a successful write, call `revalidatePath` (or `revalidateTag`) for the affected project/list paths — after the transaction commits, not before.
- Use `better-sqlite3`'s synchronous transaction wrapper only for the DB write itself; do not `await` or call `revalidatePath`/redirect inside the transaction callback.

## 3. Append-only migration for `archived_at`

`0001_create_projects.sql` only has `id, workspace_id, name` — no `archived_at` column exists, so it must be added via a **new** migration file, never by editing `0001`:

`src/server/db/migrations/0002_add_projects_archived_at.sql`:

```sql
ALTER TABLE projects ADD COLUMN archived_at TEXT;
CREATE INDEX idx_projects_workspace_id ON projects(workspace_id);
```

- `archived_at` is nullable `TEXT` storing ISO-8601 UTC (CLAUDE.md's chosen timestamp representation); `NULL` means "active," a non-null ISO string means "archived." SQLite's `ALTER TABLE ADD COLUMN` requires the new column to have no non-constant default when there's no `NOT NULL`, so a nullable column with no default is correct here and needs no backfill.
- Wrap in a transaction if the runner doesn't already wrap each file (SQLite supports transactional DDL for `ALTER TABLE ADD COLUMN` and `CREATE INDEX`).
- Since no migration runner exists yet, `src/server/db/migrate.ts` needs a `schema_migrations` (or similar) tracking table created on first run, recording each applied filename so re-running is idempotent — required before this or `0001` can be trusted to run safely in CI/deploy.
- Validate with `PRAGMA foreign_key_check` and `PRAGMA integrity_check` after applying, and run the runner twice against a scratch DB file to confirm idempotency, per CLAUDE.md.

## 4. Focused tests and commands

No test framework is installed today — this must be added, not assumed. Given `better-sqlite3` is synchronous/native, plain `node:test` (built into Node, zero new dependency) is the smallest addition consistent with "don't add dependencies for a one-off helper"; if the team prefers Vitest that's an equally reasonable call, but it wasn't already present so it can't be assumed.

Tests to add (against a scratch SQLite file, not the dev/prod db):
1. **Migration test** — run `migrate.ts` twice against a temp file; assert `0002` adds the `archived_at` column, `PRAGMA foreign_keys` reports `1`, and `PRAGMA integrity_check`/`PRAGMA foreign_key_check` pass.
2. **Tenant isolation test** — seed two workspaces with one project each; call `archiveProject` with workspace A's session but workspace B's `projectId`; assert it throws/returns not-found and workspace B's row is untouched (`archived_at` still `NULL`).
3. **Happy path test** — archive a project owned by the session's workspace; assert `archived_at` is set to a valid ISO string and a second archive call on the same row is a no-op/not-found (due to the `archived_at IS NULL` predicate).
4. **Validation test** — call the action with an empty/malformed `projectId`; assert it's rejected before touching the DB.

Commands (only what's real today, plus what the task requires adding):
- Existing: `npm run lint`, `npm run build` — run these after implementation.
- To add and then run: `npm run typecheck` (`tsc --noEmit`), `npm test` (whatever runner is chosen), `npm run db:migrate` (pointed at a throwaway/test DB file — never production, per CLAUDE.md).
- Do not claim `npm run typecheck`, `npm test`, or `npm run db:migrate` exist until they are added in this change.

## Verification

- `npm run db:migrate` (new script) against a scratch file → confirm `0001` + `0002` apply cleanly twice.
- `npm test` (new) → all four focused tests pass, especially the cross-workspace isolation test.
- `npm run lint`, `npm run typecheck` (new), `npm run build` all pass.
- Manually exercise via the (app)/projects/[projectId] page once wired: archive a project, confirm it disappears/shows archived state, and confirm attempting to archive another workspace's project id (e.g. via direct action call in a script) is rejected.
