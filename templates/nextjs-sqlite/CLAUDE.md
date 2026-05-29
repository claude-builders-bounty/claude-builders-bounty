# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude Code exactly how this project works.
Read it fully before writing any code. Do not ask clarifying questions
about structure, naming, or patterns — the answers are here.

---

## Stack & Versions

| Layer       | Choice                        | Why                                               |
|-------------|-------------------------------|---------------------------------------------------|
| Framework   | Next.js 15 (App Router)       | RSC-first, no pages/ dir, layouts built-in        |
| Database    | Turso (libsql) or better-sqlite3 | Edge-compatible (Turso) or local-only (sqlite3) |
| ORM         | Drizzle ORM                   | Type-safe, SQL-like, no magic, migrations are SQL |
| Auth        | Auth.js v5 (next-auth)        | Session cookies, no JWT footguns                  |
| Styling     | Tailwind CSS v4               | Utility-first, no CSS files unless strictly needed|
| UI          | shadcn/ui (copy-paste)        | No component library dep, we own the code         |
| Validation  | Zod                           | Single schema for DB + form + API                 |
| Email       | Resend                        | Simple API, great DX                              |
| Payments    | Stripe                        | Webhooks land in app/api/webhooks/stripe/route.ts |
| Deployment  | Vercel                        | Edge functions, easy env vars                     |

Node: 20+. TypeScript strict mode always on.

---

## Folder Structure

```
src/
  app/                        # Next.js App Router — routes only
    (auth)/                   # Route group: login, signup, forgot-password
    (dashboard)/              # Route group: authenticated SaaS UI
      layout.tsx              # Checks session, redirects if unauthed
    api/
      webhooks/
        stripe/route.ts
    globals.css
    layout.tsx                # Root layout: fonts, providers
    page.tsx                  # Marketing homepage

  components/
    ui/                       # shadcn/ui copies live here — never modify originals
    [feature]/                # Feature-scoped components, e.g. components/billing/
    layout/                   # Navbar, Sidebar, Footer

  db/
    index.ts                  # DB client singleton (Turso or better-sqlite3)
    schema.ts                 # All Drizzle schema in ONE file
    migrations/               # SQL files only — never edited by hand after creation

  lib/
    auth.ts                   # Auth.js config
    stripe.ts                 # Stripe singleton
    resend.ts                 # Resend singleton
    utils.ts                  # cn() and pure helpers only — no side effects

  server/
    [feature].ts              # Server-only data access, e.g. server/users.ts
                              # These are NOT route handlers. They run on the server.
                              # Import only in Server Components or Server Actions.

  hooks/                      # Client-side hooks only
  types/                      # Shared TypeScript types and Zod schemas
```

**Rules:**
- `app/` contains routes and layouts only — no business logic
- `server/` is the data layer — never imported from client components
- `components/` never imports from `server/` directly — use Server Components or Actions
- One component per file. File name = component name in kebab-case.

---

## Naming Conventions

| Thing                  | Convention              | Example                        |
|------------------------|-------------------------|--------------------------------|
| Files & folders        | kebab-case              | `user-profile.tsx`             |
| Components             | PascalCase              | `UserProfile`                  |
| Server functions       | verb + noun             | `getUserById`, `createInvoice` |
| DB table names         | snake_case plural       | `users`, `subscription_plans`  |
| DB column names        | snake_case              | `created_at`, `stripe_customer_id` |
| Drizzle schema vars    | camelCase               | `users`, `subscriptionPlans`   |
| Route handlers         | `route.ts` always       | `app/api/users/route.ts`       |
| Server Actions files   | `actions.ts` per feature| `app/(dashboard)/billing/actions.ts` |
| Zod schemas            | PascalCase + Schema     | `CreateUserSchema`             |
| Environment variables  | SCREAMING_SNAKE_CASE    | `DATABASE_URL`, `STRIPE_SECRET_KEY` |

---

## Database & Migration Rules

**Schema:** All tables defined in `src/db/schema.ts`. One file. No exceptions.

```ts
// src/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'

export const users = sqliteTable('users', {
  id:        text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email:     text('email').notNull().unique(),
  name:      text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' })
               .$defaultFn(() => new Date()).notNull(),
})
```

**IDs:** Always `text` UUIDs via `crypto.randomUUID()`. Never auto-increment integers.
**Timestamps:** `created_at` and `updated_at` on every table. Always `integer` with `mode: 'timestamp'`.
**Soft deletes:** Add `deleted_at` (nullable timestamp) instead of hard deletes on user-owned data.

**Migrations:**
```bash
# Generate migration SQL from schema changes
npx drizzle-kit generate

# Apply to DB
npx drizzle-kit migrate
```

- Never edit generated migration files after creation
- Never write raw SQL migrations by hand
- Never use `drizzle-kit push` in production — only `migrate`
- Commit both the migration SQL file and the updated `schema.ts`

**DB client singleton:**
```ts
// src/db/index.ts — Turso example
import { drizzle } from 'drizzle-orm/libsql'
import { createClient } from '@libsql/client'

const client = createClient({
  url:       process.env.DATABASE_URL!,
  authToken: process.env.DATABASE_AUTH_TOKEN,
})

export const db = drizzle(client)
```

Only one `db` instance. Import it from `src/db/index.ts` everywhere.

---

## Server Components & Data Fetching

**Default to Server Components.** Add `'use client'` only when you need:
- `useState` / `useEffect`
- Browser APIs
- Event handlers that can't be Server Actions

```tsx
// CORRECT: fetch data directly in a Server Component
// src/app/(dashboard)/page.tsx
import { getUserSubscription } from '@/server/billing'
import { auth } from '@/lib/auth'

export default async function DashboardPage() {
  const session = await auth()
  const sub = await getUserSubscription(session.user.id)
  return <SubscriptionCard sub={sub} />
}
```

```tsx
// WRONG: never fetch in useEffect for data that exists at render time
'use client'
useEffect(() => { fetch('/api/subscription').then(...) }, [])
```

**Loading states:** Use `loading.tsx` next to `page.tsx`. Use `<Suspense>` for partial loading.
**Error states:** Use `error.tsx` next to `page.tsx`.

---

## Server Actions

Use Server Actions for all mutations. No separate API routes for form submissions.

```ts
// src/app/(dashboard)/billing/actions.ts
'use server'
import { auth } from '@/lib/auth'
import { db } from '@/db'
import { revalidatePath } from 'next/cache'
import { z } from 'zod'

const UpdateNameSchema = z.object({
  name: z.string().min(1).max(100),
})

export async function updateUserName(formData: FormData) {
  const session = await auth()
  if (!session) throw new Error('Unauthorized')

  const { name } = UpdateNameSchema.parse({
    name: formData.get('name'),
  })

  await db.update(users).set({ name }).where(eq(users.id, session.user.id))
  revalidatePath('/dashboard/settings')
}
```

**Rules:**
- Always authenticate at the top of every Server Action — never trust the caller
- Always validate with Zod — never trust `formData` directly
- Call `revalidatePath()` or `revalidateTag()` after mutations
- Return `{ error: string }` for recoverable errors, throw for unrecoverable ones

---

## API Routes

Only for: webhooks, OAuth callbacks, and third-party integrations that need HTTP.
Everything else is a Server Action.

```ts
// src/app/api/webhooks/stripe/route.ts
import { headers } from 'next/headers'
import Stripe from 'stripe'

export async function POST(req: Request) {
  const body = await req.text()
  const sig  = (await headers()).get('stripe-signature')!
  // verify → handle event → return 200
}
```

---

## Component Patterns

```tsx
// Server Component that passes data to a Client Component
// server-side: src/app/(dashboard)/settings/page.tsx
import { SettingsForm } from '@/components/settings/settings-form'
import { getUserById } from '@/server/users'

export default async function SettingsPage() {
  const user = await getUserById(session.user.id)
  return <SettingsForm user={user} />
}

// client-side: src/components/settings/settings-form.tsx
'use client'
import { updateUserName } from '../actions'  // Server Action

export function SettingsForm({ user }: { user: User }) {
  return (
    <form action={updateUserName}>
      <input name="name" defaultValue={user.name ?? ''} />
      <button type="submit">Save</button>
    </form>
  )
}
```

**shadcn/ui:** Run `npx shadcn@latest add <component>` to add. Never install the npm package.
All copied components live in `src/components/ui/`. Modify them freely — we own them.

---

## Auth Patterns

```ts
// src/lib/auth.ts
import NextAuth from 'next-auth'
import GitHub from 'next-auth/providers/github'

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [GitHub],
})
```

```tsx
// Protect a layout (preferred over per-page protection)
// src/app/(dashboard)/layout.tsx
import { auth } from '@/lib/auth'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({ children }) {
  const session = await auth()
  if (!session) redirect('/login')
  return <>{children}</>
}
```

Never pass the full session object to Client Components. Pass only the fields needed.

---

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL=
DATABASE_AUTH_TOKEN=          # Turso only
NEXTAUTH_SECRET=              # openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
RESEND_API_KEY=
```

All env vars validated at startup with Zod in `src/lib/env.ts`:
```ts
import { z } from 'zod'

const envSchema = z.object({
  DATABASE_URL:          z.string().url(),
  NEXTAUTH_SECRET:       z.string().min(32),
  STRIPE_SECRET_KEY:     z.string().startsWith('sk_'),
  // ...
})

export const env = envSchema.parse(process.env)
```

Import from `src/lib/env.ts` — never `process.env` directly.

---

## Dev Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build — fix all TS errors first
npm run lint         # ESLint — must pass before committing
npm run typecheck    # tsc --noEmit — run this, not just lint
npx drizzle-kit studio   # Visual DB browser
npx drizzle-kit generate # Generate migration from schema change
npx drizzle-kit migrate  # Apply migrations to DB
```

---

## What We Don't Do (And Why)

| Anti-pattern                            | Why not                                                    |
|-----------------------------------------|------------------------------------------------------------|
| `pages/` directory                      | App Router only — mixing both causes cache and layout bugs |
| `getServerSideProps` / `getStaticProps` | Dead API in App Router — use async Server Components       |
| Fetching in `useEffect` for initial data| Creates loading flash, hurts SEO, defeats RSC purpose      |
| `any` in TypeScript                     | Defeats the entire point of Drizzle + Zod schemas          |
| Auto-increment integer IDs              | Leaks row count, bad for distributed systems, IDOR risk    |
| Raw SQL strings                         | Use Drizzle query builder — type-safe, injection-safe      |
| `drizzle-kit push` in production        | Destructive on conflict — only `migrate` in prod           |
| Storing secrets in `.env` committed     | Use `.env.local` — it is gitignored by Next.js by default  |
| JWT sessions                            | Session cookies via Auth.js — JWTs are not revocable       |
| One giant `utils.ts`                    | Split by feature — utils.ts holds only `cn()` and pure fns |
| Importing `server/` from client code    | Leaks DB credentials — use Server Components or Actions    |
| `console.log` in production code        | Use structured logging or remove before merge              |
| Skipping Zod in Server Actions          | `formData` is user input — always validate                 |

---

## TypeScript Rules

- `strict: true` in `tsconfig.json` — no exceptions
- No `as any` casts — if you need one, fix the type
- Prefer `type` over `interface` for data shapes
- Use `satisfies` operator for config objects
- Drizzle `InferSelectModel` / `InferInsertModel` for table types:

```ts
import type { InferSelectModel, InferInsertModel } from 'drizzle-orm'
import { users } from '@/db/schema'

export type User       = InferSelectModel<typeof users>
export type NewUser    = InferInsertModel<typeof users>
```

---

## Error Handling

- Server Actions return `{ data, error }` — never throw to the client
- Route handlers return proper HTTP status codes (400, 401, 403, 404, 500)
- Unknown errors in Server Actions are logged server-side, return generic message to client
- Never expose stack traces or DB errors to the browser

---

## Checklist Before Each PR

- [ ] `npm run typecheck` passes with zero errors
- [ ] `npm run lint` passes
- [ ] `npm run build` succeeds locally
- [ ] New DB columns have a migration generated and committed
- [ ] All Server Actions have auth check at the top
- [ ] All Server Actions validate inputs with Zod
- [ ] No `process.env` accessed directly (use `src/lib/env.ts`)
- [ ] No `console.log` left in committed code
