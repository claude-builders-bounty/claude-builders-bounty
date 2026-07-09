# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

| Technology | Version | Why |
|---|---|---|
| **Next.js** | 15.x (App Router) | React Server Components by default, streaming, server actions |
| **React** | 19.x | Concurrent features, `use()` hook for async components |
| **TypeScript** | 5.x | Strict mode enabled in tsconfig — no `any` unless absolutely unavoidable |
| **Database** | SQLite via `better-sqlite3` | Zero ops, single-file, perfect for SaaS up to ~10M rows |
| **ORM** | Drizzle ORM | Type-safe, lightweight, SQL-like syntax, no magic |
| **Auth** | Lucia v3 | Framework-agnostic, session-based, no vendor lock-in |
| **UI** | shadcn/ui + Tailwind CSS 4 | Accessible, composable, tree-shakeable components |
| **Forms** | React Hook Form + Zod | Performant, type-safe validation, minimal re-renders |
| **Email** | Resend | Transactional emails via API, React Email templates |
| **Payments** | Stripe | Webhook-first, idempotent, test mode by default |
| **Runtime** | Node.js 22 LTS | Long-term support, native fetch, glob support |

> **Reason:** Every choice above is the _boring, proven, well-documented_ option for its category. Avoid bleeding-edge or unmaintained libraries.

---

## Project Structure

```
├── src/
│   ├── app/                    # Next.js App Router pages & API routes
│   │   ├── (auth)/             # Auth group — login, signup, password reset
│   │   ├── (dashboard)/        # Dashboard group — requires auth
│   │   ├── api/                # Route handlers (webhooks, internal APIs)
│   │   └── layout.tsx          # Root layout with providers
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives (Button, Input, etc.)
│   │   ├── forms/              # Form components (signup, settings, etc.)
│   │   └── layout/             # Navbar, Sidebar, Footer
│   ├── db/
│   │   ├── schema/             # Drizzle schema files (one per domain)
│   │   │   ├── users.ts
│   │   │   ├── organizations.ts
│   │   │   ├── subscriptions.ts
│   │   │   └── index.ts        # Re-exports all schemas
│   │   ├── migrations/         # Auto-generated SQL migrations (DO NOT EDIT)
│   │   ├── seed.ts             # Development seed data
│   │   └── index.ts            # DB client singleton
│   ├── lib/
│   │   ├── auth.ts             # Lucia auth helpers
│   │   ├── stripe.ts           # Stripe client + webhook handler
│   │   ├── email.ts            # Resend email client
│   │   ├── utils.ts            # Shared utilities (cn(), formatDate(), etc.)
│   │   └── rate-limit.ts       # In-memory rate limiter
│   ├── actions/                # Server Actions (one file per domain)
│   │   ├── auth.actions.ts
│   │   ├── billing.actions.ts
│   │   └── settings.actions.ts
│   └── styles/
│       └── globals.css         # Tailwind imports + CSS variables
├── drizzle.config.ts           # Drizzle Kit config
├── tailwind.config.ts
├── next.config.ts
└── tsconfig.json
```

> **Rule:** Keep files under 200 lines. If a file exceeds 200 lines, extract logic into a `lib/` or `actions/` module.

---

## SQL & Migration Conventions

### Schema Rules

1. **Every table must have:**
   ```ts
   id: text("id").primaryKey(),                    // CUID2 or nanoid
   createdAt: text("created_at").notNull().default(sql`(current_timestamp)`),
   updatedAt: text("updated_at").notNull().default(sql`(current_timestamp)`).$onUpdate(() => new Date().toISOString()),
   ```

2. **Use `text()` for all IDs and timestamps** — SQLite has no native UUID or datetime types. Store ISO 8601 strings.

3. **Use `integer()` for booleans** — SQLite has no native boolean type:
   ```ts
   isActive: integer("is_active", { mode: "boolean" }).notNull().default(true),
   ```

4. **Use `real()` for currency** — Store in cents as integer, but format as decimal in the app layer:
   ```ts
   priceCents: integer("price_cents").notNull(),  // Always store money in cents
   ```

5. **Foreign keys must be explicit:**
   ```ts
   organizationId: text("organization_id").notNull().references(() => organizations.id, { onDelete: "cascade" }),
   ```

### Migration Workflow

```bash
# 1. Edit schema files in src/db/schema/
# 2. Generate migration:
pnpm db:generate
# 3. Review the generated SQL in src/db/migrations/
# 4. Apply migration:
pnpm db:migrate
# 5. Push seed data (dev only):
pnpm db:seed
```

> **Anti-pattern:** Never edit migration files manually. Always use `drizzle-kit generate`.

### Query Patterns

```ts
// ✅ GOOD: Prepared statements (prevents SQL injection)
const users = db.select().from(schema.users).where(eq(schema.users.email, email));

// ✅ GOOD: Transactions for multi-step operations
await db.transaction(async (tx) => {
  const org = await tx.insert(schema.organizations).values({ name }).returning();
  await tx.insert(schema.members).values({ userId, organizationId: org[0].id });
});

// ❌ BAD: Raw SQL strings (unless absolutely necessary for complex queries)
// ❌ BAD: N+1 queries in loops — use `IN` clauses or JOINs
```

---

## Component Patterns

### Server Components (Default)

```tsx
// src/app/(dashboard)/page.tsx — Server Component (no "use client")
import { db } from "@/db";
import { organizations } from "@/db/schema";
import { eq } from "drizzle-orm";
import { requireAuth } from "@/lib/auth";
import { OrganizationList } from "./organization-list";

export default async function DashboardPage() {
  const { user } = await requireAuth();
  const orgs = await db.select().from(organizations).where(eq(organizations.ownerId, user.id));
  return <OrganizationList organizations={orgs} />;
}
```

### Client Components (When Needed)

```tsx
"use client";  // Only for interactivity: forms, toasts, modals, etc.

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function CreateOrgButton() {
  const [open, setOpen] = useState(false);
  return <Button onClick={() => setOpen(true)}>Create Organization</Button>;
}
```

> **Rule:** Default to Server Components. Only add `"use client"` when you absolutely need browser APIs, state, or event handlers.

### Data Fetching

```tsx
// ✅ GOOD: Fetch in Server Component, pass down as props
// ✅ GOOD: Use React.cache() for deduplication
// ❌ BAD: Fetching in Client Components (waterfall problem)
// ❌ BAD: Using useEffect for data fetching (use Server Actions or RSC instead)
```

---

## Naming Conventions

| Category | Convention | Example |
|---|---|---|
| **Files (components)** | kebab-case | `organization-list.tsx` |
| **Files (server actions)** | kebab-case with `.actions` | `auth.actions.ts` |
| **Functions** | camelCase | `createOrganization()` |
| **Types/Interfaces** | PascalCase | `CreateOrgInput` |
| **Database columns** | snake_case | `created_at` |
| **Database tables** | snake_case, plural | `organizations` |
| **Environment vars** | UPPER_SNAKE_CASE | `DATABASE_URL` |
| **CSS classes** | Tailwind utility classes only | No custom CSS classes |

---

## Environment Variables

```env
# Database
DATABASE_URL="file:./data/saas.db"

# Auth
SESSION_SECRET="generate-256-bit-random-key"

# Stripe
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_STRIPE_PRICE_ID="price_..."

# Email
RESEND_API_KEY="re_..."

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

---

## Development Commands

```bash
pnpm dev          # Start dev server (localhost:3000)
pnpm build        # Production build
pnpm lint         # ESLint + TypeScript check
pnpm test         # Vitest (unit tests)
pnpm test:e2e     # Playwright (E2E tests)
pnpm db:generate  # Generate Drizzle migrations
pnpm db:migrate   # Apply migrations
pnpm db:seed      # Seed development data
pnpm db:studio    # Open Drizzle Studio (GUI for DB)
pnpm type-check   # tsc --noEmit (strict type checking)
```

---

## What We Don't Do (And Why)

| ❌ Don't | Why |
|---|---|
| **Use Prisma** | Drizzle is lighter, faster, and has no binary dependencies — critical for serverless/edge |
| **Use Redux or Zustand** | Server Components + URL state covers 95% of use cases; React Context for the rest |
| **Write custom CSS** | Tailwind utility classes + shadcn/ui cover all design needs consistently |
| **Use getServerSideProps** | We're on App Router — use RSC or Server Actions instead |
| **Store files in SQLite** | Use S3/R2 for file storage; SQLite is for structured data only |
| **Use plain fetch() for API calls** | Use tRPC or Server Actions for type-safe client-server communication |
| **Add `"use client"` unnecessarily** | Every client component increases bundle size and disables RSC streaming |

---

## Security Must-Haves

1. **All forms must use Server Actions** — Never expose raw API endpoints for mutations
2. **Rate limit auth endpoints** — Use in-memory rate limiter for login/signup (5 attempts per 15 min)
3. **CSRF protection** — Built into Next.js Server Actions, but verify for any `<form>` without actions
4. **Input validation** — Every Server Action must validate inputs with Zod
5. **Session rotation** — Rotate session ID on privilege escalation (login, role change)
6. **SQL injection** — Prevented by Drizzle's parameterized queries; never use raw SQL with user input
7. **Stripe webhook idempotency** — Verify `stripe-signature` header and use idempotency keys

---

## Performance Rules

1. **Keep SQLite in WAL mode** — `PRAGMA journal_mode=WAL;` in your Drizzle setup
2. **Add indexes for frequent queries** — `CREATE INDEX idx_org_id ON users(organization_id);`
3. **Use React Suspense boundaries** — Wrap async components in `<Suspense>` with fallbacks
4. **Stream long-running pages** — Use `loading.tsx` and `streaming:` in your data fetching
5. **Optimize images** — Use `next/image` with proper width, height, and priority flags
6. **Avoid `useEffect` for data** — Prefer Server Components or Server Actions
