# CLAUDE.md

> Opinionated engineering rules for Claude Code. Every directive below states **what** to do and **why**. When in doubt, follow the rule — not the general pattern.

---

## 1. Project Structure

```
src/
├── app/                    # Next.js App Router — all routes live here
│   ├── layout.tsx          # Root layout — server component by default
│   ├── page.tsx            # Home page — server component by default
│   ├── globals.css         # Global styles only — no component CSS here
│   ├── (routes)/           # Route groups for organizational grouping
│   │   ├── dashboard/
│   │   │   ├── layout.tsx  # Shared layout for dashboard group
│   │   │   └── page.tsx
│   │   └── api/
│   │       └── route.ts    # API handlers — use route handlers, not pages
├── components/
│   ├── ui/                 # Atomic, reusable UI primitives (Button, Card, Input)
│   ├── features/           # Domain-specific composables (BillingForm, UserList)
│   └── layout/             # Structural components (Nav, Sidebar, Footer)
├── lib/
│   ├── db/                 # Database layer — ALL SQLite access lives here
│   │   ├── schema.ts       # Schema definition and types
│   │   ├── client.ts       # better-sqlite3 / Turso client singleton
│   │   ├── migrate.ts      # Migration runner
│   │   └── queries/        # Query functions — one file per entity
│   ├── auth/               # Authentication utilities
│   ├── utils/              # Truly generic helpers (date formatting, cn(), etc.)
│   └── config.ts           # Environment validation and config
├── hooks/                  # Custom React hooks — client-side only
├── types/                  # Shared TypeScript types
└── scripts/                # One-off scripts (seed, generate, backfill)
```

**Rule:** If a file imports from `lib/db`, it must be a server component or route handler. Client components never touch the database directly.

**Why:** Next.js App Router blurs server/client boundaries. An explicit boundary prevents accidental bundling of `better-sqlite3` (a native module) into client code, which will crash the build.

---

## 2. Naming Conventions

| Layer | Convention | Example | Reason |
|-------|-----------|---------|--------|
| **App Router files** | `page.tsx`, `route.ts`, `layout.tsx`, `loading.tsx`, `error.tsx` | `app/dashboard/page.tsx` | Next.js convention — do not rename |
| **React Components** | PascalCase file + named export | `BillingForm.tsx` -> `export function BillingForm` | Matches Next.js/React ecosystem; grep-able |
| **Hooks** | `use` prefix, camelCase | `useDebounce`, `useBillingQuery` | React lint rule `rules-of-hooks` requires this |
| **DB queries** | `getX`, `listX`, `createX`, `updateX`, `deleteX` | `getInvoiceById`, `listInvoicesByStatus` | CRUD verb prefix makes intent clear at call site |
| **Migrations** | `NNNN_description.sql` | `0001_create_users_table.sql` | Sequential numbering prevents merge conflicts; description aids `git log` |
| **API routes** | RESTful noun-based | `GET /api/invoices/:id`, `POST /api/invoices` | Predictable URL structure |
| **CSS classes** | Tailwind utility-first — no custom class names unless via `@apply` | `className="flex items-center gap-2"` | Prevents specificity wars and dead CSS |
| **Env vars** | `PUBLIC_` prefix for client, no prefix for server | `DATABASE_URL` (server), `PUBLIC_APP_URL` (client) | Security — server vars never bundle to client |
| **Test files** | Co-located `*.test.ts(x)` | `lib/db/queries/invoice.test.ts` | Proximity reduces cognitive load |

**Do NOT abbreviate.** `usr`, `inv`, `cfg` save 2 seconds to type and cost 2 minutes to understand.

---

## 3. Database Rules (SQLite / Turso / better-sqlite3)

### 3.1 Migrations

```sql
-- 0002_add_billing_status_to_invoices.sql
-- Additive-only migration: never drop columns, never rename columns.
ALTER TABLE invoices ADD COLUMN status TEXT NOT NULL DEFAULT 'pending';
CREATE INDEX idx_invoices_status ON invoices(status);
```

**Rules:**

1. **Additive-only migrations.** Never `DROP COLUMN`, never `RENAME COLUMN`. If a column is truly deprecated, mark it `DEPRECATED` in a comment and stop writing to it in code. SQLite's `ALTER TABLE DROP COLUMN` is supported since 3.35 but migrations that destroy data destroy trust.
2. **Every migration is a new file.** Never edit an already-merged migration file. Migrations are immutable history — editing one is rewriting history that other developers (and production databases) have already run.
3. **Idempotent when possible.** Use `IF NOT EXISTS` for indexes and `CREATE TABLE IF NOT EXISTS`. This makes local resets painless.
4. **Run in a transaction.** The migration runner wraps each file in `BEGIN` / `COMMIT`. A failure in migration `0007` must roll back `0007` atomically — not leave a half-applied schema.
5. **Migrate on app boot.** Run `migrate()` at server startup (not in a separate CI step). A fresh clone + `npm run dev` must produce a working app with no manual DB setup.

### 3.2 Schema Conventions

```typescript
// lib/db/schema.ts
export interface Invoice {
  id: string;           // TEXT primary key — UUID or nanoid, never auto-increment
  amount: number;       // INTEGER — store cents, never dollars
  status: 'pending' | 'paid' | 'failed' | 'refunded';
  created_at: number;   // INTEGER — Unix epoch milliseconds, not ISO strings
  updated_at: number;
}
```

**Rules:**

1. **Primary keys are `TEXT` (UUID/nanoid).** Auto-increment integers leak business data ("we have 1,400 invoices") and make cross-database merging impossible.
2. **Money is INTEGER cents.** `INTEGER` for amount avoids floating-point errors. Format to dollars only at the display layer.
3. **Timestamps are Unix epoch milliseconds (INTEGER).** Sortable, timezone-safe, unambiguous. ISO strings in SQLite are just TEXT and sort lexicographically (which fails across timezones).
4. **No foreign keys across bounded contexts.** If two entities "reference" each other, store the ID but don't declare `FOREIGN KEY` constraints unless deletion cascade is truly needed. SQLite enforces FKs only when `PRAGMA foreign_keys = ON` is set per-connection — a footgun. Enforce referential integrity at the query layer with explicit checks.
5. **Add `updated_at` and maintain it.** Every `UPDATE` query must set `updated_at = Date.now()` explicitly. SQLite has no auto-update trigger by default.

### 3.3 Query Rules

```typescript
// lib/db/queries/invoice.ts
import { db } from '../client';

export function getInvoiceById(id: string): Invoice | undefined {
  const row = db.prepare('SELECT id, amount, status, created_at, updated_at FROM invoices WHERE id = ?').get(id);
  return row as Invoice | undefined;
}

export function listInvoicesByStatus(status: Invoice['status']): Invoice[] {
  return db
    .prepare('SELECT id, amount, status, created_at, updated_at FROM invoices WHERE status = ? ORDER BY created_at DESC')
    .all(status) as Invoice[];
}
```

**Rules:**

1. **All queries live in `lib/db/queries/`** — never inline SQL in route handlers or components. This file is the single source of truth for SQL in the codebase.
2. **Use prepared statements.** `db.prepare('...').get(param)` — never string concatenation. SQLite parameter binding prevents injection and enables query plan caching.
3. **No `SELECT *` in production queries.** Explicit column lists (`SELECT id, amount, status FROM ...`) make the contract clear and prevent breakage when columns are added.
4. **Transactions for multi-write operations.** Wrap `createInvoice` + `updateUserBalance` in a single `db.transaction(() => { ... })`. better-sqlite3 transactions are synchronous and fast — use them.
5. **No N+1 queries.** If you need invoices for 10 users, run one query with `WHERE user_id IN (...)` — not 10 individual queries. Use a helper if the `IN` clause is dynamic.

---

## 4. Development Commands

```bash
# Start dev server with hot reload
npm run dev

# Type-check without emitting
npx tsc --noEmit

# Run tests (Vitest)
npm test

# Run tests in watch mode
npm run test:watch

# Lint
npm run lint

# Database: run migrations
npm run db:migrate

# Database: reset to clean state + reseed (DESTRUCTIVE — dev only)
npm run db:reset

# Database: open interactive shell
npm run db:studio

# Build for production
npm run build
```

**`package.json` scripts block:**

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:reset": "tsx scripts/reset.ts && tsx scripts/migrate.ts && tsx scripts/seed.ts",
    "db:studio": "tsx scripts/studio.ts"
  }
}
```

**Rule:** Scripts use `tsx` to run TypeScript directly. Do not require a build step for dev-time tooling. The migration and seed scripts must run without `npm run build` first.

---

## 5. Patterns to Follow

### 5.1 Server Components by Default

```typescript
// app/dashboard/page.tsx — this is a server component by default
import { listRecentInvoices } from '@/lib/db/queries/invoice';

export default async function DashboardPage() {
  const invoices = await listRecentInvoices(); // Direct DB call — no API layer
  return <InvoiceTable invoices={invoices} />;
}
```

**Rule:** Server components fetch data directly via query functions. Do not create internal API routes that your own server components call — that's an unnecessary HTTP round-trip within the same process.

### 5.2 Client Components — Explicit Boundary

```typescript
'use client';

// Only add 'use client' when the component uses hooks, state, or browser APIs
export function InvoiceTable({ invoices }: { invoices: Invoice[] }) {
  const [selected, setSelected] = useState<string[]>([]);
  // ...
}
```

**Rule:** `'use client'` is a boundary marker, not a default. Start as a server component. Only add `'use client'` when you need interactivity. When you do, push it as far down the tree as possible — the server component wrapper can still render static HTML.

### 5.3 Data Fetching with React Server Actions

```typescript
// app/actions/invoice.ts
'use server';

import { createInvoice } from '@/lib/db/queries/invoice';
import { revalidatePath } from 'next/cache';

export async function createInvoiceAction(formData: FormData) {
  const invoice = await createInvoice(/* parsed data */);
  revalidatePath('/dashboard');
  return invoice;
}
```

**Rule:** Use Server Actions for mutations from client components. They provide type safety end-to-end, handle CSRF automatically, and integrate with `revalidatePath` for cache invalidation. Do not create API routes for forms that submit to your own app.

### 5.4 Error Handling

```typescript
// app/dashboard/error.tsx — 'use client' by convention
'use client';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
    reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong loading the dashboard</h2>
      <p>{error.digest}</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

**Rule:** Every route segment gets an `error.tsx` and a `loading.tsx`. These are not optional polish — they are the error boundary and suspense boundary for that segment. Without them, a database timeout renders a blank screen or an unhandled rejection.

### 5.5 Environment Validation

```typescript
// lib/config.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  // PUBLIC_APP_URL is exposed to the client — only safe values
  PUBLIC_APP_URL: z.string().url().default('http://localhost:3000'),
});

export const env = envSchema.parse(process.env);
```

**Rule:** Validate environment variables at module load time. Fail fast with a clear error message — not with a cryptic `undefined is not a function` three layers deep.

---

## 6. Anti-Patterns to Avoid

### DON'T put `better-sqlite3` in client component code

```typescript
// WRONG — this will crash the build
'use client';
import Database from 'better-sqlite3';
```

**Why:** `better-sqlite3` is a Node.js native addon. It cannot be bundled for the browser. Next.js will fail at build time with a cryptic "Module not found" error.

---

### DON'T create an internal API layer for server components

```typescript
// WRONG — server component calling its own API
// app/dashboard/page.tsx
const res = await fetch('/api/invoices'); // Same process, extra HTTP hop
```

**Why:** This adds serialization/deserialization overhead, network latency (even localhost), and error handling for a call that could be a direct function import. Server components can call query functions directly.

---

### DON'T edit an existing migration file

```sql
// WRONG — editing 0001_create_users_table.sql after it's been merged
ALTER TABLE users ADD COLUMN email_verified BOOLEAN;
```

**Why:** If another developer has already run `0001` locally or in production, their database has the old schema. Your edit will never re-run. The fix is to add `0002_add_email_verified.sql`.

---

### DON'T use `SELECT *` in production queries

```typescript
// WRONG — breaks when schema changes, leaks data
const rows = db.prepare('SELECT * FROM invoices').all();
```

**Why:** A future migration adding a `password_hash` column would silently include it in the response. Explicit column lists are a security boundary.

---

### DON'T run migrations as a separate CI step

```yaml
# WRONG — migrations in CI, not in app
- run: npx tsx scripts/migrate.ts
```

**Why:** A fresh developer clone should `npm install && npm run dev` and have a working database. Migrations in CI means the developer's local schema is out of sync until they manually remember to run migrations. Run `migrate()` at server startup.

---

### DON'T use floating-point for money

```typescript
// WRONG — 0.1 + 0.2 !== 0.3
amount: 19.99 // dollars as float
```

**Why:** IEEE 754 floating-point produces rounding errors. $19.99 stored as a float may compare equal to $19.99 or may not. Store as `1999` (cents, integer).

---

### DON'T skip `loading.tsx` and `error.tsx`

```typescript
// WRONG — page with no loading state
export default async function Page() {
  const data = await db.query(); // User sees blank screen for 500ms
}
```

**Why:** Without `loading.tsx`, Next.js shows nothing while the suspense boundary resolves. Without `error.tsx`, a database error crashes the entire route group. These files are cheap insurance.

---

### DON'T use `useEffect` for data fetching

```typescript
// WRONG — client-side fetching with useEffect
useEffect(() => {
  fetch('/api/invoices').then(setInvoices);
}, []);
```

**Why:** This adds a network round-trip and loading flicker. Server components render with data already present. If the data is dynamic (search filters), use a Server Action or SWR with `fallbackData` from the server component.

---

## 7. Git Commit Conventions

Format: `<type>: <description>`

| Type | Use when |
|------|----------|
| `feat:` | Adding a new feature or route |
| `fix:` | Bug fix |
| `refactor:` | Code change that neither fixes nor adds |
| `perf:` | Performance improvement |
| `db:` | Migration or schema change |
| `test:` | Adding or updating tests |
| `docs:` | Documentation changes |
| `chore:` | Tooling, config, dependency bumps |

**Rule:** Imperative mood, under 72 characters, no trailing period.

```bash
git commit -m "db: add status column to invoices table"
git commit -m "feat: add invoice detail page"
git commit -m "fix: handle null invoice in email template"
```

---

## 8. Testing Strategy

| Layer | Tool | What to test |
|-------|------|-------------|
| DB queries | Vitest + in-memory SQLite | Each query function with seeded fixture data |
| Server Actions | Vitest | Action logic with mocked DB layer |
| React Components | Vitest + Testing Library | Component rendering and interaction |
| Routes | Manual / E2E | Critical user flows (auth, billing, checkout) |

**Rule:** DB query tests use `better-sqlite3` with `:memory:` — fast, isolated, no cleanup needed. Never test against the development database.

```typescript
// lib/db/queries/invoice.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { createInvoice } from './invoice';
import { getInvoiceById } from './invoice';
import { db } from '../client';

beforeEach(() => {
  db.exec('DELETE FROM invoices');
});

it('creates an invoice with default pending status', () => {
  const invoice = createInvoice({ amount: 1999, userId: 'user_1' });
  expect(invoice.status).toBe('pending');
  expect(getInvoiceById(invoice.id)).toEqual(invoice);
});
```

---

## 9. AI Agent Instructions

When Claude Code (or any AI agent) works in this codebase:

1. **Read this file first** — all rules below are derived from it.
2. **Never modify a merged migration file.** If a schema change is needed, create `NNNN_description.sql`.
3. **Never create an API route that a server component can call directly.**
4. **Never add `'use client'` unless interactivity is required.** If you add it, check if the interactive part can be extracted into a smaller child component.
5. **Always run `npx tsc --noEmit` before committing.** TypeScript errors are not acceptable.
6. **When adding a new query, add a test.** Every function in `lib/db/queries/` must have a corresponding `.test.ts` file.
7. **When creating a new page, create `loading.tsx` and `error.tsx` in the same route segment.**
8. **Use Server Actions for mutations from client components.** Do not create internal POST routes for your own forms.
