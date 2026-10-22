# Actual Claude Code response

Both files read. Here is the validation and plan.

## What the scaffold already provides (defaults met)
- **Scripts** (`dev`, `build`, `start`, `typecheck`, `db:migrate`, `test`) match the contract exactly.
- **Driver**: `better-sqlite3 ^12.0.0` (with `@types/better-sqlite3`) — local SQLite, no ORM, matches the template.
- **Next/React**: `next ^15.0.0` + `react/react-dom ^19.0.0`, TypeScript, `server-only`, `tsx` present. Note: the lockfile was **not** inspected (only the two permitted files); the contract requires inspecting `package-lock.json` before using version-sensitive APIs (e.g. awaited `cookies()`), and the `^15.0.0` range must resolve to a patched 15.x, not a canary. That check is unverified.

## Implementation plan (defaults applied, nothing implemented)

**Database driver & connection** — `src/lib/db.ts` (`import 'server-only'`), one process-wide connection with a `globalThis` cache in dev, PRAGMAs `foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000` set outside transactions, `DATABASE_PATH` defaulting to `./data/app.db`.

**Migration strategy** — Since this is effectively an empty project, bootstrap order per the contract: create `src/lib/db.ts`, `scripts/migrate.ts` (runner creating the `_migrations` ledger, SHA-256 checksums, single-writer transaction, refuse drift/duplicate prefixes, rollback on failure), and `tests/migrate.test.ts` (fresh DB, second no-op run, checksum drift, failing-migration rollback on temp files) **before** feature migrations. Then:
- `db/migrations/0001_initial.sql` — tenant scaffolding: `workspaces`, `workspace_members`, and `notes`. No seed rows (no pretend tenants). Schema only; protected paths still fail closed because no session can be established.
- `db/migrations/0002_notes.sql` — or fold `notes` into 0001; prefer one 0001 so the feature table ships with the tenant columns (`workspace_id`, `created_by`, `created_at`, `updated_at`, `archived_at` nullable, UUID TEXT PK, NOT NULL constraints, no floats).
- Runner owns BEGIN/COMMIT; SQL files contain no PRAGMAs/transactions/side effects.

**Session/tenant handling** — `src/lib/auth.ts` (server-only) exposes a `requireUserWorkspace()` boundary that returns a typed 401 **until a real session adapter exists**; no hard-coded workspace, no `x-user-id` header trust. Every read scoped by `workspace_id` derived from verified membership; every mutation includes `id + workspace_id`; cross-tenant miss → 404. Mutations validate `Origin`; GET handlers never mutate. `src/lib/errors.ts` maps expected validation failures to field errors and unexpected errors to an opaque request ID.

**Feature files** (kebab-case, SQL kept near the feature):
- `src/features/notes/notes.repository.ts` — parameterized SQL: `list` (newest first `(created_at, id)`, default 25, max 100), `create`, `update`, `archive` (soft, sets `archived_at`, excluded from normal reads). Creator-only update/archive; membership check on every call.
- `src/features/notes/notes.schema.ts` — server-boundary validation: title ≤ 200 chars, body ≤ 100,000 chars, plain text (no HTML/Markdown).
- UI boundary — Server Components default: `src/app/(app)/notes/page.tsx` (list, empty state), `src/app/(app)/notes/new/page.tsx`, `src/app/(app)/notes/[id]/page.tsx` (detail/edit/archive). One `use client` form component (`src/components/ui/note-form.tsx` or `src/features/notes/note-form.tsx`) with accessible labels, pending state, error display, and disabled duplicate submit (plus server-side idempotency via a unique key). Pass only serializable view models.
- Route handlers/Server Actions call the same validated server functions and enforce auth themselves.

**Commands to run after implementation** (in order): `npm ci` → `npm run db:migrate` → `npm run typecheck` → `npm test` → `npm run build`. Then manual `npm run dev` smoke check. Report exact output/failures; build success won't be treated as proof of authorization.

## Missing product decision
**None.** The contract's defaults cover every aspect this feature raises: permissions (members read; creator updates/archives), 200/100,000 text limits, plain-text rendering, soft-archive delete, `(created_at, id)` sort with 25/100 pagination, no sharing/realtime. These will be stated in the plan rather than asked as setup questions.

The one genuine **blocker** (not a product choice): there is no real session adapter, so same-tenant-success and cross-tenant-denial integration tests cannot pass through the real stack yet. I would implement fail-closed 401 paths and prove anonymous rejection now, and defer the full authorization matrix until a real session adapter is configured — per "never invent completed tests or authentication."
