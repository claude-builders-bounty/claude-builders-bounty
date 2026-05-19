# Next.js 15 + SQLite SaaS Project Guidelines

This document outlines the architecture, code conventions, database workflows, and dev patterns for this Next.js 15 + SQLite (Drizzle ORM) SaaS project.

---

## 🛠️ Stack & Versions
- **Framework**: Next.js 15.x (App Router, React 19, Strict Mode)
- **Database**: SQLite (local dev: `better-sqlite3`, production: `Turso / @libsql/client`)
- **ORM**: Drizzle ORM + `drizzle-kit` for migrations
- **Authentication**: Auth.js v5 (NextAuth) or Kinde
- **Styling**: Tailwind CSS v4
- **Validation**: Zod (strict schemas)

---

## 📂 Folder Structure

```
├── src/
│   ├── app/                 # App Router (Pages, Layouts, APIs)
│   │   ├── (auth)/          # Authentication route group
│   │   ├── (dashboard)/     # Authenticated SaaS dashboard
│   │   ├── api/             # REST/Webhook endpoint handlers
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Homepage / Marketing page
│   ├── components/          # Shared components
│   │   ├── ui/              # Atom components (buttons, inputs via shadcn)
│   │   └── dashboard/       # Dashboard-specific molecular components
│   ├── db/                  # SQLite connection and schemas
│   │   ├── schema/          # Drizzle schema split by domain
│   │   │   ├── users.ts
│   │   │   └── subscriptions.ts
│   │   ├── migrations/      # Auto-generated migrations (SQL)
│   │   └── index.ts         # DB Client Export (local/remote Turso toggle)
│   ├── lib/                 # Shared utilities and Server Services
│   │   ├── actions/         # Next.js Server Actions (Mutations)
│   │   │   ├── auth.ts
│   │   │   └── stripe.ts
│   │   ├── safe-action.ts   # Typed Server Actions wrapper (next-safe-action)
│   │   └── utils.ts         # Utility helpers (cn, formatting)
│   └── hooks/               # Strictly client-side React hooks
```

---

## ⚙️ Development Commands

- **Start Dev Server**: `npm run dev`
- **Build Production**: `npm run build`
- **Lint / Type Check**: `npm run lint` & `npx tsc --noEmit`
- **DB Migrations**:
  - Generate migration: `npx drizzle-kit generate`
  - Push/Apply schema (dev): `npx drizzle-kit push`
  - Run migrations (production): `npx tsx src/db/migrate.ts`
  - Database GUI: `npx drizzle-kit studio`

---

## 🗄️ SQLite & Drizzle Migration Rules

SQLite is fast and lightweight but lacks native support for complex `ALTER TABLE` operations (e.g., dropping columns, altering constraints). Follow these rules to prevent database locked or migration failures:

1. **Snake Case Naming**: Column names in DB must be `snake_case`. TypeScript bindings must be `camelCase`.
   ```typescript
   // Good
   createdAt: integer('created_at').notNull().default(sql`(unixepoch())`),
   ```
2. **Deterministic Defaults**: Use SQLite-compatible default functions.
   - For timestamps, use `sql`(unixepoch())` or `sql`(strftime('%s', 'now'))`. Avoid JS-dependent initializers like `Date.now()`.
3. **No Dynamic Alterations**: Do not manually modify files inside `src/db/migrations/`. Always let `drizzle-kit generate` produce the SQL migrations.
4. **Foreign Keys**: Always specify `onDelete: 'cascade'` explicitly for user/account-related dependent records to avoid orphan data due to SQLite's nested delete constraints.
5. **No Parallel DB Connections**: SQLite is a single-file DB. Ensure only one client instance is instantiated in server-less/edge-functions. Use global caching:
   ```typescript
   import { drizzle } from 'drizzle-orm/better-sqlite3';
   import Database from 'better-sqlite3';
   
   const globalForDb = globalThis as unknown as { conn: Database.Database | undefined };
   export const conn = globalForDb.conn ?? new Database('sqlite.db');
   if (process.env.NODE_ENV !== 'production') globalForDb.conn = conn;
   export const db = drizzle(conn);
   ```

---

## 🧱 Component & Data Fetching Patterns

1. **Server Components by Default**: All components are React Server Components (RSC) by default. Only add `"use client"` when component requires:
   - React State (`useState`, `useReducer`)
   - Event listeners (except standard form actions)
   - Browser APIs (`window`, `localStorage`)
2. **Async Data Fetching**: Fetch data directly inside Server Components using async/await. No more `useEffect` fetches!
   ```typescript
   // src/app/(dashboard)/billing/page.tsx
   export default async function BillingPage() {
     const subscriptions = await db.select().from(subscriptionsTable);
     return <BillingDashboard initialData={subscriptions} />;
   }
   ```
3. **Server Actions for Mutations**: All state modifications (creates, updates, deletes) must be executed via Next.js Server Actions.
   - Use `"use server"` at the top of action files.
   - Always validate inputs using `zod` inside actions.
   - Return strict, predictable objects: `{ success: boolean; data?: T; error?: string }`.
4. **Form Handling**: Use modern React 19/Next 15 form components or `useActionState` for seamless loading & validation transitions without manual loading states:
   ```typescript
   'use client';
   import { useActionState } from 'react';
   import { updateProfile } from '@/lib/actions/user';

   export function ProfileForm() {
     const [state, formAction, isPending] = useActionState(updateProfile, null);
     return (
       <form action={formAction}>
         <input name="username" required />
         <button type="submit" disabled={isPending}>Save</button>
         {state?.error && <p className="error">{state.error}</p>}
       </form>
     );
   }
   ```

---

## 🚫 What We Do NOT Do (Anti-Patterns)

1. **No Data Fetching inside Client Components**: Never fetch data using REST/GraphQL APIs on mount inside client components. Use Server Components to pass data down, or use `SWR` / `React Query` if live polling is absolutely required.
2. **No Raw SQL Strings**: Do not write raw SQL strings unless explicitly optimizing a complex query that Drizzle's query builder cannot resolve. This prevents SQL injection.
3. **No Direct SQLite Write Operations from Client**: Clients must never trigger DB writes directly. All operations pass through verified Server Actions.
4. **No Heavy Client-Side State**: Do not store complex global UI state unless absolutely necessary. Rely on Next.js Search Params (`?tab=billing`) for page-state to make layouts shareable and SSR-compatible.
5. **No Blocking Operations**: Do not perform heavy synchronous tasks inside route handlers or pages. Delegate computationally heavy tasks (e.g. video processing) to background workers or serverless queues.
