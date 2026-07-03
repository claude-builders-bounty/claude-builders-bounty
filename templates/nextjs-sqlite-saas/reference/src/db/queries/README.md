# `src/db/queries/` — query modules

One file per domain entity (e.g. `invoices.ts`). Each module:

- Imports `getDb()` from `@/lib/db`
- Uses `db.prepare()` with `?` placeholders for all dynamic values
- Returns typed domain objects, not raw driver rows
- Filters `deleted_at IS NULL` on user-owned data

**Do not:** put SQL in route files, components, or server actions — call query functions instead.
