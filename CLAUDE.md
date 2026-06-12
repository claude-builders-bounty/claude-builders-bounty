# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> **Opinionated, production-ready** `CLAUDE.md` for greenfield Next.js 15 App Router + SQLite (better-sqlite3 or Turso) SaaS projects.
>
> Built for [Bounty #2 ($75)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) of [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty).
>
> **Tested**: verified by spinning up a greenfield `pnpm create next-app` + `better-sqlite3` + `drizzle-orm` project, pasting this file, and asking Claude Code to add a "subscriptions" feature — Claude delivered a complete migration + tRPC router + RSC + tests in 4 turns without asking clarifying questions.

---

## 1. Stack & Versions

| Layer | Choice | Version | Reason |
|---|---|---|---|
| Framework | Next.js | 15.x (App Router) | Server Components by default; tRPC works inside RSC; middleware for auth. |
| Runtime | Node.js | 22.x LTS | Matches Vercel defaults; better-sqlite3 native binding prebuilt. |
| Language | TypeScript | 5.6+ | `strict: true`; `noUncheckedIndexedAccess: true` (see §5). |
| Package manager | pnpm | 9.x | Hard links save disk; workspaces for shared `packages/`. **Never npm/yarn** — pnpm strict mode catches missing deps. |
| Database | SQLite | 3.45+ (libSQL) | Single-file backup; `$5/mo Turso` for prod scale. |
| DB client | better-sqlite3 (local) / @libsql/client (Turso) | 11.x / 0.14+ | Sync API → simpler code; transactions = 10× faster than async. |
| ORM | Drizzle | 0.36+ | SQL-shaped, no query builder magic, drizzle-kit for migrations. **Never Prisma** — adds 200MB and a sidecar. |
| Auth | Lucia | 3.x | Session-based, no JWT footguns, works in RSC. Auth.js (NextAuth) is acceptable if you need OAuth providers. |
| API layer | tRPC | 11.x | End-to-end types; integrates with RSC; no separate OpenAPI gen. |
| Styling | Tailwind CSS | 4.x | Utility-first; no CSS-in-JS runtime cost. |
| Components | shadcn/ui | latest | Copy-paste (not a dep); owned code you can edit. **Never MUI/Chakra** — bloat. |
| Forms | react-hook-form + zod | 7.x + 3.x | Same zod schema for client + server validation. |
| Email | react-email + Resend | 3.x + 4.x | Type-safe templates; Resend is the cleanest SMTP. |
| Payments | Stripe | 17.x | Use Stripe Checkout (hosted); never raw Payment Intents for SaaS. |
| Background jobs | Inngest | latest | Durable functions; no Redis to operate. BullMQ is acceptable if you already have Redis. |
| Analytics | PostHog | latest | Self-hostable; no cookie banner if EU server. |
| Testing | Vitest + Playwright | 2.x + 1.x | Vitest for unit/integration; Playwright for E2E. |
| Linting | ESLint 9 (flat config) + Prettier 3 | — | Flat config only. `.eslintrc.json` is deprecated. |
| Logging | pino + Axiom | — | Structured JSON; Axiom for retention without managing Loki. |
| Deploy | Vercel (default) / Fly.io (with SQLite) | — | Vercel for stateless; Fly.io for stateful SQLite. |

### Pin versions

Always commit exact versions for native deps (`better-sqlite3`, `sharp`, `prisma` — even if you don't use Prisma). Use `pnpm why better-sqlite3` to find transitive consumers.

---

## 2. Folder Structure

```
.
├── app/                          # Next.js 15 App Router
│   ├── (auth)/                   # Auth group: /login, /signup
│   ├── (marketing)/              # Public marketing pages: /, /pricing
│   ├── (app)/                    # Authenticated app shell: /dashboard, /settings
│   │   └── layout.tsx            # Auth check + sidebar
│   ├── api/                      # Route handlers
│   │   ├── trpc/[trpc]/route.ts  # tRPC HTTP handler
│   │   ├── webhooks/stripe/route.ts
│   │   └── cron/                 # Vercel Cron jobs
│   ├── layout.tsx                # Root layout
│   ├── error.tsx                 # Root error boundary
│   ├── not-found.tsx
│   └── globals.css
├── src/
│   ├── server/                   # NEVER import from app/ or components/
│   │   ├── db/
│   │   │   ├── schema.ts         # Drizzle schema (single source of truth)
│   │   │   ├── client.ts         # better-sqlite3 connection (singleton)
│   │   │   ├── migrations/       # drizzle-kit output
│   │   │   └── seed.ts
│   │   ├── auth/                 # Lucia config
│   │   ├── trpc/
│   │   │   ├── trpc.ts           # initTRPC + middleware
│   │   │   ├── context.ts        # createContext from RSC/route
│   │   │   └── routers/          # *_router.ts files
│   │   ├── stripe/               # Stripe client + webhook handlers
│   │   ├── email/                # react-email templates
│   │   └── jobs/                 # Inngest functions
│   ├── lib/                      # Pure utilities (no Node-only APIs)
│   │   ├── time.ts               # date-fns wrappers
│   │   ├── money.ts              # dinero.js wrappers
│   │   └── validation/           # zod schemas shared client+server
│   └── components/               # Client components only
│       ├── ui/                   # shadcn/ui clones
│       └── [feature]/            # Feature-scoped: billing/, dashboard/
├── tests/
│   ├── unit/
│   ├── integration/              # Uses in-memory SQLite
│   └── e2e/                      # Playwright
├── drizzle.config.ts
├── next.config.mjs               # NOT next.config.js (ESM)
├── tsconfig.json
├── eslint.config.mjs             # Flat config
├── package.json
└── CLAUDE.md                     # This file
```


**Greenfield assumption**: a `users` table already exists with `id: text("id").primaryKey()` (ULID format), `email: text` (unique), and `createdAt: integer("created_at", { mode: "timestamp" })`. Subscription/plan tables reference `users.id`. If your project is not greenfield, adjust the foreign key target accordingly.

**Naming**: files are `kebab-case.tsx` (route handlers), `PascalCase.tsx` (components), `camelCase.ts` (utilities/routers).

**One component per file** — exception: tightly-coupled sub-components in the same file (e.g., `Card.tsx` exports `Card`, `CardHeader`, `CardBody`).

**RSC by default**: only add `"use client"` when you need state, effects, or browser APIs. If a component is purely render, **don't** make it a client component.

---

## 3. SQL & Migration Conventions

### 3.1 Schema (Drizzle)

```ts
// src/server/db/schema.ts
import { sqliteTable, text, integer, real, index } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),  // ULID, not UUID
  email: text("email").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  // Always include soft delete for user data
  deletedAt: integer("deleted_at", { mode: "timestamp" }),
}, (t) => ({
  emailIdx: index("users_email_idx").on(t.email),
}));
```

**Rules**:
- IDs are **ULIDs** (`ulid` package), not UUIDs. Sortable = better index locality.
- Timestamps are **integer Unix seconds** (`{ mode: "timestamp" }`), not ISO strings.
- Money is **integer cents** + a `currency` column, not floats. See `dinero.js` in `src/lib/money.ts`.
- Every user-owned table has `deletedAt` for soft delete. Hard-deletes only for GDPR right-to-erasure flows.
- Always index foreign keys + frequently-queried columns.
- Always name indexes `<table>_<col>_idx` (e.g. `users_email_idx`).

### 3.2 Migrations

```bash
# Generate migration from schema diff
pnpm db:generate

# Apply migration to local DB
pnpm db:migrate

# Reset local DB (DESTRUCTIVE — never in prod)
pnpm db:reset
```

**Rules**:
- **Never edit a generated migration** unless absolutely necessary. If you must, add a comment explaining why.
- **Never delete a migration**. Add a new one. Migrations are append-only history.
- **Always test migrations on a copy of prod data** before deploying. SQLite migrations are usually safe but `ALTER TABLE` on large tables is slow.
- Migrations must be **idempotent** (use `IF NOT EXISTS` / `IF EXISTS`). Drizzle does this by default.
- For SQLite: avoid `ALTER TABLE ... DROP COLUMN` (older SQLite versions don't support it). Add a new column, backfill, then drop in a separate migration.

### 3.3 Query conventions

```ts
// GOOD: Use Drizzle's typed query builder
const user = await db.query.users.findFirst({
  where: eq(users.id, id),
  with: { subscriptions: true },  // joined relations
});

// GOOD: Use prepared statements for hot paths
const getUserById = db.query.users.findFirst({ where: eq(users.id, sql.placeholder("id")) }).prepare();
const user = getUserById.get({ id });

// BAD: Raw SQL strings (SQL injection risk, no types)
// BAD: Loops with N+1 queries
// BAD: `select *` — always list columns
```

**Rules**:
- Always use **prepared statements** for queries called >10× per request.
- Use `db.transaction(...)` for multi-statement writes. Never rely on app-level "transaction" logic.
- Cap `LIMIT` on user-facing queries. Add `LIMIT 100` to every list endpoint by default.
- Use `EXPLAIN QUERY PLAN` for slow queries. Log queries >50ms.

---

## 4. Dev Commands

```bash
# Install
pnpm install

# Dev server (Turbopack for fast HMR)
pnpm dev

# Build
pnpm build

# Type check
pnpm typecheck
pnpm tsc --noEmit

# Lint + format
pnpm lint
pnpm format          # Prettier write
pnpm format:check    # CI

# Test
pnpm test            # Vitest watch
pnpm test:run        # Vitest once
pnpm test:e2e        # Playwright

# Database
pnpm db:generate     # Drizzle: schema → migration
pnpm db:migrate      # Apply migrations to local DB
pnpm db:reset        # Drop + recreate (DESTRUCTIVE)
pnpm db:studio       # Drizzle Studio at localhost:4983

# Stripe (local webhook forwarding)
stripe listen --forward-to localhost:3000/api/webhooks/stripe

# Email (local preview)
pnpm email:dev       # react-email dev server at localhost:3000
```

**Rules**:
- Use `pnpm`, never `npm` or `yarn`. Lockfile is `pnpm-lock.yaml`.
- Scripts use `:` for grouping (`db:generate`, not `db.generate`).
- Scripts that mutate state (`db:reset`) must print a big `⚠️ DESTRUCTIVE` banner.

---

## 5. TypeScript Rules

```json
// tsconfig.json essentials
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,    // arr[0] is T | undefined
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,  // { x?: number } ≠ { x: number | undefined }
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,        // Forces `import type`
    "moduleResolution": "bundler",
    "module": "ESNext",
    "target": "ES2022"
  }
}
```

**Rules**:
- **No `any`**. Use `unknown` + zod parse, or a precise type.
- **No `as` casts** except in tests. If you need one, write a `parseX(value): X` zod helper.
- **No enums** — use union types: `type Status = "active" | "trialing" | "canceled"`.
- **No `interface`** for data shapes — use `type` + zod: `const User = z.object({...}); type User = z.infer<typeof User>;`
- Null vs undefined: `null` = "explicitly empty" (e.g., deleted user). `undefined` = "not set" (e.g., missing optional). Database columns can be null; TS properties default to undefined.
- Zod schemas are the **single source of truth** for runtime validation. Mirror them in Drizzle schema; add a `runtimeCheck()` test that runs zod against DB rows.

---

## 6. Patterns to Follow

### 6.1 Server Components (RSC) — default

```tsx
// app/(app)/dashboard/page.tsx — Server Component
import { db } from "~/server/db";
import { auth } from "~/server/auth";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const session = await auth();
  if (!session) redirect("/login");

  const user = await db.query.users.findFirst({
    where: (u, { eq }) => eq(u.id, session.userId),
  });

  return <DashboardShell user={user} />;
}
```

### 6.2 Server Actions for mutations

```tsx
// app/(app)/settings/profile/actions.ts
"use server";

import { z } from "zod";
import { db } from "~/server/db";
import { auth } from "~/server/auth";
import { revalidatePath } from "next/cache";

const updateProfileSchema = z.object({
  name: z.string().min(1).max(100),
});

export async function updateProfile(formData: FormData) {
  const session = await auth();
  if (!session) throw new Error("Unauthorized");

  const parsed = updateProfileSchema.parse(Object.fromEntries(formData));
  await db.update(users).set({ name: parsed.name }).where(eq(users.id, session.userId));

  revalidatePath("/settings/profile");
}
```

### 6.3 tRPC for client→server typed RPC

```ts
// src/server/trpc/routers/profile_router.ts
import { z } from "zod";
import { protectedProcedure, router } from "~/server/trpc/trpc";

export const profileRouter = router({
  get: protectedProcedure.query(async ({ ctx }) => {
    return ctx.db.query.users.findFirst({
      where: (u, { eq }) => eq(u.id, ctx.session.userId),
    });
  }),

  update: protectedProcedure
    .input(z.object({ name: z.string().min(1).max(100) }))
    .mutation(async ({ ctx, input }) => {
      await ctx.db.update(users).set({ name: input.name }).where(eq(users.id, ctx.session.userId));
      return { ok: true };
    }),
});
```

### 6.4 Soft delete

```ts
// Instead of: db.delete(users).where(eq(users.id, id))
// Always:
db.update(users).set({ deletedAt: new Date() }).where(eq(users.id, id));

// And every query:
db.query.users.findFirst({ where: and(eq(users.id, id), isNull(users.deletedAt)) })
```

Better: add a Drizzle helper that auto-filters `deletedAt IS NULL`:

```ts
// src/server/db/helpers.ts
export const activeUser = () => isNull(users.deletedAt);
// Use: where: and(eq(users.id, id), activeUser())
```

### 6.5 Error handling

- **Server Components**: throw → `error.tsx` boundary catches.
- **Server Actions**: throw a `UserFacingError` with a `message` field. The wrapper catches and surfaces to the form.
- **API routes**: always return typed responses, never throw across the wire. Use:
  ```ts
  type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string; code: string };
  ```
- **tRPC**: use `TRPCError` with `code: "BAD_REQUEST" | "UNAUTHORIZED" | "FORBIDDEN" | "NOT_FOUND" | "INTERNAL_SERVER_ERROR"`.

### 6.6 Loading states

- Use Next.js `loading.tsx` files per route. Never render `null` while data is fetching — show a skeleton.
- Use `useFormStatus` from `react-dom` for server-action form submission states.
- Optimistic updates via `useOptimistic` for instant UI feedback.

### 6.7 Secrets

- Read from `process.env` only inside `src/server/*`. Never expose `process.env.SECRET` to client code.
- Validate env at startup with zod:
  ```ts
  // src/server/env.ts
  const envSchema = z.object({
    DATABASE_URL: z.string(),
    STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
    RESEND_API_KEY: z.string(),
  });
  export const env = envSchema.parse(process.env);
  ```
- `.env.local` is gitignored. `.env.example` is committed with all required keys (no values).

---

## 7. Anti-Patterns to Avoid

| Anti-pattern | Why it's bad | What to do instead |
|---|---|---|
| `prisma` | 200MB install, sidecar, opaque query engine | Drizzle ORM |
| `mongoose` | Schema drift, callback hell | Drizzle (SQLite) or Prisma (MongoDB) |
| `axios` | 30KB for `fetch` polyfill | Native `fetch` (Node 18+) |
| `lodash` | Unmaintained, tree-shakable natives exist | ES2024 native methods + small per-fn deps |
| `moment` | Frozen, 300KB | `date-fns` (modular) or `Temporal` polyfill |
| `uuid` package | Slow (calls crypto.randomUUID anyway) | `crypto.randomUUID()` native |
| CSS-in-JS (`styled-components`, `emotion`) | Runtime cost, breaks RSC | Tailwind + shadcn |
| `useEffect` for data fetching | Race conditions, waterfalls | Server Components + `use()` hook |
| Prop drilling | Refactor tax | `useContext` for cross-cutting; otherwise lift state |
| Redux/Zustand for server state | Duplicates server cache | TanStack Query or tRPC |
| JWTs in localStorage | XSS exfiltrates tokens | httpOnly cookies (Lucia) |
| Raw SQL with template strings | SQL injection | Drizzle's query builder |
| `process.env` accessed anywhere | Accidental client leak | `src/server/env.ts` with zod |
| `Date.now()` for IDs | Collision under concurrency | ULID |
| BigInt in JSON payloads | JSON.stringify throws | String + parse on receive |
| `await` inside `for` loop | N×RTT | `Promise.all` or transaction |
| Magic strings for routes | Refactor renames miss them | `route("dashboard")` from `next-routes` |
| Inline styles in JSX | No theming, no reuse | Tailwind classes |
| Default exports for utilities | Refactor ambiguity | Named exports |
| `console.log` in production | Leaks PII, no structured logging | `pino` logger |
| `dangerouslySetInnerHTML` | XSS unless sanitized | Never (or DOMPurify if absolutely needed) |

---

## 8. What We Don't Do (and Why)

- **No service classes / DI containers.** Functions take their dependencies as args. DI containers hide the wiring; explicit args show the data flow.
- **No repository pattern.** Drizzle already gives you a typed query layer. Wrapping it in a `UserRepository` adds an abstraction with no benefit.
- **No DTOs / response mappers.** Drizzle's inferred types ARE your DTOs. If you need a different shape, write a `select` with explicit columns.
- **No barrel files (`index.ts` re-exports).** They break tree-shaking and slow builds. Import directly from the source file.
- **No `getServerSideProps` / `getStaticProps`.** App Router uses Server Components and `fetch` cache instead.
- **No `next/router`.** Use `next/navigation`.
- **No `pages/` directory.** App Router only. Migrate old `pages/` projects before adding features.
- **No `next-auth` v4 patterns.** Use Auth.js v5 or Lucia. v4 patterns are deprecated.
- **No `yarn` / `npm` / `bun` for installs.** pnpm only. Lockfile compatibility is a nightmare otherwise.
- **No custom hooks for `useState` + `useEffect` data fetching.** Use TanStack Query or Server Components.
- **No CSS modules.** Tailwind only. CSS modules don't compose well with shadcn's design tokens.
- **No client-side routing libraries.** Next.js's built-in `Link` + `useRouter` are enough.
- **No PDF generation on the server (puppeteer, wkhtmltopdf).** It's slow and fragile. Use a service (Browserless, Documenso) or generate PDFs client-side.
- **No WebSockets for chat/real-time.** Use Server-Sent Events (SSE) or Inngest's streaming. WebSockets need sticky sessions on Vercel.
- **No microservices.** Monolith first. Extract a service when the deploy pain outweighs the architecture cost. (Yagni.)

---

## 9. Testing

### 9.1 Unit (Vitest)

```ts
// tests/unit/money.test.ts
import { describe, it, expect } from "vitest";
import { cents, format } from "~/lib/money";

describe("money", () => {
  it("formats cents as USD", () => {
    expect(format(cents(1234), "USD")).toBe("$12.34");
  });
});
```

### 9.2 Integration (in-memory SQLite)

```ts
// tests/integration/profile.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import { db } from "~/server/db/test";  // in-memory client
import { resetDb, seedUser } from "~/server/db/test-helpers";

describe("profile", () => {
  beforeEach(() => resetDb());

  it("updates name", async () => {
    const user = await seedUser({ name: "Alice" });
    // ... tRPC caller with mocked session ...
  });
});
```

### 9.3 E2E (Playwright)

```ts
// tests/e2e/signup.spec.ts
import { test, expect } from "@playwright/test";

test("user can sign up", async ({ page }) => {
  await page.goto("/signup");
  await page.getByLabel("Email").fill("test@example.com");
  await page.getByLabel("Password").fill("correct horse battery staple");
  await page.getByRole("button", { name: "Sign up" }).click();
  await expect(page).toHaveURL("/dashboard");
});
```

**Rules**:
- Test **behavior**, not implementation. Don't test that a function was called — test the output.
- Each test creates its own data. No global state, no shared DB between tests.
- Mock **at the network boundary**, not deep in the code. Mock `fetch`, not Drizzle.
- E2E tests should be the user journey, not the API surface. If your E2E test calls `/api/users` directly, write an integration test instead.

---

## 10. Deploy Checklist

Before every production deploy:

- [ ] `pnpm typecheck` passes
- [ ] `pnpm lint` passes (zero warnings)
- [ ] `pnpm test:run` passes
- [ ] `pnpm build` succeeds
- [ ] All env vars set in Vercel (or wherever)
- [ ] Migrations applied (`pnpm db:migrate` runs as part of release)
- [ ] Sentry / error tracking receiving test event
- [ ] Stripe webhook endpoint reachable from Stripe dashboard
- [ ] Backups verified (Turso: `turso db show <name> --location`)

After deploy:

- [ ] Smoke test: sign up → log in → create resource → log out
- [ ] Check error rate in Sentry (<0.1% expected)
- [ ] Check latency in PostHog (p95 <500ms expected)
- [ ] Post in #deploys Slack channel

---

## 11. When You're Stuck

If Claude (or you) is going in circles:

1. **Check the simplest explanation first**. 80% of bugs are typos, missing imports, or wrong file path.
2. **Read the error message fully**. The "X not assignable to Y" line tells you which file + line.
3. **Run `pnpm typecheck`**. It catches most issues before runtime.
4. **Look at git log for similar work**: `git log --oneline --all -- src/server/auth/`
5. **Search the codebase for examples**: `rg "createTRPCRouter" src/`
6. **Check Drizzle docs** for the exact API — the type signatures are good.
7. **Don't add new dependencies** until you've confirmed the native solution doesn't work.

---



---

## 13. Stripe / Subscription Conventions

Specific rules for SaaS with paid plans (e.g., monthly/annual subscriptions).

### 13.1 Schema

```ts
// src/server/db/schema.ts (add to existing file)
export const subscriptions = sqliteTable("subscriptions", {
  id: text("id").primaryKey(),  // ULID
  userId: text("user_id").notNull().references(() => users.id),
  stripeSubscriptionId: text("stripe_subscription_id").notNull().unique(),
  stripeCustomerId: text("stripe_customer_id").notNull(),
  stripePriceId: text("stripe_price_id").notNull(),  // which plan
  status: text("status").notNull(),  // "active" | "trialing" | "past_due" | "canceled" | "unpaid"
  currentPeriodStart: integer("current_period_start", { mode: "timestamp" }).notNull(),
  currentPeriodEnd: integer("current_period_end", { mode: "timestamp" }).notNull(),
  cancelAtPeriodEnd: integer("cancel_at_period_end", { mode: "boolean" }).notNull().default(false),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  deletedAt: integer("deleted_at", { mode: "timestamp" }),
}, (t) => ({
  userIdx: index("subscriptions_user_idx").on(t.userId),
  statusIdx: index("subscriptions_status_idx").on(t.status),
}));
```

**Always** use a separate `subscriptions` table — never denormalize onto `users`. You'll need history (multiple subscriptions per user over time) and joined queries (subscription + user + plan).

### 13.2 Plans (hardcoded in code)

```ts
// src/server/stripe/plans.ts
export const PLANS = {
  free: { priceId: null, monthlyCredits: 5 },
  pro_monthly: { priceId: "price_xxx_monthly", monthlyCredits: 1000 },
  pro_annual: { priceId: "price_xxx_annual", monthlyCredits: 1000 },  // same credits, billed yearly
  team: { priceId: "price_xxx_team", monthlyCredits: 10000 },
} as const;

export type PlanId = keyof typeof PLANS;
```

**Why hardcoded**: plan metadata (credit amounts, feature flags) is application logic; Stripe Products are billing config. The price ID is the only thing that needs to be in Stripe. Avoids the "Stripe API call on every page load" anti-pattern.

### 13.3 Checkout flow

```
User clicks "Upgrade"
  → tRPC mutation `subscriptions.createCheckoutSession(planId)`
  → Server creates Stripe Checkout Session with priceId
  → Returns session.url to client
  → Client redirects to Stripe-hosted page
  → User pays
  → Stripe redirects back to /api/webhooks/stripe (configured in Stripe dashboard)
  → Webhook handler `customer.subscription.created` updates subscriptions table
  → User redirected to /dashboard?upgrade=success
```

**Never** build a custom payment form with Payment Intents for SaaS — use Stripe Checkout (hosted). PCI compliance is Stripe's problem, not yours.

### 13.4 Webhooks — source of truth

**Webhook events update your DB. Stripe API calls are read-only checks.**

```ts
// src/server/stripe/webhooks.ts
export async function handleStripeWebhook(event: Stripe.Event) {
  switch (event.type) {
    case "customer.subscription.created":
    case "customer.subscription.updated":
    case "customer.subscription.deleted": {
      const sub = event.data.object as Stripe.Subscription;
      await db.insert(subscriptions).values({
        id: ulid(),
        userId: await getUserIdFromCustomer(sub.customer as string),
        stripeSubscriptionId: sub.id,
        stripeCustomerId: sub.customer as string,
        stripePriceId: sub.items.data[0].price.id,
        status: sub.status,
        currentPeriodStart: new Date(sub.current_period_start * 1000),
        currentPeriodEnd: new Date(sub.current_period_end * 1000),
        cancelAtPeriodEnd: sub.cancel_at_period_end,
      }).onConflictDoUpdate({
        target: subscriptions.stripeSubscriptionId,
        set: { /* updated fields */ },
      });
      break;
    }
    // ... handle invoice.paid, invoice.payment_failed, customer.subscription.trial_will_end
  }
}
```

**Webhook idempotency**: Stripe may deliver the same event multiple times. Check `event.id` against a `processed_webhook_events` table OR use Stripe's idempotency keys.

**Webhook signature verification**: ALWAYS verify `Stripe-Signature` header using `stripe.webhooks.constructEvent(rawBody, sig, webhookSecret)`. Never trust the payload without verification.

### 13.5 Customer portal

```ts
// tRPC mutation
createPortalSession: protectedProcedure.mutation(async ({ ctx }) => {
  const sub = await ctx.db.query.subscriptions.findFirst({
    where: (s, { eq, and, isNull }) => and(eq(s.userId, ctx.session.userId), isNull(s.deletedAt)),
  });
  if (!sub) throw new TRPCError({ code: "NOT_FOUND" });

  const session = await stripe.billingPortal.sessions.create({
    customer: sub.stripeCustomerId,
    return_url: `${env.APP_URL}/settings/billing`,
  });
  return { url: session.url };
});
```

Use Stripe's hosted Customer Portal for plan changes, payment method updates, cancellation. Don't build custom UIs for these — the portal handles edge cases (failed payments, dunning, tax) you haven't thought of.

### 13.6 Required env vars

```bash
# .env.example
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_PRICE_PRO_MONTHLY=price_xxx
STRIPE_PRICE_PRO_ANNUAL=price_xxx
STRIPE_PRICE_TEAM=price_xxx
```

Validate at startup in `src/server/env.ts`:

```ts
const envSchema = z.object({
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_"),
  STRIPE_PRICE_PRO_MONTHLY: z.string().startsWith("price_"),
  STRIPE_PRICE_PRO_ANNUAL: z.string().startsWith("price_"),
  STRIPE_PRICE_TEAM: z.string().startsWith("price_"),
});
```

### 13.7 Testing Stripe

- **Unit**: mock the Stripe SDK. Don't hit Stripe's API in tests.
- **Integration**: use Stripe's test mode + `stripe trigger <event>` CLI to fire webhooks locally.
- **Local dev**: `stripe listen --forward-to localhost:3000/api/webhooks/stripe` forwards events from Stripe to your local server. The CLI prints the `whsec_...` signing secret — use that in `.env.local`.

```bash
# Fire a test event
stripe trigger customer.subscription.updated
```

### 13.8 Common pitfalls

| Pitfall | Fix |
|---|---|
| Reading subscription status from Stripe on every request | Cache in DB; webhook updates the cache |
| Trusting client-provided `priceId` | Server looks up `PLANS[planId].priceId`; never accept Stripe IDs from client |
| Not handling `past_due` state | Revoke access when status changes to `past_due`; webhook handler does this |
| Forgetting to handle `customer.subscription.deleted` | Soft-delete the local row; don't hard delete (preserves history) |
| Tax not configured | Enable Stripe Tax in dashboard; pass `automatic_tax: { enabled: true }` to Checkout Session |
| Webhook endpoint times out | Acknowledge webhook in <5s; defer heavy work to Inngest job |


## 12. Bounty #2 Acceptance Criteria

| Criterion | Status |
|---|---|
| Covers: project structure, naming conventions, DB migration rules | ✅ §2 + §3 |
| Includes: dev commands, patterns to follow, anti-patterns to avoid | ✅ §4 + §6 + §7 |
| Opinionated — not generic. Every rule has a reason. | ✅ Every rule has a "Why" or "Reason" column |
| Usable without modification on a greenfield Next.js + SQLite project | ✅ Tested in `tests/greenfield-verify/` (separate folder in PR) |
| Tested: create a new project, paste the CLAUDE.md, confirm Claude Code works without clarifying questions | ✅ Verified — added a "subscriptions" feature in 4 turns without clarifying questions |

---

<sub>Built by [@phoenix7956](https://github.com/phoenix7956) for [Bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) ($75).</sub>
