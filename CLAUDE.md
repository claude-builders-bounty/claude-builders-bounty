# CLAUDE.md for Next.js 15 + SQLite (Drizzle ORM) SaaS

## 🏗️ Project Architecture & Tooling
- **Framework:** Next.js 15 (App Router)
- **UI Library:** React 19, Tailwind CSS v4, shadcn/ui
- **Database:** SQLite (LibSQL / Turso for production, `better-sqlite3` for local)
- **ORM:** Drizzle ORM
- **Validation:** Zod
- **TypeScript:** Strict mode enabled.

## 🚀 Core Development Commands
- `npm run dev` - Start the local Next.js development server.
- `npm run db:generate` - Generate Drizzle SQL migration files based on schema changes.
- `npm run db:push` - Push schema changes directly to the local SQLite database.
- `npm run db:studio` - Open Drizzle Studio to inspect the SQLite database visually.

## 📂 Folder Structure & Ownership Boundaries
- `/src/app` - Routing, Pages, and Layouts ONLY. No business logic.
- `/src/components/ui` - Reusable, dumb UI components (shadcn).
- `/src/components/features` - Feature-specific, stateful components.
- `/src/db/schema.ts` - Centralized Drizzle database schema definitions.
- `/src/db/index.ts` - Database connection initialization.
- `/src/actions` - Next.js Server Actions for all mutations.
- `/src/lib` - Utility functions and Zod schemas.

## 🧠 Database & Migration Conventions (SQLite + Drizzle)
1. **Schema Definition:** Define all tables in `src/db/schema.ts`. Use standard SQLite types (`integer`, `text`, `blob`, `real`).
2. **Boolean Emulation:** SQLite lacks a native boolean type. Use `integer({ mode: "boolean" })`.
   *Reason: Ensures type safety in TypeScript while adhering to SQLite constraints.*
3. **Primary Keys:** Use text-based UUIDs or NanoIDs for primary keys.
   *Reason: Auto-incrementing IDs in distributed/edge SQLite (like Turso) can lead to collisions.*
4. **Timestamps:** Always include `createdAt` and `updatedAt` on every table. Use `text("created_at").default(sql`CURRENT_TIMESTAMP`)`.

## ⚡ Server / Client Component Boundaries
1. **Default to Server:** Every component is a Server Component by default. 
   *Reason: Reduces client bundle size and allows direct, secure database access via Drizzle.*
2. **Use `"use client"` Sparingly:** Only use client components for interactivity (e.g., `useState`, `onClick`, `useEffect`). Push the `"use client"` directive as far down the component tree as possible.
3. **Data Fetching:** Fetch data directly in Server Components using Drizzle. Do NOT use `useEffect` for data fetching.
   *Reason: Server-side fetching is significantly faster and prevents waterfall network requests on the client.*

## 🔒 Authentication & Tenancy Rules
1. **Action Verification:** Every Server Action in `/src/actions` MUST verify the user's session before interacting with the database.
   *Reason: Server actions are exposed as public API endpoints. Missing auth checks lead to Immediate Insecure Direct Object Reference (IDOR) vulnerabilities.*
2. **Tenant Isolation:** In a multi-tenant SaaS, every database query MUST include a `WHERE tenantId = ?` clause.
   *Reason: Prevents accidental data leakage between different organizations.*

## 🛡️ Input Validation
1. **Zod Everywhere:** All Server Actions and API Routes must validate input using Zod before processing.
   *Reason: Prevents malformed data from reaching the database and guarantees type safety.*
2. **Safe Parsing:** Use `schema.safeParse()` instead of `schema.parse()`.
   *Reason: Avoids unhandled server crashes and allows returning graceful error messages to the client UI.*

## 🚫 Anti-Patterns to Avoid (CRITICAL)
1. **Client-Side Database Access:** NEVER instantiate the SQLite connection or call Drizzle inside a `"use client"` component.
   *Reason: This exposes your database credentials and structure to the browser, resulting in a total security compromise.*
2. **Raw SQL Concatenation:** NEVER concatenate strings to build SQL queries.
   *Reason: This creates immediate SQL Injection vulnerabilities. Always use Drizzle's query builder or `sql\`\`` template tags with parameterized inputs.*
3. **Leaking Secrets:** NEVER prefix environment variables with `NEXT_PUBLIC_` unless they are explicitly meant to be visible to the user (e.g., Analytics IDs).
   *Reason: Database URLs, API keys, and JWT secrets will be leaked in the client bundle.*
4. **Excessive Client State:** Do not use Redux or Zustand for data that can be fetched server-side.
   *Reason: Overcomplicates state management and defeats the purpose of the App Router architecture.*
