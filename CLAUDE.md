# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Next.js 15** (App Router, Server Components by default)
- **better-sqlite3** — synchronous, high-performance SQLite driver for Node.js
- **Drizzle ORM** — type-safe query builder with zero runtime overhead
- **TypeScript 5.4+** — strict mode enabled
- **Turbopack** — enabled via `next dev --turbo`
- **Zod** — runtime validation for all API inputs/outputs
- **React 19** — concurrent features, `use()` hook

**Why:** better-sqlite3 is preferred over Turso for SaaS because it's synchronous, far faster on read-heavy workloads, and has zero connection pooling overhead. Drizzle provides compile-time SQL safety and migrates cleanly from SQLite to Postgres if needed.

---

## Folder Structure

```
src/
  app/                    # Next.js App Router pages
    (auth)/               # Auth route group
      login/
      register/
    (app)/                # Protected route group
      dashboard/
      settings/
    api/                  # Route handlers
      [...path]/route.ts
  lib/
    db/
      schema.ts           # Drizzle schema definitions
      migrations/         # SQL migration files (named: NNN_description.sql)
      index.ts            # DB singleton + drizzle client
      seed.ts             # Development seed data
    auth/
      index.ts            # Auth config (better-auth or similar)
      middleware.ts       # Auth middleware helpers
    validations/
      index.ts            # Zod schemas
  components/
    ui/                   # Primitive UI components (shadcn/ui)
    features/             # Feature-specific components
  hooks/
    use-auth.ts
    use-debounce.ts
  services/
    billing.ts            # Business logic (Stripe, credits, etc.)
    emails.ts             # Email sending
  middleware.ts           # Next.js auth/tenant middleware
  types/
    index.ts              # Global TypeScript types
  utils/
    index.ts              # Shared utilities
drizzle.config.ts         # Drizzle migration config
next.config.ts
package.json
```

**Why:** `(auth)` and `(app)` route groups enforce security boundaries at the router level. Features live in `components/features/` to keep UI logic co-located with business logic. `services/` is the single source of truth for non-trivial operations — never put business logic inside route handlers.

---

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| File names | kebab-case | `user-profile.tsx` |
| Component names | PascalCase | `<UserProfile />` |
| Database tables | snake_case plural | `users`, `subscriptions` |
| Drizzle columns | camelCase in TS, snake_case in SQL | `userId` / `user_id` |
| Migration files | `NNNN_title.sql` (zero-padded) | `0001_create_users.sql` |
| API routes | match entity name | `GET /api/users/[id]` |
| Environment variables | `NEXT_PUBLIC_` prefix for client-exposed | `NEXT_PUBLIC_APP_URL` |
| Service functions | verb-first, descriptive | `createSubscription()`, `cancelInvoice()` |

**Why:** Drizzle's `pgLite`-style mapping requires explicit column aliasing; keeping TS camelCase vs SQL snake_case distinct avoids silent data corruption. Migration numbering enforces ordering guarantees across environments.

---

## Database & Migration Rules

### Schema Definition
- All schema lives in `src/lib/db/schema.ts`
- Every table must have: `id` (text/uuid), `createdAt`, `updatedAt`
- Use `timestamps()` helper from Drizzle for consistency

```ts
import { pgTable, text, timestamp, boolean } from "drizzle-orm/pg-core";
import { sql } from "drizzle-orm";

export const users = pgTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").unique().notNull(),
  name: text("name"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at")
    .defaultNow()
    .$onUpdateFn(() => new Date()),
});
```

### Migration Workflow
1. **Always** edit `schema.ts` first — never write raw SQL directly
2. Run `pnpm db:generate` to create the migration file
3. Review the generated SQL before applying
4. Apply with `pnpm db:migrate` in dev; CI applies in staging/prod
5. Never edit an applied migration — create a new one instead

```bash
pnpm db:generate   # creates NNNN_migration_name.sql in src/lib/db/migrations/
pnpm db:migrate    # applies pending migrations
pnpm db:studio     # launches Drizzle Studio for browsing
```

### Connection Pattern
- Singleton DB instance in `src/lib/db/index.ts` — require only once
- No per-request connections; better-sqlite3 handles this natively
- Wrap transactions with `db.transaction(fn)`

```ts
// src/lib/db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database("sqlite.db");
export const db = drizzle(sqlite, { schema });
```

**Why:** A singleton prevents file-lock contention that crashes better-sqlite3 under concurrent requests. Per-request connections are an anti-pattern here — they multiply file handles and cause `Database is locked` errors.

---

## Component Patterns

### Server Components First
- All components are **Server Components by default**
- Add `"use client"` only when `useState`, `useEffect`, or event handlers are needed
- Pass data via props, never via context providers unless crossing many layers

### Route Handler Pattern
```ts
// src/app/api/users/route.ts
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { z } from "zod";

const createSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

export async function POST(req: Request) {
  const body = createSchema.parse(await req.json());
  const [user] = await db.insert(users).values(body).returning();
  return NextResponse.json(user, { status: 201 });
}
```

### Data Fetching
- Use `async` route handlers — no `useSWR` or `useQuery` in the app layer
- For client-side mutations, use `action` patterns on forms with `useFormStatus`
- Cache strategy: `fetch` with `revalidateTag` for partial revalidation

### UI Library
- Use **shadcn/ui** for primitives — customize via `components.json`
- Do not add another component library (no MUI, no Chakra)
- Tailwind CSS v4 with `@theme` directive in `globals.css`

**Why:** Server Components + route handlers eliminate the need for data-fetching libraries. shadcn/ui avoids bundle bloat and gives full design control. One UI library prevents design inconsistency across the app.

---

## Dev Commands

```bash
pnpm dev          # Start dev server with Turbopack
pnpm build        # Production build
pnpm start        # Start production server
pnpm lint         # ESLint + Biome checks
pnpm test         # Vitest (unit + integration)
pnpm db:generate  # Generate Drizzle migration from schema
pnpm db:migrate   # Apply pending migrations
pnpm db:seed      # Run seed script
pnpm db:studio    # Open Drizzle Studio
```

---

## What We Don't Do (And Why)

| Anti-Pattern | Why |
|-------------|-----|
| Client-side data fetching with SWR/React Query | Next.js 15 App Router handles caching natively; adding a second cache layer causes stale data and double-fetching |
| `prisma` or `sequelize` | Heavier than Drizzle; Prisma's SQLite support is degraded compared to its Postgres story |
| Raw `fs.readFile` for DB queries | Obscures types, bypasses migration tracking, makes schema changes error-prone |
| Context for prop drilling > 2 levels | Signals a component architecture problem — flatten the tree or lift state to the parent |
| `any` in TypeScript | Catches real bugs at compile time; use `unknown` + Zod guards instead |
| Mutating `req.body` directly | Zod `.parse()` is the gatekeeper — every input must be validated before touching the DB |
| Storing session in cookies without signing | Use `better-auth` or `next-auth` with encrypted sessions; raw cookies are a security risk |
| Mixing SQL and ORM in the same query | Breaks type safety; use Drizzle for 99% of queries, raw SQL only for complex analytics |
| Deploying without `pnpm db:migrate` in CI | schema drift between environments is the #1 cause of production incidents |
| `console.log` in production route handlers | Use structured logging via `pino` or `console.log` only in dev; prod logs must be machine-parseable |

---

## Project Setup Checklist (New Developer)

1. `cp .env.example .env.local` — fill in secrets
2. `pnpm install`
3. `pnpm db:migrate` — apply initial schema
4. `pnpm db:seed` — populate dev data
5. `pnpm dev` — verify app boots clean
6. `pnpm test` — all tests green
7. Review `src/lib/db/schema.ts` to understand the data model
8. Read `src/middleware.ts` to understand auth flow
