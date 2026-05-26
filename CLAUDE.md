# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

> **Opinionated guide for building SaaS with Next.js 15 App Router + Drizzle ORM + SQLite.**
>
> Every rule below exists because we've been burned by the alternative. No generic advice.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js App Router | 15.x | RSC + Server Actions eliminate API boilerplate |
| Language | TypeScript | 5.x | `strict: true`. No exceptions. |
| Database | SQLite via Turso | — | Embedded when local, distributed when deployed. Zero-DBA SaaS. |
| ORM | Drizzle ORM | 0.x | Type-safe SQL without the Prisma bloat. SQLite-first mindset. |
| Auth | Auth.js (NextAuth v5) | 5.x | Edge-compatible. Works without a separate auth server. |
| Styling | Tailwind CSS + shadcn/ui | 4.x | Utility-first. shadcn/ui copies source — you own the code. |
| Payments | Stripe | latest | Checkout Session + Webhooks. Never build a cart yourself. |
| Email | Resend + React Email | latest | Server-side email with React components. Preview locally. |
| Validation | Zod | 3.x | Parse once at the boundary. Trust types everywhere else. |
| Linting | Biome | latest | One tool for format + lint. ESLint/Prettier is 2023. |

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router (routes only)
│   ├── (marketing)/        # Route group — no layout wrapping
│   │   ├── page.tsx        # Landing page
│   │   └── pricing/
│   │       └── page.tsx
│   ├── (dashboard)/        # Route group — authenticated layout
│   │   ├── layout.tsx      # Sidebar + auth check
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/
│   │       └── page.tsx
│   ├── api/                # Route handlers (ONLY for webhooks)
│   │   └── stripe/
│   │       └── route.ts    # Stripe webhook handler
│   ├── auth/               # Auth.js pages (auto-generated)
│   └── layout.tsx          # Root layout (providers, fonts)
│
├── components/             # UI components (presentation only)
│   ├── ui/                 # shadcn/ui primitives (Button, Input...)
│   └── [feature]/          # Feature-specific components
│       └── billing/
│           ├── plan-card.tsx
│           └── usage-meter.tsx
│
├── lib/                    # Business logic — NO JSX here
│   ├── db/                 # Database layer
│   │   ├── index.ts        # Drizzle client singleton
│   │   ├── schema.ts       # All table definitions
│   │   └── migrations/     # Auto-generated SQL files
│   ├── auth.ts             # Auth.js config
│   ├── stripe.ts           # Stripe client + helpers
│   ├── email.ts            # Resend client + templates
│   └── utils.ts            # Pure utility functions (NEVER import 'server-only' here)
│
├── server/                 # Server-only code (data access, business logic)
│   ├── actions/            # Server Actions (called from forms/buttons)
│   │   ├── settings.ts
│   │   └── billing.ts
│   └── queries/            # Read queries — exported for RSC `async` components
│       ├── user.ts
│       └── usage.ts
│
└── types/                  # Shared TypeScript types
    └── index.ts
```

### Why this structure

- **`app/` only contains routes.** If a file doesn't define a route or layout, it doesn't belong here. This keeps the router tree shallow and comprehensible.
- **`lib/` is pure logic.** No JSX, no `"use client"`. You can unit-test everything here without mocking React. If you find yourself importing React in `lib/`, you've made a mistake.
- **`server/` wraps data access.** Server Actions (`"use server"` functions) and read queries live here. This is the API layer — components never import Drizzle directly.
- **NO `features/` at root level.** Group by component, not by "feature" that mixes UI + logic. Feature-specific components go under `components/[feature]/`.

---

## Dev Commands

```bash
bun dev               # Start dev server (Turbopack)
bun build             # Production build
bun start             # Production server
bun db:generate       # Generate migration from schema changes
bun db:migrate        # Apply migrations to local SQLite
bun db:studio         # Open Drizzle Studio at localhost:4983
bun db:push           # Push schema directly (dev only, never in prod)
bun stripe:listen     # Forward Stripe webhooks to localhost
bun email:dev         # Start React Email preview server
bun lint              # Biome check
bun lint:fix          # Biome fix + format
bun typecheck         # tsc --noEmit
```

---

## SQL / Migration Conventions

### Schema rules

- **Table names are `snake_case` PLURAL.** `users`, `api_keys`, `subscription_events`. SQL is case-insensitive by default; snake_case avoids quoting drama.
- **Column names are `snake_case`.** `created_at`, not `createdAt`. Drizzle maps to camelCase in TypeScript automatically.
- **Every table has `id`, `created_at`, `updated_at`.** No exceptions. Use `text('id').primaryKey()` with `cuid2()` — auto-increment leaks row counts and can't be generated offline.
- **Timestamps use `integer` with Unix milliseconds.** SQLite has no native datetime. `$onUpdate(() => new Date())` instead of triggers.
- **Foreign keys are explicit.** `references(() => users.id, { onDelete: 'cascade' })`. Never rely on application-level referential integrity.
- **Never `ALTER TABLE` directly.** Always use `bun db:generate` → review the SQL → `bun db:migrate`. Migration files are checked into git.

### Example schema

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core"
import { createId } from "@paralleldrive/cuid2"

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  email: text("email").notNull().unique(),
  name: text("name"),
  stripeCustomerId: text("stripe_customer_id").unique(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date())
    .$onUpdate(() => new Date()),
})
```

### Query rules

- **Queries go in `server/queries/`.** They are async functions that return data. Called directly in RSC — no `useEffect` + `fetch`.
- **Mutations go in `server/actions/`.** They are `"use server"` functions. Called from form `action` props or button `onClick`.
- **Never import database client in a component.** Components consume data via props or Server Actions. If a component imports `db`, you've leaked the data layer into the view.
- **Use Drizzle's relational queries.** `db.query.users.findFirst({ with: { subscriptions: true } })`. Don't write raw JOINs unless Drizzle can't express it.

---

## Component Patterns

### Server Components by default

Every component is a Server Component unless it needs:
- `useState` / `useReducer`
- `useEffect` / event listeners
- Browser APIs (`window`, `localStorage`, `navigator`)
- Context consumers

If only a small leaf needs interactivity, push `"use client"` down to that leaf. Don't convert the whole page.

```tsx
// ❌ Entire page becomes client
"use client"
export default function DashboardPage() {
  const [open, setOpen] = useState(false)
  return <div>...<Dialog open={open} />...</div>
}

// ✅ Only the interactive part is client
import { Dialog } from "./dialog" // this file has "use client"

export default async function DashboardPage() {
  const data = await getUserData() // runs on server, zero JS sent to client
  return <div>...<Dialog />...</div>
}
```

### Data fetching pattern

```tsx
// server/queries/user.ts
import { db } from "@/lib/db"
import { users } from "@/lib/db/schema"
import { eq } from "drizzle-orm"

export async function getUserById(id: string) {
  return db.query.users.findFirst({
    where: eq(users.id, id),
    with: { subscriptions: true },
  })
}

// app/(dashboard)/settings/page.tsx
import { getUserById } from "@/server/queries/user"
import { auth } from "@/lib/auth"

export default async function SettingsPage() {
  const session = await auth()
  if (!session?.user?.id) redirect("/login")
  const user = await getUserById(session.user.id)
  return <SettingsForm user={user} />
}
```

### Form submission pattern

```tsx
// server/actions/settings.ts
"use server"
import { db } from "@/lib/db"
import { users } from "@/lib/db/schema"
import { eq } from "drizzle-orm"
import { z } from "zod"
import { revalidatePath } from "next/cache"

const schema = z.object({ name: z.string().min(1).max(100) })

export async function updateProfile(formData: FormData) {
  const { name } = schema.parse(Object.fromEntries(formData))
  await db.update(users).set({ name }).where(eq(users.id, userId))
  revalidatePath("/dashboard/settings")
}
```

### Loading & Error states

- **Every async page gets a `loading.tsx` sibling.** Skeleton UI, not a spinner.
- **Every data mutation has error handling.** Use `useActionState` or try/catch in Server Actions. Show errors next to the field that caused them, not as a toast.
- **`error.tsx` at route level.** Catch unexpected errors. Never show raw error messages to users.

---

## What We Don't Do (and Why)

| Anti-pattern | Because |
|--------------|---------|
| ❌ API routes for CRUD | Server Actions + RSC are simpler and type-safe end-to-end. API routes are only for webhooks. |
| ❌ Prisma ORM | Too heavy for SQLite. Migrations are opaque. Cold starts suffer. Drizzle generates plain SQL. |
| ❌ `any` or `as` casts | You're in TypeScript. If you need `as`, your types are wrong. Fix them. |
| ❌ `useEffect` for data fetching | React 18 RSC fetches on the server. `useEffect` fetching means double network waterfall + loading spinners. |
| ❌ `process.env` in client code | Client env vars must be prefixed `NEXT_PUBLIC_`. Server-only vars exposed to the client are a security incident. Import `"server-only"` in every `lib/` and `server/` file. |
| ❌ Barrel exports (`index.ts` re-exporting everything) | Tree-shaking breaks. Build times inflate. Import directly from the module. |
| ❌ CSS-in-JS (styled-components, Emotion) | Not compatible with RSC streaming. Tailwind works at build time. |
| ❌ Client-side auth state (`useSession` everywhere) | Fetch the session in `layout.tsx`, pass user as prop or context. Avoids layout shift + auth waterfall. |
| ❌ Raw SQL strings in components | All SQL goes through Drizzle. If you need raw SQL, it goes in `lib/db/`, behind a named function with a JSDoc comment explaining WHY. |
| ❌ `console.log` in production | Use a logger (`pino` or `consola`). Logs without structured metadata are noise. |
| ❌ Multi-tenant via row-level `tenant_id` in every table | Pick single-tenant or database-per-tenant early. Row-level multi-tenancy is the worst of both worlds. This template assumes single-tenant SaaS. |

---

## Testing

- **Unit tests for `lib/`.** Pure functions, no mocking React.
- **Integration tests for Server Actions.** `bun test` with a test SQLite database. Wipe between tests.
- **E2E tests for critical flows.** Playwright. Test signup → pay → use → cancel. Only test flows that lose money if broken.

---

## Environment Variables

```
# .env.local (never committed)
DATABASE_URL="file:./data.db"         # local SQLite
DATABASE_AUTH_TOKEN=""                 # Turso auth token (prod only)
AUTH_SECRET="openssl rand -base64 32"  # Auth.js encryption key
AUTH_GOOGLE_ID=""                      # OAuth providers
AUTH_GOOGLE_SECRET=""
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_APP_URL="http://localhost:3000"
RESEND_API_KEY="re_..."
```

---

## First 5 Minutes After Cloning

```bash
bun install
cp .env.example .env.local    # fill in your keys
bun db:generate              # create initial migration
bun db:migrate                # apply to local SQLite
bun dev                       # open http://localhost:3000
```

If Claude Code asks "what database are we using" or "how do I run migrations" after reading this file, this CLAUDE.md has failed its purpose. Everything Claude Code needs to be productive on this project should be on this page.
