# `src/` — application source

Server-first Next.js 15 App Router layout. Each subdirectory has its own `README.md`.

| Folder | Role |
|--------|------|
| `db/` | SQL migrations and query modules — no imports from client code |
| `lib/` | Env parsing, DB singleton, auth helpers — shared server utilities |
| `server/` | `'use server'` mutations and background jobs |
| `components/` | UI primitives and feature components |

**Rules:** `src/app/` holds routing only (not shipped in this minimal reference). Query modules live in `db/queries/`; the only DB driver import is `lib/db.ts`.
