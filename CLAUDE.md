# CLAUDE.md — Next.js 15 + SQLite SaaS Template

Opinionated, production-ready guidelines for Claude Code when working in a Next.js 15 (App Router) SaaS project backed by SQLite.

## Stack & Versions

- **Next.js**: `15.x` (App Router, React Server Components by default)
- **React**: `19.x`
- **Database**: SQLite via `better-sqlite3` (synchronous, in-process, high performance for local execution) or `@libsql/client` (Turso, serverless edge compatible)
- **ORM**: `Drizzle ORM` (preferred for its type safety, light footprint, and low-overhead SQL equivalence)
- **Validation**: `Zod` (runtime verification at API and Server Action boundaries)
- **Auth**: `NextAuth.js v5` (Auth.js) or session-based cookies
- **Styling**: `Tailwind CSS v4`

*Reason*: This stack is optimized for lightning-fast start times, minimal external dependencies, robust local development, and seamless transition to Turso for serverless deployments.

---

## Folder Structure

```
/
├── app/                        # Next.js App Router root
│   ├── (auth)/                 # Route group for auth flows (login, signup)
│   ├── (dashboard)/            # Route group for authenticated user workspaces
│   │   ├── layout.tsx          # Auth-guarded dashboard skeleton
│   │   └── page.tsx            # Dashboard home view
│   ├── api/                    # Standard API route handlers (e.g., Stripe webhooks)
│   ├── layout.tsx              # Root HTML/Body wrapper and global provider injection
│   └── globals.css             # Tailwind style definitions
├── components/                 # Reusable UI component ecosystem
│   ├── ui/                     # Pure design components (shadcn/ui primitives)
│   ├── forms/                  # React Hook Form + Zod form implementations
│   └── features/               # Feature-specific, domain-bound layout parts
├── lib/                        # Shared application logic layers
│   ├── db/                     # Database client, ORM schema, and migrations
│   │   ├── client.ts           # database connection singleton
│   │   ├── schema.ts           # Unified database schema definition
│   │   └── migrations/         # Generated SQL migration history files
│   ├── auth/                   # Authentication logic and route handlers
│   └── utils.ts                # Shared helper functions (e.g., tailwind-merge)
└── scripts/                    # Standalone utility scripts (seeding, migrations)
```

*Reason*: Co-locating elements within explicit route groups makes auth gates modular, and keeping data logic strictly under `lib/` prevents spaghetti imports.

---

## Naming Conventions

| Domain | Rule | Example |
| :--- | :--- | :--- |
| **Files & Folders** | kebab-case (except components) | `app/billing-settings/page.tsx` |
| **Components** | PascalCase | `BillingDetailsTable.tsx` |
| **Server Actions** | camelCase (prefixed with action verb) | `submitPaymentIntent()` |
| **Database Tables** | snake_case | `user_billing_subscriptions` |
| **API Endpoints** | kebab-case | `/api/stripe-webhook` |

*Reason*: Strict separation makes it immediately clear what role a file plays and ensures cross-platform case sensitivity safety.

---

## SQL & Migration Conventions

### Schema Definition
1. Define all tables inside `lib/db/schema.ts` for unified schema compilation.
2. Every table must have `created_at` and `updated_at` timestamps using epoch storage or ISO-8601 strings.
3. Use soft deletes via a nullable `deleted_at` timestamp. Avoid hard `DELETE` operations on production tenant data.

### Migrations
- Perform all migrations using Drizzle-Kit: `npx drizzle-kit generate`
- Inspect every generated migration file before running `npx drizzle-kit migrate` to ensure it is additive. Avoid running `ALTER TABLE DROP` in live production environments.

### Query Best Practices
```ts
// Do: Use parameter binding or type-safe ORM parameters
const member = await db.select().from(users).where(eq(users.id, inputId));

// Do NOT: Inject variables directly into SQL template literals
const member = await db.execute(sql`SELECT * FROM users WHERE id = ${inputId}`); // Vulnerable if unparameterized
```

*Reason*: Type safety protects against SQL injection, and soft deletes preserve referential integrity and audit trails.

---

## Component & Data Fetching Patterns

### Server Components vs Client Components
- **RSC (Server Components)**: Render by default. Handle all direct database queries, context loading, and API orchestration directly inside server pages.
- **Client Components**: Restrict usage of `'use client'` to components requiring event handlers, state hooks (`useState`, `useEffect`), or DOM interactions.

### Data Mutation: Server Actions
- Write Server Actions inside dedicated files (e.g., `app/(dashboard)/actions.ts`) or specify `'use server'` at the top of the action function.
- Always validate incoming arguments using `Zod` schemas.

```ts
"use server"

import { revalidatePath } from "next/cache";
import { z } from "zod";

const taskSchema = z.object({
  title: z.string().min(1, "Title is required"),
});

export async function createNewTask(data: unknown) {
  const result = taskSchema.safeParse(data);
  if (!result.success) {
    return { error: result.error.flatten().fieldErrors };
  }
  
  // Perform database insert using db instance...
  revalidatePath("/dashboard");
  return { success: true };
}
```

---

## What We Do NOT Do (And Why)

| Anti-Pattern | Correct Approach | Why |
| :--- | :--- | :--- |
| **`useEffect` for Init** | React Server Components | Avoids loading skeletons, round trips, and duplicate waterfall queries. |
| **`any` Types** | Strict TypeScript Typing | Prevents silent runtime failures and compiler bypasses. |
| **Inline database queries** | Centralized client imports | Centralizes query optimization, schema changes, and connection pooling. |
| **Hard-coded secrets** | Environment variables (`process.env`) | Prevents exposing private API tokens and database keys in git history. |
| **Raw SQL String building** | Drizzle ORM query builders | Mitigates SQL Injection risks and keeps column naming uniform. |
