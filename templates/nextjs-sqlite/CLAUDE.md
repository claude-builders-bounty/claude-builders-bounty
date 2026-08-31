# CLAUDE.md — Next.js 15 + SQLite SaaS

This is a single-tenant SaaS starter built with Next.js 15 App Router, TypeScript, and SQLite (`better-sqlite3`). The goal is boring, explicit, easily deployable code. Every rule below exists because it prevents a real class of bug or review round-trip.

## Stack & Versions

- **Next.js 15** with App Router. Use Server Components by default; mark Client Components only when interactivity is required.
- **TypeScript** with `strict: true`. Domain mistakes should fail at compile time.
- **React 19** where bundled by Next.js 15.
- **SQLite** via `better-sqlite3` for single-node deployments. Reason: zero network latency, trivial local dev, no Docker required.
- **Drizzle ORM** for typed queries and migrations. Reason: schema stays close to SQL; migration files are plain SQL and reviewable.
- **Zod** at trust boundaries: form inputs, API bodies, env vars, webhooks. Reason: validate once, propagate validated types.
- **Turbopack** (`next dev --turbopack`) for local dev. Reason: faster HMR.
- **Vitest** for unit tests; **Playwright** for E2E.

Do not silently introduce new dependencies. If a task needs a package, add it via `npm install <pkg>` and explain why in the PR description.

## Project Structure

```text
.
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Dashboard route group
│   ├── api/                # Route handlers
│   ├── layout.tsx          # Root layout, providers, fonts
│   └── page.tsx            # Marketing landing page
├── components/
│   ├── ui/                 # Primitive, reusable UI components
│   └── forms/              # Form-specific wrappers (always Client Components)
├── db/
│   ├── index.ts            # Single database connection instance
│   ├── schema.ts           # Drizzle schema
│   ├── migrations/         # Drizzle-generated SQL migrations
│   └── queries/            # All SQL/data access lives here
├── lib/
│   ├── auth/               # Auth helpers, password hashing, sessions
│   ├── env.ts              # Validated environment variables (Zod)
│   ├── validation/         # Shared Zod schemas
│   ├── server/             # Server-only helpers
│   └── client/             # Client-only helpers
├── tests/
│   ├── unit/               # Vitest tests
│   └── e2e/                # Playwright tests
├── drizzle.config.ts
├── next.config.ts
├── tsconfig.json
└── package.json
```

Rules:
- Route-specific components stay next to their route unless reused.
- Shared presentational primitives go in `components/ui`.
- Database access is restricted to `db/queries` or narrowly scoped server modules. Pages/components must not contain ad-hoc SQL.
- `lib` is for cross-cutting helpers; feature-specific helpers do not belong there.
- Never import server-only modules (DB, filesystem, secrets) into Client Components.

## Database Conventions

### Schema (`db/schema.ts`)

- Tables: plural, `snake_case` (`users`, `team_memberships`).
- Columns: `snake_case` (`created_at`, `user_id`).
- Primary keys: `id: text("id").primaryKey().$defaultFn(() => createId())` using `nanoid`/`uuid`.
- Timestamps: always include `created_at` and `updated_at`.
- Foreign keys: name them `<table>_id` and add `.references(() => table.id)` with `onDelete`/`onUpdate` explicitly stated.
- Enums: use SQLite `TEXT` with a Drizzle `$type` helper or a small const array + check constraint. Do not use native SQLite enums (they don't exist).
- Soft deletes: prefer explicit `deleted_at` timestamps over `is_deleted` booleans.

Example:

```ts
export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  hashedPassword: text("hashed_password").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});
```

### Migrations

- Generate migrations with `npm run db:generate` (wraps `drizzle-kit generate`).
- Review generated SQL before committing. Do not blindly commit migrations.
- Never edit an already-applied migration file. If a migration is wrong and has been deployed, create a new migration to fix it.
- Migration names should describe the change: `0001_add_user_sessions`, `0002_rename_billing_address`.

### Queries

- All queries are async functions exported from `db/queries`.
- Use Drizzle's typed query builder; avoid raw SQL unless necessary for performance.
- One query file per domain entity: `db/queries/users.ts`, `db/queries/invoices.ts`.
- Return validated shapes; never return raw DB rows directly to API consumers.
- Handle `better-sqlite3` synchronous API correctly: `db.prepare(...).get()/all()/run()`.

## Naming Conventions

- Files/folders: `kebab-case`.
- React components and exported types: `PascalCase`.
- Functions/variables/constants: `camelCase`.
- Environment variables: `UPPER_SNAKE_CASE`.
- Database tables/columns: `snake_case`.
- Boolean variables start with `is`, `has`, `can`, or `should`.

## Component Patterns

### Server Components (default)

- Fetch data directly in Server Components using `db/queries`.
- Pass serialized data to Client Components; do not pass functions or non-serializable objects.
- Keep Server Components free of `useState`, `useEffect`, and browser APIs.

### Client Components

- Mark with `"use client"` only when interactivity is required.
- Keep them as small and leaf-like as possible.
- Form handling: use React state + `action` prop calling a Server Action.
- Prefer `useTransition` for pending UI states when calling Server Actions.

### Forms

- Use Zod schemas shared between client and server.
- Server Actions validate input with Zod and return typed errors.
- Display errors next to fields; do not swallow validation failures.

## Server Actions

- Place in `app/<feature>/actions.ts` or `app/api` route handlers for public/webhook endpoints.
- Always `'use server'` at the top of action files.
- Re-validate paths with `revalidatePath` after mutations.
- Redirect with `redirect` only after successful mutations.
- Never expose raw DB errors to the client; log them server-side and return generic messages.

## Environment Variables

All env vars are validated in `lib/env.ts`:

```ts
import { z } from "zod";

export const env = z.object({
  DATABASE_URL: z.string().min(1),
  SESSION_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
}).parse(process.env);
```

- `DATABASE_URL` points to the SQLite file path (`file:./local.db`).
- `SESSION_SECRET` must be >= 32 chars in production.
- Prefix client-exposed vars with `NEXT_PUBLIC_`.

## Dev Commands

```bash
npm run dev              # next dev --turbopack
npm run build            # next build
npm run start            # next start
npm run test             # vitest run
npm run test:e2e         # playwright test
npm run db:generate      # drizzle-kit generate
npm run db:migrate       # drizzle-kit migrate
npm run db:studio        # drizzle-kit studio
npm run lint             # next lint
npm run typecheck        # tsc --noEmit
```

## What We Don't Do (and Why)

- **No ORM-only migrations.** We commit raw SQL migration files so they can be reviewed. Reason: prevents accidental destructive schema changes.
- **No client-side data fetching for initial page data.** Use Server Components + Server Actions. Reason: fewer requests, better SEO, simpler hydration.
- **No `any`.** If the type system fights back, fix the types. Reason: `any` hides bugs.
- **No secrets in Client Components.** Reason: client bundles are public.
- **No unvalidated `process.env` access outside `lib/env.ts`.** Reason: centralizes validation and fails fast on missing vars.
- **No ad-hoc SQL in pages/components.** Reason: data access patterns must be reusable and testable.

## Testing

- Unit-test `db/queries`, `lib/validation`, and pure helpers with Vitest.
- Mock `better-sqlite3` with an in-memory SQLite instance (`:memory:`) for query tests.
- E2E tests cover critical user flows: sign-up → create resource → view resource → sign-out.
- Run `npm run typecheck && npm run lint && npm run test` before pushing.

## Deployment

- Build target: Node.js (not static export).
- SQLite file must be on a persistent volume; do not use SQLite on serverless ephemeral filesystems for production.
- Run migrations as the container startup command: `npm run db:migrate && npm run start`.

## Common Tasks

### Add a new table

1. Edit `db/schema.ts`.
2. Run `npm run db:generate`.
3. Review `db/migrations/` SQL.
4. Create `db/queries/<table>.ts`.
5. Add unit tests in `tests/unit/`.

### Add a new API route

1. Create `app/api/<resource>/route.ts`.
2. Validate input with Zod.
3. Call `db/queries`.
4. Return typed JSON with `NextResponse.json`.

### Add a new page

1. Create route under `app/`.
2. Use a Server Component to fetch data.
3. Render a Client Component only if interactivity is needed.
