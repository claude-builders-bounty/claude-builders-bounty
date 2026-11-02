# CLAUDE.md: Next.js 15 + SQLite SaaS Template

> **Target Stack**: Next.js 15 (App Router, Server Actions, PPR), React 19, TypeScript 5.x, SQLite (`better-sqlite3` or Turso `@libsql/client`), Drizzle ORM, Tailwind CSS v4, `shadcn/ui` (Radix primitives), and `pnpm`.

This document is the operational guide for Claude Code when building, modifying, or reviewing this codebase. Adhere strictly to the conventions and constraints outlined below.

---

## 1. Stack & Versions

- **Framework**: Next.js 15.x (React 19, Node.js >= 20.x, App Router exclusively).
- **Language**: TypeScript 5.x (`"strict": true`, `"noImplicitAny": true`, `"exactOptionalPropertyTypes": true`).
- **Database**: SQLite with `better-sqlite3` (local/containerized persistent storage) or `@libsql/client` (Turso edge replication).
- **ORM / Query Builder**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`).
- **Styling**: Tailwind CSS v4 + `clsx` + `tailwind-merge` (`cn()` utility).
- **UI Components**: `shadcn/ui` (Radix UI primitives).
- **Form & Validation**: React Hook Form + Zod (`zod/v3` or latest).
- **Authentication**: NextAuth v5 (Auth.js) or Lucia Auth with SQLite adapter.
- **Testing**: Vitest (unit/integration) + Playwright (E2E browser tests).
- **Package Manager**: `pnpm` (required; lockfile `pnpm-lock.yaml`).

---

## 2. Dev Commands

```bash
# Development
pnpm dev              # Launch local Next.js dev server with Turbopack (http://localhost:3000)
pnpm build            # Typecheck and build production bundle
pnpm start            # Run production server

# Database Operations (SQLite + Drizzle)
pnpm db:generate      # Generate SQL migration files in /drizzle from schema.ts
pnpm db:migrate       # Apply pending SQL migrations to local SQLite database
pnpm db:push          # Push schema changes directly (prototyping only; forbidden in prod)
pnpm db:studio        # Open visual Drizzle Studio web GUI on port 4983
pnpm db:seed          # Seed development database with deterministic test records

# Code Quality & Verification
pnpm lint             # Run ESLint across app, lib, and components
pnpm typecheck        # Run tsc --noEmit to verify full TypeScript compliance
pnpm test             # Run Vitest test suite
pnpm test:watch       # Run Vitest in interactive watch mode
pnpm test:e2e         # Execute Playwright end-to-end browser tests
```

---

## 3. Folder Structure

Colocate code by feature domain. Avoid global dumping grounds.

```text
├── drizzle/                     # Version-controlled SQL migration scripts
│   ├── 0000_initial_schema.sql
│   └── meta/                    # Drizzle schema snapshots
├── public/                      # Static assets (favicons, SVGs, public brand media)
├── src/
│   ├── app/                     # Next.js 15 App Router
│   │   ├── (auth)/              # Route group for unauthenticated flows (login, register)
│   │   ├── (dashboard)/         # Route group for authenticated SaaS workspace
│   │   ├── api/                 # Webhook and external third-party API endpoints
│   │   ├── favicon.ico
│   │   ├── globals.css          # Tailwind CSS root imports and theme variables
│   │   ├── layout.tsx           # Root layout with font optimization and providers
│   │   └── page.tsx             # Public landing page
│   ├── components/              # Shared UI components
│   │   ├── ui/                  # Primitives (button, dialog, dropdown, input)
│   │   └── shared/              # Cross-feature blocks (navbar, footer, theme-toggle)
│   ├── db/                      # Database connection and schema definitions
│   │   ├── index.ts             # SQLite connection initialization (WAL mode, pragmas)
│   │   ├── schema/              # Schema split by domain (users.ts, teams.ts, subscriptions.ts)
│   │   └── seed.ts              # Deterministic dev seed runner
│   ├── features/                # Domain-driven features (colocated UI, actions, queries)
│   │   ├── auth/                # Auth forms, session utilities, OAuth callbacks
│   │   ├── billing/             # Stripe webhooks, checkout actions, pricing tables
│   │   └── projects/            # Feature-specific components, mutations, and types
│   ├── hooks/                   # Generic reusable client React hooks
│   ├── lib/                     # Infrastructure helpers (auth, stripe, email, utils)
│   │   ├── auth.ts              # Auth.js / session configuration
│   │   ├── env.ts               # T3-env / runtime environment variable validation
│   │   └── utils.ts             # cn() class helper and formatting utilities
│   └── types/                   # Ambient and global TypeScript declarations
├── drizzle.config.ts            # Drizzle Kit CLI configuration
├── next.config.ts               # Next.js 15 build configuration
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
└── vitest.config.ts
```

---

## 4. SQL & SQLite Migration Conventions

### 4.1 Connection & PRAGMA Settings (`src/db/index.ts`)
SQLite requires specific PRAGMAs for SaaS workloads:
```typescript
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL || "sqlite.db");

// 1. Enable WAL mode for high concurrent read/write throughput
sqlite.pragma("journal_mode = WAL");

// 2. Enforce foreign key constraints (disabled by default in SQLite)
sqlite.pragma("foreign_keys = ON");

// 3. Optimize busy timeout to prevent 'database is locked' errors under write contention
sqlite.pragma("busy_timeout = 5000");

// 4. Synchronous NORMAL is safe in WAL mode and drastically speeds up disk writes
sqlite.pragma("synchronous = NORMAL");

export const db = drizzle(sqlite, { schema });
```

### 4.2 Migration Rules
1. **Never mutate tables directly in production**: All database changes must be generated via `pnpm db:generate` into version-controlled SQL files inside `/drizzle`.
2. **Backward-compatible column additions**: When adding columns to existing tables, provide default values or declare them nullable (`.default(...)` or `.notNull()` with default).
3. **Primary Keys**:
   - Use integer `INTEGER PRIMARY KEY AUTOINCREMENT` only for internal join tables.
   - Use URL-safe text IDs (e.g. `cuid2` or `ulid`, prefixed by domain: `usr_...`, `org_...`, `inv_...`) for all public/API-facing entity IDs to prevent enumeration attacks.
4. **Financial / Currency Calculations**:
   - Store monetary values as `INTEGER` representing the smallest unit (cents/pennies/satoshis). Never use `REAL` or floating-point decimals.
5. **Timestamps**:
   - Store timestamps as `INTEGER` (Unix milliseconds or seconds) or UTC ISO-8601 strings. Always use `default: sql`(CURRENT_TIMESTAMP)`.

---

## 5. Component & Architecture Patterns

### 5.1 Server Components by Default
- All components inside `src/app/` are **React Server Components (RSC)** by default.
- Fetch data directly inside Server Components using async/await and typed Drizzle queries.
- Push `"use client"` down to the lowest possible leaf components that require:
  - Event listeners (`onClick`, `onChange`).
  - Browser APIs (`localStorage`, `window`, Web Audio).
  - React client hooks (`useState`, `useEffect`, `useReducer`, `useOptimistic`).

### 5.2 Server Actions for Mutations (`src/features/*/actions.ts`)
- All database writes and mutations occur via Next.js Server Actions marked with `"use server"`.
- Validate **all** action inputs using Zod schemas before running business logic:
```typescript
"use server";

import { z } from "zod";
import { db } from "@/db";
import { projects } from "@/db/schema";
import { revalidatePath } from "next/cache";

const CreateProjectSchema = z.object({
  name: z.string().trim().min(2, "Name must be at least 2 characters").max(64),
  description: z.string().trim().max(255).optional(),
});

export type ActionState = {
  success: boolean;
  message?: string;
  fieldErrors?: Record<string, string[]>;
};

export async function createProjectAction(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const parsed = CreateProjectSchema.safeParse({
    name: formData.get("name"),
    description: formData.get("description"),
  });

  if (!parsed.success) {
    return {
      success: false,
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    await db.insert(projects).values(parsed.data);
    revalidatePath("/projects");
    return { success: true };
  } catch (error) {
    return { success: false, message: "Database insertion failed." };
  }
}
```

### 5.3 Optimistic UI
- Use `useOptimistic` alongside `useTransition` when updating UI list state before the server response returns.

---

## 6. What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It | What To Do Instead |
| :--- | :--- | :--- |
| **`any` or loose type assertions (`as unknown as T`)** | Destroys TypeScript compiler guarantees and leads to subtle runtime crashes. | Use explicit interfaces, generics, or Zod schemas with `z.infer<typeof Schema>`. |
| **`useEffect` data fetching in Client Components** | Creates network waterfalls, flash of unstyled content (FOUC), and bloated client JS bundles. | Fetch data in Server Components or pass promises into React `use()`. |
| **Direct database queries inside Client Components** | Next.js build will fail or leak database connection / secrets into client bundles. | Route queries through Server Components or Server Actions. |
| **Storing floats for currency (`REAL`)** | IEEE-754 rounding errors cause rounding drift on financial balance sheets. | Always store monetary amounts in cents as integer values (`INTEGER`). |
| **Raw SQL string interpolation** | Exposes the application to SQL injection attacks. | Use Drizzle parameterization (`db.select().from(...)` or `sql` tagged template strings). |
| **Un-migrated schema changes (`db:push` in production)** | Causes schema drift and breaks deployments across multiple environments. | Generate and commit migrations via `pnpm db:generate` and run `pnpm db:migrate`. |
| **Monolithic page files (>250 lines)** | Degrades maintainability, modularity, and readability for both human and AI editors. | Break views into domain-specific subcomponents in `src/features/<feature>/components/`. |
| **Unvalidated environment variables** | Causes silent failures in production when required API keys are missing. | Validate all environment variables at startup using a typed schema in `src/lib/env.ts`. |

---

## 7. Operational Checklist for AI Assistance

When writing or modifying code in this repository:
1. **Always inspect existing types and schemas** before proposing new columns or components.
2. **Preserve backward compatibility** on existing database queries.
3. **Verify build and types** by running `pnpm typecheck` and `pnpm lint` before considering tasks complete.
4. **Return structured error objects** rather than throwing uncaught exceptions in Server Actions.
