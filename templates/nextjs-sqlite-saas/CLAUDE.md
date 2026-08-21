# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated project configuration for Claude Code.
> Paste this file into the root of a Next.js 15 + SQLite project.

## Stack & Versions

- **Next.js**: 15.x (App Router, no Pages Router)
- **React**: 19.x
- **Database**: SQLite via `better-sqlite3` (local dev) or Turso (production)
- **ORM**: Drizzle ORM (not Prisma — Drizzle generates cleaner SQL and has better SQLite support)
- **Styling**: Tailwind CSS 4.x
- **TypeScript**: 5.x, strict mode
- **Runtime**: Node.js 22 LTS

Do not suggest Prisma, PlanetScale, MySQL, or any non-SQLite database. The entire point of this stack is zero-config local development with a single-file database.

## Folder Structure

```
src/
├── app/                    # App Router pages and layouts
│   ├── (auth)/             # Route group: auth pages (login, register)
│   ├── (dashboard)/        # Route group: authenticated app
│   ├── api/                # API routes
│   │   └── [resource]/     # RESTful resource endpoints
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── db/
│   ├── schema.ts           # All Drizzle table definitions
│   ├── migrations/         # SQL migration files (hand-written, not generated)
│   ├── index.ts            # Database connection singleton
│   └── seed.ts             # Seed script
├── lib/
│   ├── auth.ts             # Session management (use lucia-auth, not NextAuth)
│   ├── validations.ts      # Zod schemas for all inputs
│   └── utils.ts            # Shared utilities
├── components/
│   ├── ui/                 # Primitive components (Button, Input, etc.)
│   └── [feature]/          # Feature-scoped components
└── middleware.ts           # Auth middleware
```

Rules:
- Every file in `app/` must be a route, layout, or loading/error boundary. No utility functions in `app/`.
- `db/schema.ts` is the single source of truth for all tables. Never scatter table definitions across files.
- Feature components live under `components/[feature]/`, never under `app/`.

## SQL & Migration Conventions

- **All migrations are hand-written SQL files**, not auto-generated. This is non-negotiable. Auto-generated migrations from Drizzle's Kit produce unreadable diffs and hide intent.
- Migration files use the naming convention: `NNNN_description.sql` (e.g. `0001_create_users_table.sql`).
- Every migration has a corresponding `NNNN_description.down.sql` for rollback.
- Run migrations with `tsx db/migrate.ts` — never run `drizzle-kit push` in production.
- All tables use `INTEGER PRIMARY KEY` (not UUIDs — SQLite handles integer auto-increment natively and faster).
- Timestamps are stored as Unix epoch integers (`INTEGER`), not ISO strings. SQLite has no native datetime type; integer comparison is faster.
- Foreign keys: always `ON DELETE CASCADE` unless there's a specific reason not to.
- Never use `SELECT *` in application code. Always specify columns explicitly.

### Schema example:

```typescript
// db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at').notNull().default(sql`unixepoch()`),
  updatedAt: integer('updated_at').notNull().default(sql`unixepoch()`),
});
```

## Component Patterns

- Server Components by default. Only add `"use client"` when you need interactivity (useState, useEffect, event handlers).
- Data fetching happens in Server Components, not in client-side hooks.
- Never use `useEffect` for data fetching. Use Server Components or Server Actions.
- Forms use Server Actions (`"use server"` functions), not API routes.
- Validation: every Server Action starts with a Zod parse. If it fails, return typed errors.

### Server Action example:

```typescript
'use server';
import { z } from 'zod';
import { db } from '@/db';

const schema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

export async function createUser(input: unknown) {
  const data = schema.parse(input);
  await db.insert(users).values(data);
}
```

## Development Commands

```bash
npm run dev          # Start dev server (Next.js + Turbopack)
npm run build        # Production build
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed database
npm run db:studio    # Open Drizzle Studio
```

Always run `npm run typecheck` after making changes. Do not commit if it fails.

## What We Don't Do (and Why)

1. **No Prisma** — Prisma's SQLite migration story is fragile and its generated client adds 2MB+ to bundle size. Drizzle is lighter and generates actual SQL you can read.

2. **No NextAuth / Auth.js** — It abstracts away session management too aggressively. For SQLite-based SaaS, `lucia-auth` gives you direct control over session storage in SQLite.

3. **No UUID primary keys** — SQLite's `INTEGER PRIMARY KEY` is an alias for rowid, which is the fastest possible lookup. UUIDs as text keys are 3-5x slower in SQLite joins.

4. **No auto-generated migrations** — `drizzle-kit push` skips the migration review step entirely. In a SaaS with user data, every schema change must be reviewable and rollback-able.

5. **No client-side data fetching** — Next.js 15 Server Components are strictly better for initial page load. Client-side fetching means a loading spinner, which is worse UX than server-rendered content.

6. **No `SELECT *`** — Adding a column to a table silently changes the shape of `SELECT *` results. Explicit columns make schema changes safe and auditable.

7. **No environment variables without validation** — All env vars go through `src/lib/env.ts` which validates them with Zod at startup. Missing env vars crash the server immediately, not at first use.

8. **No barrel files** (`index.ts` that re-exports) — They break tree-shaking and make it impossible to trace imports. Import from the actual file.

## Testing

- Unit tests: Vitest (not Jest — Jest is slow with ESM/TypeScript)
- E2E: Playwright
- Every API route has at least one integration test
- Never mock the database. Use a separate test SQLite file (`test.db`) that gets recreated per test run
