# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated, production-ready context file for Claude Code.
> Drop this into the root of any greenfield Next.js 15 App Router + SQLite project.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | Server Components, streaming, built-in optimizations |
| Language | TypeScript | 5.x (strict) | Catch bugs at compile time, not runtime |
| Database | better-sqlite3 | 11.x | Synchronous, zero-config, fastest SQLite driver for Node |
| ORM | Drizzle ORM | 0.36+ | Type-safe queries, migration CLI, works with better-sqlite3 |
| Auth | NextAuth.js v5 | 5.x (beta) | App Router native, multi-provider, edge-compatible |
| Styling | Tailwind CSS | 4.x | Utility-first, zero runtime cost |
| Validation | Zod | 3.x | Shared schemas for client + server + API routes |
| Testing | Vitest + Playwright | latest | Fast unit tests + real browser E2E |

**Do not substitute** unless the project explicitly requires it. These choices are made to minimize config hell and maximize Claude Code's ability to reason about the codebase.

---

## Project Structure

```
src/
├── app/                      # Next.js App Router
│   ├── (auth)/               # Auth route group (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/          # Protected route group
│   │   ├── layout.tsx        # Dashboard layout with sidebar
│   │   ├── page.tsx          # Dashboard home
│   │   └── settings/page.tsx
│   ├── api/                  # API route handlers
│   │   └── [...route]/route.ts
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Landing page
│   └── globals.css
├── components/
│   ├── ui/                   # Reusable primitives (Button, Input, Dialog, etc.)
│   └── features/             # Feature-specific composite components
├── db/
│   ├── index.ts              # Database connection singleton
│   ├── schema.ts             # Drizzle table definitions
│   ├── migrations/           # Generated SQL migrations
│   └── seed.ts               # Development seed data
├── lib/
│   ├── auth.ts               # NextAuth config
│   ├── validations/          # Zod schemas (shared client/server)
│   └── utils.ts              # cn(), formatDate(), etc.
├── hooks/                    # Custom React hooks
├── types/                    # Shared TypeScript types
└── env.ts                    # Type-safe env validation with @t3-oss/env-nextjs
```

**Rules:**
- Route groups `(auth)` and `(dashboard)` enforce layout separation without URL impact
- Every API route lives under `app/api/`
- Database code never leaks into components — go through server actions or API routes
- `components/ui/` is for generic, stateless primitives. Feature components go in `components/features/`

---

## Database Conventions

### Schema Definition (Drizzle)

```typescript
// db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),           // nanoid, never auto-increment
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull().default(sql`(unixepoch())`),
});
```

### Rules

1. **Primary keys are `text` nanoids** — never integer auto-increment. Predictable, URL-safe, no enumeration risk.
2. **Timestamps are `integer` unix epochs** with `{ mode: 'timestamp' }`. Never store ISO strings.
3. **Migrations are one-way** — always `drizzle-kit generate` then `drizzle-kit migrate`. Never edit migration files by hand.
4. **No raw SQL** — use Drizzle query builder. If you need raw SQL, put it in `db/` with a comment explaining why.
5. **Foreign keys are enforced** — `PRAGMA foreign_keys = ON` is set in the connection singleton.
6. **Seed data is idempotent** — `db/seed.ts` must be safe to run multiple times.
7. **Connection is singleton** — one `Database` instance per process, created in `db/index.ts`:

```typescript
// db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(process.env.DATABASE_URL || './data.db');
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');

export const db = drizzle(sqlite, { schema });
```

### Migration Workflow

```bash
# 1. Edit db/schema.ts
# 2. Generate migration
pnpm drizzle-kit generate
# 3. Review the generated SQL in db/migrations/
# 4. Apply
pnpm drizzle-kit migrate
```

**Never** `db.push` in production. Always generate → review → migrate.

---

## Component Patterns

### Server Components (default)

```tsx
// app/(dashboard)/page.tsx — Server Component
import { db } from '@/db';
import { DashboardCard } from '@/components/features/dashboard-card';

export default async function DashboardPage() {
  const stats = await db.select().from(users); // Direct DB query in server component
  return <DashboardCard stats={stats} />;
}
```

**Rule:** Start with Server Components. Only add `"use client"` when you need browser APIs (useState, useEffect, onClick, etc.)

### Client Components

```tsx
// components/ui/counter.tsx — Client Component
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Server Actions

```tsx
// app/(dashboard)/settings/action.ts
'use server';

import { db } from '@/db';
import { settings } from '@/db/schema';
import { revalidatePath } from 'next/cache';
import { updateSettingsSchema } from '@/lib/validations/settings';

export async function updateSettings(formData: FormData) {
  const raw = Object.fromEntries(formData);
  const data = updateSettingsSchema.parse(raw); // Always validate
  await db.update(settings).set(data).where(eq(settings.userId, data.userId));
  revalidatePath('/settings'); // Always revalidate after mutation
}
```

**Rules:**
- Server Actions are in `action.ts` files co-located with their route
- Always validate input with Zod before any mutation
- Always `revalidatePath()` or `revalidateTag()` after mutations
- Never pass sensitive data to the client

---

## Anti-Patterns (Do Not Do These)

| ❌ Anti-Pattern | ✅ Instead |
|---|---|
| `getServerSideProps` or `getStaticProps` | Use Server Components directly |
| `mysql2` or `pg` | Use `better-sqlite3` — this is a SQLite project |
| Prisma | Use Drizzle — lighter, faster, better SQLite support |
| `pages/` directory | Use `app/` directory (App Router) |
| `axios` | Use `fetch` — native, no dependency |
| `moment.js` | Use native `Intl.DateTimeFormat` or `date-fns` |
| Global state (Redux, Zustand) for server data | Use Server Components + RSC patterns |
| `useEffect` for data fetching | Use Server Components |
| `any` type | Use proper types or `unknown` with narrowing |
| `eval()`, `Function()`, dynamic code execution | Never. Hard-code logic. |
| Storing secrets in `.env.local` without validation | Use `env.ts` with `@t3-oss/env-nextjs` |
| `NEXT_PUBLIC_` for server-only secrets | Only use for truly public values |
| Inline styles (except dynamic Tailwind) | Use Tailwind classes |
| `console.log` in production code | Use a logger or remove before merge |

---

## Dev Commands

```bash
# Development
pnpm dev                    # Start dev server (turbo mode)
pnpm dev --turbopack        # With Turbopack bundler

# Database
pnpm db:generate            # Generate migration from schema changes
pnpm db:migrate             # Apply migrations
pnpm db:studio              # Open Drizzle Studio (visual DB browser)
pnpm db:seed                # Seed development data

# Testing
pnpm test                   # Run Vitest unit tests
pnpm test:e2e               # Run Playwright E2E tests
pnpm test -- --watch        # Watch mode

# Build & Deploy
pnpm build                  # Production build
pnpm start                  # Start production server
pnpm lint                   # ESLint
pnpm type-check             # TypeScript compiler check (no emit)

# Code Quality
pnpm format                 # Prettier format
```

---

## Environment Variables

```bash
# .env.example
DATABASE_URL=./data.db                # SQLite file path
NEXTAUTH_SECRET=                      # Generate: openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000     # Dev URL
GITHUB_ID=                            # OAuth provider
GITHUB_SECRET=                        # OAuth provider
GOOGLE_ID=                            # OAuth provider (optional)
GOOGLE_SECRET=                        # OAuth provider (optional)
```

**All env vars must be validated** in `src/env.ts` using `@t3-oss/env-nextjs`. If a var is missing, the app should fail to start, not silently use `undefined`.

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Files & dirs | `kebab-case` | `user-profile.tsx`, `api-handlers/` |
| React components | `PascalCase` | `UserProfile`, `DashboardCard` |
| Hooks | `use-camelCase` | `useAuth`, `useDebounce` |
| Server actions | `camelCase` verbs | `updateSettings`, `deleteUser` |
| DB tables | `snake_case` plural | `users`, `user_sessions` |
| DB columns | `snake_case` | `created_at`, `user_id` |
| Zod schemas | `camelCase` + `Schema` | `updateSettingsSchema` |
| Types | `PascalCase` | `User`, `ApiResponse` |
| API routes | `kebab-case` | `/api/user-profile` |
| CSS classes | Tailwind utilities | `bg-white dark:bg-gray-900` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |

---

## What We Don't Do (And Why)

1. **No microservices** — This is a single-process SQLite app. One server, one database. If you need scale, migrate to PostgreSQL first, then consider services.
2. **No WebSocket** — Use Server-Sent Events or polling. SQLite doesn't handle concurrent writes well enough for real-time sync.
3. **No file uploads to SQLite** — Store files on disk (with a CDN in front) or use S3. Store only the path in the database.
4. **No client-side database queries** — Every DB access goes through a Server Component, Server Action, or API Route.
5. **No CSS-in-JS** — Tailwind only. No styled-components, emotion, or CSS modules.
6. **No dynamic imports for critical path** — Only `next/dynamic` for below-the-fold content.
7. **No optimistic updates for mutations** — SQLite is synchronous; the mutation completes before the UI updates. Just revalidate.
8. **No ORM query builders other than Drizzle** — We chose Drizzle for type safety and SQLite compatibility. Don't add Prisma, Knex, or Kysely.

---

## Git Conventions

- **Commit format**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Branch naming**: `feat/short-description`, `fix/issue-number`
- **PRs require**: description, type-check pass, lint pass, at least one test
- **Squash merge** into main

---

## When Claude Code Gets Confused

If Claude starts:
- Creating `pages/` routes → redirect to `app/` directory
- Importing from `@prisma/client` → redirect to `@/db`
- Adding `useEffect` for data fetching → use Server Components
- Creating MySQL/Postgres schemas → this is SQLite, use `drizzle-orm/sqlite-core`
- Adding Redux or Zustand → use Server Components for state, URL params for client state
