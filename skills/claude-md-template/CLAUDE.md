# CLAUDE.md — Next.js 15 SaaS + SQLite

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js | 15.x (App Router) | RSC + server actions. No pages router. |
| Language | TypeScript | 5.x | Strict mode. No `any` without `// eslint-disable-next-line`. |
| Database | SQLite via better-sqlite3 | 11.x | Zero-infrastructure OLTP. Good enough for single-server SaaS. |
| ORM / Query | Drizzle ORM | 0.38+ | Type-safe. No hidden N+1. No migration file bloat. |
| Auth | Lucia v3 | 3.x | Framework-agnostic. No vendor lock-in. Session-based (no JWT). |
| UI | shadcn/ui + Tailwind CSS v4 | Latest | Copy-paste components. No component library dependency. |
| Validation | Zod | 3.x | Single source of truth for forms + API + DB. |
| Package manager | pnpm | Latest | Strict dependency hoisting. No phantom dependencies. |

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Route group — login, register
│   │   ├── login/
│   │   │   ├── page.tsx    # Server component. Form is a client child.
│   │   │   └── actions.ts  # Server actions only (never route handlers here)
│   │   └── register/
│   ├── (dashboard)/        # Route group — authenticated pages
│   │   ├── layout.tsx      # Checks session, redirects to /login if null
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/
│   └── api/                # Route handlers — for external webhooks only
│       └── stripe/
│           └── webhook/
│               └── route.ts
├── components/
│   ├── ui/                 # shadcn/ui primitives (generated, do not edit manually)
│   └── features/           # Feature-specific components
│       ├── dashboard/
│       └── auth/
├── db/
│   ├── schema/             # Drizzle schema files (one file per domain)
│   │   ├── users.ts
│   │   ├── subscriptions.ts
│   │   └── index.ts        # Re-exports all tables, enums, relations
│   ├── queries/            # Reusable DB query functions
│   │   ├── users.ts
│   │   └── subscriptions.ts
│   ├── migrate.ts          # Migration runner (call programmatically, never CLI)
│   ├── seed.ts             # Dev seed data
│   └── index.ts            # DB client singleton
├── lib/
│   ├── auth.ts             # Lucia auth instance
│   ├── stripe.ts           # Stripe client singleton
│   ├── email.ts            # Email sending (Resend / Plunk)
│   └── utils.ts            # cn(), formatDate(), etc.
└── middleware.ts            # Next.js middleware — session refresh, geo, rate-limit
```

**Rules:**
- Every file has exactly **one** exported default or named responsibility.
- No barrel files beyond `db/schema/index.ts`.
- Server actions live in `actions.ts` next to the page, never in a global `actions/` directory.

## Naming Conventions

| What | Convention | Example | Reason |
|------|-----------|---------|--------|
| Files (components) | PascalCase | `UserAvatar.tsx` | Matches component name. Findable by class name. |
| Files (utils) | kebab-case | `format-date.ts` | Distinguishable from components at a glance. |
| Functions | camelCase | `getUserById()` | Standard JS. |
| DB tables | snake_case | `user_sessions` | SQL convention. No quoting needed. |
| DB columns | snake_case | `stripe_customer_id` | Same as tables. Drizzle maps camelCase in TS. |
| Env vars | UPPER_SNAKE | `DATABASE_URL` | Standard across all runtimes. |
| Directories | kebab-case | `user-avatar/` | URL-friendly. No case-sensitivity issues. |

## DB & Migration Rules

**Rule 1 — Every migration is a reversible transaction.** Write both `up` and `down` in the same file:

```ts
// db/migrations/001_add_billing_cycle.ts
import { sqliteTable, text } from "drizzle-orm/sqlite-core";

export async function up(db: DB) {
  await db.run(sql`ALTER TABLE subscriptions ADD COLUMN billing_cycle text NOT NULL DEFAULT 'monthly'`);
}

export async function down(db: DB) {
  await db.run(sql`ALTER TABLE subscriptions DROP COLUMN billing_cycle`);
}
```

**Rule 2 — Never delete a column without a deprecation window.** Mark as deprecated for 2 weeks, then remove.
Reason: zero-downtime deploys. Old instances still reference the column.

**Rule 3 — Every query goes through `db/queries/`.** No raw SQL in components, server actions, or route handlers.
Exception: DDL (ALTER TABLE, CREATE INDEX) in migrations only.

**Rule 4 — Use Drizzle relations, not manual JOINs.**

```ts
// ✅ Good
const userWithPosts = await db.query.users.findFirst({
  with: { posts: true }
});

// ❌ Bad — manual JOIN string
const userWithPosts = await db.all(`SELECT ... JOIN ...`);
```

**Rule 5 — Index any column used in WHERE or ORDER BY.** Run `EXPLAIN QUERY PLAN` before shipping.

## Server & Client Component Patterns

### When to use Server vs Client

| Scenario | Component Type | Reason |
|----------|---------------|--------|
| Fetching data from DB | Server | Reduces client JS. No waterfall. |
| Forms with validation | Client (shallow) | `useActionState` + Zod. Submit calls server action. |
| Interactive UI (modals, dropdowns) | Client | Needs `useState`, `useEffect`, event handlers. |
| Static marketing page | Server | Zero JS shipped. |
| Real-time data | Client + SWR/SSE | Polling or push. |

**Rule — Add `"use client"` only when you absolutely need it.** If a component only renders props, keep it server.

```tsx
// ✅ Good: server component, client boundary pushed to leaf
// app/dashboard/page.tsx (server)
import { DashboardChart } from "./dashboard-chart"; // this is "use client"

// ❌ Bad: entire page becomes client because of one interactive element
// app/dashboard/page.tsx (use client)
```

### Form Pattern

```tsx
// app/(dashboard)/settings/actions.ts (server)
"use server";
import { z } from "zod";

const schema = z.object({ name: z.string().min(1).max(50) });

export async function updateName(_prev: unknown, formData: FormData) {
  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: "Invalid name" };
  await db.update(users).set({ name: parsed.data.name }).where(eq(users.id, session.userId));
  return { success: true };
}

// app/(dashboard)/settings/page.tsx (client)
"use client";
import { useActionState } from "react";
import { updateName } from "./actions";

export function NameForm() {
  const [state, action] = useActionState(updateName, null);
  return (
    <form action={action}>
      <input name="name" required />
      <button type="submit">Save</button>
      {state?.error && <p className="text-red-500">{state.error}</p>}
    </form>
  );
}
```

## Dev Commands

```bash
pnpm dev              # Next.js dev server (port 3000)
pnpm build            # Production build
pnpm test             # Vitest (unit + integration)
pnpm test:e2e         # Playwright (E2E)
pnpm db:generate      # Generate Drizzle migrations
pnpm db:migrate       # Apply migrations (calls db/migrate.ts)
pnpm db:seed          # Seed dev data
pnpm lint             # ESLint + Prettier check
pnpm typecheck        # tsc --noEmit (run before every PR)
```

## Anti-Patterns (Do Not Do These)

| Anti-Pattern | Why We Don't Do It | Alternative |
|-------------|-------------------|-------------|
| `pages router` | Deprecated. RSC incompatible. | Use App Router exclusively. |
| Prisma | Heavy binary. Slow migration. No SQLite-native JSON. | Drizzle ORM. |
| JWT for sessions | Can't revoke. No server-side control. | Lucia sessions (DB-backed). |
| Global `fetch()` without error handling | Silent 500s in production. | Wrap in `try/catch` or use `neverthrow`. |
| `useEffect` for data fetching | Waterfall. No Suspense. No dedup. | Server component + `async` or `use()` + Suspense. |
| `any` type | TypeScript loses all value. | `unknown` + narrowing, or Zod parse. |
| `DELETE FROM table` without WHERE | Destroys all data. | Always add WHERE. Use `db.delete(tbl).where(...)`. |
| Catch-all error handlers in API routes | Leaks internal state. | Return structured `{ error: string }` responses. |
| `npm` | Slower. Loose lockfile. No content-addressable install. | `pnpm` only. |

## Database Connection

```ts
// db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL!);
sqlite.pragma("journal_mode = WAL");   // Performance: concurrent reads
sqlite.pragma("foreign_keys = ON");    // Safety: referential integrity

export const db = drizzle(sqlite, { schema });
```

**Turso note:** If using Turso in production, swap `better-sqlite3` for `@libsql/client` and change `DATABASE_URL` to `libsql://...`. The Drizzle API stays identical.

## Environment Variables

```env
# Required
DATABASE_URL=file:./data/app.db
SESSION_SECRET=                            # openssl rand -hex 32
RESEND_API_KEY=                            # Email sending

# Optional
STRIPE_SECRET_KEY=                         # Payments (omit to disable billing)
STRIPE_WEBHOOK_SECRET=                     # Webhook verification
NEXT_PUBLIC_POSTHOG_KEY=                   # Analytics
```
