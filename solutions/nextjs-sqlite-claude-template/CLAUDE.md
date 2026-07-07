# CLAUDE.md - Next.js 15 + SQLite SaaS Development Guidelines

This guide defines the standards, project structure, and coding patterns for the **Next.js 15 App Router + SQLite (via Drizzle ORM)** SaaS stack. Follow these instructions strictly to maintain security, high performance, and codebase clarity.

---

## 🛠️ Stack & Versions
- **Framework**: Next.js 15.x (App Router, Server Components by default)
- **Database**: SQLite (Local: `better-sqlite3`, Production/Cloud: `@libsql/client` / Turso)
- **ORM**: Drizzle ORM (TypeScript-first query builder and migration generator)
- **Styling**: Tailwind CSS
- **Components**: Shadcn UI (Radix UI + Tailwind)
- **Validation**: Zod (for forms, API payloads, and database inputs)

---

## 📂 Folder Structure
We enforce a strict modular architecture inside the `src/` directory:

```text
src/
├── app/                  # Next.js App Router (pages, layouts, actions)
│   ├── layout.tsx        # Global layout
│   ├── page.tsx          # Home page
│   ├── dashboard/        # Dashboard route group
│   │   ├── page.tsx      # Dashboard page (RSC)
│   │   └── actions.ts    # Dashboard-specific Server Actions
│   └── error.tsx         # Global error boundary
├── components/           # Shared UI components
│   ├── ui/               # Base UI elements (Shadcn)
│   └── dashboard/        # Dashboard UI components (Client/Server)
├── db/                   # Database files, schemas, and configurations
│   ├── index.ts          # Database client initialization
│   ├── schema.ts         # Consolidated database schema definition
│   └── migrations/       # Drizzle-generated SQL migrations
├── lib/                  # Shared helper functions and configurations
│   ├── utils.ts          # Styling/tailwind utilities
│   └── auth.ts           # Authentication logic
└── hooks/                # Reusable client-side React hooks
```

---

## 💻 Dev & Build Commands
- **Dev Server**: `npm run dev`
- **Build App**: `npm run build`
- **Lint Check**: `npm run lint`
- **Drizzle Studio**: `npx drizzle-kit studio` (UI for database browsing)
- **Generate Migrations**: `npx drizzle-kit generate`
- **Apply Migrations**: `npx drizzle-kit migrate`

---

## 🗄️ SQL & Migration Conventions

### 1. Schema Definitions (`src/db/schema.ts`)
- Use **snake_case** for database table and column names:
  ```typescript
  import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

  export const users = sqliteTable("users", {
    id: text("id").primaryKey(),
    email: text("email").notNull().unique(),
    createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  });
  ```
- Use **camelCase** for TypeScript property names (`createdAt` -> `created_at`).
- Define explicit foreign keys and cascade rules on delete:
  ```typescript
  export const posts = sqliteTable("posts", {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  });
  ```

### 2. Database Migrations Workflow
- **Never modify database state manually or execute raw schema-changing DDL.**
- Always edit `src/db/schema.ts` first.
- Run `npx drizzle-kit generate` to produce the SQL migration file under `src/db/migrations/`.
- Review the generated SQL files to ensure correct alterations.
- Apply the migration in development with `npx drizzle-kit migrate`.
- In production startup, run migrations programmatically prior to server boot:
  ```typescript
  import { migrate } from "drizzle-orm/better-sqlite3/migrator";
  // Run during application bootstrap
  migrate(db, { migrationsFolder: "src/db/migrations" });
  ```

---

## 🏗️ Component & Data Fetching Patterns

### 1. React Server Components (RSC) by Default
- All pages, layouts, and components are Server Components by default. Keep them that way.
- **Fetch data directly in Server Components**: Do not create or call `/api` routes internally. Use direct DB queries:
  ```typescript
  // src/app/dashboard/page.tsx
  import { db } from "@/db";
  import { users } from "@/db/schema";

  export default async function DashboardPage() {
    const allUsers = await db.select().from(users);
    return <UserList users={allUsers} />;
  }
  ```

### 2. Client Components (Leaf Level)
- Mark components with `"use client"` only when client interactivity is required (e.g. `onClick`, `useState`, `useEffect`, Framer Motion).
- Keep client components at the lowest possible level in the DOM tree (leaf components).

### 3. Data Mutation: Server Actions
- All mutations (creates, updates, deletes) must be executed using **Server Actions** (`"use server"`).
- Always validate request payloads using **Zod** schemas inside the action.
- Wrap Server Actions in `useActionState` or `useTransition` on the client side to handle pending/loading states.
  ```typescript
  // src/app/dashboard/actions.ts
  "use server";
  import { db } from "@/db";
  import { users } from "@/db/schema";
  import { revalidatePath } from "next/cache";
  import { z } from "zod";

  const createUserSchema = z.object({
    email: z.string().email(),
  });

  export async function createUserAction(formData: FormData) {
    const validated = createUserSchema.safeParse({
      email: formData.get("email"),
    });
    if (!validated.success) return { error: "Invalid email address" };

    await db.insert(users).values({
      id: crypto.randomUUID(),
      email: validated.data.email,
      createdAt: new Date(),
    });

    revalidatePath("/dashboard");
    return { success: true };
  }
  ```

---

## 🚫 What We Don't Do (And Why)

1. **No Client-side Database Client Instantiation**
   - *Why*: SQLite is a server-side file-based database. Instantiating or passing db credentials/libs to client-side components will leak keys or crash the client bundle. Keep all database queries strictly inside server components, helper modules, or server actions.
2. **No Raw String SQL Interpolation**
   - *Why*: Direct string concatenation in queries (e.g., `db.run("SELECT * FROM users WHERE name = '" + input + "'")`) creates SQL injection vulnerabilities. Always use Drizzle's query builder methods or parameterized template tags: `sql` from `drizzle-orm`.
3. **No Redundant Internal `/api` Routes**
   - *Why*: Calling `/api/users` from a client page to load or save data introduces network overhead, boilerplate code, and authentication checks. Use React Server Components to load data directly and Server Actions to mutate data.
4. **No Heavy Client-side Global State Managers**
   - *Why*: Redux, MobX, or even complex Zustand setups increase bundle size and complicate code. Prefer using URL Search Parameters (via `useSearchParams` and Next.js router) for UI state like active tabs, pagination, filters, and modals.
5. **No Database Queries in Loops (N+1 Problem)**
   - *Why*: Querying in a `.map()` loop (e.g., fetching comments for each post individually) triggers dozens of sequential database roundtrips, causing performance latency. Always write SQL `JOIN` queries or use Drizzle's relational query API to fetch nested structures in a single batch query.
