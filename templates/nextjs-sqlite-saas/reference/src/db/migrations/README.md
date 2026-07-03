# `src/db/migrations/` — SQL migrations

Append-only `.sql` files named `YYYYMMDDHHMMSS_snake_slug.sql` (UTC). Applied by `scripts/migrate.ts` via `pnpm db:migrate`.

**Rules:**

1. Never edit a migration already on `main` — fix forward with a new file.
2. One schema concern per file.
3. Prefer `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.
4. Child tables reference parents via `org_id` for tenant scope.

Each applied file is recorded in `_migrations`; CI asserts file count matches recorded rows.
