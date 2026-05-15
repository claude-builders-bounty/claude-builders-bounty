# CLAUDE.md — Next.js 15 + SQLite SaaS

> **Opinionated rules for Claude Code on this Next.js 15 + SQLite SaaS project.**
> If you are unsure, follow these rules. Every rule here has a reason — if you
> want to change one, update this file and explain why in the commit message.

---

## 1. Stack & Versions

| Layer | Choice | Reason |
|-------|--------|--------|
| **Framework** | Next.js 15 (App Router) | Latest stable; `cacheComponents` stable |
| **Runtime** | Node.js 20 LTS | Supports edge + serverless; minimum version for Next.js 15 |
| **Language** | TypeScript 5.x | `strict: true`, no `any` |
| **Database** | SQLite (dev) → Turso (prod) | Zero-config local, cloud edge SQLite in production |
| **ORM** | better-sqlite3 (dev) + `@libsql/client` (Turso) | Synchronous API for development; Turso for edge |
| **Styling** | Tailwind CSS 3.x + shadcn/ui | Utility-first + accessible component library |
| **Forms** | React Hook Form + Zod | Type-safe validation |
| **Auth** | Lucia (or NextAuth v5) | Flexibile session management |
| **Testing** | Vitest + Playwright | Fast unit & E2E tests |

---

## 2. Folder Structure

```
src/
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Auth group (layout)
│   ├── (marketing)/            # Public pages
│   ├── (app)/                  # App group (dashboard, settings)
│   ├── layout.tsx              # Root layout
│   └── globals.css             # Tailwind imports + base styles
├── components/
│   ├── ui/                     # shadcn/ui component overrides
│   ├── features/               # Domain-specific compound components
│   └── providers/              # Client providers
├── lib/
│   ├── db/                     # Database client + schema
│   │   ├── client.ts           # better-sqlite3 (dev) / Turso (prod)
│   │   └── schema.sql          # Canonical SQL schema
│   ├── auth/                   # Lucia config + server helpers
│   ├── utils/                  # Pure functions (date, validation, etc.)
│   └── hooks/                  # Reusable React hooks
├── types/                      # Shared TypeScript types
└── utils/                      # General utility functions
```

### Rules

- **All routes are Server Components** by default. Use `"use client"` only when
  you need state, effects, or browser APIs.
- **Never put business logic in client components**. Lift it to a server action
  or a `lib/` helper.
- **One domain concept per file**. `app/dashboard/page.tsx` composes sub-components
  from `components/features/dashboard/`. Not the other way around.

---

## 3. SQL & Migration Conventions

### Tooling

- **Dev:** `better-sqlite3` — synchronous, zero-config, in-process.
- **Prod:** `@libsql/client` — async, connects to Turso (`LIBSQL_URL` env var).

### Schema Management

- All schema changes live in `src/lib/db/schema.sql`.
- Apply with `npm run db:apply` (never run raw SQL by hand).
- **Every schema change requires a migration file** in `src/lib/db/migrations/`.

### Migration File Format

```
src/lib/db/migrations/
└── YYYYMMDD_NNN__description.sql
```

Example: `20250615_001__add_users_table.sql`

```
-- Migration: Add users table
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Rules

- **Never use `SELECT *`.** Always list columns explicitly.
- **Always index foreign keys.**
- **Use TEXT for ISO-8601 timestamps** (never store as JavaScript Date).
- **SQLite uses `TEXT NOT NULL DEFAULT (datetime('now'))` for created_at.**

---

## 4. Component Patterns

### Server vs Client

```tsx
// ✅ src/app/dashboard/page.tsx  (Server Component)
import { getDashboardData } from '@/lib/db/queries';
export default async function DashboardPage() { ... }

// ✅ src/components/features/dashboard/refresh-button.tsx  ("use client")
'use client';
export function RefreshButton() { ... }
```

### Data Fetching

- Fetch in Server Components or server actions only.
- **Never use `fetch` in client components** — use Next.js Server Actions or route handlers.
- Route handlers go in `src/app/api/<resource>/route.ts`.

### Forms & Validation

```tsx
// ✅ Use server actions
import { z } from 'zod';
const schema = z.object({ email: z.string().email() });
export async function addUser(form: FormData) { ... }
```

### Rules

- **Zod schema = single source of truth.** Validate both server-side and client-side.
- **Never trust client data.** Server actions must re-validate.
- **Props are typed.** Use `interface` not `type` for object-shaped props.

---

## 5. What We Don't Do (And Why)

| Pattern | Why We Don't Do It |
|---------|-------------------|
| **Server-side rendering without cache tags** | Stale data; always declare `revalidate` or `no-store`. |
| **Server Actions for writes without revalidation** | Cache gets stale; add `revalidatePath()` or `revalidateTag()`. |
| **`fetch` without `revalidate` in server components** | Stale data; Next.js caches indefinitely by default. |
| **Database writes in client components** | Exposes query logic to the browser. |
| **Prisma / Drizzle ORM** | We use raw better-sqlite3 / libsql. Includes tooling overhead.