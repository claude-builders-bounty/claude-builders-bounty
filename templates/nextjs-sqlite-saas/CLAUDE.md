# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated, production-ready context file. Drop into any Next.js 15 App Router + SQLite
SaaS project root and Claude Code will understand the project without clarifying questions.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Runtime | Node.js | 22 LTS | Active LTS; native `fetch` stable |
| Package manager | pnpm | 9 | Strict hoisting prevents phantom deps |
| Framework | Next.js App Router | 15 | Server Components reduce JS bundle by default |
| Language | TypeScript | 5.7+ strict | `noUncheckedIndexedAccess` catches array bugs at compile time |
| Styling | Tailwind CSS | v4 | Zero-runtime CSS; no stylesheet merge conflicts |
| Database (dev) | better-sqlite3 | latest | Synchronous API; no async waterfall for simple queries |
| Database (prod) | Turso (libSQL) | latest | SQLite semantics with replication; same Drizzle driver |
| ORM | Drizzle ORM | latest | Type-safe SQL, not magic — generated SQL is readable |
| Auth | NextAuth.js | v5 (beta) | First-class App Router support; credentials + OAuth |
| Validation | Zod | 3 | Runtime + compile-time safety from a single schema |
| Forms | react-hook-form + zod resolver | latest | Uncontrolled inputs; only re-renders on error/submit |
| Testing (unit) | Vitest | latest | Vite-native, fast; same config as Next.js |
| Testing (e2e) | Playwright | latest | First-class network interception; runs in CI without flakiness hacks |

**Turso vs better-sqlite3 decision:** Use `better-sqlite3` locally and switch to Turso in
production by setting `DATABASE_URL` to a `libsql://` URI. The Drizzle driver auto-selects.
Never run better-sqlite3 in a serverless environment — it requires a persistent filesystem.

---

## Folder Structure

```
src/
  app/
    (auth)/               # Unauthenticated routes: /login, /register, /forgot-password
      login/page.tsx
      register/page.tsx
    (dashboard)/          # Authenticated routes — middleware enforces session here
      layout.tsx          # Loads org context; redirects if no active subscription
      page.tsx            # Dashboard home
      settings/
        page.tsx
    api/
      auth/[...nextauth]/ # NextAuth handler — keep thin, put logic in lib/auth.ts
      webhooks/
        stripe/route.ts   # Stripe webhook — raw body required, do not use bodyParser
  components/
    ui/                   # shadcn/ui primitives only — never edit these directly
    forms/                # Controlled forms: each file exports one <XxxForm> component
    layouts/              # Shell, Sidebar, TopBar — structural, no business logic
    [feature]/            # Feature components co-located with their route when possible
  lib/
    db/
      schema.ts           # Single source of truth for all tables
      index.ts            # DB singleton — imported everywhere as `import { db } from '@/lib/db'`
      migrations/         # Drizzle-generated — never edit by hand
      seed.ts             # Test data only; never runs in production
    auth.ts               # NextAuth config + session helpers
    env.ts                # Zod-validated env — import from here, never from process.env directly
    utils.ts              # cn(), slugify(), formatCurrency() — pure functions only
    validations.ts        # Shared Zod schemas reused by forms AND server actions
  server/
    actions/              # Server Actions — one file per domain (billing.ts, api-keys.ts, ...)
    queries.ts            # All DB read functions — always accept `orgId` as first arg
    mutations.ts          # All DB write functions — same scoping rule
  middleware.ts           # Auth check + org context — runs on every (dashboard) request
  types/
    index.ts              # Shared TypeScript types not derivable from schema
```

---

## Environment Variables

All env vars are validated at startup via Zod. **Never** read `process.env.FOO` directly —
import from `src/lib/env.ts` so missing vars crash at boot, not silently at runtime.

```ts
// src/lib/env.ts
import { z } from 'zod';

const schema = z.object({
  DATABASE_URL:             z.string().min(1),
  NEXTAUTH_SECRET:          z.string().min(32),
  NEXTAUTH_URL:             z.string().url(),
  STRIPE_SECRET_KEY:        z.string().startsWith('sk_'),
  STRIPE_WEBHOOK_SECRET:    z.string().startsWith('whsec_'),
  NEXT_PUBLIC_APP_URL:      z.string().url(),
});

export const env = schema.parse(process.env);
```

`NEXT_PUBLIC_*` vars are the only ones exposed to the browser. Everything else is server-only.
Never put a server secret into a `NEXT_PUBLIC_*` var — it will be sent to every user's browser.

---

## Dev Commands

```bash
pnpm dev              # Dev server on :3000 with Turbopack
pnpm build            # Production build — run before every PR
pnpm start            # Serve production build locally
pnpm typecheck        # tsc --noEmit — run after every schema change
pnpm lint             # ESLint + Prettier
pnpm lint:fix         # Auto-fix lint + format
pnpm test             # Vitest unit tests
pnpm test:e2e         # Playwright — requires `pnpm build && pnpm start` first
pnpm db:generate      # After editing schema.ts: generate SQL migration file
pnpm db:migrate       # Apply pending migrations (dev + CI)
pnpm db:push          # Skip migration file — dev-only quick sync, never in CI
pnpm db:studio        # Drizzle Studio GUI at :4983
pnpm db:seed          # Load seed data — only against local DB
```

---

## SQL / Migration Conventions

**Schema changes always follow this order:**
1. Edit `src/lib/db/schema.ts`
2. `pnpm db:generate` — creates a new numbered file in `migrations/`
3. **Review the generated SQL** before committing — it can DROP columns you didn't intend
4. `pnpm db:migrate` — applies it locally
5. CI runs `pnpm db:migrate` on every push to verify the migration is clean

**Naming:**
- Tables: `snake_case`, plural — `users`, `api_keys`, `org_members`
- Columns: `snake_case` — `created_at`, `stripe_customer_id`
- Foreign keys: suffix `_id` — `user_id`, `org_id`

**Every table must have these three columns:**
```ts
id:         text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
created_at: text('created_at').notNull().default(sql`(datetime('now'))`),
updated_at: text('updated_at').notNull().default(sql`(datetime('now'))`),
```
UUIDs as text PKs avoid integer sequence leakage to end users. `datetime('now')` is SQLite's
ISO-8601 string format — consistent with JavaScript's `Date.toISOString()`.

**Multi-tenant scoping (critical):** Every function in `server/queries.ts` takes `orgId` as
its first argument and includes it in the WHERE clause. No global query may exist.
A query missing `orgId` is a security bug — it leaks data across tenants.

```ts
// CORRECT
export function getApiKeys(orgId: string) {
  return db.select().from(apiKeys).where(eq(apiKeys.orgId, orgId));
}
// WRONG — every org sees every key
export function getAllApiKeys() {
  return db.select().from(apiKeys);
}
```

**Soft deletes:** Add `deleted_at: text('deleted_at')` and filter `isNull(table.deletedAt)`.
Hard DELETE only for GDPR erasure — always through a dedicated `eraseUser(userId)` function
that also deletes related rows and notifies Stripe.

**Indexes:** Add explicit indexes on every column used in WHERE or ORDER BY that isn't the PK.
```ts
// Inside the Drizzle table definition:
apiKeyOrgIdx: index('idx_api_keys_org_id').on(t.orgId),
```

---

## Component Patterns

**Server-first:** Default to Server Components. Add `'use client'` only when the component
needs `useState`, `useEffect`, browser APIs, or event handlers. A Server Component that just
renders data sends zero JS to the browser.

**Data fetching:** Call query functions directly in Server Components — no `useEffect`, no SWR
in server context. Co-locate the query with the component that renders it:

```tsx
// app/(dashboard)/settings/page.tsx
import { getOrgSettings } from '@/server/queries';
import { auth } from '@/lib/auth';

export default async function SettingsPage() {
  const session = await auth();
  const settings = await getOrgSettings(session.user.orgId);
  return <SettingsForm settings={settings} />;
}
```

**Forms:** Always a Client Component calling a Server Action. Validate with Zod on both sides:
client for instant feedback, server for security. Server Actions return a discriminated union —
never throw into the client.

**Loading states:** `loading.tsx` per route segment for full-page skeletons; `<Suspense>` for
component-level loading within a page. Never use `isLoading` state driven by `useEffect`.

**Empty states:** Always explicit. An empty array that renders nothing causes confusing blank UI.
```tsx
if (items.length === 0) return <EmptyState message="No API keys yet." />;
return items.map(item => <ApiKeyRow key={item.id} item={item} />);
```

---

## Auth Conventions

Session lives in a JWT cookie managed by NextAuth. Middleware at `src/middleware.ts` enforces
the session on every `(dashboard)` route — no per-page auth check needed.

```ts
// In any Server Component:
import { auth } from '@/lib/auth';
const session = await auth();
if (!session) redirect('/login');
```

**Never use `useSession()` alone for access control.** Client state can be spoofed.
Data protection lives at the query layer via `orgId` scoping. The session check is only for UI
redirects.

**Middleware responsibilities:**
1. Verify valid session cookie
2. Check active Stripe subscription — redirect to `/billing` if expired
3. Set `x-org-id` request header for downstream Server Components

---

## Server Actions vs Route Handlers

| Use | When |
|---|---|
| Server Action | Authenticated form submit, dashboard mutation |
| Route Handler (`route.ts`) | Webhook, public API, OAuth callback |
| Query in Server Component | Read-only data display — no user input involved |

Never put business logic inside a route handler. Extract to `server/mutations.ts` and call it
from both the action and the handler so logic isn't duplicated.

---

## Error Handling

**Server Actions return a union — never throw into the client:**
```ts
type ActionResult<T> = { success: true; data: T } | { success: false; error: string };
```

**Route Handlers return explicit status codes:**
```ts
return NextResponse.json({ error: 'Not found' }, { status: 404 });
```

**`error.tsx` per route segment** catches unexpected errors. Always log with a correlation ID
server-side before returning the fallback UI. Include a "Try again" button calling `reset()`.

**Never swallow errors silently.** A catch block that does nothing creates ghost bugs.
If you catch and don't re-throw, you must log.

---

## Caching Strategy

Next.js 15 defaults to no caching. Be explicit on every `fetch`:

```ts
fetch(url, { next: { revalidate: 60 } }); // ISR — revalidate every 60s
fetch(url, { cache: 'no-store' });         // Always fresh (user-specific data)
fetch(url, { cache: 'force-cache' });      // Indefinite — until revalidatePath()
```

After every mutation call `revalidatePath('/path')` — not `router.refresh()`.
`router.refresh()` in a Server Component context has no effect.

---

## What We Don't Do (and Why)

| Rule | Why |
|---|---|
| No raw SQL in route handlers | All queries go through `server/queries.ts`. Bypassing this breaks multi-tenant scoping and makes queries impossible to audit in one place. |
| No `any` types | Use `unknown` + Zod narrowing. `any` silently defeats TypeScript and causes runtime crashes that look impossible from the type system. |
| No `useEffect` for data fetching | Use Server Components or React Query. `useEffect` causes request waterfalls and double-fetch in React StrictMode. |
| No `db:push` in CI | `db:push` skips migration files. CI always runs `db:migrate` to prove migrations apply cleanly against a real DB state. |
| No bare `process.env` reads | All env vars are validated in `lib/env.ts`. A missing var crashes at boot with a clear error, not silently at runtime when that code path is hit. |
| No tenant-unscoped query functions | Every query function takes `orgId` as its first argument. A function with no tenant scope is a data leak by definition. |
| No `dangerouslySetInnerHTML` without DOMPurify | XSS. If you must render HTML, run it through DOMPurify before setting it. |
| No Stripe business logic outside `webhooks/stripe/route.ts` | Webhook verification via `stripe.webhooks.constructEvent()` requires the raw body. Next.js body-parsing middleware corrupts it. |
| No hand-edited migration files | Drizzle validates migration hashes. Editing a generated file causes `db:migrate` to fail or silently skip. |
| No `useSession()` as an access gate | Client state can be spoofed. Protect data at the query layer with `orgId`. Use `useSession()` only to render the user's name in the UI. |

---

## How Claude Code Should Work in This Project

When implementing a feature, always follow this order:

1. **Schema first** — add or modify tables in `schema.ts`, then `pnpm db:generate && pnpm db:migrate`
2. **Queries/mutations** — add typed functions in `server/queries.ts` or `server/mutations.ts`; scope to `orgId`
3. **Server Action** — thin: validate input with the shared Zod schema, call the mutation, return `ActionResult<T>`
4. **UI** — Server Component for the page shell; Client Component only for interactive parts
5. **Types from schema** — use `InferSelectModel<typeof tableName>` instead of writing duplicate interfaces

When unsure: Server Action vs Route Handler → check the table above.

After any schema change: run `pnpm typecheck` immediately — Drizzle schema changes often
require type updates in query files, and the compiler will tell you exactly where.

When fixing a bug: write a failing Vitest test first, then fix, then confirm the test passes.
