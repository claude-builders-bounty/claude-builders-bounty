# Next.js 15 + SQLite SaaS — Production Guidelines & Architecture

This repository is a production multi-tenant SaaS application built with **Next.js 15 (App Router)**, **React 19**, **TypeScript (Strict)**, **Tailwind CSS v4**, and **SQLite (better-sqlite3 / Turso libSQL via Drizzle ORM)**.

---

## 1. Stack & Pinned Versions
- **Framework**: Next.js 15 (App Router with React Server Components by default)
- **Runtime**: Node.js >= 20.x / LTS
- **Database Engine**: Embedded SQLite via `better-sqlite3` (Local/Self-hosted) / `@libsql/client` (Distributed Turso edge)
- **ORM & Schema**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Authentication**: Auth.js / NextAuth v5 or Lucia Auth (Database session strategy in SQLite)
- **Styling & UI**: Tailwind CSS v4, Lucide React icons, Radix UI primitives
- **Validation & Parsing**: Zod v3 for all API boundaries, Server Action payloads, and environment variables
- **Testing**: Vitest for unit/integration tests, Playwright for end-to-end tests

---

## 2. Project & Folder Structure

```text
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── (auth)/               # Unauthenticated route group (login, register, forgot-password)
│   │   ├── (dashboard)/          # Authenticated app shell route group
│   │   │   ├── dashboard/        # Main tenant dashboard
│   │   │   ├── settings/         # Organization & profile settings
│   │   │   └── layout.tsx        # Dashboard layout with sidebar, auth boundary, and tenant context
│   │   ├── api/                  # Route handlers (webhooks, external integrations ONLY)
│   │   ├── layout.tsx            # Root HTML layout with providers and fonts
│   │   ├── page.tsx              # Public marketing / landing page
│   │   └── globals.css           # Tailwind CSS directives and design tokens
│   ├── components/               # UI Component Hierarchy
│   │   ├── ui/                   # Reusable, primitive atomic components (Button, Input, Dialog, etc.)
│   │   ├── forms/                # Form compositions with React Hook Form + Zod resolvers
│   │   └── layout/               # Navbars, Sidebars, Footers, and Breadcrumbs
│   ├── db/                       # Database layer
│   │   ├── schema/               # Modular Drizzle table definitions (*.table.ts)
│   │   │   ├── users.table.ts
│   │   │   ├── sessions.table.ts
│   │   │   ├── tenants.table.ts
│   │   │   └── index.ts          # Central schema export
│   │   ├── migrations/           # Auto-generated SQL migration files (drizzle-kit)
│   │   ├── client.ts             # Instantiated SQLite/Turso client with connection pooling & WAL mode
│   │   └── seed.ts               # Local development seeder script
│   ├── server/                   # Server-side business logic
│   │   ├── actions/              # Next.js Server Actions ("use server") for mutations
│   │   ├── queries/              # Pure async database read queries (cached via React cache() / unstable_cache)
│   │   └── services/             # Third-party integrations (Stripe, Resend, S3/R2 storage)
│   ├── lib/                      # Pure utilities, shared constants, and type guards
│   │   ├── env.ts                # Runtime type-safe environment variable parser (Zod)
│   │   ├── utils.ts              # ClassName merger (clsx + tailwind-merge), formatters
│   │   └── errors.ts             # Standardized domain error classes
│   └── types/                    # Ambient TypeScript interfaces and inferred Drizzle model types
├── drizzle.config.ts             # Drizzle Kit migration and introspection configuration
├── vitest.config.ts              # Vitest test suite configuration
├── next.config.ts                # Next.js compiler settings & security headers
└── tsconfig.json                 # TypeScript strict compiler options with `@/*` path alias
```

---

## 3. SQL & SQLite Migration Conventions

### SQLite Engine Optimization
1. **Write-Ahead Logging (WAL)**: All SQLite instances MUST execute `PRAGMA journal_mode = WAL;` on startup. This allows concurrent readers while a write transaction is in progress.
2. **Busy Timeout & Foreign Keys**: Always enforce:
   ```sql
   PRAGMA busy_timeout = 5000;
   PRAGMA foreign_keys = ON;
   PRAGMA synchronous = NORMAL;
   ```
3. **Primary Keys**: Use sortable UUIDv7 strings or monotonic ULIDs for distributed safety, or integer autoincrement for lightweight internal tables.

### Drizzle Migration Rules
- Never hand-edit files inside `src/db/migrations/`.
- Generate migrations strictly via CLI: `pnpm db:generate`.
- Apply migrations strictly via CLI: `pnpm db:migrate`.
- For column additions on populated tables, always declare a `.default()` or make the column nullable `.nullable()`.
- Use Drizzle transactions (`db.transaction(async (tx) => { ... })`) whenever mutating across more than one table.

---

## 4. Development & Operation Commands

```bash
# Development
pnpm dev             # Start local Next.js dev server with Turbo (http://localhost:3000)
pnpm build           # Typecheck and compile production Next.js build
pnpm start           # Run production build locally

# Database Operations
pnpm db:generate     # Generate Drizzle migration SQL from schema changes
pnpm db:migrate      # Execute pending migrations against local/remote SQLite
pnpm db:studio       # Launch Drizzle Studio GUI for inspecting database rows
pnpm db:seed         # Seed database with mock tenants and test users

# Quality & Testing
pnpm lint            # Run Next.js ESLint rules
pnpm typecheck       # Run tsc --noEmit to verify strict type correctness
pnpm test            # Run unit and integration tests via Vitest
pnpm test:e2e        # Run end-to-end browser tests via Playwright
```

---

## 5. Architecture & Component Patterns

### React Server Components (RSC) vs Client Components
- **Default to RSC**: Every file in `src/app/` is a Server Component unless interactive browser APIs (state, effects, event handlers) are explicitly required.
- **Client Boundaries**: Add `"use client"` only at leaf components (e.g., `<ThemeToggle />`, `<InteractiveChart />`, `<ModalTrigger />`).
- **Data Fetching**: Fetch data directly inside Server Components using async queries from `src/server/queries/`. Do NOT create internal REST API routes solely to fetch data for RSC.

### Server Actions for Mutations
- Colocate mutations in `src/server/actions/`.
- Validate input using Zod before any database execution.
- Return structured result objects `{ success: true, data } | { success: false, error: string }` instead of throwing unhandled exceptions to the client.
- Call `revalidatePath()` or `revalidateTag()` after successful mutations to invalidate Next.js data cache.

```typescript
// Example: src/server/actions/create-project.action.ts
"use server";

import { z } from "zod";
import { db } from "@/db/client";
import { projects } from "@/db/schema";
import { revalidatePath } from "next/cache";

const CreateProjectSchema = z.object({
  title: z.string().min(3).max(100),
  tenantId: z.string().uuid(),
});

export async function createProjectAction(rawInput: unknown) {
  const result = CreateProjectSchema.safeParse(rawInput);
  if (!result.success) {
    return { success: false, error: result.error.errors[0].message };
  }

  try {
    const [project] = await db.insert(projects).values(result.data).returning();
    revalidatePath("/dashboard/projects");
    return { success: true, data: project };
  } catch (err: any) {
    return { success: false, error: "Failed to create project in database." };
  }
}
```

---

## 6. What We DON'T Do (and Why)

1. ❌ **Don't use `useEffect` for data fetching on initial load.**
   - *Why:* Causes waterfall network delays, client layout shifts, and exposes database queries to the client bundle. Use React Server Components with async data access.
2. ❌ **Don't use raw SQL strings without parameterized bindings.**
   - *Why:* Vulnerable to SQL injection. Always use Drizzle ORM query builders or `sql` tagged template literals with variable interpolation.
3. ❌ **Don't store database files in volatile ephemeral containers without persistent volume mounts.**
   - *Why:* SQLite stores all state in a local `.sqlite` / `.db` file on disk. Serverless containers (like default Vercel serverless functions) will lose state on teardown unless using Turso libSQL edge over HTTP or mounted persistent storage.
4. ❌ **Don't leave foreign keys disabled in SQLite.**
   - *Why:* SQLite disables foreign key constraints by default for backwards compatibility. Always enable `PRAGMA foreign_keys = ON;` in `src/db/client.ts`.
5. ❌ **Don't import client-only libraries into Server Components or database models into Client Components.**
   - *Why:* Leaks secrets/database connection strings to the client browser and triggers bundler errors. Use package boundaries like `server-only` to enforce server isolation.
