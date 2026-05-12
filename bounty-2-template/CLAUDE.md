# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

- **Framework**: Next.js 15 (App Router only, no Pages Router)
- **Language**: TypeScript 5.x with `strict: true` — no `any`, no `as` casts unless interfacing with untyped libs
- **Database**: SQLite via `better-sqlite3` in WAL mode — not Turso, not Prisma, not Drizzle
- **Styling**: Tailwind CSS 4 — no CSS modules, no styled-components
- **Components**: shadcn/ui — copy-paste into `components/ui/`, customize freely
- **Auth**: `better-auth` — not NextAuth (too complex for SQLite setups)
- **Testing**: Vitest for unit/integration, Playwright for e2e
- **Package manager**: pnpm — lockfile committed, no `npm` or `yarn`
- **Node**: 22 LTS

## Project Structure

```
app/                    # Next.js App Router routes only
  (auth)/               # Route group for auth pages (login, register)
  (dashboard)/          # Route group for authenticated pages
  api/                  # Route Handlers — only for webhooks & external APIs
  layout.tsx            # Root layout
  page.tsx              # Landing page
components/
  ui/                   # shadcn/ui primitives (Button, Input, Dialog, etc.)
  [feature].tsx         # Feature-specific components, one per file
lib/
  db.ts                 # Database singleton (better-sqlite3 instance)
  auth.ts               # Auth configuration
  [domain].ts           # Business logic grouped by domain (users.ts, billing.ts)
db/
  migrations/           # Numbered SQL files: 001_create_users.sql, 002_add_billing.sql
  seed.ts               # Seed script for development
  migrate.ts            # Migration runner (reads db/migrations/*.sql in order)
  schema.sql            # Full schema dump for reference (auto-generated)
types/
  index.ts              # Shared TypeScript types — no barrel re-exports elsewhere
public/                 # Static assets only
```

**Why this structure**: Flat is better than nested. No `src/` directory (unnecessary indirection). No barrel `index.ts` files in subdirectories (they break tree-shaking and obscure imports). Every import path should point to a specific file.

## Database Rules

### SQLite Configuration

```typescript
// lib/db.ts — the ONLY file that creates a database connection
import Database from "better-sqlite3";

const db = new Database("data/app.db", { verbose: console.log });
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");
db.pragma("busy_timeout = 5000");

export default db;
```

**Why WAL mode**: Allows concurrent reads during writes. Essential for a web server.
**Why foreign_keys ON**: SQLite disables them by default. Always enforce referential integrity.

### Migrations

- Numbered SQL files in `db/migrations/`: `001_create_users.sql`, `002_add_teams.sql`
- Each file contains both `-- up` and `-- down` sections separated by `-- down` comment
- Run with `pnpm migrate` (calls `db/migrate.ts`)
- Migration state tracked in a `_migrations` table
- **Never** modify a migration that has been committed. Create a new one.
- **Never** use an ORM. Write raw SQL with prepared statements.

```sql
-- db/migrations/001_create_users.sql
-- up
CREATE TABLE users (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_email ON users(email);

-- down
DROP TABLE IF EXISTS users;
```

### Query Patterns

```typescript
// Always use prepared statements — never interpolate values
const user = db.prepare("SELECT * FROM users WHERE id = ?").get(userId);

// Use transactions for multi-step writes
const createTeamWithOwner = db.transaction((team, userId) => {
  const result = db.prepare("INSERT INTO teams (name) VALUES (?)").run(team.name);
  db.prepare("INSERT INTO team_members (team_id, user_id, role) VALUES (?, ?, 'owner')").run(result.lastInsertRowid, userId);
  return result;
});
```

**Why no ORM**: SQLite queries are simple. An ORM adds bundle size, abstraction overhead, and its own migration system that fights with raw SQL. For a SaaS with <50 tables, raw SQL is faster to write and debug.

## Component Patterns

### Server Components by Default

Every component is a Server Component unless it needs interactivity. Add `'use client'` only when you need:
- `useState`, `useEffect`, `useRef`
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`window`, `document`)

**Why**: Server Components have zero JS bundle cost. Keep the client bundle small.

### File Naming

- Components: `PascalCase.tsx` — `UserCard.tsx`, `BillingForm.tsx`
- Utilities: `camelCase.ts` — `formatDate.ts`, `parseQuery.ts`
- Routes: `kebab-case` directories — `app/team-settings/page.tsx`
- One component per file. No multi-component files.

### No Default Exports (except pages)

```typescript
// WRONG
export default function UserCard() { ... }

// RIGHT
export function UserCard() { ... }

// EXCEPTION: Next.js pages and layouts MUST use default export
export default function Page() { ... }
```

**Why**: Named exports enable auto-imports, are refactor-safe, and prevent naming inconsistencies.

### Data Fetching

```typescript
// In Server Components — call lib functions directly
import { getUser } from "@/lib/users";

export default async function ProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = await getUser(id);
  if (!user) notFound();
  return <UserProfile user={user} />;
}
```

**Why**: No `fetch()` to your own API routes from Server Components. Call the function directly — it runs on the server already.

### Mutations

Use Server Actions for all mutations. No API route handlers for internal mutations.

```typescript
// app/(dashboard)/settings/actions.ts
"use server";

import db from "@/lib/db";
import { revalidatePath } from "next/cache";

export async function updateProfile(formData: FormData) {
  const name = formData.get("name") as string;
  // validate, then:
  db.prepare("UPDATE users SET name = ?, updated_at = datetime('now') WHERE id = ?").run(name, userId);
  revalidatePath("/settings");
}
```

**Why**: Server Actions are simpler than API routes for mutations, handle form states natively, and work with progressive enhancement.

## API Route Handlers

Only use Route Handlers (`app/api/`) for:
- Webhooks from external services (Stripe, GitHub)
- Public API endpoints consumed by third parties
- File downloads

**Why**: Internal mutations should use Server Actions. Route Handlers are for external integration points.

## Error Handling

- Use `error.tsx` boundaries at the route group level — not per-page
- Use `not-found.tsx` for 404 states
- Validate all user input at the boundary (Server Actions, Route Handlers) with zod
- Throw `notFound()` or `redirect()` — don't return error objects from Server Components

## What We Don't Do (and Why)

| Anti-pattern | Why we avoid it |
|---|---|
| **Prisma / Drizzle** | Overkill for SQLite. Adds 5MB+ to node_modules, generates its own types, and its migration system conflicts with raw SQL. |
| **Redux / Zustand** | Server Components eliminate most client state. For the little client state we have, React's `useState` and URL search params are sufficient. |
| **CSS Modules** | Tailwind handles all styling. CSS Modules add cognitive overhead switching between two styling systems. |
| **`src/` directory** | Adds one level of unnecessary nesting. Next.js works fine without it. |
| **Barrel exports (`index.ts`)** | Break tree-shaking, create circular dependency risks, and obscure the actual file you're importing from. |
| **`fetch()` to own API from server** | Server Components already run on the server. Calling your own API route adds a network roundtrip to yourself. |
| **NextAuth** | Over-engineered for SQLite. `better-auth` is simpler, has fewer dependencies, and supports SQLite natively. |
| **`any` type** | Defeats the purpose of TypeScript. Use `unknown` and narrow with type guards. |
| **Relative imports** | Use `@/` path alias exclusively. Relative paths break when files move. |
| **ENV in client code** | Only `NEXT_PUBLIC_` vars reach the client. Keep secrets server-side. Never prefix secrets with `NEXT_PUBLIC_`. |

## Dev Commands

```bash
pnpm dev          # Start Next.js dev server
pnpm build        # Production build
pnpm start        # Start production server
pnpm migrate      # Run pending database migrations
pnpm seed         # Seed development data
pnpm test         # Run Vitest unit tests
pnpm test:e2e     # Run Playwright e2e tests
pnpm lint         # ESLint + TypeScript check
pnpm db:reset     # Drop database + re-migrate + re-seed (dev only)
pnpm db:dump      # Dump current schema to db/schema.sql
```

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add team invitation flow
fix: prevent duplicate billing webhooks
chore: upgrade better-sqlite3 to v12
refactor: extract auth middleware to lib/auth.ts
docs: add deployment guide
```

- Scope is optional but encouraged: `feat(billing): add usage-based pricing`
- Body explains **why**, not what (the diff shows what)
- Breaking changes: `feat!: change user ID format to UUID`

## Deployment

- Deploy to Vercel or any Node.js host
- SQLite database file lives on a persistent volume (Fly.io, Railway, or VPS)
- **Not serverless-compatible** — SQLite needs a persistent filesystem
- Set `DATABASE_PATH` env var in production to point to the persistent volume
- Run migrations on deploy: `pnpm migrate` in the build/start script

## Performance Rules

- Images: always use `next/image` with explicit `width` and `height`
- Fonts: use `next/font` — no external font CDNs
- Bundle: check `pnpm build` output. Client JS budget: <100KB first-load per route
- Database: add indexes for any column used in `WHERE` or `ORDER BY`
- Queries: no `SELECT *` — list columns explicitly
