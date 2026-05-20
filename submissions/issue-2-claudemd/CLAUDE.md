# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework:** Next.js 15 (App Router only — no Pages Router)
- **Runtime:** Node.js 20+
- **Database:** SQLite via `better-sqlite3` (local dev) or `@libsql/client` (Turso in production)
- **ORM:** None — raw SQL only. Type safety via hand-written repository functions.
- **Auth:** `next-auth` v5 (Auth.js)
- **Styling:** Tailwind CSS v4
- **Language:** TypeScript (strict mode, no `any`)
- **Package manager:** `pnpm`

---

## Folder Structure

```
.
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Route group: login, register
│   ├── (dashboard)/            # Route group: authenticated pages
│   │   └── [feature]/
│   │       ├── page.tsx        # Server Component — fetch + render
│   │       └── actions.ts      # Server Actions for mutations
│   ├── api/                    # API routes (webhooks, OAuth callbacks only)
│   └── layout.tsx
├── components/
│   ├── ui/                     # Stateless primitives (Button, Input, Badge)
│   └── [feature]/              # Feature-scoped components
├── db/
│   ├── client.ts               # Single DB connection singleton
│   ├── migrations/             # Sequential .sql files: 0001_init.sql, 0002_...sql
│   └── repositories/           # One file per domain: users.ts, subscriptions.ts
├── lib/
│   ├── auth.ts                 # next-auth config
│   └── utils.ts                # Shared pure functions only
├── types/                      # Global TypeScript interfaces
└── middleware.ts               # Auth guard — protects /dashboard routes
```

**Rules:**
- Never import from `app/` into `components/` or `lib/` — data flows downward only.
- `repositories/` functions are the only code allowed to touch `db/client.ts`.
- Server Actions live in `actions.ts` files co-located with the route that uses them.

---

## Database & Migration Rules

### Connection

```ts
// db/client.ts
import Database from 'better-sqlite3';

const db = new Database(process.env.DATABASE_PATH ?? 'local.db');
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

export default db;
```

Always enable WAL mode and foreign keys on connect. These are not defaults.

### Migrations

- Files are named `0001_init.sql`, `0002_add_teams.sql` — four-digit prefix, snake_case description.
- Migrations are **append-only**. Never edit an existing migration file.
- Apply with: `pnpm db:migrate` (a simple script that runs all unapplied files in order).
- Every `CREATE TABLE` must include `created_at INTEGER NOT NULL DEFAULT (unixepoch())`.
- Use `INTEGER` for timestamps (Unix epoch), not `TEXT` or `DATETIME`.

### Repository Pattern

```ts
// db/repositories/users.ts
import db from '../client';

export interface User {
  id: number;
  email: string;
  created_at: number;
}

export function getUserByEmail(email: string): User | undefined {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email) as User | undefined;
}

export function createUser(email: string, passwordHash: string): User {
  const stmt = db.prepare('INSERT INTO users (email, password_hash) VALUES (?, ?) RETURNING *');
  return stmt.get(email, passwordHash) as User;
}
```

- Use `RETURNING *` on INSERT/UPDATE to avoid a second SELECT.
- Use prepared statements — never string-concatenate SQL.
- Repository functions are synchronous (`better-sqlite3` is sync). Do not wrap in `async`.

---

## Component Patterns

### Server Components (default)

Use for anything that reads data. Fetch directly inside the component — no prop drilling of raw data.

```tsx
// app/(dashboard)/invoices/page.tsx
import { getInvoicesByUser } from '@/db/repositories/invoices';
import { auth } from '@/lib/auth';

export default async function InvoicesPage() {
  const session = await auth();
  const invoices = getInvoicesByUser(session!.user.id);
  return <InvoiceTable invoices={invoices} />;
}
```

### Client Components

Add `'use client'` only when you need:
- `useState` / `useEffect`
- Browser APIs
- Event handlers that aren't form submissions

Keep Client Components as leaves — they should receive data as props, not fetch it themselves.

### Server Actions (mutations)

```ts
// app/(dashboard)/invoices/actions.ts
'use server';
import { revalidatePath } from 'next/cache';
import { createInvoice } from '@/db/repositories/invoices';
import { auth } from '@/lib/auth';

export async function createInvoiceAction(formData: FormData) {
  const session = await auth();
  if (!session) throw new Error('Unauthorized');

  const amount = Number(formData.get('amount'));
  if (!amount || amount <= 0) throw new Error('Invalid amount');

  createInvoice({ userId: session.user.id, amount });
  revalidatePath('/invoices');
}
```

- Always authenticate inside the action — never trust the client.
- Validate inputs before touching the DB.
- Call `revalidatePath` after writes so the UI reflects the change.

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `kebab-case` | `invoice-table.tsx` |
| Components | `PascalCase` | `InvoiceTable` |
| Functions | `camelCase` | `getUserByEmail` |
| DB columns | `snake_case` | `created_at` |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_PATH` |
| Routes | `kebab-case` | `/billing-history` |

---

## Development Commands

```bash
pnpm dev          # Start dev server (localhost:3000)
pnpm build        # Production build
pnpm typecheck    # tsc --noEmit (run before every commit)
pnpm db:migrate   # Apply pending SQL migrations
pnpm db:studio    # Open SQLite browser (optional: Beekeeper Studio)
```

Always run `pnpm typecheck` before committing. A passing build does not mean type-safe code.

---

## Patterns to Follow

- **Co-locate mutations with routes.** `actions.ts` lives next to the `page.tsx` that triggers it.
- **One repository per domain.** `users.ts`, `invoices.ts`, `subscriptions.ts` — not one giant `db.ts`.
- **Fail loudly in dev, gracefully in prod.** Throw errors in repository functions; catch and show user-friendly messages in Server Actions.
- **Use `revalidatePath` not `router.refresh()`.** Server-side cache invalidation is more reliable.
- **Derive don't duplicate.** If a value can be computed from DB data, don't store it separately.

---

## Anti-Patterns to Avoid

| Anti-pattern | Why | Do this instead |
|-------------|-----|----------------|
| `useEffect` for data fetching | Race conditions, no caching | Fetch in Server Components |
| String-concatenated SQL | SQL injection risk | Prepared statements always |
| Storing timestamps as `TEXT` | Sorting and arithmetic break | `INTEGER` (Unix epoch) |
| Editing migration files | Breaks reproducibility | Add a new migration |
| `any` type | Defeats TypeScript | Type every repository return |
| Fetching in layout.tsx | Runs on every nav | Fetch in page.tsx or below |
| Calling Server Actions from Server Components | Not supported | Use direct function calls |
| Multiple DB connections | WAL contention, file locks | Single singleton in `db/client.ts` |

---

## Environment Variables

```env
# .env.local (never commit this file)
DATABASE_PATH=./local.db          # Path to SQLite file
NEXTAUTH_SECRET=<random-32-chars> # Required by next-auth
NEXTAUTH_URL=http://localhost:3000

# Production (Turso)
TURSO_DATABASE_URL=libsql://...
TURSO_AUTH_TOKEN=...
```

Switch between `better-sqlite3` (local) and `@libsql/client` (Turso) by checking `NODE_ENV` in `db/client.ts`. The repository layer stays identical — only the client changes.

---

## What Claude Should Never Do In This Project

- Generate `useEffect` for loading data — always ask if a Server Component would work.
- Add an ORM without explicit instruction — raw SQL is intentional.
- Create new migration files without showing the SQL first for review.
- Use `router.push()` after a mutation — prefer `revalidatePath` + redirect in Server Actions.
- Add `console.log` statements — use `throw` to surface errors during development.
