# CLAUDE.md

## 1. Stack & Versions

| Layer       | Choice                  | Version | Non-negotiable |
|-------------|-------------------------|---------|----------------|
| Framework   | Next.js (App Router)    | 15.x    | No Pages Router. Ever. |
| Language    | TypeScript              | 5.x     | Strict mode. No `any`. |
| Database    | SQLite via better-sqlite3 | latest | Synchronous driver. No async DB wrappers. |
| ORM         | Drizzle ORM             | latest  | Schema in TypeScript. Migrations in SQL. |
| Styling     | Tailwind CSS            | 4.x     | No CSS modules. No styled-components. |
| UI Library  | shadcn/ui               | latest  | Copy-paste components only. No npm package. |
| Auth        | better-auth             | latest  | Session-based. No JWT for auth. |
| Validation  | Zod                     | latest  | Single source of truth for types + validation. |
| Testing     | Vitest + Playwright     | latest  | Unit + E2E. No Jest. |
| Package Mgr | pnpm                    | 9.x     | Not npm. Not yarn. |

Node.js >= 20. SQLite DB file at `./data/app.db`. Git-ignored. Created on first migration.

## 2. Folder Structure

```
├── app/                        # Routes, layouts, pages — data-fetching lives here
│   ├── (auth)/                 # Route group: login, register, forgot-password
│   ├── (dashboard)/            # Route group: authenticated pages
│   │   ├── layout.tsx          # Auth-guarded layout
│   │   ├── projects/
│   │   │   ├── page.tsx        # List view — server component
│   │   │   ├── [id]/page.tsx   # Detail view — server component
│   │   │   ├── [id]/edit/page.tsx
│   │   │   ├── loading.tsx     # Suspense fallback
│   │   │   └── error.tsx       # Error boundary
│   │   └── settings/
│   ├── api/                    # Route handlers — webhooks and external integrations ONLY
│   │   └── webhooks/
│   └── layout.tsx              # Root layout
├── components/                 # Reusable UI only. No data fetching. No server components.
│   ├── ui/                     # shadcn/ui primitives (button, input, dialog)
│   └── [feature]/              # Feature-scoped composites (project-card.tsx, user-avatar.tsx)
├── lib/                        # Shared utilities, pure functions
│   ├── auth.ts                 # better-auth server config
│   ├── auth-client.ts          # better-auth client config
│   ├── validators.ts           # Zod schemas — shared between client and server
│   └── utils.ts                # cn() helper, formatters, constants
├── db/
│   ├── index.ts                # DB connection singleton (better-sqlite3 instance)
│   ├── schema.ts               # Drizzle table definitions — single file until >20 tables
│   ├── migrations/             # SQL migration files (0000_initial.sql, 0001_add_projects.sql)
│   └── seed.ts                 # Dev seed script
├── actions/                    # Server actions — one file per domain
│   ├── projects.ts             # createProject, updateProject, deleteProject
│   └── auth.ts                 # signIn, signUp, signOut
├── middleware.ts               # Auth session check, redirects
├── drizzle.config.ts
└── .env.local                  # DATABASE_URL, BETTER_AUTH_SECRET
```

**Ownership rules:**
- `app/` owns pages and data fetching. If it fetches data, it lives in `app/`.
- `components/` owns presentation. Takes props, renders UI, nothing else.
- `actions/` owns mutations. Every form submission calls a server action.
- `lib/` owns pure logic. No React imports. No DB imports. Exception: `lib/auth.ts`.
- `db/` owns everything database. Schema, connection, migrations, seeds.

## 3. Dev Commands

```bash
pnpm dev              # next dev --turbopack
pnpm build            # next build
pnpm start            # next start
pnpm lint             # next lint + tsc --noEmit
pnpm test             # vitest run
pnpm test:watch       # vitest
pnpm test:e2e         # playwright test
pnpm db:generate      # drizzle-kit generate — creates SQL migration from schema diff
pnpm db:migrate       # drizzle-kit migrate — applies pending migrations
pnpm db:seed          # tsx db/seed.ts
pnpm db:studio        # drizzle-kit studio — visual DB browser
```

Run `pnpm db:migrate` after every pull. Run `pnpm db:generate` after changing `db/schema.ts`.

## 4. SQL / Migration Conventions

**Naming:**
- Tables: plural snake_case → `users`, `project_members`, `api_keys`
- Columns: snake_case → `created_at`, `user_id`, `is_active`
- Foreign keys: `{referenced_table_singular}_id` → `user_id`, `project_id`
- Indexes: `idx_{table}_{columns}` → `idx_users_email`
- Booleans: `is_` or `has_` prefix → `is_active`, `has_verified_email`
- Timestamps: always INTEGER (Unix epoch seconds). No SQLite native datetime.

**Migration rules:**
- One migration per feature branch. Squash if needed before merge.
- **Never modify an existing migration file.** Create a new one to alter.
- Migration files are sequential: `0000_`, `0001_`, `0002_`. Drizzle generates these.
- Every table gets `id TEXT PRIMARY KEY` (use `crypto.randomUUID()`). No auto-increment integers — they leak count and break multi-tenancy later.
- Every table gets `created_at INTEGER NOT NULL DEFAULT (unixepoch())`.
- Every table gets `updated_at INTEGER NOT NULL DEFAULT (unixepoch())`.
- Use `STRICT` mode: `CREATE TABLE users (...) STRICT;`
- Enable WAL mode in `db/index.ts`: `db.pragma('journal_mode = WAL')`.

**Schema example (`db/schema.ts`):**
```typescript
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const projects = sqliteTable('projects', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  owner_id: text('owner_id').notNull().references(() => users.id),
  is_active: integer('is_active', { mode: 'boolean' }).notNull().default(true),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().defaultNow(),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().defaultNow(),
});
```

## 5. Component Patterns

- **Server components by default.** Every file in `app/` is a server component unless marked otherwise.
- Add `'use client'` only for: event handlers, useState, useEffect, browser APIs, third-party client libs.
- **Data fetching happens in `page.tsx` or `layout.tsx`** — pass data down as props.
- Never use `useEffect` to fetch data. Never use `fetch()` in client components to load page data.
- Every route segment with async data gets `loading.tsx` (skeleton UI) and `error.tsx` (error boundary).
- Forms use `<form action={serverAction}>`. Not `onSubmit` + `fetch`. Use `useActionState` for pending/error states.
- Use `useFormStatus` for submit button loading states.
- Colocate types with components if used nowhere else. Otherwise, put in `lib/validators.ts` as Zod schemas and infer types.

**File naming:**
- Components: kebab-case → `project-card.tsx`, `user-avatar.tsx`
- No `index.tsx` barrel files. Name the file what the component is.
- One component per file. Exception: small tightly-coupled pairs (e.g., `table.tsx` with Table + TableRow).

## 6. API Patterns

**API routes (`app/api/`) are for external integrations only:** webhooks, OAuth callbacks, cron endpoints.

- Internal mutations → server actions in `actions/`.
- Internal reads → direct DB queries in server components.
- Never build a REST API for the frontend to consume. This is not an SPA.

**When you need a route handler:**
```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const webhookSchema = z.object({ type: z.string(), data: z.unknown() });

export async function POST(req: NextRequest) {
  const body = await req.json();
  const parsed = webhookSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid payload' }, { status: 400 });
  }
  // process webhook...
  return NextResponse.json({ received: true }, { status: 200 });
}
```

- Always validate input with Zod. Never trust `req.json()` raw.
- Return proper HTTP status codes: 200 success, 400 bad input, 401 unauthed, 500 unexpected.
- Never catch errors silently. Log them. Rethrow if unrecoverable.

## 7. Auth Pattern

Using **better-auth** with SQLite session storage.

- `lib/auth.ts` — server-side auth instance. Configures providers, session table, callbacks.
- `lib/auth-client.ts` — client-side helpers (`signIn`, `signOut`, `useSession`).
- `middleware.ts` — checks session on requests to `(dashboard)` routes. Redirects to `/login` if no session.
- Session data lives in the `sessions` table. better-auth manages schema.
- **Never roll your own auth.** No custom JWT. No custom session tokens.
- Access `session.user` in server components via `auth.api.getSession({ headers: await headers() })`.
- Pass user data from layout to pages via props or React context — don't re-fetch session per page.

## 8. What We Don't Do (Anti-Patterns)

| Don't | Why |
|-------|-----|
| Use API routes for form submissions | Server actions are simpler, type-safe, and colocated with the form. |
| Use `useEffect` + `fetch` for data loading | Server components exist. Client-side fetching causes waterfalls and loading spinners. |
| Use `any` or `as unknown as X` | Fix the type. Zod validates at runtime; infer the type from the schema. |
| Use Prisma | Prisma's query engine is overkill for SQLite. Drizzle is lighter, faster, SQL-native. |
| Use `index.tsx` barrel exports | They break tree-shaking, cause circular deps, and make file search harder. |
| Use relative imports beyond `../` | Use `@/` path alias: `@/components/ui/button`, `@/db/schema`, `@/lib/utils`. |
| Store files in the database | Use local filesystem or S3. SQLite blob performance degrades past 100KB. |
| Use `Date` objects in the DB layer | Store Unix timestamps as integers. Convert to `Date` at the application boundary. |
| Use `console.log` in production code | Use a structured logger or delete `console.log` after debugging. |
| Build god components (>200 lines) | Split. Extract. Compose. If a component fetches + manages state + renders, it's three components. |
| Use `export default` | Use named exports — they're refactor-safe and searchable. Exception: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` (Next.js requires default exports). |
| Mutate data in GET requests or server component renders | Mutations happen in server actions or POST route handlers. Never on page load. |
| Use `npm install` or `yarn add` | This is a pnpm project. Use `pnpm add`. Lock file is `pnpm-lock.yaml`. |

## 9. Testing

**Vitest** for unit and integration tests. **Playwright** for E2E.

- Test files live next to source: `lib/utils.test.ts`, `actions/projects.test.ts`.
- E2E tests live in `e2e/` at project root: `e2e/auth.spec.ts`, `e2e/projects.spec.ts`.
- Use a separate test database: `./data/test.db`. Set via `DATABASE_URL` in test env.
- Run `pnpm db:migrate` before test suite (in `globalSetup`).
- Test server actions directly — import and call with a mocked session.
- Test components with Vitest + React Testing Library only for complex client-side logic.
- Don't unit test server components — cover them via E2E instead.
- Minimum coverage: actions 90%, lib 90%, components 50%, E2E covers all critical user flows.

**Test naming:** `describe('createProject')` → `it('creates a project with valid input')`, `it('rejects unauthenticated requests')`.

## 10. Git & PR Conventions

- Branch naming: `feat/add-projects`, `fix/login-redirect`, `chore/update-deps`
- Commit messages: conventional commits → `feat: add project CRUD`, `fix: handle null user in session`, `chore: bump drizzle-orm`
- One migration per branch. Squash migrations before merging if you made many during development.
- PR title = commit message format (squash merge).
- PRs must pass: `pnpm lint`, `pnpm test`, `pnpm build`. No exceptions.
- Never commit `data/app.db` or `.env.local`. Both are in `.gitignore`.
- Keep PRs under 400 lines diff. If bigger, split into stacked PRs.
- Every PR that touches `db/schema.ts` must include the corresponding migration file.

---

**When in doubt:** Server-first. Type-safe. Simple. No abstraction until the third use case.
