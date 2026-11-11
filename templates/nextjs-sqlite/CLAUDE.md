# CLAUDE.md — Next.js 15 + SQLite SaaS Architecture Guide

> Opinionated, zero-ambiguity rules for autonomous SWEs and human contributors building production Next.js 15 App Router applications backed by SQLite (better-sqlite3 / Turso libSQL).

---

## 1. Stack & Pinned Ecosystem

| Layer | Technology | Pinned Version / Boundary | Rationale |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js App Router | 15.x (React 19) | Server Components by default; zero client waterfall. |
| **Language** | TypeScript (Strict) | 5.5+ (`noImplicitAny`, `strictNullChecks`) | Compile-time truth; zero untyped `any` leaks. |
| **Database** | SQLite / libSQL | `better-sqlite3` (local) / `@libsql/client` (Turso edge) | Sub-millisecond latency; embedded zero-network query loops. |
| **ORM / Query** | Drizzle ORM | 0.35+ with `drizzle-kit` | Type-safe SQL builder with zero runtime overhead and clear migration files. |
| **Validation** | Zod | 3.23+ | Strict request & server action payload boundary validation. |
| **Styling** | Tailwind CSS v4 + shadcn/ui | Radix primitives | Headless, accessible, atomic class styling with zero runtime CSS-in-JS. |
| **Testing** | Vitest + Playwright | Unit + E2E | Ultra-fast in-memory SQLite runner with isolated test transactions. |

---

## 2. Directory Hierarchy

```text
├── src/
│   ├── app/                        # Next.js 15 App Router root
│   │   ├── (auth)/                 # Route group: authentication flows
│   │   ├── (dashboard)/            # Route group: authenticated SaaS app
│   │   ├── api/                    # Route Handlers (Webhooks & external APIs only)
│   │   ├── layout.tsx              # Root layout (fonts, providers, metadata)
│   │   └── page.tsx                # Public marketing landing page
│   ├── components/
│   │   ├── ui/                     # Primitives (button, dialog, input) from shadcn
│   │   └── shared/                 # Domain-shared composite components
│   ├── db/
│   │   ├── schema/                 # Drizzle schema definitions by domain
│   │   │   ├── users.ts
│   │   │   ├── subscriptions.ts
│   │   │   └── index.ts            # Re-exports all tables & relations
│   │   ├── migrations/             # Generated SQL migration files (drizzle-kit)
│   │   └── index.ts                # Database connection singleton & client
│   ├── lib/
│   │   ├── actions/                # Server Actions (Mutations & form submissions)
│   │   ├── queries/                # Read-only Server Component data fetchers
│   │   ├── auth.ts                 # Session and token validation helpers
│   │   └── utils.ts                # Pure formatting / class merging (clsx + twMerge)
│   └── types/                      # Global domain types & inferred DB schemas
├── tests/
│   ├── unit/                       # Vitest unit & schema tests
│   └── e2e/                        # Playwright browser integration tests
├── drizzle.config.ts               # Drizzle migration generator config
├── next.config.ts                  # Next.js production configuration
├── package.json
└── tsconfig.json
```

---

## 3. Database & Migration Invariants

1. **WAL Mode Mandatory:** Every local SQLite connection must immediately execute `PRAGMA journal_mode = WAL;` and `PRAGMA foreign_keys = ON;`. WAL mode allows concurrent readers and prevents database locks during writes.
2. **Deterministic Migration Scripts:**
   - Run `pnpm db:generate` to produce timestamped, immutable `.sql` migration files in `src/db/migrations/`.
   - Never mutate existing migration files; generate a new migration for schema changes.
   - Run `pnpm db:migrate` before deploying or launching the production server.
3. **Primary Keys & Timestamps:**
   - Every table must have an `id TEXT PRIMARY KEY` generated via `nanoid()` or ULID (avoids sequential ID scraping).
   - Every table must include `created_at INTEGER NOT NULL DEFAULT (unixepoch())` and `updated_at INTEGER NOT NULL DEFAULT (unixepoch())`.
4. **Transactions for Multi-Write Operations:**
   - Always wrap correlated mutations inside `db.transaction(async (tx) => { ... })`. If an error occurs, SQLite rolls back atomically.

---

## 4. Component & Server Action Patterns

1. **Server Components by Default:**
   - Fetch data directly in Server Components using functions from `src/lib/queries/`.
   - Never use `useEffect` or client-side fetchers (`axios`, `swr`, `react-query`) for primary page data.
2. **Server Actions for Mutations:**
   - Place all mutations in `src/lib/actions/*.ts` with `"use server";` at top.
   - Every Server Action must validate its input through a Zod schema before touching the database:
     ```ts
     "use server";
     import { z } from "zod";
     import { db } from "@/db";
     import { revalidatePath } from "next/cache";

     const UpdateProfileSchema = z.object({
       userId: z.string().min(1),
       name: z.string().min(2).max(50),
     });

     export async function updateProfile(rawInput: unknown) {
       const { userId, name } = UpdateProfileSchema.parse(rawInput);
       await db.update(users).set({ name, updatedAt: new Date() }).where(eq(users.id, userId));
       revalidatePath("/dashboard/settings");
       return { success: true };
     }
     ```
3. **Client Components Only When Interactive:**
   - Add `"use client";` only to files requiring React event handlers (`onClick`, `onChange`), browser APIs, or state (`useState`).

---

## 5. Development & Testing Commands

| Purpose | Command | Description |
| :--- | :--- | :--- |
| **Development** | `pnpm dev` | Starts local Next.js dev server on `http://localhost:3000`. |
| **Build & Typecheck** | `pnpm build` | Executes TypeScript verification (`tsc --noEmit`) and Next.js static optimization. |
| **Lint & Format** | `pnpm lint` | Runs ESLint and Prettier checks. |
| **Generate Migration** | `pnpm db:generate` | Inspects `src/db/schema/` and generates SQL migrations in `src/db/migrations/`. |
| **Apply Migrations** | `pnpm db:migrate` | Applies pending migrations to the active SQLite/libSQL database. |
| **DB Studio** | `pnpm db:studio` | Launches Drizzle visual database manager. |
| **Unit Tests** | `pnpm test` | Runs Vitest in-memory test runner. |

---

## 6. What We NEVER Do (And Why)

1. **NO Client-Side Database Calls:**
   - *Why:* Leaks database credentials and schema structure to the browser. All DB calls belong in Server Components or Server Actions.
2. **NO Prisma or Heavy Run-Time ORMs:**
   - *Why:* Prisma engine binaries inflate serverless/edge bundle size and add substantial cold-start latency. Drizzle is lightweight, zero-dependency, and compiles directly to typed SQL.
3. **NO Unvalidated Client Payloads:**
   - *Why:* Prevents SQL injection, parameter tampering, and type coercion vulnerabilities. Zod guards every boundary.
4. **NO Manual Foreign Key Ignoring in SQLite:**
   - *Why:* SQLite defaults to foreign keys disabled unless explicitly enabled via `PRAGMA foreign_keys = ON;`. We enable it on every connection to maintain relational integrity.
5. **NO Global State Managers (Redux / MobX):**
   - *Why:* Next.js Server Components eliminate 95% of client state requirements. Use React URL parameters (`useSearchParams`) or lightweight Zustand stores for local UI toggles only.
