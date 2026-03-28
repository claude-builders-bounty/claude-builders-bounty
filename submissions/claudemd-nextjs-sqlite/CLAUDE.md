# CLAUDE.md

## Stack

- **Framework:** Next.js 15 (App Router, React 19, Server Components by default)
- **Database:** SQLite via `better-sqlite3` (local dev) / Turso `@libsql/client` (production)
- **ORM:** None. Raw SQL with typed helpers. ORMs hide SQLite's strengths and add startup cost.
- **Auth:** `next-auth` v5 (Auth.js) with database session strategy
- **Styling:** Tailwind CSS 4 with `cn()` utility (clsx + tailwind-merge)
- **Package manager:** pnpm (lockfile committed, no npm/yarn)
- **Node:** >=20. Required for native `better-sqlite3` bindings.

## Project Structure

```
app/
  (auth)/login/page.tsx          # Auth route group (no layout chrome)
  (auth)/register/page.tsx
  (dashboard)/layout.tsx         # Authenticated layout with sidebar
  (dashboard)/page.tsx           # Dashboard home
  (dashboard)/settings/page.tsx
  (marketing)/page.tsx           # Public landing page
  (marketing)/pricing/page.tsx
  api/webhooks/stripe/route.ts   # Webhook handlers only — no REST APIs
lib/
  db/
    client.ts                    # Database connection singleton
    migrate.ts                   # Migration runner (runs on startup)
    migrations/                  # Numbered SQL files: 001_create_users.sql
    queries/
      users.ts                   # Typed query functions: getUserById(), createUser()
      teams.ts
  auth.ts                        # Auth.js config
  utils.ts                       # cn(), formatDate(), etc. (no grab-bag files over 100 lines)
components/
  ui/                            # Primitives: button.tsx, input.tsx, dialog.tsx
  forms/                         # Form-specific: login-form.tsx, settings-form.tsx
  layouts/                       # Sidebar, header, footer
actions/
  users.ts                       # Server Actions: updateProfile(), deleteAccount()
  billing.ts
types/
  db.ts                          # Database row types — mirrors table schemas exactly
  index.ts                       # App-wide shared types
```

## Dev Commands

```bash
pnpm dev                  # Start dev server (runs migrations automatically)
pnpm build                # Production build (type-checks + builds)
pnpm test                 # Run vitest (unit + integration)
pnpm test:e2e             # Playwright end-to-end tests
pnpm db:migrate           # Run pending migrations: tsx lib/db/migrate.ts
pnpm db:seed              # Seed dev data: tsx lib/db/seed.ts
pnpm db:studio            # Open Drizzle Studio or sqlite3 CLI for inspection
pnpm lint                 # ESLint + tsc --noEmit
pnpm typecheck            # tsc --noEmit only
```

## Database Conventions

### Connection

```typescript
// lib/db/client.ts — ONE connection, reused everywhere
import Database from "better-sqlite3";
const db = new Database("data/app.db", { wal: true }); // WAL mode always
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");       // SQLite doesn't enforce FKs by default
db.pragma("busy_timeout = 5000");     // Wait 5s on lock instead of failing
export default db;
```

For Turso in production, swap the import to `@libsql/client` and use `createClient({ url, authToken })`. The query interface stays the same because all SQL lives in typed functions, not scattered across components.

### Migrations

- Files: `lib/db/migrations/001_create_users.sql`, `002_add_teams.sql`, ...
- Sequential numbering, never reorder. Name describes what it does.
- Each file is a single transaction. Wrap DDL in `BEGIN; ... COMMIT;`.
- **Never modify a shipped migration.** Write a new one. SQLite has limited `ALTER TABLE` — use the rename-and-recreate pattern for column changes.
- Migration runner executes on app startup in dev. In production, run explicitly before deploy.
- Track applied migrations in a `_migrations` table (name TEXT PRIMARY KEY, applied_at TEXT).

### SQL Style

- Table names: `snake_case`, plural (`users`, `team_members`, `api_keys`)
- Columns: `snake_case` (`created_at`, `updated_at`, `is_active`)
- Every table has `id TEXT PRIMARY KEY` (ULID or nanoid — not autoincrement, which breaks distributed sync with Turso)
- Every table has `created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))`
- Use `TEXT` for dates (ISO 8601). SQLite has no native date type; text sorts correctly and is human-readable.
- Use `INTEGER` for booleans (0/1). Name them `is_*` or `has_*`.
- Foreign keys always have `ON DELETE CASCADE` or explicit `ON DELETE SET NULL` — never leave it as default NO ACTION silently.

### Query Functions

```typescript
// lib/db/queries/users.ts
import db from "../client";
import type { User } from "@/types/db";

export function getUserById(id: string): User | undefined {
  return db.prepare("SELECT * FROM users WHERE id = ?").get(id) as User | undefined;
}

export function createUser(data: { id: string; email: string; name: string }): User {
  return db.prepare(
    "INSERT INTO users (id, email, name) VALUES (?, ?, ?) RETURNING *"
  ).get(data.id, data.email, data.name) as User;
}
```

Every query is a named function with typed inputs and outputs. No raw SQL outside `lib/db/queries/`.

## Component Patterns

- **Server Components by default.** Only add `"use client"` when you need interactivity (onClick, useState, useEffect). Most pages are server components that fetch data directly.
- **Server Actions for mutations.** Define in `actions/*.ts` with `"use server"` at the top. Use `useActionState` (React 19) for form state, not useState + fetch.
- **No API routes for internal data.** `app/api/` is only for webhooks and external integrations. Internal reads happen in Server Components; writes go through Server Actions.
- **Colocate loading/error states.** Use `loading.tsx` and `error.tsx` in route segments, not manual Suspense boundaries everywhere.
- **Props over context.** Pass data down from Server Components. React Context is for client-side-only state (theme, sidebar open). Never use context to avoid prop drilling of server data.
- **One component per file.** File name matches the default export: `login-form.tsx` exports `LoginForm`.

### Naming

- Components: `PascalCase` (`UserCard`, `LoginForm`)
- Files: `kebab-case` (`user-card.tsx`, `login-form.tsx`)
- Server Actions: `camelCase` verbs (`updateProfile`, `deleteTeam`)
- Query functions: `camelCase` with get/create/update/delete prefix
- Types: `PascalCase`, matching the DB table singular (`User`, `Team`, `ApiKey`)
- Route groups: `(parenthetical)` for layout grouping, never for URL segments

## What We Don't Do (and Why)

| Anti-pattern | Why it's bad |
|---|---|
| `"use client"` on pages or layouts | Opts out of Server Components. You lose streaming, direct DB access, and zero-JS delivery. Add it only to the smallest interactive leaf. |
| Prisma or Drizzle ORM | Adds 2-10s cold start penalty. SQLite is fast *because* it's embedded — an ORM's query planner fights SQLite's. Raw SQL with typed helpers is 50 lines of code and zero dependencies. |
| `useEffect` for data fetching | Server Components fetch data during render. `useEffect` means client waterfalls, loading spinners, and double requests in dev. |
| `fetch('/api/...')` from client components | Use Server Actions instead. Internal API routes add latency, need separate auth checks, and create two sources of truth for validation. |
| `autoincrement` integer primary keys | Breaks Turso multi-region sync. Text IDs (ULID/nanoid) are globally unique and sort chronologically. |
| `.env.local` for database path | Database path is in `lib/db/client.ts`. One source of truth. Env vars are for secrets (auth tokens, API keys), not config that varies per-environment — use `next.config.ts` for that. |
| Barrel exports (`index.ts` re-exports) | Barrel files break tree-shaking and slow down TypeScript language server. Import directly from the source file. |
| `any` type assertions | Use `unknown` + type narrowing. `as any` silently breaks type safety and hides bugs that SQLite's loose typing already makes easy to introduce. |
| Storing JSON blobs in SQLite columns | Use proper relational tables. JSON columns can't be indexed, can't have foreign keys, and turn your database into a document store without the document store tooling. |
| `moment` or `dayjs` for dates | Use native `Intl.DateTimeFormat` and `Date`. The app stores ISO 8601 strings — formatting is a presentation concern handled in components with zero dependencies. |

## Testing

- **Unit tests:** Vitest for query functions and utilities. Test against a real SQLite in-memory database (`:memory:`), not mocks. SQLite is fast enough that mocking it adds complexity for no benefit.
- **Component tests:** Vitest + React Testing Library for interactive client components.
- **E2E tests:** Playwright for critical paths (signup, login, core CRUD).
- **No test for every component.** Test behavior, not implementation. A Server Component that just renders data doesn't need a test — the E2E covers it.

## Error Handling

- Server Actions return `{ success: boolean; error?: string }` — never throw from Server Actions. The client uses `useActionState` to read the result.
- Database errors in query functions: let them throw. The nearest `error.tsx` boundary catches it.
- Validate all inputs at the Server Action boundary with zod. The database is the last line of defense, not the first.
