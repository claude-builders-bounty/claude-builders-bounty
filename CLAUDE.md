# CLAUDE.md — Next.js 15 + SQLite SaaS Template Guidelines

This document guides Claude Code on project structure, code patterns, database management, and development commands for this Next.js 15 App Router and SQLite (Drizzle ORM) SaaS template.

---

## 🛠 Stack & Versions

- **Framework**: Next.js 15 (App Router, React 19)
- **Database**: SQLite (via `better-sqlite3` for local sync, `libsql` for Turso in production)
- **Database Tooling**: Drizzle ORM (query builder) + Drizzle Kit (migration tool)
- **Language**: TypeScript 5+ (Strict mode enabled)
- **Styling**: Tailwind CSS v4 + Tailwind Merge
- **UI Components**: Shadcn UI (Radix UI primitives + Lucide React icons)

---

## 📁 Folder Structure

Follow this strict directory structure:

```text
├── src/
│   ├── app/                 # Next.js App Router (RSC by default)
│   │   ├── (auth)/          # Authentication routes (grouped)
│   │   ├── (dashboard)/     # Dashboard layouts & views (grouped)
│   │   ├── actions/         # Server Actions (mutations, schema validated)
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Landing page
│   ├── components/          # Reusable UI components
│   │   ├── ui/              # Shadcn components (atomic elements)
│   │   └── dashboard/       # Feature-specific dashboard components
│   ├── db/                  # SQLite connection & schema definitions
│   │   ├── schema.ts        # Database schema definitions
│   │   ├── index.ts         # DB Client instantiation
│   │   └── migrations/      # Drizzle-Kit auto-generated migrations
│   ├── hooks/               # Custom React hooks (client-side only)
│   ├── lib/                 # Utility files, contexts, and API clients
│   │   └── utils.ts         # Class name mergers and styling helpers
│   └── types/               # Globally shared TypeScript interfaces
```

---

## 🗄 SQL & Migration Conventions

1. **Schema Definition (`src/db/schema.ts`)**:
   - Every table must have `id` (text, primary key, uuid or nanoid), `created_at` (integer/text, defaults to current time), and `updated_at`.
   - Explicitly define SQLite constraints (e.g., `.notNull()`, `.unique()`).
   - SQLite tables use plural names (e.g. `users`, `organizations`, `subscriptions`).

2. **Foreign Keys**:
   - Define explicit foreign key constraints with `.references()`.
   - Always enable foreign key enforcement on client instantiation:
     ```typescript
     const sqlite = new Database('sqlite.db');
     sqlite.pragma('foreign_keys = ON'); // Crucial for SQLite referential integrity
     ```

3. **Migrations**:
   - **Generation**: Run `npm run db:generate` to output sql migrations into `src/db/migrations/`. Never edit migration SQL files manually.
   - **Execution**: Migrations must run on server bootstrap (in `src/db/index.ts` during initialization or via a separate migration runner script before startup).

---

## 🧩 Component & Data Fetching Patterns

1. **Server Components (RSC) by Default**:
   - All layouts, pages, and large structure containers must be Server Components.
   - Fetch data directly inside Server Components using Drizzle ORM:
     ```typescript
     // src/app/dashboard/page.tsx
     import { db } from "@/db";
     import { users } from "@/db/schema";
     
     export default async function Page() {
       const allUsers = await db.select().from(users);
       return <UserList users={allUsers} />;
     }
     ```

2. **Client Components (`"use client"`)**:
   - Use Client Components *only* when interactivity is required: browser APIs, local state (`useState`, `useReducer`), or React lifecycle events (`useEffect`).
   - Keep Client Components at the leaves of the render tree. Do not make entire page folders client-rendered.

3. **Mutations via Server Actions (`"use server"`)**:
   - Handle all database writes and mutations using Server Actions in `src/app/actions/`.
   - Always validate input schemas in Server Actions using a validator library like `zod`.
   - Handle authentication and authorization checks in every Action before running DB operations.
   - Trigger UI updates on success/failure using the React `useActionState` (or `useTransition`) hook in the Client Component.

---

## ❌ What We Don't Do (And Why)

- **❌ No API Routes (`/api/...`) for Internal Operations**: Do not write `/api/` endpoints just to fetch or mutate data for internal page components. Use direct database calls in RSCs and Server Actions. This saves HTTP roundtrip latency and simplifies auth.
- **❌ No Heavy ORMs (Prisma, TypeORM)**: SQLite works best with lightweight clients. Prisma adds unnecessary engine overhead that causes slow cold start times in serverless environments. Drizzle ORM is preferred for native speed, zero-overhead client libraries, and SQL-like transparency.
- **❌ No Client-Side Global State Managers (Redux, Zustand) by Default**: Use Next.js URL SearchParams or React Context for simple state sharing. RSCs handle data retrieval directly, rendering global client state redundant for typical SaaS templates.
- **❌ No Unparameterized Raw SQL**: Never construct SQL query strings via concatenation. Use Drizzle's parameterization or prepared statements to prevent SQL Injection vulnerabilities.
- **❌ No Concurrent Migrations**: Never run Drizzle migrations concurrently across multiple serverless instances. Run migrations in a single, isolated pre-deployment step.
