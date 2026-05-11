# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack

- **Framework**: Next.js 15 (App Router, React 19, Server Components by default)
- **Runtime**: Node.js 22 LTS
- **Database**: SQLite via `better-sqlite3` (dev/staging) or Turso `@libsql/client` (production)
- **ORM**: Drizzle ORM with `drizzle-kit` for migrations
- **Auth**: Auth.js v5 (`next-auth@beta`) with database session strategy
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Validation**: Zod for all inputs (forms, API, env vars)
- **Package manager**: pnpm

## Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm start        # Start production server
pnpm db:generate  # Generate migration from schema changes
pnpm db:migrate   # Apply pending migrations
pnpm db:studio    # Open Drizzle Studio (visual DB browser)
pnpm lint         # ESLint
pnpm typecheck    # tsc --noEmit
pnpm test         # Vitest unit + integration tests
pnpm test:e2e     # Playwright E2E tests
```

## Folder Structure

```
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Auth route group (login, register, forgot-password)
│   │   ├── (dashboard)/        # Authenticated route group
│   │   │   ├── layout.tsx      # Dashboard shell with sidebar
│   │   │   ├── page.tsx        # Dashboard home
│   │   │   └── settings/
│   │   ├── api/                # API routes (use sparingly — prefer Server Actions)
│   │   │   └── webhooks/       # Stripe, auth provider callbacks
│   │   ├── layout.tsx          # Root layout (html, body, providers)
│   │   └── page.tsx            # Landing page
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives (do not edit directly)
│   │   └── [feature]/          # Feature-specific components
│   ├── db/
│   │   ├── schema.ts           # Drizzle schema (single source of truth)
│   │   ├── index.ts            # DB client singleton
│   │   └── migrations/         # Generated SQL migrations (never hand-edit)
│   ├── lib/
│   │   ├── actions/            # Server Actions grouped by domain
│   │   ├── queries/            # Read-only data access functions
│   │   ├── validators/         # Zod schemas shared between client and server
│   │   └── utils.ts            # Small, pure utility functions
│   ├── hooks/                  # Client-side React hooks
│   └── types/                  # Shared TypeScript types
├── drizzle.config.ts
├── next.config.ts
└── .env.local                  # Never commit — template in .env.example
```

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files (components) | PascalCase | `UserAvatar.tsx` |
| Files (utils, hooks, actions) | camelCase | `useUser.ts`, `getUser.ts` |
| Route folders | kebab-case | `forgot-password/` |
| Route groups | `(name)` | `(dashboard)/` |
| DB tables | snake_case, plural | `user_sessions` |
| DB columns | snake_case | `created_at` |
| Zod schemas | camelCase + `Schema` suffix | `createProjectSchema` |
| Server Actions | camelCase + verb prefix | `createProject`, `deleteUser` |
| Environment variables | UPPER_SNAKE_CASE | `DATABASE_URL` |

## Database Rules

### Schema (`src/db/schema.ts`)

- This file is the single source of truth. Never write raw SQL for schema changes.
- Every table has: `id` (text, UUID default), `createdAt`, `updatedAt`.
- Use `text` for IDs (UUIDs), not auto-increment integers. SQLite has no native UUID — generate with `crypto.randomUUID()`.
- Timestamps are ISO 8601 strings stored as `text` (SQLite has no date type).
- All foreign keys use `references` with explicit `onDelete` behavior.
- Indexes go in the schema file, not in separate migrations.

```typescript
// Pattern for every table
export const projects = sqliteTable("projects", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  name: text("name").notNull(),
  ownerId: text("owner_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  createdAt: text("created_at").notNull().$defaultFn(() => new Date().toISOString()),
  updatedAt: text("updated_at").notNull().$defaultFn(() => new Date().toISOString()),
});
```

### Migrations

- Run `pnpm db:generate` after every schema change. Commit the generated SQL.
- Never hand-edit migration files.
- Never delete or rename migration files that have been applied.
- Test migrations against a fresh database before committing.

### Queries (`src/lib/queries/`)

- Read-only functions. No mutations.
- Always use Drizzle's query builder — no raw SQL.
- Return plain objects, not Drizzle row types. Map at the boundary.
- Paginate by default: every list query accepts `{ limit, offset }`.

### Server Actions (`src/lib/actions/`)

- All mutations go through Server Actions, not API routes.
- Every action validates input with Zod before touching the database.
- Every action checks authorization before mutating.
- Return `{ success: true, data }` or `{ success: false, error: string }` — never throw from actions.
- Wrap DB writes in transactions when multiple tables are involved.

```typescript
"use server";

import { z } from "zod";
import { db } from "@/db";
import { projects } from "@/db/schema";
import { createProjectSchema } from "@/lib/validators/project";
import { getAuthOrThrow } from "@/lib/auth";

export async function createProject(input: z.infer<typeof createProjectSchema>) {
  const session = await getAuthOrThrow();
  const parsed = createProjectSchema.safeParse(input);
  if (!parsed.success) return { success: false as const, error: parsed.error.message };

  const [project] = await db.insert(projects).values({
    name: parsed.data.name,
    ownerId: session.user.id,
  }).returning();

  return { success: true as const, data: project };
}
```

## Component Patterns

### Server Components (default)

- Fetch data directly — no `useEffect`, no loading states for initial data.
- Pass data as props to Client Components when interactivity is needed.
- Never import client-only libraries (useState, useEffect, browser APIs) in Server Components.

### Client Components

- Add `"use client"` directive only when the component needs interactivity.
- Keep Client Components small — wrap only the interactive part, not the whole page.
- Use `useActionState` for form submissions backed by Server Actions.

### Loading & Error States

- Every route segment with data fetching has a `loading.tsx`.
- Every route segment has an `error.tsx` with a retry button.
- Use Suspense boundaries for granular loading states within a page.

## What We Don't Do (and Why)

| Don't | Why | Instead |
|-------|-----|---------|
| Use API routes for data mutations | Server Actions are simpler, type-safe, progressively enhanced | Server Actions in `src/lib/actions/` |
| Use `prisma` | Prisma's query engine adds cold start latency and doesn't support SQLite edge well | Drizzle ORM — zero overhead, SQL-like API |
| Use `integer` for IDs | Auto-increment leaks info, is hard to merge across DB replicas | UUID `text` IDs with `crypto.randomUUID()` |
| Store dates as numbers | Unreadable in DB browsers, timezone confusion | ISO 8601 text strings |
| Hand-write SQL migrations | Drift between schema and reality, error-prone | `drizzle-kit generate` from schema |
| Use `getServerSession()` in Server Actions | Verbose, easy to forget | `getAuthOrThrow()` wrapper that throws 401 |
| Put business logic in API routes | Scatters logic, hard to reuse | Colocate in `lib/actions/` and `lib/queries/` |
| Use `any` type | Defeats TypeScript's purpose | `unknown` + Zod parsing, or proper types |
| Commit `.env.local` | Leaks secrets | `.env.example` with dummy values |
| Use `fetch` in Server Components for own API | Unnecessary network hop | Import queries/actions directly |

## Environment Variables

Validated at startup with Zod in `src/lib/env.ts`:

```typescript
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Required variables are documented in `.env.example`. If a variable is missing, the app crashes at import time with a clear message — not at runtime deep in a handler.
