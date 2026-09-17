# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Template

> **Architecture Manifesto**: This repository is an opinionated, production-grade SaaS starter built with Next.js 15 App Router, React 19 Server Components, SQLite (via LibSQL / Turso / better-sqlite3), and Drizzle ORM.

---

## 🛠️ Stack & Recommended Versions

- **Framework**: Next.js `15.x` (App Router, Turbopack, React 19)
- **Language**: TypeScript `5.x` (Strict mode, `noImplicitAny: true`, `exactOptionalPropertyTypes: true`)
- **Database Engine**: SQLite / LibSQL (`@libsql/client` for Turso edge compatibility or `better-sqlite3` for local Node.js)
- **ORM & Migrations**: Drizzle ORM (`drizzle-orm`, `drizzle-kit`)
- **Validation**: Zod `3.x` (Used strictly on all Server Actions and API input boundaries)
- **Styling**: Tailwind CSS `v4` with CSS Variables and Radix UI primitives / shadcn-ui
- **Package Manager**: `pnpm` (required for deterministic dependency locking)

---

## 📁 Repository Structure

```
├── drizzle/                   # Generated SQL migration files (Never edit manually)
├── public/                    # Static public assets
├── src/
│   ├── actions/               # Server Actions (Mutations & business logic)
│   │   ├── auth.actions.ts
│   │   └── billing.actions.ts
│   ├── app/                   # App Router pages and layouts
│   │   ├── (auth)/            # Route group: Login, Register, Forgot Password
│   │   ├── (dashboard)/       # Route group: Authenticated SaaS portal
│   │   │   ├── layout.tsx     # Dashboard sidebar & top navigation
│   │   │   └── page.tsx       # Main dashboard overview
│   │   ├── api/               # External webhooks (Stripe, Resend)
│   │   ├── layout.tsx         # Root HTML layout with providers
│   │   └── page.tsx           # Marketing landing page
│   ├── components/
│   │   ├── ui/                # Atomic primitives (Button, Input, Dialog, Card)
│   │   ├── forms/             # Client form components using useActionState
│   │   └── layout/            # Navigation, Sidebar, UserDropdown
│   ├── db/
│   │   ├── index.ts           # Database connection client instance
│   │   ├── schema.ts          # Consolidated Drizzle SQLite table definitions
│   │   └── seed.ts            # Seed script for initial dev data
│   ├── lib/
│   │   ├── auth/              # Session management, password hashing, guards
│   │   ├── utils.ts           # Pure helpers (cn, formatters)
│   │   └── errors.ts          # Standardized error hierarchy
│   └── types/
│       └── index.ts           # Shared TypeScript domain interfaces
├── drizzle.config.ts          # Drizzle Kit configuration
├── next.config.ts             # Next.js runtime configuration
├── package.json
└── tsconfig.json
```

---

## ⚙️ Essential Developer Commands

```bash
# Development
pnpm dev                       # Start dev server with Turbopack on http://localhost:3000
pnpm build                     # Production build with type checking
pnpm start                     # Start production server

# Database & Migrations
pnpm db:generate               # Generate SQL migrations from schema.ts
pnpm db:migrate                # Apply pending migrations to local SQLite database
pnpm db:seed                   # Populate database with development fixtures
pnpm db:studio                 # Launch Drizzle Studio web GUI on http://localhost:4983

# Code Quality & Tests
pnpm lint                      # Run ESLint validation
pnpm typecheck                 # Run TypeScript tsc --noEmit check
pnpm test                      # Run Vitest unit & integration test suite
```

---

## 🗄️ Database & Migration Conventions

1. **Table Definitions (`src/db/schema.ts`)**:
   - Use **plural `snake_case`** for SQL table names (e.g. `users`, `organizations`, `billing_invoices`).
   - Use **`camelCase`** for TypeScript schema properties that map to `snake_case` database columns:
     ```typescript
     import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

     export const users = sqliteTable("users", {
       id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
       email: text("email").notNull().unique(),
       fullName: text("full_name"),
       createdAt: integer("created_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
       updatedAt: integer("updated_at", { mode: "timestamp" }).$onUpdate(() => new Date())
     });
     ```
2. **Deterministic Migrations**:
   - Never write raw `ALTER TABLE` commands manually. Always modify `src/db/schema.ts` and execute `pnpm db:generate`.
   - SQLite does not support all `ALTER TABLE` operations directly; Drizzle Kit automatically handles table recreation safely.
3. **Foreign Keys & Cascades**:
   - Always declare explicit foreign key cascades (`onDelete: "cascade"` or `onDelete: "restrict"`) to prevent orphaned rows.

---

## 🧩 Component & Server Action Patterns

### 1. Server Components by Default
- All pages and components in `src/app/` are **React Server Components (RSC)** by default.
- Fetch data directly in Server Components using async/await and Drizzle ORM queries:
  ```typescript
  // src/app/(dashboard)/projects/page.tsx
  import { db } from "@/db";
  import { projects } from "@/db/schema";
  import { requireAuth } from "@/lib/auth";

  export default async function ProjectsPage() {
    const session = await requireAuth();
    const userProjects = await db.query.projects.findMany({
      where: (p, { eq }) => eq(p.userId, session.user.id)
    });

    return <ProjectList items={userProjects} />;
  }
  ```

### 2. Client Components Leaf-Only
- Mark components with `'use client'` only when they require browser events, local state (`useState`), or hooks (`useFormStatus`, `useActionState`).
- Keep Client Components at the leaves of your component tree.

### 3. Server Actions with Typed Result Wrapper
- All mutations must be defined in `src/actions/*.ts` with `'use server'`.
- Validate all inputs with **Zod**.
- Return a discriminated union `ActionResponse<T>` instead of throwing untyped errors:
  ```typescript
  "use server";

  import { z } from "zod";
  import { db } from "@/db";
  import { projects } from "@/db/schema";
  import { revalidatePath } from "next/cache";

  const CreateProjectSchema = z.object({
    title: z.string().min(3).max(100),
  });

  export async function createProjectAction(prevState: any, formData: FormData) {
    const parsed = CreateProjectSchema.safeParse({
      title: formData.get("title")
    });

    if (!parsed.success) {
      return { success: false, errors: parsed.error.flatten().fieldErrors };
    }

    try {
      await db.insert(projects).values({ title: parsed.data.title });
      revalidatePath("/dashboard/projects");
      return { success: true, message: "Project created successfully" };
    } catch (err) {
      return { success: false, message: "Database insertion failed" };
    }
  }
  ```

---

## 🚫 What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
|---|---|---|
| **No Prisma ORM** | Prisma adds heavy binaries and engine overhead in serverless/edge environments. | We use **Drizzle ORM** for zero-overhead, type-safe SQL queries. |
| **No Client-side Data Fetching (`useEffect` + `fetch`)** | Causes request waterfalls, bloated client bundles, and SEO penalties. | We fetch directly inside **React Server Components**. |
| **No Global Redux / Zustand for Server State** | Server state quickly goes out of sync with the database and adds boilerplate. | We rely on **URL Search Params** for UI state and **Server Actions + `revalidatePath`** for cache invalidation. |
| **No Unvalidated API / Action Payloads** | Accepts malformed or malicious payload injections. | We enforce strict **Zod schemas** on every Action and Endpoint. |
| **No `any` Types** | Bypasses TypeScript's compiler protections and causes runtime errors. | We use strict domain interfaces and Drizzle inferred types (`typeof table.$inferSelect`). |
