# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project guide for Claude Code. Every rule has a reason.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components reduce client JS; App Router is the stable path forward |
| Runtime | Node.js | 20 LTS | Required for `better-sqlite3` native bindings |
| Language | TypeScript | 5.4+ | `satisfies` operator, `const` type parameters |
| Database | better-sqlite3 | 11.x | Synchronous API eliminates async complexity for local SQLite; 10x faster than `sqlite3` npm |
| Auth | Better Auth | latest | Self-hosted, SQLite-native, no external services |
| ORM | Drizzle ORM | 0.35+ | Type-safe SQL without the abstraction overhead; generates migrations from schema |
| Styling | Tailwind CSS | 4.x | Utility-first; co-located with markup; no naming debates |
| UI Components | shadcn/ui | latest | Copy-pasted, not imported — you own the code |
| Validation | Zod | 3.x | Runtime + compile-time validation from one schema |
| Testing | Vitest | 2.x | Fast, native ESM, Jest-compatible API |

---

## Project Structure

```
app/
  (marketing)/          # Public pages (no auth required)
    page.tsx            # Landing page
    pricing/page.tsx
  (auth)/               # Auth pages
    login/page.tsx
    signup/page.tsx
  (dashboard)/          # Protected pages (auth required)
    layout.tsx          # Checks session, redirects if missing
    page.tsx            # Dashboard home
    settings/page.tsx
  api/
    [...]/route.ts      # API routes grouped by resource
  layout.tsx            # Root layout — fonts, providers, metadata
  globals.css

lib/
  db/
    schema.ts           # Drizzle schema (single source of truth)
    migrate.ts          # Migration runner (called at startup)
    index.ts            # Exports `db` singleton
  auth.ts               # Better Auth instance
  errors.ts             # Typed error classes (AppError, NotFoundError, etc.)
  utils.ts              # Pure utility functions (no side effects)

components/
  ui/                   # shadcn/ui components (untouched copies)
  forms/                # Form components with Zod validation
  layout/               # Header, Sidebar, Footer
  [feature]/            # Feature-specific components

server/
  actions/              # "use server" functions — one per file
  queries/              # Read-only DB queries (called from RSC and actions)

emails/                 # React Email templates
public/                 # Static assets
tests/
  unit/                 # Vitest unit tests
  e2e/                  # Playwright e2e tests
```

### Why this structure

- **Route groups `(marketing)`, `(auth)`, `(dashboard)`** — share layouts without affecting URLs
- **`server/` separates data access from UI** — prevents accidental client-side DB imports
- **`lib/db/` is a single module** — avoids multiple SQLite connections (SQLite is single-writer)
- **No `src/` directory** — adds nesting for no benefit in a full-stack app

---

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files (components) | kebab-case | `user-avatar.tsx` |
| Files (routes) | `page.tsx` / `layout.tsx` / `route.ts` | Next.js convention |
| Components | PascalCase | `UserAvatar` |
| Database tables | snake_case, plural | `user_accounts`, `subscription_items` |
| DB columns | snake_case | `created_at`, `stripe_customer_id` |
| TypeScript types | PascalCase | `UserAccount`, `CreateInvoiceInput` |
| Zod schemas | camelCase + `Schema` suffix | `createInvoiceSchema` |
| Server actions | camelCase + verb prefix | `createInvoice()`, `updateUser()` |
| Environment vars | SCREAMING_SNAKE_CASE | `DATABASE_URL`, `STRIPE_SECRET_KEY` |

---

## Database Rules (SQLite + Drizzle)

### Schema is the source of truth

All tables are defined in `lib/db/schema.ts`. Never create tables via raw SQL migrations without updating the schema file first.

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),           // nanoid, not auto-increment
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
});
```

### ID strategy: nanoid, not auto-increment

- Use `nanoid()` for all primary keys — it's URL-safe, no coordination needed, works across SQLite files
- Never use `INTEGER PRIMARY KEY AUTOINCREMENT` — it leaks row count, doesn't work with distributed data

### Migration workflow

```bash
# 1. Edit lib/db/schema.ts
# 2. Generate migration
npx drizzle-kit generate
# 3. Review the SQL in drizzle/ folder
# 4. Apply
npx drizzle-kit migrate
# 5. Commit BOTH schema.ts AND the migration file
```

- **Never** run `db.run("ALTER TABLE ...")` manually in code
- **Always** commit generated migration files — they are the audit trail
- Migrations are **forward-only** — no `down()` functions. If you need to reverse, write a new forward migration

### SQLite-specific rules

- **WAL mode is mandatory** — add `PRAGMA journal_mode=WAL;` in `lib/db/index.ts`
- **Foreign keys are OFF by default in SQLite** — enable with `PRAGMA foreign_keys=ON;` on every connection
- **No concurrent writers** — SQLite allows one writer at a time. In Next.js, use a single `better-sqlite3` instance (singleton in `lib/db/index.ts`)
- Use `INTEGER` for booleans (0/1), `INTEGER` for timestamps (Unix epoch seconds)
- Use `TEXT` for JSON blobs with a Zod schema to validate on read

---

## Authentication

We use **Better Auth** with SQLite. Configuration lives in `lib/auth.ts`.

```typescript
// lib/auth.ts
import { betterAuth } from "better-auth";

export const auth = betterAuth({
  database: { url: "file:./data/db.sqlite" },
  emailAndPassword: { enabled: true },
  session: { expiresIn: 60 * 60 * 24 * 30 }, // 30 days
});
```

### Auth rules

- **Every route in `(dashboard)/` must check the session** in its layout
- **Server actions must verify the session** — never trust the client
- Use `auth.api.getSession({ headers })` in server components
- Use `useSession()` hook only in Client Components

---

## Server Actions & Data Access

### Server actions live in `server/actions/`

One action per file. Every action:
1. Validates input with Zod
2. Verifies the session (if protected)
3. Performs the operation
4. Returns a typed result (never throws to the client)

```typescript
// server/actions/create-invoice.ts
"use server";

import { z } from "zod";
import { db } from "@/lib/db";
import { invoices } from "@/lib/db/schema";
import { auth } from "@/lib/auth";
import { headers } from "next/headers";

const inputSchema = z.object({
  amount: z.number().positive(),
  description: z.string().min(1).max(500),
});

export async function createInvoice(rawInput: unknown) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return { error: "Unauthorized" } as const;

  const input = inputSchema.parse(rawInput);

  const [invoice] = db.insert(invoices).values({
    id: nanoid(),
    userId: session.user.id,
    amount: input.amount,
    description: input.description,
    createdAt: new Date(),
  }).returning();

  return { data: invoice } as const;
}
```

### Queries live in `server/queries/`

Read-only, called from both RSC and actions. Never mutate here.

```typescript
// server/queries/get-invoices.ts
import { db } from "@/lib/db";
import { invoices } from "@/lib/db/schema";
import { eq, desc } from "drizzle-orm";

export function getInvoicesByUser(userId: string) {
  return db.select().from(invoices)
    .where(eq(invoices.userId, userId))
    .orderBy(desc(invoices.createdAt));
}
```

---

## Component Patterns

### Server Components are the default

- **Start every component as a Server Component** — only add `"use client"` when you need interactivity
- Never add `"use client"` to a layout or page just for data fetching
- Fetch data in Server Components, pass it down as props

### Client Components are for interactivity only

```typescript
// components/forms/invoice-form.tsx
"use client";

import { useTransition } from "react";
import { createInvoice } from "@/server/actions/create-invoice";

export function InvoiceForm() {
  const [isPending, startTransition] = useTransition();

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    startTransition(async () => {
      const result = await createInvoice(Object.fromEntries(formData));
      // handle result
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* inputs */}
      <button disabled={isPending}>{isPending ? "Saving..." : "Create"}</button>
    </form>
  );
}
```

### shadcn/ui components

- Install: `npx shadcn@latest add button card dialog`
- They are copied into `components/ui/` — you own and modify them
- Never import from `@shadcn/ui` directly

---

## Dev Commands

```bash
npm run dev          # Start dev server (turbopack)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
npm run test         # Vitest
npm run test:e2e     # Playwright
npm run db:generate  # Drizzle: generate migration
npm run db:migrate   # Drizzle: apply migrations
npm run db:studio    # Drizzle Studio (browse DB)
```

---

## Anti-Patterns (and why)

### ❌ Don't use `useEffect` for data fetching
**Why:** Server Components fetch data before render. `useEffect` fetches after mount, causing loading spinners and waterfalls.

### ❌ Don't use ORMs like Prisma with SQLite
**Why:** Prisma spawns a separate binary query engine. For SQLite, you want the driver in-process. Drizzle + better-sqlite3 is direct, fast, and debuggable.

### ❌ Don't use `Date.now()` for timestamps
**Why:** Inconsistent across serverless invocations. Always use `new Date()` and let Drizzle handle it. SQLite stores as integer.

### ❌ Don't create API routes for data mutations
**Why:** Server Actions replace API routes for mutations. They're type-safe, work with progressive enhancement, and don't need endpoint management. Use API routes only for webhooks and external integrations.

### ❌ Don't store sessions in the database
**Why:** Better Auth handles session storage. SQLite is fast enough for session lookups on every request. Don't add Redis for a SaaS under 10k users.

### ❌ Don't use `React.lazy` for code splitting in App Router
**Why:** Next.js already splits by route. `React.lazy` adds Suspense boundaries for no gain in a server-rendered app.

### ❌ Don't import from `@/lib/db` in Client Components
**Why:** Database drivers can't run in the browser. Data fetching belongs in Server Components or server actions.

### ❌ Don't use `any` — ever
**Why:** `unknown` forces you to validate. `any` disables the type system entirely.

---

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL=file:./data/db.sqlite
BETTER_AUTH_SECRET=    # generate with: openssl rand -base64 32
BETTER_AUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
```

- Access via `process.env.VARIABLE_NAME` — no validation library needed, just Zod-parse at startup
- **Never** use `NEXT_PUBLIC_` for secrets — it's bundled into client JS

---

## What We Don't Do (and Why)

| Decision | Reason |
|----------|--------|
| No monorepo / Turborepo | One app, one package.json. Monorepos add tooling overhead for zero benefit until you have 3+ packages |
| No Docker for dev | SQLite doesn't need a container. `npm run dev` is enough |
| No GraphQL | REST + Server Actions cover SaaS needs. GraphQL adds resolver boilerplate for no measurable benefit |
| No Redux / Zustand for global state | Server Components pass props. Use React Context sparingly for cross-cutting UI state (theme, sidebar) only |
| No Tailwind `@apply` abstractions | Use component composition instead. `@apply` hides the design system |
| No `middleware.ts` for auth | Check auth in layouts — middleware runs on every request including static assets and adds latency |
| No optimistic updates (initially) | Server Actions are fast enough. Add `useOptimistic` only when UX demands it |
| No multi-tenant architecture | Single-tenant SQLite file per deploy. Add multi-tenancy later with separate SQLite files per org |

---

## Git Conventions

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- **Branch naming**: `feat/thing`, `fix/thing`
- **PR title** matches commit format
- **Squash merge** to main — one commit per PR

---

## Adding a New Feature (Checklist)

1. Create migration: edit `lib/db/schema.ts` → `npx drizzle-kit generate`
2. Add queries in `server/queries/`
3. Add server action in `server/actions/`
4. Build UI in `components/` (Server Component by default)
5. Wire up in `app/(dashboard)/feature/page.tsx`
6. Add tests in `tests/unit/`
7. PR with conventional commit title
