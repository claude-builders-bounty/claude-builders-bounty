# `src/db/` — database layer

All SQL lives here. Application code never imports `better-sqlite3` or `@libsql/client` except via `src/lib/db.ts`.

| Subfolder | Purpose |
|-----------|---------|
| `migrations/` | Append-only `.sql` files applied in lexicographic order |
| `queries/` | One module per aggregate; parameterized reads and writes |

**Rules:** Migrations are never edited after merge — add new files. Queries bind dynamic values with `?` placeholders, never string concatenation.
