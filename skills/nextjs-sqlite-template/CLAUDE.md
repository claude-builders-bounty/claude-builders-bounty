# CLAUDE.md — Next.js 15 + SQLite SaaS Project

This CLAUDE.md defines the architecture, conventions, and constraints for a greenfield SaaS project using Next.js 15 (App Router) and SQLite (better-sqlite3 or Turso). Claude Code should follow these rules without asking clarifying questions.

## Stack & Versions

- **Runtime:** Node.js 20+ (use `.nvmrc` to pin version)
- **Framework:** Next.js 15 with React 19, App Router, Server Actions
- **Database:** SQLite via `better-sqlite3` (synchronous, simple) or `@libsql/ws` (Turso)
- **ORM:** None. Raw SQL only. No Prisma/TypeORM/Drizzle.
- **Auth:** NextAuth.js v5 (Auth.js) with Credentials provider + JWT
- **Styling:** Tailwind CSS (utility-first, no component libraries)
- **UI Components:** Build custom; shadcn/ui allowed if you install locally
- **State Management:** React server components + URL search params; no Redux/Zustand
- **Deployment:** Vercel (Edge/Node) or self-hosted (Docker)
- **Package Manager:** pnpm (strict node-linker=isolated)

## Folder Structure

```
/app
  /api                # Route handlers (no /pages)
    /auth
    /webhooks
    /...route.ts
  /dashboard          # Protected UI (server components by default)
    /page.tsx
    /settings
  /login
    /page.tsx
  /(auth)             # Auth group (public)
    /signup
    /forgot-password
/components
  /ui                 # Reusable UI primitives (shadcn-compatible)
  /features           # Feature-specific composite components
/lib
  /db                 # Database connection singleton
    /migrations       # SQL migration files (numbered)
    /schema.sql       # Current full schema (generated)
  /utils.ts           # Shared utilities (no React hooks)
  /validations.ts     # Zod schemas for inputs
  /constants.ts       # App constants
/public
  /images
  /fonts
/tests                # Integration tests (Vitest)
  /fixtures
  /helpers.ts
```

**Rules:**
- Server components default; add `'use client'` only when necessary.
- Route handlers in `/app/api/*/route.ts`; no custom servers.
- Components go in `/components`; collect feature-specific ones in subfolders.
- Database code lives in `/lib/db`; never import DB in React components (use Server Actions).

## SQL & Migration Conventions

1. **Write raw SQL only.** No query builder or ORM.
2. **Migrations are sequential, numbered files** in `/lib/db/migrations`:
   ```
   001_create_users_table.sql
   002_add_subscription_status_to_users.sql
   ```
   Each migration must be idempotent (safe to re-run) or include `down` SQL.
3. **Schema source of truth**: `schema.sql` is auto-generated from migrations. Do not edit directly.
4. **Naming:**
   - Tables: plural, lowercase (`users`, `subscriptions`, `orgs`).
   - Columns: snake_case (`created_at`, `updated_at`, `email`).
   - Indexes: `idx_table_column`.
5. **Foreign keys:** Use `REFERENCES` with `ON DELETE CASCADE` only when dependent data should be deleted. Prefer `ON DELETE RESTRICT`.
6. **Transactions:** Wrap multi-step writes in a transaction. Use `db.exec('BEGIN')` / `COMMIT` / `ROLLBACK`.
7. **Timestamps:** Every table has `created_at DATETIME DEFAULT CURRENT_TIMESTAMP` and `updated_at DATETIME`. Update `updated_at` via triggers or application logic.
8. **Never interpolate user input directly**. Use prepared statements with `?` placeholders:

   ```sql
   -- GOOD
   const stmt = db.prepare('SELECT * FROM users WHERE email = ?')
   const user = stmt.get(userEmail)

   -- BAD
   db.exec(`SELECT * FROM users WHERE email = '${userEmail}'`)
   ```

## Component Patterns

- **Server Components:** Default. Accept props (serializable only). No `useState`, `useEffect`.
- **Client Components:** Wrap only when interactivity needed. Keep minimal.
- **Data Fetching:** Use Server Actions or direct DB access in Server Components. Do not fetch from client via API routes unless necessary.
- **Forms:** Use Server Actions (`action={foo}`). Validate with Zod on server before DB writes.
- **Error Handling:** Throw errors in Server Actions; use `try/catch` and return `{ error: string }` objects to client.

**Example Server Action:**

```ts
// /lib/actions.ts
'use server'

import { revalidatePath } from 'next/cache'
import { db } from '@/lib/db'
import { signupSchema } from '@/lib/validations'

export async function createUser(formData: FormData) {
  const data = Object.fromEntries(formData)
  const parsed = signupSchema.parse(data)

  const stmt = db.prepare(`
    INSERT INTO users (email, password_hash, created_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
  `)
  stmt.run(parsed.email, hash(parsed.password))
  revalidatePath('/dashboard')
  return { success: true }
}
```

## What We Don't Do (And Why)

- **No TypeScript `any`**: always type server actions, db queries, and API responses. Use `zod` for runtime validation.
- **No large client bundles**: avoid importing heavy libraries in client components; keep under 100KB gzip per route.
- **No custom dotenv loading**: Next.js env vars only (`process.env.MY_VAR`). Validate at startup.
- **No `any` external API without cache**: use `fetch` with `next: { revalidate: <seconds> }`.
- **No global CSS overrides**: only utilities + Tailwind design tokens.
- **No `console.log` in production code**: use structured logger (`pino`) for server logs.

## Dev Commands

- `dev` — `next dev --turbo`
- `build` — `next build`
- `start` — `next start`
- `lint` — `next lint`
- `db:migrate` — run pending migrations (custom script in `/lib/db/migrate.ts`)
- `db:seed` — seed dev database (optional)
- `test` — `vitest`

---

## For Claude Code

When generating code:
- Follow the folder structure exactly.
- Use SQLite with parameterized queries.
- Prefer Server Actions over API routes.
- Add Zod validation for all inputs.
- Keep components small and composable.
- Write code that is understandable without additional context.

If unsure, default to the simplest, most standard approach that aligns with Next.js 15 conventions and SQLite's synchronous nature.
