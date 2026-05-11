# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude Code exactly how this project works. Read it before writing any code.

---

## Stack & Versions

| Layer | Choice | Version |
|-------|--------|---------|
| Framework | Next.js App Router | 15.x |
| Language | TypeScript | 5.x (strict mode) |
| Database | SQLite via Turso | `@libsql/client` latest |
| ORM | None — raw SQL only | — |
| Auth | `better-auth` | latest |
| Styling | Tailwind CSS | 4.x |
| Deployment | Vercel + Turso cloud | — |

**Why Turso over better-sqlite3?** Turso works in edge runtimes and serverless. better-sqlite3 is Node-only and blocks the event loop. Use Turso's `@libsql/client` everywhere.

---

## Folder Structure

```
/
├── app/                        # Next.js App Router only — no pages/
│   ├── (auth)/                 # Route group: login, register, forgot-password
│   ├── (dashboard)/            # Route group: authenticated app routes
│   │   ├── layout.tsx          # Auth guard lives here
│   │   └── [feature]/
│   │       ├── page.tsx        # Server Component — fetch data here
│   │       └── _components/    # Feature-scoped components (not shared)
│   ├── api/                    # API routes (Route Handlers only)
│   │   └── [resource]/
│   │       └── route.ts
│   └── layout.tsx              # Root layout
├── components/                 # Shared UI components only
│   └── ui/                     # Primitives (Button, Input, Modal, etc.)
├── lib/
│   ├── db/
│   │   ├── client.ts           # Turso client singleton
│   │   ├── migrations/         # SQL migration files — numbered sequentially
│   │   │   └── 001_init.sql
│   │   └── queries/            # One file per domain (users.ts, subscriptions.ts)
│   ├── auth.ts                 # better-auth config
│   └── utils.ts                # General utilities (cn, formatDate, etc.)
├── hooks/                      # Custom React hooks — client-side only
├── types/                      # Shared TypeScript interfaces and types
└── middleware.ts               # Auth + redirect logic
```

**Rules:**
- `_components/` inside a route = private to that route. Don't import across routes.
- `components/ui/` = pure UI primitives only. No data fetching, no business logic.
- Never create a `utils/` folder. Everything shared goes in `lib/`.

---

## Database & Migration Rules

### Client setup (`lib/db/client.ts`)

```typescript
import { createClient } from '@libsql/client';

export const db = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});
```

Export `db` as a singleton. Import it directly in query files — never instantiate a new client elsewhere.

### Migration conventions

- Migrations live in `lib/db/migrations/` as plain `.sql` files
- Name format: `001_init.sql`, `002_add_users_table.sql`, `003_add_stripe_customer_id.sql`
- **Never edit a migration that has already been applied to production.** Write a new one.
- Run migrations manually with: `npx tsx lib/db/migrate.ts`
- Every table gets: `id TEXT PRIMARY KEY` (use `crypto.randomUUID()`), `created_at INTEGER NOT NULL DEFAULT (unixepoch())`, `updated_at INTEGER NOT NULL DEFAULT (unixepoch())`

### SQL conventions

```sql
-- ✅ Correct
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch())
);

-- ❌ Wrong — no auto-increment integers as PKs
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT);
```

- Always use `TEXT` PKs with UUIDs. Never `INTEGER AUTOINCREMENT`.
- Store timestamps as `INTEGER` (Unix epoch), not `TEXT` or `DATETIME`.
- Use `NOT NULL` by default. Nullable columns are intentional — add a comment explaining why.
- No foreign key constraints in SQLite unless you explicitly enable them with `PRAGMA foreign_keys = ON` at connection time.

### Query files (`lib/db/queries/`)

One file per domain. Export typed async functions. Raw SQL only — no query builders.

```typescript
// lib/db/queries/users.ts
import { db } from '../client';

export type User = {
  id: string;
  email: string;
  name: string | null;
  created_at: number;
};

export async function getUserByEmail(email: string): Promise<User | null> {
  const result = await db.execute({
    sql: 'SELECT id, email, name, created_at FROM users WHERE email = ?',
    args: [email],
  });
  return (result.rows[0] as unknown as User) ?? null;
}

export async function createUser(data: Pick<User, 'id' | 'email' | 'name'>): Promise<void> {
  await db.execute({
    sql: 'INSERT INTO users (id, email, name) VALUES (?, ?, ?)',
    args: [data.id, data.email, data.name],
  });
}
```

**Never** write SQL inline in components, pages, or API routes. All DB access goes through `lib/db/queries/`.

---

## Component Patterns

### Server Components (default)

All `page.tsx` files are Server Components. Fetch data directly — no `useEffect`, no client fetch.

```typescript
// app/(dashboard)/invoices/page.tsx
import { getInvoicesByUser } from '@/lib/db/queries/invoices';
import { auth } from '@/lib/auth';

export default async function InvoicesPage() {
  const session = await auth();
  const invoices = await getInvoicesByUser(session.user.id);
  return <InvoiceList invoices={invoices} />;
}
```

### Client Components

Add `'use client'` only when you need: `useState`, `useEffect`, event handlers, browser APIs.

```typescript
'use client';
// Keep client components small — they're leaves, not containers
```

### Data mutations — Server Actions

Use Server Actions for all form submissions and mutations. No separate API routes for CRUD.

```typescript
// app/(dashboard)/invoices/_components/InvoiceForm.tsx
'use server';

export async function createInvoiceAction(formData: FormData) {
  const session = await auth();
  const title = formData.get('title') as string;
  await createInvoice({ id: crypto.randomUUID(), userId: session.user.id, title });
  revalidatePath('/invoices');
}
```

### API Routes

Only create Route Handlers (`app/api/`) for:
- Webhooks (Stripe, etc.)
- Third-party OAuth callbacks
- Public REST endpoints consumed by external clients

Never create API routes just to wrap a DB query that a Server Action could handle.

---

## Dev Commands

```bash
# Install
pnpm install

# Dev server
pnpm dev

# Type check
pnpm tsc --noEmit

# Run migrations
npx tsx lib/db/migrate.ts

# Lint
pnpm lint

# Build
pnpm build
```

Always use `pnpm`. Never `npm` or `yarn` — lockfile conflicts will break CI.

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | kebab-case | `invoice-form.tsx` |
| Components | PascalCase | `InvoiceForm` |
| Server Actions | camelCase + `Action` suffix | `createInvoiceAction` |
| Query functions | camelCase + verb first | `getUserByEmail`, `listInvoices` |
| DB tables | snake_case plural | `users`, `invoice_items` |
| DB columns | snake_case | `created_at`, `user_id` |
| Env vars | SCREAMING_SNAKE | `TURSO_DATABASE_URL` |
| Route groups | lowercase in parens | `(dashboard)`, `(auth)` |

---

## What We Don't Do (And Why)

| Pattern | Why We Avoid It |
|---------|----------------|
| Prisma or Drizzle ORM | Adds abstraction over simple SQL. Raw queries are easier to audit and debug. |
| `useEffect` for data fetching | Server Components fetch data. Client Components receive props. |
| `pages/` directory | We're App Router only. Mixing causes subtle bugs and confused caching. |
| `any` type in TypeScript | Defeats the purpose. Use `unknown` and narrow it. |
| Integer PKs | UUIDs are portable, safe to expose in URLs, and don't leak row counts. |
| Inline SQL in components | Query files are the contract. Scattering SQL makes migrations dangerous. |
| `npm` or `yarn` | pnpm only — consistent installs, disk-efficient, monorepo-ready. |
| Client-side API calls for mutations | Server Actions handle mutations. Fewer round-trips, simpler auth. |
| Storing timestamps as strings | Unix epoch integers sort correctly, compare cheaply, and have no timezone issues. |
| Multiple Turso client instances | One singleton in `lib/db/client.ts`. Multiple instances = connection exhaustion. |

---

## Environment Variables

```bash
# Required
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-token

# Auth
BETTER_AUTH_SECRET=your-secret-32-chars-minimum
BETTER_AUTH_URL=http://localhost:3000

# Optional: Stripe
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Never commit `.env`. Always add new vars to `.env.example` with a placeholder value and a comment explaining what it does.

---

## TypeScript Rules

- `strict: true` in `tsconfig.json` — non-negotiable
- No `as any`. Use `unknown` + type guards or Zod for external data
- All DB query return types are explicitly typed (see query file example above)
- Use `type` not `interface` for data shapes. Use `interface` only for things that will be extended/implemented.

---

## Auth Pattern

Auth is handled by `better-auth`. The session is always fetched server-side.

```typescript
// In any Server Component or Server Action
import { auth } from '@/lib/auth';
const session = await auth();
if (!session) redirect('/login');
```

The `(dashboard)` route group layout handles the auth guard — individual pages don't need to re-check.

---

## Common Mistakes Claude Should Avoid

1. **Don't create `pages/` files** — App Router only
2. **Don't use `fetch('/api/...')` inside Server Components** — call the query function directly
3. **Don't write SQL anywhere except `lib/db/queries/`**
4. **Don't add `'use client'` to page.tsx** — keep pages as Server Components
5. **Don't use `Date.now()` for DB timestamps** — use `unixepoch()` in SQL or `Math.floor(Date.now() / 1000)` in TS
6. **Don't create new Turso client instances** — import from `lib/db/client.ts`
7. **Don't skip the `IF NOT EXISTS` in migrations** — idempotent migrations prevent errors on re-run

---

*Assisted-by: Claude (Anthropic)*
