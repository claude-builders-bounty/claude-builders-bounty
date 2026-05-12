# Project: SaaS Platform

## Stack & Versions

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js App Router | 15.x |
| Language | TypeScript | 5.x (strict mode) |
| Database | SQLite via better-sqlite3 | 11.x |
| Migrations | Custom migration runner | — |
| Auth | next-auth (Auth.js) | 5.x (beta) |
| Styling | Tailwind CSS | 4.x |
| UI Components | shadcn/ui | latest |
| Forms | react-hook-form + zod | latest |
| Testing | vitest + @testing-library/react | latest |
| Linting | ESLint (flat config) + Prettier | latest |
| Package Manager | pnpm | 9.x |

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth routes (login, register, verify)
│   ├── (dashboard)/       # Authenticated dashboard routes
│   │   ├── _components/   # Dashboard-specific components (NOT a route)
│   │   └── settings/      # /dashboard/settings
│   ├── api/               # API routes
│   └── layout.tsx         # Root layout
├── components/            # Shared UI components
│   ├── ui/               # shadcn/ui primitives (Button, Input, etc.)
│   └── [feature]/        # Feature-specific shared components
├── db/
│   ├── schema.ts         # Drizzle ORM schema definitions
│   ├── migrations/       # SQL migration files (0001_xxx.sql)
│   ├── migrate.ts        # Migration runner
│   └── index.ts          # Database connection + client export
├── lib/                   # Business logic, utilities, config
│   ├── auth.ts           # Auth configuration
│   ├── email.ts          # Email sending (Resend/SES)
│   └── billing.ts        # Payment processing (Stripe/LemonSqueezy)
├── hooks/                 # Shared React hooks
├── emails/                # react-email templates
└── types/                 # Shared TypeScript types
```

**Routes as folders, components prefixed with `_` are private.** The `_components` convention prevents Next.js from treating them as routes.

## Naming Conventions

### Files
- **Components:** PascalCase: `UserProfile.tsx`, `SignUpForm.tsx`
- **Utilities:** camelCase: `formatDate.ts`, `validateEmail.ts`
- **Types:** PascalCase: `User.ts`, `BillingPlan.ts`
- **Database:** snake_case for columns, plural table names: `users`, `user_id`
- **Migrations:** `NNNN_description.sql` — zero-padded sequential: `0001_create_users.sql`

### Components
- **Server Components by default.** Only add `'use client'` when you need interactivity, browser APIs, or hooks.
- **One component per file.** Exceptions: small private sub-components (<20 lines) can live in the same file.
- **Props interface exported:** `export interface UserProfileProps { ... }`
- **Use function declarations** for components: `export function UserProfile({ userId }: UserProfileProps)`
- **No default exports for components.** Named exports only — it forces consistent naming and improves IDE autocompletion.

### Variables & Functions
- **Descriptive names over short ones.** `getUserByEmail` not `getUser`. `isSubscriptionActive` not `isActive`.
- **Boolean variables prefixed:** `is`, `has`, `should`, `can` — `isLoading`, `hasPermission`, `canDelete`
- **Event handlers:** `handle` prefix — `handleSubmit`, `handleDelete`, `handleToggle`
- **Async functions:** Always return `Promise<T>`, never `void`

## Database & Migrations

### Schema
- **Every table has:** `id` (INTEGER PRIMARY KEY), `created_at` (TEXT DEFAULT current_timestamp), `updated_at` (TEXT DEFAULT current_timestamp)
- **Foreign keys:** `ON DELETE` must be explicit — RESTRICT by default. Never silently CASCADE unless there's a documented reason.
- **Enums in code, strings in DB.** SQLite doesn't have native enums. Store as TEXT, validate with zod.
- **JSON columns are last resort.** SQLite JSON functions work but break type safety. Use a separate table instead if you need to query into the JSON.

### Migrations
- **One migration per logical change.** Don't combine schema changes and seed data in the same file.
- **Migrations are append-only.** Never edit a migration that's been applied. Create a new one.
- **Always write a down migration comment** at the bottom of each file:
  ```sql
  -- Down: ALTER TABLE users DROP COLUMN avatar_url;
  ```
- **Test migrations against a copy of production** before merging.
- **Migration files are plain SQL.** No ORM migration DSL — plain SQL is portable and reviewable.

### Queries
- **Use parameterized queries always.** Never string interpolation: `db.prepare('SELECT * FROM users WHERE id = ?').get(userId)`
- **No ORM abstraction over SQLite.** better-sqlite3's synchronous API is the abstraction. Use `db.prepare().all()` / `.get()` / `.run()` directly.
- **Transactions are explicit:**
  ```typescript
  const result = db.transaction(() => {
    const user = db.prepare('INSERT INTO users ...').run(...)
    db.prepare('INSERT INTO accounts ...').run(user.lastInsertRowid, ...)
    return user
  })()
  ```

## Component Patterns

### Server Components (Default)
```typescript
// src/app/(dashboard)/page.tsx
import { getUser } from '@/lib/auth'
import { db } from '@/db'

export async function DashboardPage() {
  const user = await getUser()
  const stats = db.prepare('SELECT ...').all()

  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <StatsGrid data={stats} />
    </div>
  )
}
```

### Client Components (Only When Needed)
```typescript
'use client'

import { useState } from 'react'

export interface CopyButtonProps {
  text: string
}

export function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  return (
    <button onClick={() => { navigator.clipboard.writeText(text); setCopied(true) }}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}
```

### Data Fetching
- **Server Components fetch data directly.** No `useEffect` for initial data loads — that's a client-side anti-pattern in App Router.
- **`fetch` calls are cached by default.** Use `cache: 'no-store'` for dynamic data.
- **React's `cache()` for deduplication:**
  ```typescript
  import { cache } from 'react'
  export const getUser = cache(async () => { ... })
  ```
- **No client-side data fetching libraries** (TanStack Query, SWR) unless you have real-time requirements. Server Components handle 90% of cases.

### Error & Loading States
- **Every route segment gets `loading.tsx` and `error.tsx`.**
- **`error.tsx` must be a Client Component** (`'use client'`). Log errors server-side, show user-friendly message client-side.
- **Use React Suspense for async components**, not manual loading flags.

## Forms

- **react-hook-form + zod for all forms.**
- Schema defined in same file as the form component:
  ```typescript
  const signUpSchema = z.object({
    email: z.string().email(),
    password: z.string().min(8),
  })
  type SignUpInput = z.infer<typeof signUpSchema>
  ```
- **Server Actions for form submission.** No API routes for form POST.
- **useActionState for pending state and errors** in Next.js 15.

## Auth

- **next-auth v5 with a credential provider backed by our SQLite password hashes.**
- **Middleware protects routes, not components.** Route groups `(auth)` and `(dashboard)` are the auth boundary.
- **Session is accessed via `auth()` on the server, `useSession()` on the client.**
- **No client-side auth checks for sensitive operations.** Always re-verify on the server.

## Billing

- **Stripe Checkout for subscription management.** Webhook handles fulfillment.
- **Billing state lives in Stripe, mirrored to our `subscriptions` table.**
- **Feature gating checks the DB, not Stripe API** (latency + rate limits).
- **Pricing page is a static route.** Dynamic pricing from config, not an API call.

## What We Don't Do (And Why)

- **No ORMs (Prisma, Drizzle ORM for SQLite).** They add a layer between you and SQL that hides performance characteristics. better-sqlite3's synchronous API is clean enough. Plain SQL with parameterized queries is safer and more reviewable.
- **No CSS-in-JS.** Tailwind is the single styling system. Mixing systems creates specificity wars and bloated bundles. If you need a complex animation, use Framer Motion on a single element.
- **No barrel exports (`index.ts` re-exporting everything).** They break tree-shaking, slow down compilation, and create circular dependency traps. Import from the file directly.
- **No `any` types.** Ever. If you're fighting the type system, the architecture is wrong — not the types. Use `unknown` and narrow it.
- **No API routes for CRUD.** Server Actions replace them. The only API routes are webhooks (Stripe, Resend) and external-facing endpoints.
- **No client-side database queries.** All DB access happens in Server Components or Server Actions. The client never touches the database.
- **No `useEffect` for data fetching.** App Router Server Components fetch data at render time. `useEffect` fetching is a Pages Router pattern that causes waterfalls and flicker.
- **No `.env` files committed.** `.env.example` documents required variables with dummy values.

## Dev Commands

```bash
pnpm dev            # Start dev server (localhost:3000)
pnpm build          # Production build
pnpm start          # Start production server
pnpm lint           # ESLint + Prettier check
pnpm lint:fix       # Auto-fix lint issues
pnpm test           # Run vitest suite
pnpm test:watch     # Watch mode
pnpm db:migrate     # Apply pending migrations
pnpm db:seed        # Seed development data
pnpm db:studio      # Open Drizzle Studio (if installed)
pnpm typecheck      # tsc --noEmit
```

## Key Libraries

```bash
pnpm add better-sqlite3 @types/better-sqlite3
pnpm add next-auth@beta @auth/core
pnpm add @radix-ui/react-*  # (via shadcn/ui)
pnpm add tailwindcss @tailwindcss/typography @tailwindcss/forms
pnpm add react-hook-form @hookform/resolvers zod
pnpm add stripe @stripe/stripe-js
pnpm add resend react-email
pnpm add date-fns  # Not moment/dayjs — tree-shakeable
```

## Code Standards

- **TypeScript strict mode is ON.** `strict: true` in tsconfig. No exceptions.
- **No `// @ts-ignore` or `// @ts-expect-error`** without a comment explaining WHY the type is wrong.
- **Prefer `const` over `let`, never `var`.**
- **Async/await over raw promises.** `async function` is clearer than `.then()` chains.
- **Early returns over nested if-else.** Guard clauses at the top, main logic below.
- **Functions under 50 lines.** If longer, extract a helper with a clear name.
- **Error messages are user-facing, not developer-facing.** "We couldn't process your payment" not "StripeError: card_declined".
- **Logs use structured format:** `console.log({ event: 'user.created', userId })` not `console.log('User created: ' + userId)`
