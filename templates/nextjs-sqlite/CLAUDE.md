# CLAUDE.md — Next.js 15 (App Router) + SQLite / Drizzle SaaS Blueprint

This document sets the development standards, architecture rules, and conventions for this SaaS project. Always follow these patterns.

---

## 🛠️ Stack & Key Dependencies

- **Framework**: Next.js 15+ (App Router, Server Components by default)
- **Runtime / DB Engine**: SQLite (Local: `better-sqlite3` / Remote production: `@libsql/client` or Turso)
- **ORM & Migrations**: Drizzle ORM (`drizzle-orm`, `drizzle-kit`)
- **Validation**: Zod
- **Styling / UI**: Tailwind CSS v4, Lucide React
- **Auth**: NextAuth / Auth.js (v5) or Lucia with SQLite session adapter

---

## 📁 Project Directory Structure

```
├── src/
│   ├── app/                    # Next.js 15 App Router routes & layouts
│   │   ├── (auth)/             # Route group: login, signup, verify
│   │   ├── (dashboard)/        # Route group: authenticated workspace
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── api/                # Route handlers (webhooks & external APIs only)
│   │   ├── globals.css
│   │   └── layout.tsx
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Primitives (Button, Dialog, Input)
│   │   └── forms/              # Domain-specific client forms
│   ├── db/                     # Database layer
│   │   ├── schema/             # Drizzle table schemas (.ts per domain)
│   │   │   ├── users.ts
│   │   │   ├── subscriptions.ts
│   │   │   └── index.ts        # Re-export all schema objects
│   │   ├── migrations/         # Generated SQL migration files (drizzle-kit)
│   │   └── index.ts            # DB connection client singleton
│   ├── actions/                # Server Actions (Mutations & form submissions)
│   ├── lib/                    # Shared utilities, auth helpers, stripe/payment
│   └── types/                  # Shared TypeScript interfaces & Zod schemas
├── drizzle.config.ts           # Drizzle Kit CLI configuration
└── package.json
```

---

## ⚡ Development & Maintenance Commands

```bash
# Package & Dev
npm run dev               # Start development server
npm run build             # Build production bundle
npm run lint              # Run Next.js & ESLint checks
npm run typecheck         # tsc --noEmit

# Database & Migrations (Drizzle ORM)
npx drizzle-kit generate  # Generate migration SQL from schema changes
npx drizzle-kit migrate   # Apply pending migrations to SQLite DB
npx drizzle-kit studio    # Open interactive DB viewer UI
```

---

## 📐 Architecture & Coding Patterns

### 1. Server Components First
- Default to **React Server Components (RSC)** for all data-fetching pages.
- Query the SQLite database directly inside server components:
  ```typescript
  import { db } from "@/db";
  import { users } from "@/db/schema";
  
  export default async function DashboardPage() {
    const userList = await db.select().from(users);
    return <UserTable data={userList} />;
  }
  ```
- Use `"use client"` **only** for interactive leaves (forms with state, modals, event listeners).

### 2. Server Actions for All Data Mutations
- Place data mutations in `src/actions/*.ts` with `"use server"`.
- Validate all incoming payloads with **Zod** before touching the database:
  ```typescript
  "use server";
  import { z } from "zod";
  import { db } from "@/db";
  import { users } from "@/db/schema";
  import { revalidatePath } from "next/cache";

  const UpdateUserSchema = z.object({
    id: z.string().uuid(),
    name: z.string().min(2),
  });

  export async function updateUserAction(formData: FormData) {
    const parsed = UpdateUserSchema.safeParse(Object.fromEntries(formData));
    if (!parsed.success) {
      return { error: parsed.error.flatten().fieldErrors };
    }
    await db.update(users).set({ name: parsed.data.name }).where(eq(users.id, parsed.data.id));
    revalidatePath("/dashboard");
    return { success: true };
  }
  ```

### 3. Database & SQLite Best Practices
- **WAL Mode**: Ensure SQLite connection initializes with `PRAGMA journal_mode = WAL;` and `PRAGMA foreign_keys = ON;`.
- **Schema Separation**: Split table schemas into modular files under `src/db/schema/*.ts` and re-export via `src/db/schema/index.ts`.
- **Strict Timestamps**: Use integer timestamps (Unix epochs in ms) or ISO 8601 strings with helper transformers.

---

## 🚫 What We DON'T Do (And Why)

1. **DON'T create API routes (`/api/*`) for internal app mutations**:
   - *Why*: Server Actions provide type safety, automatic CSRF protection, and co-location with UI caching.
2. **DON'T perform database queries in `useEffect` or client components**:
   - *Why*: Avoids client-side waterfalls and protects backend credentials.
3. **DON'T edit migration files manually**:
   - *Why*: Always update schema definitions in `src/db/schema/` and run `npx drizzle-kit generate` to preserve migration consistency.
4. **DON'T use heavy ORMs that require binary engines (e.g. standard Prisma)**:
   - *Why*: Drizzle compiles to lightweight SQL queries with zero runtime overhead on edge/serverless runtimes.
