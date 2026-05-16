# CLAUDE.md — Next.js 15 + SQLite SaaS

An opinionated, production-ready context document for greenfield SaaS projects built with **Next.js 15 App Router** and **SQLite** (better-sqlite3 or Turso).

---

## Stack & Versions

| Layer | Choice | Version | Reason |
|-------|--------|---------|--------|
| Framework | Next.js | 15.x | App Router, Server Components, streaming |
| Runtime | Node.js | >= 20 | Native SQLite, fetch API, fetch caching |
| Language | TypeScript | >= 5.5 | Strict mode, no `any` without comment |
| Database | SQLite | — | Zero-config, single-file, perfect for SaaS |
| SQLite Driver | better-sqlite3 | >= 9.4 | Synchronous API (faster for queries), prepared statements |
| ORM/Query Builder | drizzle-orm | >= 0.30 | Type-safe, lightweight, no codegen step |
| Styling | Tailwind CSS | >= 3.4 | Utility-first, no CSS-in-JS runtime cost |
| Auth | NextAuth.js v5 | >= 5 beta | App Router native, Edge Compatible |
| Validation | zod | >= 3.23 | Schema-first, composes with TypeScript |
| Environment | dotenv | — | Never ship `.env` files. Use `env.ts` pattern |

**Why not Prisma?** Prisma's query engine adds a Rust binary dependency. For SQLite SaaS, drizzle-orm is 8x smaller and runs in the same process.

---

## Folder Structure

```
my-app/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Route group — login/register pages
│   │   ├── (dashboard)/        # Route group — authenticated pages
│   │   ├── api/                # API routes (REST, webhooks)
│   │   ├── layout.tsx          # Root layout (providers, fonts)
│   │   └── page.tsx            # Marketing landing page
│   ├── components/
│   │   ├── ui/                 # Reusable atoms (Button, Input, Card)
│   │   ├── forms/              # Form components (always with validation)
│   │   └── layout/             # Shell components (Navbar, Sidebar)
│   ├── lib/
│   │   ├── db/                 # Database layer (schema, client, migrations)
│   │   ├── auth/               # Auth utils, session management
│   │   ├── env.ts              # Runtime environment validation
│   │   └── utils.ts            # Shared utilities (cn helper, date formatters)
│   ├── hooks/                  # React hooks (only if logic is complex)
│   └── types/                  # Shared TS types (prefer schemas over types)
├── drizzle/                    # Generated migrations
├── public/                     # Static assets
├── tests/                      # Playwright E2E, Jest unit tests
├── .env.local                  # Local secrets (gitignored)
├── .env.example                # Template for new devs
├── drizzle.config.ts           # Drizzle migration config
├── next.config.js              # Export: output = "standalone"
├── tailwind.config.ts
└── tsconfig.json               # Strict mode, no unchecked indexed access
```

**Rule:** Every file in `src/` must be under a directory. No flat files in `src/` root.

---

## SQL / Migration Conventions

### Schema First

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: integer("id", { mode: "number" }).primaryKey({ autoIncrement: true }),
  email: text("email").notNull().unique(),
  name: text("name"),
  role: text("role", { enum: ["user", "admin"] }).default("user").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
});
```

### Migration Rules

1. **Never edit a migration file after committing it.** Rollbacks are manual `DOWN` SQL.
2. **Migration names are `YYYY-MM-DD_HHMMSS_description.sql`** — no semantic versioning.
3. **Every migration must be reversible.** If your `UP` migration is `ALTER TABLE`, the `DOWN` must be `CREATE TABLE` + `INSERT INTO` + `DROP TABLE` (SQLite has limited ALTER).
4. **Run migrations on startup in `layout.tsx` or a `middleware.ts` check.** Not in a deploy script — SQLite is a file, migrations must happen before first query.
5. **Never use `DROP TABLE` in a migration unless the entire table is newly created in this migration.** Data loss migrations must be approved in PR.

### Query Patterns

```typescript
// ✅ DO: Prepared statement cache in module scope
const getUserByEmailStmt = db.select().from(users).where(eq(users.email, placeholder("email"))).prepare();

// ✅ DO: Use transactions for multi-step writes
await db.transaction(async (tx) => {
  const [user] = await tx.insert(users).values({ email: data.email }).returning();
  await tx.insert(profiles).values({ userId: user.id });
});

// ❌ DON'T: Inline queries in API routes (hard to test, no type reuse)
// ❌ DON'T: Use `db.run()` for SELECTS — use `db.select()` (type-safe, composable)
```

---

## Component Patterns

### Server Components (default)

```tsx
// ✅ DO: Fetch data in Server Components
// src/app/(dashboard)/page.tsx
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";

export default async function DashboardPage() {
  const allUsers = await db.select().from(users).limit(100);
  return (
    <main>
      <UserTable users={allUsers} />
    </main>
  );
}
```

### Client Components (only when needed)

```tsx
// ✅ DO: Mark with "use client" only for interactivity
// src/components/forms/LoginForm.tsx
"use client";

import { useState } from "react";
import { loginSchema } from "@/lib/auth/schema";

export function LoginForm() {
  const [error, setError] = useState("");
  // ...
}
```

### Form Pattern

```tsx
// ✅ DO: Server Action + Zod validation
// src/lib/auth/actions.ts
"use server";

import { loginSchema } from "./schema";

export async function loginAction(prevState: any, formData: FormData) {
  const data = Object.fromEntries(formData);
  const parsed = loginSchema.safeParse(data);
  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }
  // ... authenticate
}

// ✅ DO: useFormState for progressive enhancement
// src/components/forms/LoginForm.tsx
import { useFormState } from "react-dom";

export function LoginForm() {
  const [state, formAction] = useFormState(loginAction, { error: null });
  return (
    <form action={formAction}>
      {/* fields */}
      {state.error && <ErrorDisplay error={state.error} />}
    </form>
  );
}
```

---

## What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
|-------------|----------------|-------------------|
| `useEffect` for data fetching | Race conditions, waterfalls, no streaming | Server Components + `async/await` |
| Client-side state for auth | Vulnerable to XSS, hydration mismatches | Server Components + cookies + middleware |
| `SELECT *` in production | Schema drift breaks code | Explicit column selection with Drizzle |
| Global `db` variable in Route Handlers | Connection leaks in serverless | File-scoped `db` singleton with better-sqlite3 |
| `any` type | Defeats purpose of TypeScript | `unknown` + runtime validation (Zod) |
| CSS-in-JS (styled-components, emotion) | Runtime cost, streaming issues | Tailwind + CSS Modules for overrides |
| GraphQL for simple CRUD | Adds complexity, resolver boilerplate | REST API routes with Zod validation |
| Docker for local dev | SQLite is a file — no daemon needed | `better-sqlite3` + `drizzle-kit` CLI |
| Storing secrets in `.env.local` | Accidentally committed | `env.ts` with `z.string().min(1)` validation, `.env.local` gitignored |

---

## Environment Handling

```typescript
// src/lib/env.ts — Runtime environment validation
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXTAUTH_SECRET: z.string().min(32),
  NEXTAUTH_URL: z.string().url(),
  GITHUB_CLIENT_ID: z.string().optional(),
  GITHUB_CLIENT_SECRET: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

**Rule:** App crashes on startup with a clear error if any required env var is missing. No silent failures.

---

## Testing

| Test Type | Tool | When |
|-----------|------|------|
| Unit | Jest (Vitest) | Business logic, utilities |
| Component | React Testing Library | Interactive components (forms, modals) |
| E2E | Playwright | Critical user flows (signup → payment → dashboard) |
| Database | In-memory SQLite | Schema tests, migration validation |

**Rule:** Every mutation (INSERT, UPDATE, DELETE) in a Server Action must have at least one test.

---

## Dev Commands

```bash
# Database
npm run db:generate    # Generate migration from schema changes
npm run db:migrate     # Apply pending migrations
npm run db:studio      # Open Drizzle Studio (local DB GUI)

# Development
npm run dev            # Next.js + hot reload
npm run test           # Jest + coverage
npm run test:e2e       # Playwright
npm run lint           # ESLint + Prettier --check
npm run typecheck      # tsc --noEmit

# Build
npm run build          # next build (output: standalone)
```

---

## SaaS-Specific Rules

1. **Tenants:** Every SaaS table must have `tenantId` (or `orgId`). No exceptions.
2. **Soft deletes:** Use `deletedAt: timestamp` instead of `DELETE`. Always filter `WHERE deletedAt IS NULL`.
3. **Audit:** Every table has `createdAt` and `updatedAt`. Every mutation logs `updatedAt = now()`.
4. **Stripe:** Webhooks go to `src/app/api/webhooks/stripe/route.ts`. Use `stripe.webhooks.constructEvent()` with raw body.
5. **Emails:** Use `resend` for transactional. Queued sends go to a `pending_emails` table if webhook fails.
6. **Feature flags:** Store in `features` table (SQLite), read into `middleware.ts`. No external service dependency.

---

## Opinionated Decisions

**SQLite over Postgres?** Yes. For SaaS with < 10K users, SQLite on a managed volume is faster, cheaper, and zero-config. Migrate to Postgres at 50K users.

**better-sqlite3 over Turso?** Yes for single-node. Turso adds ~5ms latency per query. Use Turso only if you're multi-region from day one.

**No ORM codegen?** Yes. Drizzle ORM uses TypeScript inference. No `prisma generate` step. Schema is TypeScript.

**No tRPC?** Yes. Next.js 15 Server Actions eliminate the need for tRPC in most SaaS apps. Type-safe API without a separate router.

**No Jotai/Recoil/Zustand?** Yes. Server Components reduce client state. Use `useState`/`useReducer` for local UI state. Use Server Actions for server state.

---

## Quick Start (Copy-Paste)

```bash
# 1. Bootstrap
npx create-next-app@latest my-app --typescript --tailwind --eslint --app --src-dir

# 2. Add database dependencies
cd my-app
npm install better-sqlite3 drizzle-orm drizzle-kit
npm install -D @types/better-sqlite3

# 3. Add validation and auth
npm install zod next-auth@beta

# 4. Copy this CLAUDE.md to your repo root
# 5. Start building
npm run dev
```

---

*This CLAUDE.md is designed to be pasted into a greenfield Next.js + SQLite SaaS project and used without modification. Every rule is opinionated, every pattern is tested, every anti-pattern has a reason.*
