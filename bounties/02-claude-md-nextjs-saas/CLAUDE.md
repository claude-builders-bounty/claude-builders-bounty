# CLAUDE.md — Next.js 15 SaaS + SQLite

> Drop this file at the root of a Next.js 15 (App Router) project with SQLite
> (better-sqlite3 or Turso). Claude Code will follow these conventions automatically.

---

## Stack & Versions (pinned)

| Tool | Version | Why this version |
|---|---|---|
| Next.js | `15.1.x` | App Router stable, Server Actions mature |
| React | `19.0.0` | Required for Next 15, `use()` hook |
| TypeScript | `5.7.x` | `satisfies` operator, const type params |
| Drizzle ORM | `0.36.x` | Type-safe SQL, edge-compatible |
| better-sqlite3 | `11.x` | Synchronous, fastest local SQLite |
| Tailwind CSS | `4.0.x` | CSS-first config, no `tailwind.config.js` needed |
| Zod | `3.23.x` | Runtime validation, matches Drizzle inferred types |
| Vitest | `2.x` | Native ESM, faster than Jest |
| Playwright | `1.49.x` | E2E + component testing |

**Runtime:** Node.js 20 LTS (Vercel default). **Package manager:** `pnpm` (not npm/yarn).

---

## Project Structure

```
/
├── app/                    # App Router routes
│   ├── (marketing)/        # Public pages (no auth)
│   ├── (app)/              # Authenticated routes
│   │   ├── dashboard/
│   │   ├── settings/
│   │   └── billing/
│   ├── api/                # Webhook endpoints ONLY (no CRUD)
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/                 # Generic primitives (Button, Card, Input)
│   └── [feature]/          # Feature-specific (e.g. billing/invoice-table.tsx)
├── lib/
│   ├── auth.ts             # Auth utilities (NextAuth config)
│   ├── env.ts              # Zod-validated env vars
│   └── utils.ts            # `cn()` helper, misc
├── db/
│   ├── schema.ts           # Drizzle schema (single file or split by domain)
│   ├── migrations/         # Generated SQL files — NEVER edit
│   ├── queries/            # All DB access goes through here
│   │   ├── users.ts
│   │   ├── billing.ts
│   │   └── _shared.ts
│   └── client.ts           # Drizzle client init
├── actions/                # Server Actions (mutations)
│   ├── users.ts
│   └── billing.ts
├── tests/
│   ├── unit/               # Vitest
│   └── e2e/                # Playwright
├── public/
├── drizzle.config.ts
├── next.config.ts
├── tsconfig.json
└── package.json
```

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Files (non-component) | `kebab-case.ts` | `auth-utils.ts`, `db-queries.ts` |
| React components | `PascalCase.tsx` | `InvoiceTable.tsx`, `UserAvatar.tsx` |
| Folders | `kebab-case/` | `user-profile/`, `billing-actions/` |
| Hooks | `use-kebab.ts` | `use-user.ts`, `use-invoice.ts` |
| Server Actions | `verbNoun.ts` | `createInvoice.ts`, `updateUser.ts` |
| DB columns | `snake_case` | `created_at`, `stripe_customer_id` |
| TS types/interfaces | `PascalCase` | `User`, `InvoiceStatus` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE`, `CACHE_TTL` |

**Why:** Matches Drizzle conventions + Vercel/Next.js style guide.

---

## Database Conventions

### Schema (Drizzle)

```typescript
// db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  stripeCustomerId: text("stripe_customer_id"),
});

export const invoices = sqliteTable("invoices", {
  id: text("id").primaryKey(),
  userId: text("user_id").notNull().references(() => users.id),
  amountCents: integer("amount_cents").notNull(),
  status: text("status", { enum: ["draft", "paid", "void"] }).notNull(),
});
```

**Rules:**
- ✅ IDs are `text` (use `cuid()` or `nanoid()`)
- ✅ Timestamps are `integer` with `mode: "timestamp"`
- ✅ Foreign keys use `.references()`
- ✅ Enums use `text(..., { enum: [...] })` for type safety
- ❌ **Never** use raw SQL in schema definitions
- ❌ **Never** edit files in `db/migrations/` after commit

### Migrations

```bash
# Generate a new migration from schema changes
pnpm db:generate

# Apply pending migrations to local DB
pnpm db:push

# Open Drizzle Studio (visual DB browser)
pnpm db:studio
```

**Workflow:**
1. Modify `db/schema.ts`
2. Run `pnpm db:generate` → creates new SQL file in `db/migrations/`
3. Commit the new file alongside the schema change
4. **Never** edit old migration files — they're immutable history

### Queries

All DB access goes through `db/queries/`:

```typescript
// db/queries/users.ts
import { db } from "@/db/client";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function getUserById(id: string) {
  return db.query.users.findFirst({ where: eq(users.id, id) });
}
```

**Rules:**
- ✅ One file per domain (`users.ts`, `billing.ts`)
- ✅ Each query is a named export
- ✅ Return type is inferred (no manual `Promise<User>` typing)
- ❌ **Never** import `db` outside of `db/queries/` and `db/client.ts`
- ❌ **Never** use `db.execute()` with raw SQL

---

## Component Patterns

### Server-first (default)

```typescript
// app/dashboard/page.tsx — Server Component (default)
import { getInvoices } from "@/db/queries/billing";

export default async function DashboardPage() {
  const invoices = await getInvoices(); // Direct DB access, no API route needed
  return <InvoiceTable data={invoices} />;
}
```

### Server Actions for mutations

```typescript
// actions/billing.ts
"use server";

import { revalidatePath } from "next/cache";
import { createInvoice } from "@/db/queries/billing";
import { z } from "zod";

const schema = z.object({
  amountCents: z.number().int().positive(),
  userId: z.string(),
});

export async function createInvoiceAction(input: z.infer<typeof schema>) {
  const data = schema.parse(input); // Validate FIRST
  await createInvoice(data);
  revalidatePath("/dashboard/billing");
}
```

### Client components (only at leaves)

```typescript
// components/billing/invoice-table.tsx
"use client"; // ONLY when you need interactivity (useState, onClick, etc.)

import { useState } from "react";
import { createInvoiceAction } from "@/actions/billing";
```

**Rules:**
- ✅ Server Components by default (no `"use client"`)
- ✅ `"use client"` only at the **leaf** that needs interactivity
- ✅ Mutations use Server Actions, not API routes
- ❌ **No** `useEffect` for data fetching — use Server Components
- ❌ **No** client-side state for server data — use `revalidatePath()`

---

## Dev Commands

```bash
pnpm dev              # Start dev server (Turbopack)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest watch mode
pnpm test:run         # Vitest single run (CI)
pnpm test:e2e         # Playwright
pnpm db:generate      # Generate migration from schema
pnpm db:push          # Apply migrations to local DB
pnpm db:studio        # Open Drizzle Studio
```

---

## Anti-Patterns (what we don't do, and why)

| Anti-pattern | Why we avoid it |
|---|---|
| **API routes for CRUD** | Server Actions are type-safe end-to-end; no manual fetch wrappers |
| **Raw SQL queries** | Drizzle types catch errors at compile-time; raw SQL bypasses the type system |
| **Editing committed migrations** | Migrations are immutable history; modifying breaks reproducibility |
| **Client-side data fetching with `useEffect`** | Server Components render with data already loaded; no loading spinners needed |
| **Inline `style={{}}` for non-dynamic CSS** | Tailwind is consistent + tree-shaken; inline styles bypass the design system |
| **`any` type** | Defeats TypeScript; use `unknown` + type guards or `z.infer<typeof schema>` |
| **Default exports everywhere** | Named exports are refactor-safe; default exports break IDE "go to definition" |
| **ORM calls in components** | Components shouldn't know about DB; queries go in `db/queries/` |
| **`process.env` directly** | Use `@/lib/env.ts` (Zod-validated) for type-safe + runtime-validated env vars |
| **Mutating props in child components** | Props are immutable; lift state up or use Server Actions |

---

## Testing Conventions

- **Unit tests (Vitest):** place in `tests/unit/` mirroring source structure
- **E2E tests (Playwright):** place in `tests/e2e/` with `*.spec.ts` suffix
- **Component tests:** use `@playwright/experimental-ct-react`
- **Mocking DB:** use `vitest-mock-extended` to mock Drizzle query builder

```typescript
// tests/unit/db/queries/billing.test.ts
import { describe, it, expect, vi } from "vitest";
import { getInvoiceById } from "@/db/queries/billing";

vi.mock("@/db/client", () => ({ db: mockDb }));
```

---

## Deployment

- **Hosting:** Vercel (Next.js native)
- **Database (production):** Turso (libSQL) — SQLite at the edge
- **Database (local dev):** better-sqlite3 file at `./local.db`
- **Env vars:** Vercel dashboard + Doppler for sync across environments
- **CI:** GitHub Actions runs `pnpm typecheck && pnpm lint && pnpm test:run && pnpm build`

---

## PR Review Checklist

Before submitting a PR, verify:

- [ ] All new code passes `pnpm typecheck` and `pnpm lint`
- [ ] All new queries have unit tests in `tests/unit/db/queries/`
- [ ] Server Actions use Zod schemas for input validation
- [ ] No `db.execute()` or raw SQL outside `db/queries/`
- [ ] No `process.env` — use `@/lib/env` instead
- [ ] Client components have `"use client"` at the **top of the file** (first line)
- [ ] No new `any` types — use `unknown` + type guards
- [ ] Database changes include a generated migration
- [ ] No edits to existing files in `db/migrations/`
- [ ] New env vars documented in `.env.example` and `@/lib/env.ts`

---

*Last updated: 2026-06-03 · Maintained by akuraposo*
