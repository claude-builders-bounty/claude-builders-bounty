# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | File-based routing, Server Components, Server Actions, route handlers |
| Runtime | Node.js >=20 | Required by Next.js 15; supports better-sqlite3 natively |
| Language | TypeScript 5 (strict) | Non-negotiable. Every file is `.ts` or `.tsx` |
| Database | SQLite via `better-sqlite3` | Zero infra, single file, fast sync API. For serverless → Turso (libSQL) |
| ORM | Drizzle ORM | Type-safe, SQL-like API, first-class SQLite support. Not Prisma (too heavy, slow migrations) |
| Validation | Zod | Schema validation at API boundaries and server action inputs |
| Auth | NextAuth.js / Auth.js v5 | Adaptable, supports credentials + OAuth, works with Drizzle adapter |
| Styling | Tailwind CSS v4 | Utility-first, no runtime, great with Server Components |
| Payments | Stripe | Subscription management, webhooks |
| Testing | Vitest (unit) + Playwright (e2e) | Fast, modern, no Jest migration baggage |

---

## Project Structure

```
├── src/
│   ├── app/                    # App Router — routing only. Thin files.
│   │   ├── (marketing)/        # Route group: public marketing pages
│   │   │   ├── page.tsx
│   │   │   └── layout.tsx
│   │   ├── (app)/              # Route group: authenticated app
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx      # Auth guard + sidebar layout
│   │   ├── (admin)/            # Route group: admin panel
│   │   │   └── layout.tsx      # Admin-specific layout
│   │   ├── api/                # Route handlers (REST endpoints)
│   │   │   ├── auth/
│   │   │   │   └── [...nextauth]/
│   │   │   │       └── route.ts
│   │   │   └── stripe/
│   │   │       └── webhook/
│   │   │           └── route.ts
│   │   ├── layout.tsx          # Root layout (<html>, <body>, providers)
│   │   ├── globals.css         # Tailwind base + global styles
│   │   └── favicon.ico
│   ├── features/               # Feature modules. Every folder is self-contained.
│   │   ├── billing/
│   │   │   ├── _components/    # Private folder — not routable
│   │   │   │   └── PlanCard.tsx
│   │   │   ├── _actions/       # Server Actions
│   │   │   │   └── create-checkout-session.ts
│   │   │   ├── _queries/       # DB queries (server-only)
│   │   │   │   └── get-subscription.ts
│   │   │   └── _schemas/       # Zod schemas
│   │   │       └── billing.ts
│   │   ├── auth/
│   │   ├── projects/
│   │   └── teams/
│   ├── components/             # Shared UI components (domain-agnostic)
│   │   ├── ui/                 # Primitive UI: Button, Input, Modal, etc.
│   │   └── layouts/            # AppShell, Sidebar, Navbar
│   ├── lib/                    # Shared utilities
│   │   ├── db/
│   │   │   ├── index.ts        # DB client singleton
│   │   │   ├── schema.ts       # Drizzle schema (all tables)
│   │   │   └── migrations/     # Generated migration files
│   │   ├── auth.ts             # Auth.js config
│   │   ├── stripe.ts           # Stripe client
│   │   ├── email.ts            # Email library
│   │   └── utils.ts            # Misc helpers
│   ├── hooks/                  # Shared React hooks
│   └── types/                  # Shared TypeScript types
├── public/                     # Static assets (images, fonts)
├── drizzle.config.ts           # Drizzle Kit config
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

**Key rules:**
- `src/app/` files are thin — under 30 lines. They compose features, nothing more.
- `src/features/` owns everything for a domain: schema, queries, actions, components, tests.
- `src/components/ui/` is for generic primitives (Button, Input, Modal). No business logic.
- `_` prefix inside features means "private to this folder" — not imported outside.
- Every feature folder has a `_queries/` and `_actions/` subfolder. No `page.tsx` imports DB directly.

---

## Naming Conventions

### Files
| Pattern | Example | Where |
|---------|---------|-------|
| `page.tsx` | `dashboard/page.tsx` | Route UI — must be default export, async Server Component |
| `layout.tsx` | `(app)/layout.tsx` | Shared layout — wraps children |
| `loading.tsx` | `dashboard/loading.tsx` | Suspense fallback for route segment |
| `error.tsx` | `dashboard/error.tsx` | Error boundary for route segment |
| `route.ts` | `api/stripe/webhook/route.ts` | API endpoint — named exports: `GET`, `POST`, etc. |
| `[param]/` | `projects/[id]/page.tsx` | Dynamic route segment |
| `_actions/` | `billing/_actions/` | Server Actions — one file per action or domain |
| `_queries/` | `billing/_queries/` | Database queries — pure data access functions |
| `_components/` | `billing/_components/` | Feature-specific components |
| `_schemas/` | `billing/_schemas/` | Zod schemas for validation |

### Functions & Variables
- **React components**: PascalCase (`PlanCard`, `SubscriptionStatus`)
- **Server Actions**: camelCase, verb-first (`createCheckoutSession`, `cancelSubscription`)
- **Database queries**: camelCase, noun-first (`getSubscription`, `listProjectsByTeam`)
- **Utilities**: camelCase (`formatCurrency`, `sendEmail`)
- **Types/Interfaces**: PascalCase, `Type` suffix for primitives, no `I` prefix (`UserType`, `SubscriptionStatus`)
- **Environment variables**: `SCREAMING_SNAKE_CASE`, prefixed `NEXT_PUBLIC_` only if client-visible

### Database
- **Tables**: snake_case, plural (`users`, `subscriptions`, `project_members`)
- **Columns**: snake_case (`created_at`, `stripe_customer_id`)
- **Primary keys**: `id` text/CUID (not auto-increment — CUIDs work in Postgres too if you migrate)
- **Timestamps**: `created_at`, `updated_at` (integer unix epoch for SQLite)
- **Foreign keys**: `{table}_id` pattern (`user_id`, `project_id`)

---

## Database Conventions

### Connection Singleton (mandatory)

```ts
// src/lib/db/index.ts
import { drizzle } from 'drizzle-orm/better-sqlite3';
import Database from 'better-sqlite3';
import * as schema from './schema';

declare global {
  var __db__: ReturnType<typeof createDrizzle> | undefined;
}

function createDrizzle() {
  const sqlite = new Database('data/app.db');
  sqlite.pragma('journal_mode = WAL');   // Allow concurrent reads during writes
  sqlite.pragma('busy_timeout = 5000');  // Wait 5s before throwing SQLITE_BUSY
  return drizzle(sqlite, { schema });
}

export const db = globalThis.__db__ ??= createDrizzle();
```

**Why**: In development, Next.js hot-reloads modules. Without `globalThis`, you'd create a new connection per reload → "database is locked." In production, the singleton is created once at startup.

**For serverless (Turso)**: Replace `better-sqlite3` with `@libsql/client`. The singleton pattern stays the same.

### Sync Queries & Prerendering

`better-sqlite3` is synchronous. Next.js 15 treats sync I/O as static during prerendering. **Always call `connection()` before sync DB queries in components:**

```ts
import { connection } from 'next/server';

export async function getCurrentUser() {
  await connection(); // Opts out of static prerendering
  return db.query.users.findFirst({ ... });
}
```

This rule applies to every page/data component that uses the DB — not to API routes (those are always dynamic).

### Migrations

Use Drizzle Kit with raw SQL generation:

```bash
# Generate migration after schema changes
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate

# Push schema directly (dev only)
npx drizzle-kit push
```

Migration files live in `src/lib/db/migrations/`. They are committed to git.

**Migration rules:**
- Never edit an already-applied migration. Create a new one.
- Every migration must be reversible (have a down.sql or be additive-only).
- Test migrations against a copy of production data before applying.

### Schema Design

```ts
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),                             // CUID — not auto-increment
  email: text('email').notNull().unique(),
  name: text('name'),
  hashedPassword: text('hashed_password'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});
```

**SQLite-specific:**
- Use `integer` for timestamps (unix epoch), not `text` or `real`.
- Use `text` for IDs (CUID/ULID), not `integer` auto-increment.
- No `enum` type — use `text` with a Zod union at the application layer.
- WAL mode enables concurrent reads; single-writer remains (fine for <50k users).

---

## Component Patterns

### Server Components First

Every component is a Server Component by default. Add `"use client"` only when you need:
- `useState`, `useEffect`, `useContext`
- Browser-only APIs (`localStorage`, `navigator`)
- Event handlers (`onClick`, `onSubmit`)
- Custom hooks that use any of the above

**Keep client components as leaves** — small, near the bottom of the tree. Push data fetching up to Server Components.

### Server Actions for Mutations

```ts
// src/features/billing/_actions/create-checkout-session.ts
'use server';

import { auth } from '@/lib/auth';
import { stripe } from '@/lib/stripe';
import { z } from 'zod';

const schema = z.object({
  priceId: z.string(),
  successUrl: z.string().url(),
});

export async function createCheckoutSession(formData: FormData) {
  const session = await auth();
  if (!session?.user?.id) throw new Error('Unauthorized');

  const { priceId, successUrl } = schema.parse({
    priceId: formData.get('priceId'),
    successUrl: formData.get('successUrl'),
  });

  const checkout = await stripe.checkout.sessions.create({
    customer_email: session.user.email!,
    line_items: [{ price: priceId, quantity: 1 }],
    mode: 'subscription',
    success_url: successUrl,
    cancel_url: `${successUrl}?canceled=true`,
  });

  return { url: checkout.url };
}
```

**Rules for Server Actions:**
- One file per action or related action group
- Validate inputs with Zod on every action
- Return typed responses (not `Response` objects)
- Call `revalidatePath()` or `revalidateTag()` after mutations
- Never trust `formData` — always validate

### Data Flow

```
Page (Server Component)
  → Feature page component (Server Component, calls queries)
    → Shared UI components (Button, Card — client if interactive)
    → Feature components (may be client for interactivity)
      → Server Action (on form submit)
        → Validate (Zod) → Mutate DB → Revalidate → Redirect
```

**Never:**
- ❌ Call `db.query()` in a Client Component
- ❌ Fetch data in `useEffect` when a Server Component can do it
- ❌ Pass entire DB rows to client components — select only needed fields
- ❌ Use `getServerSession` in Client Components

---

## What We Don't Do (And Why)

| Anti-pattern | Why We Don't Do It |
|--------------|-------------------|
| **Prisma ORM** | Heavy binary downloads, slow `prisma generate`, opaque query layer. Drizzle is SQL-like, faster, and has native SQLite support. |
| **Pages Router** | Legacy. App Router has been stable since Next.js 14. No new features for Pages Router. |
| **Redux / Zustand for server state** | Server Components + Server Actions replace most global state. Use `React Query` only if you have heavy client-side data requirements. |
| **`getServerSideProps` / `getStaticProps`** | App Router pattern: `async` Server Component fetches data directly. No `getServerSideProps` equivalent needed. |
| **Auto-increment IDs** | Breaks on migration to Postgres. CUID/ULID works everywhere. |
| **Database queries in Client Components** | Obvious security risk + defeats SSR benefits. Queries stay in Server Components or Server Actions. |
| **Re-creating DB connection per request** | `SQLITE_BUSY` errors every time. Always use the `globalThis` singleton. |
| **Using `next.config.js` (CommonJS)** | Next.js 15 supports ESM. Use `next.config.ts` (TypeScript). |
| **Custom Express server** | Next.js replaces your app server. Custom servers lose many optimizations. |
| **`redux-toolkit` / `redux-saga`** | Server Components + URL search params + React context handle 95% of what redux was used for. |

---

## Dev Commands

```bash
# Development
pnpm dev                  # Start dev server (localhost:3000)

# Database
pnpm db:generate          # Generate Drizzle migration from schema changes
pnpm db:migrate           # Apply pending migrations
pnpm db:push              # Push schema directly (dev only, no migration file)
pnpm db:studio            # Open Drizzle Studio GUI

# Code quality
pnpm typecheck            # tsc --noEmit
pnpm lint                 # next lint + ESLint
pnpm format               # Prettier
pnpm test                 # Vitest (unit)
pnpm test:e2e             # Playwright (e2e)

# Build & deploy
pnpm build                # Production build
pnpm start                # Start production server
```

---

## Environment Variables

```env
# Database
DATABASE_URL="file:./data/app.db"        # Local SQLite
# TURSO_DATABASE_URL="libsql://..."      # Production (Turso)
# TURSO_AUTH_TOKEN="..."

# Auth
AUTH_SECRET="..."
AUTH_GITHUB_ID="..."
AUTH_GITHUB_SECRET="..."

# Stripe
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_..."

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

Use `@t3-oss/env-nextjs` with Zod for validated env vars at build time:

```ts
// src/lib/env.ts
import { createEnv } from '@t3-oss/env-nextjs';
import { z } from 'zod';

export const env = createEnv({
  server: {
    DATABASE_URL: z.string().url(),
    AUTH_SECRET: z.string().min(1),
    STRIPE_SECRET_KEY: z.string().min(1),
  },
  client: {
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string().min(1),
    NEXT_PUBLIC_APP_URL: z.string().url(),
  },
  runtimeEnv: {
    DATABASE_URL: process.env.DATABASE_URL,
    AUTH_SECRET: process.env.AUTH_SECRET,
    STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
});
```

---

## Git Workflow

- `main` — production. Protected. No direct pushes.
- `feat/*` — feature branches from main.
- `fix/*` — bugfix branches.
- Commit messages: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`).
- Squash merge to main. Linear history.

---

## Learnings & Context (for Claude Code)

When generating code in this project:

1. **Server-first**: Default to Server Components. Only add `"use client"` when necessary.
2. **Singleton DB**: Always use the `db` from `src/lib/db/index.ts`. Never `new Database()` inline.
3. **`connection()`**: Call `await connection()` before sync DB queries in components (not in API routes).
4. **Thin routes**: Route files compose features. Business logic lives in `src/features/`.
5. **Zod at every boundary**: Server Actions, API routes, webhook handlers — validate inputs.
6. **CUIDs for IDs**: Not auto-increment. Not UUID (too long). CUID2 is the sweet spot.
7. **revalidate after mutations**: Every Server Action that writes must call `revalidatePath()` or `revalidateTag()`.
8. **No direct DB imports from `app/`**: Routes import from features. Features import from `src/lib/db/`.

Ask if any of these conventions need clarification before generating code.
