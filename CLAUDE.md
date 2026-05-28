# CLAUDE.md

This file provides instructions to AI coding assistants working in this
codebase. Start your session by reading it — it establishes the rules,
conventions, and rationale that keep this project maintainable.

---

## Stack & Versions

| Concern              | Choice                        | Why                                                                 |
| -------------------- | ----------------------------- | ------------------------------------------------------------------- |
| Runtime              | Node.js 22 LTS                | Active LTS; needed for ESM-only packages and modern fetch           |
| Framework            | Next.js 15 (App Router)       | RSC, streaming, server actions, ISR — battery-included full-stack   |
| Language             | TypeScript 5.x, strict mode   | Catches entire classes of bugs before they reach production         |
| Styling              | Tailwind CSS 4 + shadcn/ui    | Utility-first velocity; shadcn gives accessible, composable primitives |
| Database             | Turso (libSQL over HTTP)      | Edge-friendly, SQLite-compatible, managed backups, branching        |
| ORM / query layer    | Drizzle ORM                   | Type-safe, lightweight, SQL-like DX, first-class Turso/libSQL support |
| Auth                 | Better Auth v1                | Framework-native, works in middleware, passwords + OAuth + MFA      |
| Payments             | Stripe (via `@ stripe/stripe-js` + webhooks) | Gold standard for SaaS billing; Checkout + Customer Portal |
| Email                | Resend                        | Modern React-email integration, webhook delivery events             |
| Validation           | Zod                           | Runtime type safety for form data, API routes, and server actions   |
| Background jobs      | Trigger.dev (optional)        | Durable task runner when you outgrow server actions                 |
| Testing              | Vitest + Playwright           | Unit/integration (Vitest) + E2E (Playwright)                        |
| Package manager      | pnpm                          | Strict, fast, and disk-efficient                                    |
| Formatting / linting | Prettier + ESLint (flat config) + Biome (optional) | Consistent code style, zero-config mostly      |

**Never** introduce a new dependency without an explicit instruction. Stay on the
chosen path — swapping the ORM, auth library, or CSS framework mid-project
causes far more damage than any marginal improvement justifies.

---

## Project Structure

```
.
├── src/
│   ├── app/                    # Next.js App Router pages and API routes
│   │   ├── (marketing)/        # Route group — public pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── pricing/
│   │   │   └── blog/
│   │   ├── (dashboard)/        # Route group — authenticated pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx        # Dashboard home
│   │   │   ├── settings/
│   │   │   └── api/            # Authenticated API routes (server-side)
│   │   ├── api/                # Public API routes (webhooks, health)
│   │   │   ├── webhooks/
│   │   │   │   └── stripe/
│   │   │   └── health/
│   │   └── layout.tsx          # Root layout
│   ├── components/             # Shared UI components
│   │   ├── ui/                 # shadcn/ui primitives (Button, Input, etc.)
│   │   ├── forms/              # Reusable form components
│   │   ├── marketing/          # Components for public pages only
│   │   └── dashboard/          # Components for authenticated pages only
│   ├── db/                     # Everything database-related
│   │   ├── schema/             # Drizzle schema files (one file per domain)
│   │   │   ├── users.ts
│   │   │   ├── teams.ts
│   │   │   ├── subscriptions.ts
│   │   │   └── index.ts        # Barrel export, merges relations
│   │   ├── migrations/         # Auto-generated SQL migration files
│   │   └── seed.ts             # Seed/dev data script
│   ├── lib/                    # Pure utility code, no React
│   │   ├── auth.ts             # Better Auth configuration
│   │   ├── auth-client.ts      # Client-side auth helpers
│   │   ├── db.ts               # Drizzle + Turso client singleton
│   │   ├── stripe.ts           # Stripe server-side helpers
│   │   ├── email.ts            # Resend client
│   │   ├── env.ts              # Zod-validated environment variables
│   │   └── utils.ts            # Generic helpers (cn(), formatCurrency(), etc.)
│   ├── actions/                # Server Actions — one file per domain
│   │   ├── auth.ts
│   │   ├── billing.ts
│   │   ├── teams.ts
│   │   └── settings.ts
│   ├── services/               # Business logic layer (callable from actions or API routes)
│   │   ├── billing-service.ts
│   │   ├── team-service.ts
│   │   └── user-service.ts
│   ├── hooks/                  # Client-side React hooks
│   ├── middleware.ts           # Next.js middleware (auth gating, rewrites)
│   └── instrumentation.ts     # Trigger.dev or OpenTelemetry setup
├── public/                     # Static assets
├── tests/
│   ├── unit/
│   └── e2e/
├── drizzle.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── next.config.ts
├── package.json
└── .env.local                  # NEVER commit — use .env.example
```

### Structure Rationale

- **Route groups** `(marketing)` and `(dashboard)` keep URL segments clean while
  letting each group have its own layout, middleware, and loading states.
- **`src/` directory** is non-negotiable — it separates application code from
  config files at the project root, and colocation in the App Router works best
  with clear boundaries.
- **`db/schema/`** is split by domain, not a single monolithic file. A
  five-table SaaS is fine; a forty-table SaaS needs this from day one.
- **`services/`** is the only place business logic lives. Server actions
  and API routes are thin wrappers — they parse input, call a service, and
  return a result. If you need the same logic in a webhook handler AND a
  server action, you put it in a service.  No duplication.
- **`lib/` vs `services/`**: `lib/` is stateless infrastructure (clients,
  configs, helpers). `services/` is stateful business logic (orchestrates
  database calls, external APIs, side effects).

---

## Database & SQL Conventions

### Schema Design Rules

1. **Every table gets `id`, `createdAt`, `updatedAt`:**
   ```ts
   export const users = sqliteTable("users", {
     id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
     createdAt: integer("created_at", { mode: "timestamp" })
       .notNull()
       .default(sql`(unixepoch())`),
     updatedAt: integer("updated_at", { mode: "timestamp" })
       .notNull()
       .default(sql`(unixepoch())`)
       .$onUpdate(() => new Date()),
     // ... domain columns
   });
   ```
   Reason: Audit trails, debugging, and soft-delete support happen later.

2. **UUIDs as primary keys, never auto-increment integers.** UUIDs allow
   merging data across environments, prevent enumeration attacks, and work in
   distributed systems. Exception: junction tables where a composite PK is
   more appropriate.

3. **`snake_case` in the database, `camelCase` in TypeScript.** Drizzle
   handles the mapping. Use explicit column name overrides:
   ```ts
   displayName: text("display_name").notNull(),
   ```

4. **Always declare `$onUpdate` for `updatedAt`** — Drizzle cannot infer this
   from SQLite and you'll spend hours debugging stale timestamps.

5. **Enums go in a separate file** (`src/db/schema/enums.ts`) and are shared
   across schema files:
   ```ts
   export const PLAN_NAMES = ["free", "pro", "enterprise"] as const;
   export const USER_ROLES = ["owner", "admin", "member"] as const;
   ```

6. **Foreign keys are explicit,** even though Turso/libSQL requires a pragma:
   ```ts
   teamId: text("team_id")
     .notNull()
     .references(() => teams.id, { onDelete: "cascade" }),
   ```

### Migration Rules

- **Never edit a migration file after it's been applied.** Once `drizzle-kit
  generate` creates it and it runs against any database, it's immutable.
- **Always run `drizzle-kit generate`** after changing a schema file.
- **Never write raw DDL** unless Drizzle cannot express it (rare).
- **Always test migrations** against a local copy before deploying:
  ```bash
  pnpm db:generate   # creates migration SQL
  pnpm db:migrate    # applies to local dev DB
  pnpm db:studio     # opens Drizzle Studio to verify
  ```
- **Turso-specific:** Production schemas use `turso db shell` for manual
  inspection. Never run migrations against production directly — use a CI
  pipeline with a backup step.

### Query Patterns

**Do this — Drizzle's relational query API:**
```ts
const usersWithTeams = await db.query.users.findMany({
  with: { team: true },
  where: eq(users.plan, "pro"),
});
```

**Not this — raw SQL in source files:**
```ts
// ANTI-PATTERN
const rows = await db.run(sql`SELECT * FROM users WHERE plan = 'pro'`);
```

Reserve raw SQL for migrations (generated by Drizzle) and complex
analytics queries where the ORM gets in the way — and isolate those in
a `src/services/analytics-service.ts`.

---

## Component Patterns

### Server Components (Default)

Every component starts as a server component. You only add `"use client"` when
you *must* — for event handlers, state, effects, or browser APIs.

```tsx
// Default: server component — can be async, can read DB directly
// File: src/app/(dashboard)/page.tsx
import { getUserDashboardData } from "@/services/user-service";
import { getCurrentUser } from "@/lib/auth";

export default async function DashboardPage() {
  const user = await getCurrentUser();
  const data = await getUserDashboardData(user.id);
  return <DashboardView data={data} />;
}
```

### Client Components (Only When Necessary)

```tsx
// File: src/components/dashboard/interactive-widget.tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function InteractiveWidget() {
  const [count, setCount] = useState(0);
  return <Button onClick={() => setCount(count + 1)}>Clicks: {count}</Button>;
}
```

### Data Fetching

- **In server components:** Call the service layer directly. No `useEffect`
  for data fetching unless it's client-side interactivity.
- **In client components:** Use server actions passed as props, or
  `useActionState` / `useOptimistic` for mutations.
- **Never** import `db` (the Drizzle client) directly into a component or
  client-side file. That leaks server-only code.

### Forms & Mutations

All mutations go through **server actions**, not API routes:

```tsx
// File: src/actions/settings.ts
"use server";

import { revalidatePath } from "next/cache";
import { getCurrentUser } from "@/lib/auth";
import { updateUserDisplayName } from "@/services/user-service";
import { displayNameSchema } from "@/lib/validations";

export async function updateDisplayName(formData: FormData) {
  const user = await getCurrentUser();
  if (!user) throw new Error("Unauthorized");

  const parsed = displayNameSchema.parse({
    displayName: formData.get("displayName"),
  });

  await updateUserDisplayName(user.id, parsed.displayName);
  revalidatePath("/dashboard/settings");
}
```

### Error Boundaries

Use the `error.tsx` convention from Next.js, not ad-hoc try/catch in templates:

```
src/app/(dashboard)/error.tsx     # error boundary for all dashboard routes
src/app/(dashboard)/billing/error.tsx  # scoped to billing
```

---

## Naming Conventions

| Thing                  | Convention                 | Example                                  |
| ---------------------- | -------------------------- | ---------------------------------------- |
| Route segments         | kebab-case                 | `/team-settings`, `/billing-history`     |
| Component files        | kebab-case                 | `user-profile-form.tsx`                  |
| Component functions    | PascalCase                 | `UserProfileForm`                        |
| Server action files    | kebab-case, domain-named   | `billing.ts`, `teams.ts`                 |
| Server action functions | camelCase                  | `createCheckoutSession`, `inviteMember`  |
| Service files          | kebab-case, `-service`     | `billing-service.ts`                     |
| Service functions      | camelCase, verb-led        | `createSubscription`, `cancelSubscription` |
| Database tables        | snake_case, plural         | `users`, `team_members`, `subscriptions` |
| Database columns       | snake_case                 | `display_name`, `stripe_customer_id`     |
| Schema files           | kebab-case or one-word     | `users.ts`, `teams.ts`                   |
| Zod schemas            | camelCase, suffixed Schema | `createTeamSchema`, `displayNameSchema`  |
| Utility functions      | camelCase                  | `formatCurrency`, `cn`                   |
| Environment variables  | UPPER_SNAKE, prefixed      | `DATABASE_URL`, `STRIPE_SECRET_KEY`      |
| Test files             | `*.test.ts` (unit), `*.spec.ts` (e2e) | `billing-service.test.ts`    |

---

## Dev Commands

```bash
# Development
pnpm dev                  # Start Next.js dev server (Turbopack)
pnpm dev:https            # Dev server with HTTPS (needed for some OAuth providers)

# Database
pnpm db:generate          # Generate migration SQL from schema changes
pnpm db:migrate           # Apply pending migrations to local dev DB
pnpm db:push              # Push schema directly to DB (dev only — no migration file)
pnpm db:studio            # Open Drizzle Studio at localhost:4983
pnpm db:seed              # Seed the database with sample data

# Code quality
pnpm lint                 # ESLint across the project
pnpm format               # Prettier
pnpm typecheck            # tsc --noEmit

# Testing
pnpm test                 # Vitest (unit + integration)
pnpm test:e2e             # Playwright
pnpm test:e2e:ui          # Playwright with UI mode

# Build & production
pnpm build                # Next.js production build
pnpm start                # Start production server (after build)
pnpm analyze              # Bundle analysis (if @next/bundle-analyzer is set up)

# Stripe
pnpm stripe:listen        # Stripe CLI webhook forwarding to localhost
pnpm stripe:trigger       # Trigger a test webhook event
```

---

## Environment Variables

Define all env vars in `src/lib/env.ts` using Zod for runtime validation:

```ts
// File: src/lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  DATABASE_AUTH_TOKEN: z.string().min(1),
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url().default("http://localhost:3000"),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_"),
  RESEND_API_KEY: z.string().min(1),
});

export const env = envSchema.parse(process.env);
```

Never access `process.env` directly — always import from `src/lib/env.ts`.

---

## What We Don't Do (And Why)

| Anti-Pattern                                | Reason                                                                 |
| ------------------------------------------- | ---------------------------------------------------------------------- |
| **API routes for mutations**                | Server actions eliminate boilerplate, give progressive enhancement for free |
| **`any` type**                              | Just don't. `unknown` if you must, then narrow it.                    |
| **Default exports for components**          | Named exports improve IDE auto-import, tree-shaking, and grep-ability |
| **Inline SQL in components**                | Tightly couples UI to schema; breaks if the schema changes            |
| **Client-side data fetching with `useEffect`** | Wastes a round trip; server components + RSC payload is zero-cost    |
| **Mixing business logic into server actions** | Actions become untestable; `services/` is the single source of truth |
| **Monolithic schema file**                  | Becomes unreadable past ~15 tables; split by domain from the start    |
| **Auto-increment PKs**                      | Enumeration risk, no multi-environment merge support                   |
| **Skipping error boundaries**               | A single uncaught error takes down the entire page, not just a widget |
| **Committing `.env` files**                 | Leaks secrets into git history — use `.env.example` and 1Password/Infisical |
| **Direct `process.env` access**             | No validation, no IntelliSense, crashes at runtime with missing vars  |
| **`npm` or `yarn`**                         | pnpm is enforced via `packageManager` in `package.json`               |

---

## Auth Guard Pattern

Every authenticated route must be gated. Use a shared layout check:

```tsx
// File: src/app/(dashboard)/layout.tsx
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return <>{children}</>;
}
```

Additionally, every server action must independently verify authentication:

```ts
// In every server action:
const user = await getCurrentUser();
if (!user) throw new Error("Unauthorized");
```

Layout-level gating prevents the page from rendering; action-level gating
prevents unauthenticated mutations. You need both.

---

## Billing & Subscription Pattern

When creating or modifying Stripe-related logic:

1. **Always use Stripe Checkout** for subscriptions — never build a custom
   credit-card form unless you have a dedicated PCI compliance team.
2. **Always verify the webhook signature** before trusting the event:
   ```ts
   const sig = request.headers.get("stripe-signature")!;
   const event = stripe.webhooks.constructEvent(body, sig, env.STRIPE_WEBHOOK_SECRET);
   ```
3. **Store `stripeCustomerId` on the user or team,** not on the subscription.
   One customer can have multiple subscriptions; you need to find the
   right entity.
4. **Read subscription state from your database**, not from Stripe's API, on
   every page load. Keep your DB in sync via webhooks.

---

## Getting Started (Greenfield)

After cloning this template, run:

```bash
pnpm install
cp .env.example .env.local
# Fill in .env.local with your Turso, Stripe, Resend keys
pnpm db:generate
pnpm db:migrate
pnpm db:seed    # optional
pnpm dev
```

Visit `http://localhost:3000`. The marketing pages are public; `/dashboard`
redirects unauthenticated users to `/login`.
