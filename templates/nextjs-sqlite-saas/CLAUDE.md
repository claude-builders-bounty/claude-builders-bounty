# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS Blueprint

This document sets the architectural constraints, style rules, and development guidelines for this repository. Every rule exists to ensure deterministic behavior, high performance, and zero runtime ambiguity.

---

## 1. Stack & Pinned Versions

- **Framework:** Next.js 15 (App Router, React 19 canary, Server Actions)
- **Language:** TypeScript 5.6+ (`strict: true`, `noImplicitAny: true`)
- **Database:** SQLite with `better-sqlite3` (local/VPS) or `@libsql/client` (Turso edge replication)
- **ORM / Query Builder:** Drizzle ORM (type-safe, zero overhead, single SQL generation)
- **Validation:** Zod v3 (strict input parsing for all Server Actions and route handlers)
- **Styling:** Tailwind CSS v4 + Lucide React (no heavy runtime CSS-in-JS)
- **Auth & Session:** Jose / iron-session (lightweight cookie sessions, no heavy external auth bloat)

---

## 2. Directory Structure

```
├── app/
│   ├── (auth)/               # Auth route group (login, register)
│   ├── (dashboard)/          # Authenticated app layout and pages
│   │   ├── dashboard/
│   │   └── settings/
│   ├── api/                  # Webhook and external endpoints only (not for internal queries)
│   ├── layout.tsx            # Root HTML shell
│   └── page.tsx              # Public landing page
├── db/
│   ├── schema/               # Modular Drizzle schemas (*.sql.ts)
│   │   ├── users.ts
│   │   ├── subscriptions.ts
│   │   └── index.ts          # Consolidated schema export
│   ├── migrations/           # Versioned migration SQL files (drizzle-kit generate)
│   ├── client.ts             # WAL-configured SQLite singleton connection
│   └── seed.ts               # Local development seed script
├── server/
│   ├── actions/              # Server Actions (mutations only, grouped by domain)
│   │   ├── auth.actions.ts
│   │   └── user.actions.ts
│   └── queries/              # Reusable read-only data queries (called directly by Server Components)
├── components/
│   ├── ui/                   # Primitive design tokens (button, input, modal)
│   └── features/             # Domain-specific components
├── lib/
│   ├── env.ts                # Validated environment variables (t3-env pattern)
│   └── errors.ts             # AppError custom domain error types
└── drizzle.config.ts         # Migration & database generator config
```

---

## 3. Database & SQL Rules

### SQLite Production Pragma Rules
SQLite MUST always be initialized with WAL mode and foreign key enforcement enabled:
```ts
// db/client.ts
import Database from 'better-sqlite3';
const sqlite = new Database(process.env.DATABASE_URL || 'sqlite.db');
sqlite.pragma('journal_mode = WAL');     // Concurrency: non-blocking reads while writing
sqlite.pragma('synchronous = NORMAL');   // Fast durability without corruption risk
sqlite.pragma('foreign_keys = ON');       // Enforce relational referential integrity
sqlite.pragma('busy_timeout = 5000');     // Avoid immediate busy errors under lock contention
```

### Migration Discipline
- **Never edit applied migrations:** Once a migration file in `db/migrations/` is created, it is immutable.
- Always use `pnpm db:generate` to produce schema migrations.
- Index all foreign keys and query filters: SQLite full-table scans destroy performance.

---

## 4. Component & Architecture Patterns

### Server Components by Default
- All pages and feature components are React Server Components (`RSC`) by default.
- Fetch data directly in the Server Component using server queries:
  ```tsx
  // app/(dashboard)/dashboard/page.tsx
  import { getOrganizationUsers } from '@/server/queries/users';
  export default async function DashboardPage() {
    const users = await getOrganizationUsers();
    return <UserList initialUsers={users} />;
  }
  ```

### Client Components are Leaf Nodes
- Add `'use client'` ONLY to components that need `useState`, `useEffect`, or browser event handlers.
- Never wrap large page containers in `'use client'`. Keep the client boundary as small and deep as possible.

### Server Actions for Mutations
- Every Server Action must validate inputs with Zod before touching the database.
- Always return a typed discriminated union: `{ success: true, data: T } | { success: false, error: string }`.
- Never throw unhandled exceptions across the action boundary.

---

## 5. Development Commands

| Task | Command |
|---|---|
| Run dev server | `pnpm dev` |
| Build for production | `pnpm build` |
| Run migrations | `pnpm db:migrate` |
| Generate new migration | `pnpm db:generate` |
| Drizzle Studio (DB UI) | `pnpm db:studio` |
| Type check & lint | `pnpm check` (`tsc --noEmit && eslint .`) |
| Seed database | `pnpm db:seed` |

---

## 6. What We Do NOT Do (And Why)

1. **NO Client-Side `useEffect` Data Fetching for Initial Render**
   * *Why:* Causes layout shifts, waterfall latency, and leaks business logic to the client. Use Server Components.
2. **NO Prisma or Heavy TypeORM**
   * *Why:* Prisma's query engine binary has massive cold-start penalties and memory overhead on lightweight/serverless nodes. Drizzle ORM compiles to plain zero-cost SQL.
3. **NO Raw Unsanitized SQL Queries**
   * *Why:* SQL injection vulnerability. All queries must use Drizzle ORM query builders or parameterized statements.
4. **NO Storing Secrets or Unhashed Passwords**
   * *Why:* Passwords must use `argon2id` or `scrypt`. Never log credentials or tokens.
5. **NO Catch-All Route Handlers for Simple CRUD**
   * *Why:* Server Actions eliminate the need for redundant boilerplate API routes for internal UI interactions.
