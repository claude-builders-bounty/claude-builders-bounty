# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS Project Guidelines

This file is the single source of truth for Claude Code when developing in this repository. Follow these patterns, rules, and constraints strictly.

---

## 1. Stack & Tech Specifications

| Layer | Technology | Version / Rule |
|---|---|---|
| **Framework** | Next.js (App Router) | `15.x` (`src/app/` layout, React Server Components by default) |
| **Runtime** | Node.js (LTS) / React | React `19.x`, strict TypeScript `5.x` |
| **Database** | SQLite | `better-sqlite3` (single-container/embedded) or `@libsql/client` (Turso edge) |
| **ORM & Migrations** | Drizzle ORM | `drizzle-orm` + `drizzle-kit` |
| **Styling** | Tailwind CSS & shadcn/ui | Radix UI primitives, `class-variance-authority`, `tailwind-merge` |
| **Validation** | Zod | All Server Action inputs and external payloads MUST use `z.object()` |
| **Icons** | Lucide React | `lucide-react` |
| **Testing** | Vitest | Node / Happy-DOM test environment |

---

## 2. Directory & File Organization

Organize files by feature domain, maintaining strict separation between server-only logic and client components:

```text
├── src/
│   ├── app/                    # Next.js 15 App Router pages and layouts
│   │   ├── (auth)/             # Route group: login, signup, reset-password
│   │   ├── (dashboard)/        # Route group: protected SaaS user dashboard
│   │   │   ├── layout.tsx      # Dashboard shell with sidebar & navigation
│   │   │   ├── page.tsx        # Overview / analytics
│   │   │   └── settings/       # Account / billing settings
│   │   ├── api/                # External webhook handlers ONLY (e.g. Stripe)
│   │   ├── layout.tsx          # Root layout (fonts, providers, metadata)
│   │   └── page.tsx            # Public landing page
│   ├── actions/                # Server Actions ('use server')
│   │   ├── auth.ts             # Sign in, sign out, password reset
│   │   ├── billing.ts          # Subscription checkout & portal sessions
│   │   └── organization.ts     # Org creation, member invitations
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Atomic design primitives (Button, Input, Card)
│   │   ├── features/           # Domain components (BillingTable, InviteModal)
│   │   └── shared/             # Header, Footer, Sidebar, UserMenu
│   ├── db/                     # Database layer
│   │   ├── index.ts            # SQLite client & Drizzle db singleton
│   │   ├── schema.ts           # Unified relational Drizzle schema
│   │   └── migrations/         # Drizzle-kit generated SQL migrations
│   ├── lib/                    # Shared utilities
│   │   ├── auth.ts             # Auth session helpers (Iron-Session or Lucia)
│   │   ├── safe-action.ts      # Typed Server Action wrapper with Zod
│   │   ├── utils.ts            # cn() helper for Tailwind classes
│   │   └── stripe.ts           # Stripe SDK instance & customer helpers
│   └── types/                  # Ambient TypeScript interfaces and ActionState
└── drizzle.config.ts           # Drizzle Kit migration configuration
```

---

## 3. Database & SQL Conventions

### 3.1 SQLite Initialization
SQLite must run with Write-Ahead Logging (WAL) and foreign key enforcement enabled:

```typescript
// src/db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL || "sqlite.db");
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("foreign_keys = ON");
sqlite.pragma("synchronous = NORMAL");

export const db = drizzle(sqlite, { schema });
```

### 3.2 Schema Design Rules
- **IDs**: Primary keys must use collision-resistant alphanumeric string IDs (nanoid/cuid2) rather than autoincrement integers to prevent enumeration attacks:
  ```typescript
  export const users = sqliteTable("users", {
    id: text("id").primaryKey().$defaultFn(() => createId()),
    email: text("email").notNull().unique(),
    createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
    updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  });
  ```
- **Timestamps**: Always store timestamps as UTC integers (`{ mode: "timestamp" }` in Drizzle) to avoid timezone discrepancies.
- **Foreign Keys**: Always declare explicit cascades (`onDelete: "cascade"` or `onDelete: "restrict"`).
- **Indexes**: Create explicit indexes on all foreign keys and frequently queried status/tenant columns:
  ```typescript
  export const subscriptions = sqliteTable("subscriptions", {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    status: text("status", { enum: ["active", "trialing", "canceled"] }).notNull(),
  }, (t) => [
    index("idx_subscriptions_user").on(t.userId),
    index("idx_subscriptions_status").on(t.status),
  ]);
  ```

### 3.3 Migration Workflow
- **NEVER** modify raw database tables directly.
- Generate migrations: `npm run db:generate`
- Apply migrations: `npm run db:migrate`
- Inspect database GUI: `npm run db:studio`

---

## 4. Server Actions & Mutation Patterns

### 4.1 Standard Action Return Type
Every Server Action must return a strongly typed `ActionState<T>`:

```typescript
export type ActionState<T> = {
  success: boolean;
  data?: T;
  error?: string;
  fieldErrors?: Record<string, string[]>;
};
```

### 4.2 Server Action Template
Always follow the 5-step mutation flow:
1. Validate input schema with Zod.
2. Authenticate and authorize session.
3. Execute database transaction via Drizzle.
4. Call `revalidatePath()` or `revalidateTag()` to invalidate cache.
5. Return structured result.

```typescript
"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";
import { db } from "@/db";
import { projects } from "@/db/schema";
import { getSession } from "@/lib/auth";
import type { ActionState } from "@/types";

const CreateProjectSchema = z.object({
  name: z.string().trim().min(3, "Name must be at least 3 characters").max(50),
});

export async function createProject(
  _prevState: ActionState<{ id: string }>,
  formData: FormData
): Promise<ActionState<{ id: string }>> {
  const session = await getSession();
  if (!session?.user) {
    return { success: false, error: "Unauthorized" };
  }

  const validated = CreateProjectSchema.safeParse({
    name: formData.get("name"),
  });

  if (!validated.success) {
    return {
      success: false,
      fieldErrors: validated.error.flatten().fieldErrors,
    };
  }

  try {
    const [project] = await db.insert(projects).values({
      name: validated.data.name,
      ownerId: session.user.id,
    }).returning({ id: projects.id });

    revalidatePath("/dashboard/projects");
    return { success: true, data: { id: project.id } };
  } catch (err) {
    return { success: false, error: "Failed to create project. Please try again." };
  }
}
```

---

## 5. Component Patterns

### 5.1 Server Components by Default
Every component is a Server Component unless it requires client hooks (`useState`, `useEffect`, `useActionState`, browser APIs).
- Fetch data directly inside Server Components using `await db.query...`
- Do NOT serialize data through REST endpoints to feed your own UI.

### 5.2 Interactive Client Leaves
Place `'use client'` only at interactive leaf components (forms, dialog triggers, toggle buttons).

```tsx
// src/components/features/create-project-form.tsx
"use client";

import { useActionState } from "react";
import { createProject } from "@/actions/projects";
import { Button } from "@/components/ui/button";

export function CreateProjectForm() {
  const [state, action, isPending] = useActionState(createProject, { success: false });

  return (
    <form action={action} className="space-y-4">
      {state.error && <p className="text-sm text-destructive">{state.error}</p>}
      <div>
        <label htmlFor="name" className="text-sm font-medium">Project Name</label>
        <input id="name" name="name" required className="border p-2 rounded w-full" />
        {state.fieldErrors?.name && (
          <p className="text-xs text-destructive">{state.fieldErrors.name[0]}</p>
        )}
      </div>
      <Button type="submit" disabled={isPending}>
        {isPending ? "Creating..." : "Create Project"}
      </Button>
    </form>
  );
}
```

---

## 6. What We DON'T Do (and Why)

| Anti-Pattern | Why We Forbid It | What To Do Instead |
|---|---|---|
| **`useEffect` for initial data fetching** | Causes layout shift, network waterfalls, and client bundle bloat. | Fetch data in async Server Components directly from SQLite via Drizzle. |
| **Internal `/api/...` route handlers for mutations** | Redundant HTTP serialization, no type-safety across boundary, extra boilerplate. | Use Server Actions (`'use server'`) with Zod validation. Keep `/api/` strictly for third-party webhooks (Stripe, GitHub). |
| **Client-side direct database access** | Security vulnerability; exposes SQLite file/socket and leaks environment secrets. | Keep all database queries in `src/db/`, Server Components, or Server Actions. |
| **Unvalidated Server Action parameters** | Susceptible to prototype pollution, SQL injection, and invalid state. | Always use `Schema.safeParse()` with Zod before touching the database. |
| **Raw SQL string interpolation** | Vulnerable to SQL injection (`PRAGMA` or input injection). | Use Drizzle parameterised query builders or `sql` tagged template literals. |
| **Autoincrement integer primary keys** | Allows competitors/attackers to enumerate total users, orgs, and documents. | Use alphanumeric prefixed nanoids/cuid2 strings (`user_abc123`). |
| **Barrel re-exports (`index.ts` exporting all components)** | Severely slows down Next.js compile/Fast Refresh times and degrades tree-shaking. | Import directly from component file: `@/components/ui/button`. |
| **Implicit `any` types** | Degrades refactoring safety and breaks TypeScript's inference guarantees. | Maintain strict TypeScript checks with explicit type signatures. |

---

## 7. Standard Development Commands

```bash
# Development
npm run dev             # Start Next.js local development server (port 3000)
npm run build           # Build optimized production bundle
npm run start           # Start production server

# Database & Migrations
npm run db:generate     # Generate SQL migration files from src/db/schema.ts
npm run db:migrate      # Apply pending migrations to SQLite database
npm run db:studio       # Launch Drizzle Studio browser interface for SQLite data
npm run db:seed         # Seed database with development test data

# Quality Assurance
npm run lint            # Run Next.js ESLint checks
npm run typecheck       # Run `tsc --noEmit` to verify type safety
npm test                # Execute test suite via Vitest
```
