# CLAUDE.md 鈥?Next.js 15 + SQLite SaaS Starter

> Drop this into any greenfield Next.js 15 + SQLite (better-sqlite3) project.
> Claude Code will understand the full context without asking clarifying questions.

---

## Stack & Versions

| Layer       | Technology               | Why                                        |
| ----------- | ------------------------ | ------------------------------------------ |
| Framework   | Next.js 15 (App Router)  | RSC-first, server components by default    |
| Language    | TypeScript (strict)      | Type safety across client + server         |
| Database    | better-sqlite3           | Zero-config, 10x faster than Turso for dev |
| ORM         | Drizzle ORM              | Lightweight, SQL-like DX, no Prisma bloat  |
| Auth        | Lucia Auth v3            | Session-based, multi-provider, no vendor lock-in |
| Styling     | Tailwind CSS v4          | Utility-first, tree-shakeable              |
| UI          | shadcn/ui                | Copy-paste components, full control        |
| Validation  | Zod                      | Shared schemas across client + server      |
| Payments    | Stripe                   | Best DX, webhooks, test mode               |
| Email       | Resend                   | React emails, 100 free/day                 |
| Hosting     | Vercel / Railway         | Edge + serverless or long-running          |

---

## Project Structure

```
src/
  app/                    # Next.js App Router pages
    (marketing)/          # Public pages (no auth required)
      page.tsx
      pricing/
      blog/
    (dashboard)/          # Authenticated pages (protected by middleware)
      layout.tsx
      page.tsx           # /dashboard
      settings/
    api/                  # Route handlers
      auth/
      stripe/
      webhooks/
  components/
    ui/                   # shadcn/ui primitives (don't edit these)
    shared/               # Reusable across features
    features/             # Domain-specific components
      billing/
      teams/
  lib/                    # Business logic, no JSX
    db/
      schema.ts           # Drizzle schema definitions
      index.ts            # DB client singleton
      migrate.ts          # Migration runner
    auth.ts               # Lucia config + helpers
    stripe.ts             # Stripe client
    email.ts              # Resend + templates
  server/                 # Server-only actions (use 'server only')
    actions/
      auth.ts             # login, logout, signup
      billing.ts          # createCheckoutSession, etc.
  types/                  # Shared TypeScript types
  config/                 # Environment-based config
```

### Rules
- **`app/` contains routes only** 鈥?no business logic beyond page-level data fetching
- **`lib/` has no JSX** 鈥?pure logic, can be tested independently
- **`server/actions/` has `"server only"` at the top of every file** 鈥?defends against accidental client import
- **Components in `features/` own their data fetching** 鈥?don't hoist everything to a page

---

## Database Conventions

### Migrations
```bash
# Generate: edit schema 鈫?run this
npx drizzle-kit generate

# Apply: applies generated SQL (NEVER write raw ALTER TABLE)
npx drizzle-kit push
```

### Schema Rules
- **No circular foreign keys** 鈥?leads to migration deadlocks
- **No `cascade: true` on deletes without `deleted_at` soft-delete first** 鈥?prefer soft-delete in SaaS
- **UUIDs for public IDs** (`cuid2`), auto-increment for internal PKs
- **Timestamp columns**: always `createdAt` + `updatedAt` on every table (use Drizzle helpers)
- **Stripe IDs stored as `text`, not integer**

### Example Schema
```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { createId } from "@paralleldrive/cuid2";

export const users = sqliteTable("users", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  publicId: text("public_id").$defaultFn(() => createId()).unique(),
  email: text("email").unique().notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).$onUpdateFn(() => new Date()),
});
```

---

## Naming Conventions

| Thing                  | Convention              | Example                    |
| ---------------------- | ----------------------- | -------------------------- |
| Files                  | kebab-case              | `user-settings.tsx`        |
| Components             | PascalCase              | `UserSettings`             |
| Server actions         | camelCase               | `createCheckoutSession`    |
| DB tables              | snake_case, plural      | `user_subscriptions`       |
| DB columns             | snake_case              | `created_at`               |
| Zod schemas            | `CamelCase + Schema`    | `UserSettingsSchema`       |
| Route groups           | `(groupName)`           | `(dashboard)`              |
| Private folders        | `_underscore`           | `_components/`             |

---

## Component Patterns

### Server Component (default)
```tsx
// src/app/(dashboard)/settings/page.tsx
import { getAuthenticatedUser } from "@/lib/auth";
import { SettingsForm } from "@/components/features/settings/settings-form";

export default async function SettingsPage() {
  const user = await getAuthenticatedUser(); // throws 鈫?middleware handles
  return <SettingsForm user={user} />;
}
```

### Client Component (explicit)
```tsx
// src/components/features/settings/settings-form.tsx
"use client";

import { useState } from "react";
import { updateSettings } from "@/server/actions/settings";
import type { User } from "@/lib/auth";

export function SettingsForm({ user }: { user: User }) {
  return (
    <form action={updateSettings}>
      {/* ... */}
    </form>
  );
}
```

### Server Actions
```typescript
// src/server/actions/settings.ts
"server only";

import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";

export async function updateSettings(formData: FormData) {
  const name = formData.get("name") as string;
  await db.update(users).set({ name }).where(eq(users.id, 1));
  revalidatePath("/settings");
}
```

---

## Auth Pattern

```typescript
// src/lib/auth.ts
import { Lucia } from "lucia";
import { DrizzleSQLiteAdapter } from "@lucia-auth/adapter-drizzle";
import { db } from "./db";
import { sessions, users } from "./db/schema";

const adapter = new DrizzleSQLiteAdapter(db, sessions, users);

export const lucia = new Lucia(adapter, {
  sessionCookie: { attributes: { secure: process.env.NODE_ENV === "production" } },
  getUserAttributes: (data) => ({ email: data.email }),
});
```

---

## Anti-Patterns We NEVER Do

- 鉂?**API routes for data mutations** 鈥?use Server Actions (zero serialization overhead)
- 鉂?**`any` type** 鈥?defeats TypeScript, always define a proper type or `unknown` + narrow
- 鉂?**`useEffect` for data fetching** 鈥?server components + Suspense is the React 19 way
- 鉂?**Environment variables in client components** 鈥?they leak. Prefix with `NEXT_PUBLIC_` or keep server-only
- 鉂?**Direct DB access from client components** 鈥?always go through Server Actions
- 鉂?**Console.log in production code** 鈥?use a logger utility
- 鉂?**Monolithic components over 200 lines** 鈥?extract smaller sub-components
- 鉂?**`ts-ignore` or `as any`** 鈥?fix the actual type error
- 鉂?**Mixed import sources** 鈥?don't import from both `next/navigation` and use both `useRouter` and `redirect`
- 鉂?**Raw SQL outside of $default migrations** 鈥?use Drizzle query builder

---

## Dev Commands

```bash
npm run dev           # Start dev server (Turbopack)
npm run build         # Production build
npm run start         # Production server
npm run lint          # ESLint + next lint
npm run typecheck     # tsc --noEmit
npm run db:generate   # Generate migration
npm run db:push       # Apply migration
npm run db:studio     # Open Drizzle Studio
npm run test          # vitest
npm run test:e2e      # Playwright
```

---

## Environment Variables

```bash
# .env.local (gitignored)
DATABASE_URL=sqlite.db          # SQLite file path
NEXTAUTH_SECRET=                # openssl rand -hex 32
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
RESEND_API_KEY=re_...
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## File Headers

Every new file gets one of these:

```typescript
// For server actions:
"server only";

// For client components:
"use client";
```

---

## When In Doubt

1. **Server component first** 鈥?only add `"use client"` when you need interactivity
2. **Server Action over API route** 鈥?less code, types flow automatically
3. **Zod validator before DB write** 鈥?validate at the boundary
4. **Soft delete over hard delete** 鈥?users make mistakes
5. **Commit + push before asking for help** 鈥?I can't see your uncommitted code
