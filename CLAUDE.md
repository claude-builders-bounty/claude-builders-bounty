# CLAUDE.md — Next.js 15 + SQLite SaaS Stack Guide

This document defines the strict engineering standards, architectural decisions, and development workflows for this Next.js 15 SaaS application powered by SQLite and Drizzle ORM. Claude Code must adhere to these conventions for all code generation, refactoring, and database operations.

---

## 1. Stack & Pinned Versions

- **Framework**: Next.js 15 (App Router, Turbopack enabled)
- **Language**: TypeScript 5.x (Strict mode enabled, `noImplicitAny: true`)
- **UI & Styling**: React 19, Tailwind CSS v4, Lucide React icons, Shadcn UI (Radix primitives)
- **Database**: SQLite via `@libsql/client` (Turso) or `better-sqlite3` (Local file: `data/app.db`)
- **ORM**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Authentication**: NextAuth.js v5 (Auth.js) with SQLite adapter
- **Validation**: Zod v3.x (mandatory for all Server Actions and API inputs)

---

## 2. Directory Structure

```
├── data/
│   └── app.db               # Local SQLite database file (WAL mode enabled)
├── drizzle/                 # Generated SQL migrations (do not edit manually)
├── src/
│   ├── app/                 # Next.js App Router routes & layouts
│   │   ├── (auth)/          # Authentication route group (login, register)
│   │   ├── (dashboard)/     # Authenticated SaaS dashboard route group
│   │   │   └── layout.tsx   # Dashboard navigation and sidebar layout
│   │   ├── api/             # Webhook handlers and external REST endpoints
│   │   ├── layout.tsx       # Root layout (fonts, providers, theme)
│   │   └── page.tsx         # Public marketing landing page
│   ├── components/          # Reusable UI components
│   │   ├── ui/              # Primitive Shadcn/Radix components (Button, Input, etc.)
│   │   └── forms/           # Form components wrapping Server Actions
│   ├── actions/             # Server Actions (Mutations with 'use server')
│   ├── db/                  # Database client, schemas, and queries
│   │   ├── index.ts         # SQLite connection singleton
│   │   └── schema.ts        # Drizzle schema definitions
│   ├── lib/                 # Utility functions, helpers, and formatters
│   └── types/               # Shared TypeScript interfaces and types
├── drizzle.config.ts        # Drizzle migration and schema configuration
├── package.json
└── tsconfig.json
```

---

## 3. Essential Dev Commands

```bash
# Development server (with Turbopack)
npm run dev

# Production build & lint
npm run build
npm run lint

# Database operations (Drizzle)
npm run db:generate          # Generate SQL migration files from schema.ts
npm run db:migrate           # Apply pending migrations to the SQLite database
npm run db:push              # Push schema directly to DB (fast prototyping in local dev)
npm run db:studio            # Launch Drizzle Studio GUI on localhost:4983

# Tests
npm run test                 # Run Vitest test suite
```

---

## 4. Database & SQLite Conventions

1. **Connection Singleton**: SQLite is file-backed. Always use a cached singleton in `src/db/index.ts` to prevent multiple connection handles during Next.js hot reload.
2. **WAL Mode**: Always execute `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;` on connection initialization to support concurrent reads while writes occur.
3. **Primary Keys**: Use text-based nanoIDs or UUIDv4 for IDs (`text("id").primaryKey()`) to ensure safe distributed generation and prevent sequential ID enumeration attacks.
4. **Timestamps**: Store timestamps as Unix epoch integers (`integer("created_at", { mode: "timestamp" })`) for consistent sorting and zero timezone drift.
5. **Foreign Keys**: Always define `onDelete: "cascade"` or `onDelete: "set null"` explicitly on relational foreign keys.

---

## 5. Component & Data Fetching Patterns

- **Server Components by Default**: All components in `src/app/` are React Server Components (RSC). Fetch data directly in the component via async queries:
  ```tsx
  // Good: Direct DB query inside Server Component
  export default async function DashboardPage() {
    const user = await getCurrentUser();
    const projects = await db.query.projects.findMany({ where: eq(projects.userId, user.id) });
    return <ProjectList items={projects} />;
  }
  ```
- **Client Components ('use client')**: Use only for interactive UI elements that require browser hooks (`useState`, `useEffect`, `onClick`, event handlers). Keep them at the leaf nodes of the component tree.
- **Form Mutations**: Always use Server Actions with `useActionState` and Zod validation:
  ```ts
  // src/actions/projects.ts
  'use server';
  import { z } from 'zod';
  import { db } from '@/db';

  const CreateProjectSchema = z.object({
    name: z.string().min(2).max(50),
  });

  export async function createProjectAction(prevState: any, formData: FormData) {
    const parsed = CreateProjectSchema.safeParse({ name: formData.get('name') });
    if (!parsed.success) return { error: parsed.error.flatten().fieldErrors };
    
    await db.insert(projects).values({ name: parsed.data.name });
    revalidatePath('/dashboard');
    return { success: true };
  }
  ```

---

## 6. Critical Anti-Patterns to Avoid

| Anti-Pattern | Why It Is Prohibited | Proper Alternative |
| :--- | :--- | :--- |
| **Direct DB query in Client Component** | Leaks database credentials and bloats client JS bundle. | Fetch in a Server Component or call a Server Action. |
| **`useEffect` for initial data fetching** | Causes layout shift, request waterfalls, and flash of loading states. | Fetch data directly on the server in Server Components. |
| **Raw unparameterized SQL queries** | Creates severe SQL injection vulnerabilities. | Use Drizzle ORM query builders or `sql` tagged template literals. |
| **Omitting WAL mode in SQLite** | Causes `SQLITE_BUSY: database is locked` errors during concurrent requests. | Enable `PRAGMA journal_mode = WAL;` on the connection. |
| **Client-side auth checks only** | Easy to bypass by inspecting network traffic or disabling JavaScript. | Protect routes via Next.js Middleware and verify sessions in Server Actions. |

---

## 7. Rules for Claude Code

1. Never install heavy external state libraries (Redux, MobX). Rely on React Server State, URL query parameters, and Server Actions.
2. When creating new database tables, always update `src/db/schema.ts`, run `npm run db:generate`, and verify TypeScript exports.
3. Every API endpoint or Server Action must validate incoming input with **Zod** before touching the database.
4. Keep all components responsive (mobile-first using Tailwind CSS classes).
