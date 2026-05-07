# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Tech Stack (Opinionated)

| Layer | Choice | Rationale |
|---|---|---|
| Framework | **Next.js 15** (App Router) | Stable, full-stack, React 19, RSC-first |
| Database | **SQLite via turso/libsql** (or better-sqlite3) | Zero-infra, single-file, perfect for SaaS MVPs & edge |
| ORM / Query | **Drizzle ORM** | Type-safe, no hidden magic, raw SQL when needed, excellent SQLite support |
| Auth | **Lucia v3** or **NextAuth v5 (Auth.js)** | Lightweight, session-based, no vendor lock-in |
| Validation | **Zod** | Schemas at the edge — validate DB, API, forms from one source |
| UI | **shadcn/ui + Tailwind v4** | Accessible, composable, copy-paste ownership |
| Forms | **React Hook Form + Zod** | Performant, minimal re-renders |
| Styling | **Tailwind CSS v4** | Utility-first, CSS-in-JS alternative |

## Project Structure

```
src/
├── app/                          # Next.js App Router (file-based routing)
│   ├── (auth)/                   # Auth route group (layout wraps sign-in/up)
│   │   ├── sign-in/              #   /sign-in
│   │   ├── sign-up/              #   /sign-up
│   │   └── layout.tsx
│   ├── (dashboard)/              # Authenticated route group
│   │   ├── dashboard/            #   /dashboard
│   │   ├── settings/             #   /settings
│   │   └── layout.tsx            #   Auth guard, sidebar, nav
│   ├── api/                      # Route handlers (REST endpoints)
│   │   ├── auth/                 #   Auth endpoints
│   │   │   ├── sign-in/route.ts
│   │   │   └── sign-out/route.ts
│   │   ├── webhooks/             #   Stripe, Clerk, etc.
│   │   └── trpc/                 #   (optional: tRPC HTTP endpoints)
│   ├── layout.tsx                # Root layout (fonts, providers)
│   └── page.tsx                  # Landing page
├── components/
│   ├── ui/                       # shadcn/ui primitives (button, input, etc.)
│   ├── forms/                    # Form components (compose shadcn + RHF)
│   ├── layout/                   # Navbar, Sidebar, Footer
│   └── shared/                   # Feature-agnostic reusable components
├── db/
│   ├── schema/                   # Drizzle table definitions
│   │   ├── users.ts
│   │   ├── sessions.ts
│   │   ├── projects.ts
│   │   └── subscriptions.ts
│   ├── queries/                  # Encapsulated DB query functions
│   │   ├── users.ts
│   │   └── projects.ts
│   ├── migrations/               # Auto-generated Drizzle Kit migrations
│   ├── seed.ts                   # Seed data script
│   ├── index.ts                  # DB client singleton (libsql/better-sqlite3)
│   └── migrate.ts                # Migration runner
├── lib/
│   ├── auth.ts                   # Lucia/NextAuth config & helpers
│   ├── stripe.ts                 # Stripe client (if billing)
│   ├── email.ts                  # Resend / SendGrid client
│   └── utils.ts                  # cn(), formatDate(), etc.
├── server/                       # Server-only utilities (never imported in client)
│   └── actions/                  # Next.js Server Actions
│       ├── auth.ts               #   signIn, signOut, signUp actions
│       └── projects.ts           #   createProject, deleteProject
├── validations/                  # Zod schemas (shared between server & client)
│   ├── auth.ts
│   └── project.ts
├── hooks/                        # React hooks (client-only)
│   ├── use-auth.ts
│   └── use-media-query.ts
└── styles/
    └── globals.css               # Tailwind imports, CSS variables
```

### File Naming Conventions

| Pattern | Rule | Example |
|---|---|---|
| **Components** | PascalCase, `.tsx` | `UserAvatar.tsx`, `ProjectCard.tsx` |
| **Hooks** | camelCase, `use` prefix | `useAuth.ts`, `useDebounce.ts` |
| **DB Schemas** | kebab-case | `subscription-plans.ts`, `team-members.ts` |
| **Queries** | kebab-case | `team-members.ts` |
| **Actions** | camelCase, grouped by domain | `auth.ts`, `projects.ts`, `billing.ts` |
| **Route Handlers** | `route.ts` inside `app/api/[domain]/` | `app/api/auth/sign-in/route.ts` |
| **Validation Schemas** | camelCase, one file per domain | `auth.ts`, `project.ts` |
| **Utils** | camelCase, descriptive | `formatDate.ts`, `cn.ts` |
| **Types** | Co-located with domain or `types/*.ts` | `types/next-auth.d.ts` |

### Database Naming Convention

```
Tables:        plural_snake_case        → users, projects, team_members
Columns:       singular_snake_case      → first_name, created_at, stripe_customer_id
Primary Keys:  `id` (TEXT/UUID v7)      → id TEXT PRIMARY KEY
Foreign Keys:  [referenced_table]_id    → project_id, user_id
Timestamps:    created_at, updated_at   → managed by Drizzle `.$defaultNow()`
Soft Delete:   deleted_at (nullable)    → nullable timestamp, filter in queries
Indexes:       idx_[table]_[column]     → idx_users_email
```

## Database Migration Rules

### Tools
- **Drizzle Kit** (`drizzle-kit`): generate, push, migrate, introspect
- **SQLite** via `@libsql/client` (Turso) or `better-sqlite3` (local)

### Workflow

```bash
# 1. Edit schema files in src/db/schema/
# 2. Generate migration
pnpm db:generate

# 3. Review the generated SQL in src/db/migrations/
#    — ALWAYS review before applying
# 4. Apply migration locally
pnpm db:migrate

# 5. (Optional) Push schema directly (dev only)
pnpm db:push
```

### Rules (Non-Negotiable)

1. **Never edit migration files by hand.** If a migration is wrong, roll back and regenerate.
2. **One migration per schema change.** Squash before production deploys if too granular.
3. **All new columns must be nullable or have a default.** SQLite doesn't support `ALTER TABLE ADD COLUMN ... NOT NULL` without a default.
4. **Use `text` for all string types.** SQLite has no `varchar` distinction; Drizzle maps `text()` to `TEXT`.
5. **Prefer integer for booleans.** SQLite has no native boolean; use `integer({ mode: 'boolean' })`.
6. **Always add `.$defaultNow()` for `created_at`.** Never set it from application code.
7. **Prefer `uuidv7` over autoincrement IDs.** UUID v7 is time-ordered, index-friendly, and safe for multi-tenant.
8. **Keep `updated_at` triggers in the schema.** Use Drizzle's `.$onUpdate` or a custom hook.
9. **Seed data belongs in `src/db/seed.ts`** — run with `pnpm db:seed`.
10. **Migration files are committed to git.** They are the source of truth for production schema.

### Example Schema

```ts
// src/db/schema/projects.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';
import { users } from './users';

export const projects = sqliteTable('projects', {
  id: text('id').primaryKey().$defaultFn(createId),
  name: text('name').notNull(),
  slug: text('slug').notNull().unique(),
  description: text('description'),
  ownerId: text('owner_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  isArchived: integer('is_archived', { mode: 'boolean' }).notNull().default(false),
  createdAt: text('created_at').notNull().$defaultFn(() => new Date().toISOString()),
  updatedAt: text('updated_at').notNull().$defaultFn(() => new Date().toISOString()),
  deletedAt: text('deleted_at'),
});

export type Project = typeof projects.$inferSelect;
export type NewProject = typeof projects.$inferInsert;
```

## Dev Commands

```bash
# === Core ===
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint + Prettier check
pnpm typecheck        # tsc --noEmit
pnpm format           # Prettier write

# === Database ===
pnpm db:generate      # Generate Drizzle Kit migration
pnpm db:migrate       # Apply pending migrations
pnpm db:push          # Push schema directly (dev only, no migration file)
pnpm db:seed          # Run seed script
pnpm db:studio        # Open Drizzle Studio (GUI)
pnpm db:reset         # Drop all tables and re-migrate + seed

# === Testing ===
pnpm test             # Vitest (unit + integration)
pnpm test:e2e         # Playwright (E2E)
pnpm test:run         # Vitest single run (CI)
pnpm test:ui          # Vitest UI mode

# === Codegen ===
pnpm gen:component    # Scaffold a component (Turso)
```

## Patterns to Follow

### 1. Server Actions over API Routes
- Use **Next.js Server Actions** for form submissions and data mutations inside the app.
- Reserve `app/api/` route handlers for external-facing endpoints (webhooks, OAuth callbacks, mobile clients).
- Server Actions live in `src/server/actions/[domain].ts`.

### 2. Co-location, Not Barrel Files
- Test files go next to the module they test: `Button.tsx` → `Button.test.tsx`.
- Types live next to the component or in `types/` if shared app-wide.
- No `index.ts` barrel files unless it's a public library boundary.

### 3. Zod is the Single Source of Truth
- Define Zod schemas in `src/validations/`.
- Use `z.infer<typeof schema>` to derive TypeScript types — never hand-write DB types.
- Validate at every boundary: **Server Action input → DB write → RSC data fetch**.

### 4. RSC-First, Client Islands
- Default to **React Server Components**. Only add `'use client'` when you need interactivity (hooks, event handlers, browser APIs).
- Keep `'use client'` components as leaf nodes — don't wrap providers unnecessarily.

### 5. Error Handling
- Use `result` / `either` pattern for Server Action returns: `{ data: T, error: null } | { data: null, error: string }`.
- Catch errors at the route group boundary with `error.tsx`.
- Use `not-found.tsx` for 404 states per route group.

### 6. Auth in Layouts
- Auth check goes in the **dashboard layout**, not in every page.
- `(dashboard)/layout.tsx` calls `auth()` redirect; children are always authenticated.
- Public routes (`(auth)`) redirect away if already logged in.

### 7. Seed Data Must Be Idempotent
- `pnpm db:seed` should be safe to run multiple times — use `INSERT OR IGNORE` or upserts.
- Include at least one demo user, one project, and representative data for every feature.

### 8. Environment Variables
```env
# .env.local (gitignored)
DATABASE_URL="file:./data/saas.db"
AUTH_SECRET="..."
STRIPE_SECRET_KEY="..."
RESEND_API_KEY="..."

# .env.example (committed — no secrets)
DATABASE_URL="file:./data/saas.db"
AUTH_SECRET="sk-..."
STRIPE_SECRET_KEY="sk_test_..."
RESEND_API_KEY="re_..."
```

## Anti-Patterns (Do NOT Do)

### ❌ `'use client'` on the root layout
- Providers should be as deep as possible. Root layout should be a server component.

### ❌ Fetching directly from components
- Server Components use the DB directly via Drizzle queries. No `fetch()` for internal data.
- Exception: fetching from external APIs (Stripe, GitHub) — use server-side fetch in RSCs.

### ❌ `async useEffect` data loading
- No `useEffect` for data fetching on the client. Use Server Components or Server Actions.

### ❌ Barrel exports (`index.ts`)
- Leads to circular dependencies and bloated bundle sizes. Import directly from the module file.

### ❌ Raw SQL in components or actions
- All DB access goes through `src/db/queries/` functions. No `db.run(sql...)` outside of migrations.

### ❌ Autoincrement IDs exposed in URLs
- Use slugs (e.g., `/dashboard/projects/my-project`) or UUIDs. Never expose sequential IDs.

### ❌ Mixing App Router and Pages Router
- This is Next.js 15. Pages Router is legacy. All routes go in `app/`.

### ❌ Storing secrets in `.env` files committed to git
- Use `.env.local` for secrets. `.env.example` for docs-only.
- For production: use platform secrets (Vercel, Railway, Fly.io).

### ❌ Ignoring SQLite limitations
- No concurrent write-heavy workloads (SQLite is single-writer).
- No `ALTER COLUMN` / `DROP COLUMN` in older SQLite builds — Drizzle Kit handles this with recreates.
- No foreign key enforcement by default — run `PRAGMA foreign_keys = ON;` in `libsql` client init.

### ❌ Monolithic migration files in production
- Every deploy runs migrations. Keep them small, reviewed, and tested.
- Never run `db:push` in production — always use `db:migrate` with generated SQL files.

### ❌ Props drilling with React Context
- Use Server Components + `searchParams` for data passing. If you need client-wide state, use Zustand or Jotai, not React Context.

## Commit Conventions

Follow **Conventional Commits**:

```
feat: add project creation with team invites
fix: prevent double submission on sign-up form
chore: upgrade drizzle-kit to 0.28
refactor: extract billing queries to separate module
docs: add migration rollback instructions to CLAUDE.md
db: add subscription_plans table and seed data
```
