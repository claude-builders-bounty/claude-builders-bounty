# CLAUDE.md — Next.js 15 + SQLite SaaS

You are working on a multi-tenant SaaS built with **Next.js 15 App Router**, **TypeScript strict**, **SQLite** (via `better-sqlite3` locally; Turso/libSQL in production), and **Tailwind CSS**. Treat this file as the source of truth. Do not ask the user to restate stack choices.

## Stack & pinned versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 App Router | Server Components by default; colocate routes and UI |
| Language | TypeScript `strict: true` | Catch data-shape bugs at compile time |
| Database | SQLite + Drizzle ORM | Zero-ops local dev; typed queries; easy migrations |
| Auth | Auth.js v5 (NextAuth) | Session cookies; works in Server Components |
| Styling | Tailwind CSS 4 + `cn()` helper | Utility-first; no CSS modules unless animation-heavy |
| Validation | Zod | Shared schemas for forms, API, and DB inserts |
| Tests | Vitest + React Testing Library | Fast unit tests; no Jest |

**Package manager:** `pnpm` only. Never add `package-lock.json` or `yarn.lock`.

## Commands

```bash
pnpm dev              # http://localhost:3000
pnpm build            # production build (must pass before PR)
pnpm lint             # eslint
pnpm test             # vitest
pnpm db:generate      # drizzle-kit generate (after schema change)
pnpm db:migrate       # apply migrations to ./data/app.db
pnpm db:studio        # drizzle-kit studio (local only)
```

Environment files: `.env.local` (never commit). Required keys:

```
DATABASE_URL=file:./data/app.db
AUTH_SECRET=          # openssl rand -base64 32
AUTH_URL=http://localhost:3000
```

## Folder structure

```
app/
  (marketing)/          # public pages — no auth
  (app)/                # authenticated SaaS shell
    dashboard/
    settings/
  api/                  # Route Handlers only when RSC cannot suffice
components/
  ui/                   # dumb primitives (Button, Input) — no business logic
  features/             # domain components (InvoiceTable, TeamSwitcher)
lib/
  db/
    schema.ts           # Drizzle table definitions (single file until >300 lines)
    index.ts            # db client singleton
    migrations/         # SQL files — committed, never hand-edit after merge
  auth/
    session.ts          # getSession(), requireUser()
  validators/           # Zod schemas named {entity}Schema
  utils/                # cn(), formatDate(), etc.
data/                   # gitignored — local SQLite files
drizzle.config.ts
```

**Naming**

- Routes: kebab-case folders (`app/(app)/billing-history/page.tsx`)
- React components: PascalCase files (`TeamSwitcher.tsx`)
- Server actions: `actions.ts` colocated in the route segment that owns the mutation
- DB tables: snake_case plural (`team_members`, not `TeamMember`)
- Types: `{Entity}Row` from Drizzle inference; `{Entity}DTO` for API boundaries

## Database & migrations

1. **Schema lives in** `lib/db/schema.ts`. One table per export; relations declared explicitly.
2. **Never** run raw `ALTER TABLE` in application code. Change schema → `pnpm db:generate` → review SQL → `pnpm db:migrate`.
3. **Migrations are append-only.** Do not edit a migration file after it has merged to `main`.
4. **Foreign keys ON.** Enable in Drizzle/sqlite: `PRAGMA foreign_keys = ON` on every connection.
5. **Soft deletes** for user-owned entities (`deleted_at` column). Hard delete only for join tables and audit logs.
6. **Multi-tenancy:** every tenant-scoped table has `organization_id TEXT NOT NULL` with an index. Every query filters by org from session — no exceptions.
7. **IDs:** `TEXT PRIMARY KEY` with `crypto.randomUUID()` — not auto-increment integers (safe for sync/export).

```ts
// lib/db/index.ts pattern — singleton, foreign keys enforced
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL!.replace("file:", ""));
sqlite.pragma("foreign_keys = ON");

export const db = drizzle(sqlite, { schema });
```

**Turso/production:** swap the driver to `@libsql/client` + `drizzle-orm/libsql`; keep identical schema and migration files.

## Component & data patterns

### Default to Server Components

- `page.tsx` and `layout.tsx` are Server Components unless they need hooks or browser APIs.
- Fetch data in the page/layout; pass serializable props to client children.
- Add `"use client"` only on the smallest leaf that needs interactivity.

### Server Actions for mutations

```ts
"use server";
import { requireUser } from "@/lib/auth/session";
import { db } from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function updateProjectName(projectId: string, name: string) {
  const user = await requireUser();
  // validate with Zod, scope by organization_id, then mutate
  revalidatePath("/dashboard/projects");
}
```

- Validate all inputs with Zod at the top of every action.
- Return `{ error: string } | { data: T }` — never throw to the client for validation failures.

### Route Handlers (`app/api/...`)

Use only for: webhooks, OAuth callbacks, or third-party integrations. **Not** for internal CRUD — use Server Actions instead.

### Loading & errors

- Every route segment that fetches data gets `loading.tsx` (skeleton) and `error.tsx` (retry button).
- Use `<Suspense>` boundaries around slow widgets, not whole pages.

## What we don't do (and why)

| Don't | Why |
|-------|-----|
| `useEffect` for data fetching | Use RSC or SWR only in client widgets that poll |
| `pages/` router | App Router only — mixed routers confuse Claude and humans |
| ORM outside Drizzle | One query layer; migrations stay in sync |
| Global Redux/Zustand for server data | Server Components + cache revalidation is enough |
| `any` or `@ts-ignore` | Fix the type; use `unknown` + Zod parse at boundaries |
| Env vars in client components | Leaks secrets; pass config from server parent |
| `SELECT *` in hot paths | Explicit columns — SQLite is fast but payloads matter |
| Middleware auth for static assets | Keep middleware matcher narrow: `/app/:path*` only |
| Creating tables in seed scripts | Seeds insert data; schema changes go through migrations |
| Multiple SQLite files per tenant | Single DB, row-level `organization_id` — simpler backups |

## Security checklist (every PR)

- [ ] Mutations check `organization_id` from session, never from client input alone
- [ ] User input validated with Zod before DB touch
- [ ] No secrets in logs, error messages, or client bundles
- [ ] SQL via Drizzle query builder only — no string concatenation

## When adding a feature

1. Extend `lib/db/schema.ts` if persistence changes → generate migration
2. Add Zod schema in `lib/validators/`
3. Server Action or RSC data loader in the owning route segment
4. UI in `components/features/{domain}/`
5. Vitest for validators and pure helpers; RTL smoke test for complex forms

## Git conventions

- Conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`
- One logical change per PR; migrations in the same PR as schema change
- Run `pnpm build && pnpm lint && pnpm test` before pushing
