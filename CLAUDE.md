# CLAUDE.md — Next.js 15 + SQLite (better-sqlite3)

> Claude Code context file for a production SaaS built with Next.js 15 App Router and
> better-sqlite3. Every rule exists because a real bug happened. Delete a rule at
> your own risk. This file is the source of truth — when in doubt, re-read it.

---

## Stack (versions are locked for a reason)

| Dependency | Version | Why this exact version |
|-----------|---------|------------------------|
| Node.js | >= 20.11 | App Router requires `react-server-dom-webpack` APIs only in 20+ |
| Next.js | 15.x | App Router stable, Partial Prerendering, React 19 |
| better-sqlite3 | 11.x | Synchronous API is the only sane choice for server components |
| TypeScript | 5.5+ | Decorators, isolatedDeclarations, better ESM interop |
| Tailwind CSS | 3.4 | v4 is not production-ready for shadcn/ui |
| Zod | 3.x | Validation that infers types — never write types by hand |

**DO NOT upgrade Next.js across major versions without reading the migration guide.**
Next.js 15 removed `fetch` caching defaults — this WILL break your app if ignored.

---

## Project Structure

```
├── app/                         # Router: every folder = a route segment
│   ├── (marketing)/            # Route group: unauthenticated pages
│   │   ├── page.tsx            # Landing (uses / layout)
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (app)/                  # Route group: authenticated pages
│   │   ├── layout.tsx          # Auth guard + sidebar + org picker
│   │   └── [orgSlug]/          # Multi-tenant: all app routes scoped
│   │       ├── page.tsx        # Dashboard
│   │       ├── settings/page.tsx
│   │       └── billing/page.tsx
│   ├── api/                    # Route handlers — thin, delegate immediately
│   │   ├── auth/[...nextauth]/route.ts
│   │   └── stripe/webhook/route.ts
│   ├── layout.tsx              # Root layout: fonts, metadata, Clerk/NextAuth provider
│   ├── globals.css
│   └── not-found.tsx
├── components/                 # React components only
│   ├── ui/                     # shadcn/ui primitives — NEVER edit these
│   ├── forms/                  # react-hook-form + zod form components
│   └── [feature]/              # Domain components: invoice-table.tsx, etc.
├── lib/                        # Pure TS — no React imports, no JSX
│   ├── db/                     # Database layer
│   │   ├── connection.ts       # Singleton — the ONLY file that imports better-sqlite3
│   │   ├── schema.sql          # Raw DDL — the source of truth for tables
│   │   ├── migrate.ts          # Migration runner (idempotent, called at startup)
│   │   └── queries/            # One file per domain: users.ts, invoices.ts
│   ├── auth.ts                 # Session helpers, hashing, token verification
│   ├── validators.ts           # Zod schemas — shared between server actions and API
│   ├── rate-limit.ts           # In-memory rate limiter (IP-based, resets on restart)
│   └── utils.ts                # cn(), formatCurrency(), slugify()
├── hooks/                      # Client-side React hooks ONLY
│   └── use-org.ts              # e.g., current org from context
├── scripts/                    # One-off CLI scripts (seed, backup, data fix)
│   ├── seed.ts
│   └── backup.ts
├── public/                     # Static assets served from /
├── .env.local                  # Secrets — NEVER commit
├── .env.example                # Template without secrets
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

**Key rules that will save you hours:**

1. `lib/` has ZERO React imports. If you're importing `"react"` in `lib/`,
   you've made a mistake. Move it to `components/` or `hooks/`.

2. `app/api/` route handlers are thin wrappers. Never put SQL queries directly
   in `route.ts`. Delegate to `lib/db/queries/`. This keeps route handlers
   testable and swappable.

3. `components/ui/` is shadcn/ui. These files are generated. Edit them and you'll
   hate yourself when you need to update. Override styles in your own components.

4. Multi-tenant routes use `[orgSlug]` — the org is in the URL, not a cookie or
   header. This makes every page deep-linkable and avoids hydration mismatches.

---

## Naming Conventions

| Thing | Convention | Example | Why |
|-------|-----------|---------|-----|
| Files & folders | `kebab-case` | `user-settings/page.tsx` | Next.js routing convention |
| React components | `PascalCase` | `UserAvatar.tsx` | JSX requires capitalized tags |
| Server actions | `camelCase` + verb | `createInvoice()` | Distinguishable from React components |
| Database tables | `snake_case` plural | `user_sessions` | SQL standard, avoids reserved words |
| Database columns | `snake_case` | `created_at`, `org_id` | Consistent with table naming |
| TypeScript types | `PascalCase` | `InsertUser`, `UserRow` | Type naming convention |
| Zod schemas | `camelCase` + `Schema` | `createUserSchema` | Clearly identifies as validation |
| CSS classes | Tailwind only | `className="flex gap-2"` | No CSS modules, no styled-jsx |
| Environment vars | `UPPER_SNAKE` | `DATABASE_PATH` | Shell convention |
| Constants | `UPPER_SNAKE` | `MAX_LOGIN_ATTEMPTS` | Immediately recognizable |

**Variables and functions:**
- Functions that return data: `getUser()`, `listInvoices()`, `findOrgBySlug()`
- Functions that mutate: `createUser()`, `updateSettings()`, `deleteSession()`
- Boolean flags: `isLoading`, `hasPermission`, `shouldRetry`
- Event handlers: `handleSubmit`, `handleDelete`, `onToggle`

---

## Core Architectural Rules

### Server Components are the default

Everything starts as a Server Component. You add `"use client"` ONLY when you
need one of these three things:

1. `useState` / `useReducer` (client state)
2. `useEffect` / lifecycle (side effects in browser)
3. Browser-only APIs (`window`, `localStorage`, event handlers like `onClick`)

**Why:** Server Components run at build/request time on the server. They can
directly access the database, read files, and fetch from internal APIs without
REST overhead. Defaulting to Server Components eliminates an entire class of
loading-spinner-and-refetch bugs.

### Data flows down, not across

```
┌─────────────────────────────────────┐
│ Server Component (page.tsx)          │
│ ├─ Reads DB directly                 │
│ ├─ Owns all data fetching            │
│ └─ Passes data as props ──────────┐  │
└────────────────────────────────────┘  │
                                       ▼
┌─────────────────────────────────────┐
│ Client Components (below)           │
│ ├─ Receive data as props            │
│ ├─ Call server actions to mutate    │
│ └─ NEVER fetch directly             │
└─────────────────────────────────────┘
```

A page fetches data. Client components receive it. Client components mutate via
server actions. Never use `fetch()` in a client component to load data a parent
already has.

### Server Actions are the mutation boundary

```typescript
// ✅ DO: Server action in a separate file
// lib/actions/invoices.ts
"use server"

export async function createInvoice(formData: FormData) {
  const session = await getSession()   // Auth check first
  if (!session) throw new Error("Unauthorized")

  const parsed = createInvoiceSchema.parse(Object.fromEntries(formData))
  const db = getDb()
  return db.transaction(() => {
    const invoice = insertInvoice(db, { ...parsed, orgId: session.orgId })
    auditLog(db, session.userId, "invoice.created", invoice.id)
    revalidatePath(`/${session.orgSlug}`)
    return invoice
  })()
}
```

**Rules for server actions:**
- Always `"use server"` at the top of the file (not inline in a component)
- Auth check is the FIRST line — before validation, before anything
- Use Zod to parse input — never trust `formData.get("foo")` directly
- Wrap mutations in `db.transaction()` when touching multiple tables
- Call `revalidatePath()` or `revalidateTag()` after state-changing operations
- Return the created/updated entity so the client can optimistically update

---

## Database Rules (better-sqlite3 specific)

### Connection Singleton

There is exactly ONE file that imports `better-sqlite3`: `lib/db/connection.ts`.
Everything else gets the db instance from this file.

```typescript
// lib/db/connection.ts
import Database from "better-sqlite3"
import path from "path"

let db: Database.Database | null = null

export function getDb(): Database.Database {
  if (!db) {
    const dbPath = process.env.DATABASE_PATH || path.join(process.cwd(), "data.db")
    db = new Database(dbPath, {
      // WAL mode enables concurrent reads during writes — essential for serverless
      // but in better-sqlite3 it means parallel read queries don't block each other
    })
    db.pragma("journal_mode = WAL")
    db.pragma("busy_timeout = 5000")  // Wait 5s instead of immediate SQLITE_BUSY
    db.pragma("foreign_keys = ON")    // Not default in SQLite!
    db.pragma("synchronous = NORMAL") // Safe in WAL mode, 10x faster writes
  }
  return db
}
```

**Why these pragmas:**
- `WAL` (Write-Ahead Logging): Readers never block writers, writers never block
  readers. Without WAL, any concurrent access will throw `SQLITE_BUSY`.
- `busy_timeout = 5000`: Instead of crashing on lock contention, SQLite waits
  up to 5 seconds. Prevents transient errors under load.
- `foreign_keys = ON`: SQLite has foreign key support but it's OFF by default.
  Turn it on or you WILL get orphaned rows.
- `synchronous = NORMAL`: Safe in WAL mode. The default `FULL` syncs twice per
  write — a 10x performance penalty for no gain.

### Schema management — raw SQL, not ORM migrations

We use raw SQL files for migrations. No Drizzle, no Prisma, no Knex. Here's why:

- better-sqlite3 has NO async API. Drizzle's async query builder only works with
  libsql/Turso, not better-sqlite3. Using drizzle-orm with better-sqlite3
  requires the sync driver wrapper which is poorly documented and brittle.
- Raw SQL means you always know exactly what query runs. No generated SQL
  surprises in production.
- SQLite's SQL dialect is simple. The abstraction cost exceeds the benefit.

```sql
-- lib/db/schema.sql
-- Source of truth for database structure. Idempotent: uses IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS orgs (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
  id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email           TEXT NOT NULL UNIQUE,
  password_hash   TEXT NOT NULL,
  display_name    TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS org_members (
  org_id   TEXT NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role     TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  PRIMARY KEY (org_id, user_id)
);

-- Add indexes on foreign keys that appear in WHERE clauses
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON org_members(user_id);
```

**Migration rules:**
1. Each migration is a `.sql` file in `lib/db/migrations/`, numbered sequentially:
   `001_initial.sql`, `002_add_billing.sql`, `003_add_audit_log.sql`
2. Migrations run at app startup via `lib/db/migrate.ts`, which reads the
   `schema_version` table and applies only new files.
3. Migrations MUST be additive-only. Never `DROP COLUMN` or `ALTER TABLE ... DROP`
   in a migration that has already run in production. Add a new column, deploy,
   then drop the old column in a later migration.
4. Every migration is wrapped in a transaction. If a migration fails, it rolls
   back completely.
5. Test migrations with a copy of the production database before deploying.

### Query patterns

```typescript
// lib/db/queries/users.ts
import { getDb } from "../connection"

export function getUserByEmail(email: string) {
  // Parameterized query — ALWAYS use ? placeholders
  return getDb().prepare("SELECT * FROM users WHERE email = ?").get(email) as UserRow | undefined
}

export function getOrgWithMembers(orgId: string) {
  // JOINs are fine in SQLite — it handles them well up to ~10 tables
  return getDb().prepare(`
    SELECT o.*, json_group_array(json_object('userId', om.user_id, 'role', om.role)) as members
    FROM orgs o
    LEFT JOIN org_members om ON om.org_id = o.id
    WHERE o.id = ?
    GROUP BY o.id
  `).get(orgId)
}

export function createUser(user: InsertUser) {
  // Timestamps set by SQLite, not application code — consistency guarantee
  const stmt = getDb().prepare(`
    INSERT INTO users (email, password_hash, display_name)
    VALUES (@email, @password_hash, @display_name)
  `)
  // Named parameters are safer than positional for INSERT with many columns
  return stmt.run(user)
}
```

**Rules:**
- NEVER use string interpolation to build queries. Parameterized queries ONLY.
- The query function returns `unknown`. Always cast to your type. TypeScript
  cannot know what the SQL returns.
- Use named parameters (`@param`) for INSERT/UPDATE with more than 3 columns.
  Use positional (`?`) for simple SELECT/WHERE.
- `json_group_array()` and `json_object()` are your friends for nested data.
  SQLite has great JSON support built in.

### Transactions

```typescript
export function transferProjectOwnership(projectId: string, fromUserId: string, toUserId: string) {
  const db = getDb()
  return db.transaction(() => {
    // All-or-nothing: if any statement fails, everything rolls back
    db.prepare("DELETE FROM project_members WHERE project_id = ? AND user_id = ?").run(projectId, fromUserId)
    db.prepare("INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, 'owner')").run(projectId, toUserId)
    db.prepare("UPDATE project_members SET role = 'member' WHERE project_id = ? AND user_id = ?").run(projectId, fromUserId)
  })()
}
```

**Always use transactions when** modifying more than one row or more than one
table. SQLite without a transaction wraps every statement in its own implicit
transaction — slow and leaves partial state on error.

---

## API Route Conventions

```typescript
// app/api/stripe/webhook/route.ts
import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    // 1. Verify — signature, auth, rate limit
    const signature = req.headers.get("stripe-signature")
    if (!signature) return NextResponse.json({ error: "Missing signature" }, { status: 400 })

    // 2. Parse — Zod, never manual casting
    const body = await req.text()
    const event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!)

    // 3. Delegate — to lib/, not inline
    await handleStripeEvent(event)

    // 4. Respond — always return JSON, never null
    return NextResponse.json({ received: true })
  } catch (error) {
    console.error("Stripe webhook error:", error)
    return NextResponse.json({ error: "Internal error" }, { status: 500 })
  }
}
```

**Rules for API routes:**
- Every route handler has exactly 4 steps: Verify → Parse → Delegate → Respond
- Always return `NextResponse.json()`. Returning `undefined` causes hanging requests.
- Webhooks respond with 200 BEFORE processing long tasks (Stripe retries on non-200).
- Never do database writes in a GET handler.

---

## Validation (Zod — one source of truth)

```typescript
// lib/validators.ts
import { z } from "zod"

export const createOrgSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(50),
  slug: z.string()
    .min(3)
    .max(30)
    .regex(/^[a-z0-9-]+$/, "Slug can only contain lowercase letters, numbers, and hyphens")
    .refine(async (slug) => !(await orgSlugExists(slug)), "This slug is already taken"),
})

// Infer the type — never write types by hand
export type CreateOrg = z.infer<typeof createOrgSchema>
```

**Rules:**
- Schemas in `lib/validators.ts`, shared between server actions and API routes.
- Every user-input boundary (form, API, webhook) goes through a Zod schema.
- Use `.refine()` for async validation (unique email, slug availability).
- Infer types from schemas with `z.infer`. Never write a type that Zod already
  generates for you.

---

## Form Patterns

```typescript
// components/forms/create-org-form.tsx
"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { createOrgSchema, type CreateOrg } from "@/lib/validators"
import { createOrg } from "@/lib/actions/orgs"

export function CreateOrgForm() {
  const form = useForm<CreateOrg>({
    resolver: zodResolver(createOrgSchema),
    defaultValues: { name: "", slug: "" },
  })

  async function onSubmit(data: CreateOrg) {
    const result = await createOrg(data)
    if (result.error) {
      form.setError("root", { message: result.error })
    }
    // Success — parent revalidates and redirects
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* form fields */}
    </form>
  )
}
```

**Rules:**
- react-hook-form + zodResolver — no other form library needed.
- Server-side validation (Zod in the action) is mandatory. Client-side is UX only.
- Forms call server actions, never fetch().
- Use `useFormStatus()` for submit button loading state — it works without
  prop drilling.

---

## Error Handling

```
Component tree:
┌──────────────────────────┐
│ page.tsx (Server)        │  ← Wrap in error boundary (error.tsx)
│ └── <Suspense>          │  ← loading.tsx handles loading state
│     └── <ClientComponent>│
│         └── try/catch    │  ← Only for expected errors (network, parsing)
└──────────────────────────┘
```

**Rules:**
1. **`error.tsx`** files handle UNEXPECTED errors in Server Components. Next.js
   automatically catches unhandled errors and renders the nearest `error.tsx`.
2. **`loading.tsx`** handles loading states — never manually manage loading
   booleans in data-fetching components.
3. **`not-found.tsx`** handles 404s — call `notFound()` in your page when a
   database lookup returns null.
4. Server actions return `{ error: string } | { data: T }` discriminated unions.
   Never throw from a server action — the client can't catch it.
5. API routes return error JSON with proper status codes. Never return HTML
   error pages from API routes.

---

## What We Don't Do (and why)

| Anti-pattern | Why it's banned |
|-------------|-----------------|
| `any` type | Hides bugs from the compiler. Use `unknown` and narrow. |
| Raw SQL in components | Database code in React components breaks testing and SSR. |
| `useEffect` for data fetching | Causes waterfall requests, flash of empty state, race conditions. |
| CSS modules or styled-jsx | Tailwind is the single styling system. Two systems = inconsistency. |
| API calls between server components | Call the DB directly. REST calls to your own API from SSR adds latency. |
| Next.js `fetch()` without `cache: "no-store"` | Next 15 changed the default. Explicit is always better. |
| `process.env` in client components | Must be `NEXT_PUBLIC_` prefixed. Otherwise it's `undefined` in browser. |
| `Date.now()` in DB queries | SQLite's `datetime('now')` is consistent within a transaction. JS Date is not. |
| ORMs (Drizzle, Prisma) with better-sqlite3 | The sync adapter is poorly maintained. Raw SQL + TypeScript types is simpler. |
| `as` type assertions (except for DB results) | Circumvents the type checker. Use Zod `.parse()` and proper type guards. |
| `export default` for utilities and DB queries | Named exports enable better tree-shaking and IDE auto-import. |

---

## Dev Commands

```bash
# Development
npm run dev              # Start Next.js dev server on port 3000
npm run build            # Production build (runs type check + lint)
npm run start            # Start production server
npm run typecheck        # tsc --noEmit — catches type errors without building

# Database
npm run db:migrate       # Apply pending migrations
npm run db:seed          # Seed development database with sample data
npm run db:backup        # Copy data.db to backups/data-YYYY-MM-DD.db
npm run db:reset         # Delete data.db, re-run migrations, re-seed (dev only!)

# Quality
npm run lint             # ESLint across all files
npm run format           # Prettier write
npm run format:check     # Prettier check in CI — fails if any file is unformatted
npm run test             # Vitest unit tests
npm run test:e2e         # Playwright end-to-end tests (requires dev server running)
```

---

## Environment Variables

```bash
# .env.example — commit this. .env.local — NEVER commit.

# Database
DATABASE_PATH=data.db                          # SQLite file path (default: data.db)

# Auth (NextAuth.js v5 / Better Auth)
AUTH_SECRET=openssl rand -base64 32            # Generate fresh per environment
AUTH_URL=http://localhost:3000                 # App URL for auth callbacks

# Stripe
STRIPE_SECRET_KEY=sk_test_...                  # Server-side only — NEVER NEXT_PUBLIC_
STRIPE_WEBHOOK_SECRET=whsec_...                # For verifying webhook signatures
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_... # Safe for client — starts with NEXT_PUBLIC_

# Email (Resend / SendGrid / SMTP)
EMAIL_FROM=noreply@example.com
RESEND_API_KEY=re_...
```

---

## Testing Strategy

```
lib/db/queries/__tests__/users.test.ts   # Unit tests with in-memory SQLite
lib/validators.test.ts                    # Zod schema validation tests
lib/auth.test.ts                          # Password hashing, token verification
__tests__/e2e/signup.spec.ts              # Playwright: full user flows
```

**Rules:**
- Use `better-sqlite3` in-memory (`:memory:`) for unit tests that touch the DB.
- Each test file creates its own tables (from `schema.sql`) and tears them down.
- Never test against the development database. Tests must be isolated.
- Integration tests use a temporary file-based SQLite database that's deleted after.
- Playwright E2E tests run against a production build with a separate test database.

---

## Git Workflow

- Branch from `main`: `feat/billing-dashboard`, `fix/login-redirect`, `chore/update-deps`
- Commit messages: imperative, present tense. "Add Stripe webhook handling",
  NOT "Added" or "Adds". First line max 72 chars, body after blank line.
- PRs must pass: typecheck, lint, format:check, test, test:e2e
- Squash-merge to main. Linear history only.

---

## When Claude Code Gets It Wrong

If Claude Code generates code that violates these rules, the most common fixes are:

1. **It added `"use client"` unnecessarily** → Remove it. Only add for hooks/events.
2. **It used `fetch()` from a Server Component** → Call the DB directly instead.
3. **It imported better-sqlite3 from a component file** → Always go through `getDb()`.
4. **It used string interpolation in SQL** → Replace with `?` or `@param` placeholders.
5. **It wrote `as` casts for user input** → Use Zod `.parse()` instead.
6. **It used `any` as a type** → Replace with `unknown` and narrow with type guards.
7. **It created a CSS file instead of Tailwind classes** → Convert to Tailwind tokens.
