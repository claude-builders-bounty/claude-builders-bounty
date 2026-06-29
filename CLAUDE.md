# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project context for Claude Code. Every rule has a reason. Copy this file to your project root — Claude will read it automatically.

---

## Stack & Versions

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Framework | Next.js | ^15.x | App Router, SSR, API routes in one framework |
| Runtime | Node.js | >=20 | Native `fetch`, `structuredClone`, stable test runner |
| Language | TypeScript | ^5.4 | Strict mode. No `any` without `@ts-expect-error` comment |
| Database | SQLite | 3.x | `better-sqlite3` for sync simplicity, or Turso for edge |
| ORM / Query | Drizzle ORM | ^0.30 | Type-safe SQL, schema-first, lightweight vs Prisma |
| Auth | Lucia | ^3.x | Session-based auth designed for SQLite/edge, no bloat |
| Styling | Tailwind CSS | ^3.4 | Utility-first, design system via config, no runtime CSS |
| Validation | Zod | ^3.22 | Shared schemas across client, server, API boundaries |
| Testing | Vitest | ^1.x | Fast, native TS, `next-test` for component testing |

**Why not Prisma?** Prisma's query engine adds 50MB+ to your Docker image and requires a separate binary. Drizzle compiles to raw SQL, runs at the speed of `better-sqlite3`, and the schema IS your migration.

**Why not NextAuth.js?** Auth.js is framework-agnostic bloat. Lucia gives you typed sessions, cookie management, and CSRF protection with zero abstraction overhead.

---

## Folder Structure

```
├── apps/
│   └── web/                    # Next.js app (App Router only)
│       ├── src/
│       │   ├── app/            # Routes, layouts, loading.tsx, error.tsx
│       │   │   ├── (auth)/     # Route group: login, register, forgot-password
│       │   │   ├── (dashboard)/ # Route group: protected routes
│       │   │   ├── api/        # API routes (auth handlers, webhooks)
│       │   │   └── layout.tsx  # Root layout: fonts, metadata, providers
│       │   ├── components/
│       │   │   ├── ui/         # Primitive components (Button, Input, Modal)
│       │   │   │   └── index.ts # Barrel export, always
│       │   │   ├── forms/      # Form-specific components
│       │   │   └── layouts/    # Layout-specific components
│       │   ├── lib/
│       │   │   ├── db/         # Database: schema.ts, client.ts, migrations/
│       │   │   ├── auth/       # Lucia setup, session validation
│       │   │   ├── validations/# Zod schemas shared client/server
│       │   │   └── utils.ts    # cn() helper, formatters
│       │   ├── hooks/          # React hooks, always prefixed with use
│       │   └── types/          # Global types (not per-component)
│       ├── drizzle.config.ts
│       └── next.config.js
├── packages/
│   └── shared/                 # Shared types, validation schemas
│       ├── src/
│       │   ├── schemas.ts      # Zod schemas (User, Project, Task)
│       │   └── types.ts        # TypeScript interfaces derived from schemas
│       └── package.json
├── scripts/
│   └── migrate.ts              # Custom migration runner (not drizzle-kit in prod)
└── CLAUDE.md                   # This file
```

**No `src/` at root.** The monorepo root is for orchestration only. All code lives in `apps/` or `packages/`.

**No barrel exports from `components/ui/` subdirectories.** Only `index.ts` at the `ui/` level re-exports. Deep imports like `components/ui/button` are forbidden — use `components/ui`.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | kebab-case | `user-profile.tsx`, `auth-utils.ts` |
| Components | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase, `use` prefix | `useAuth.ts` |
| Server actions | camelCase, `Action` suffix | `createUserAction.ts` |
| Database tables | snake_case, plural | `users`, `team_members` |
| Columns | snake_case | `created_at`, `email_verified` |
| Zod schemas | PascalCase, `Schema` suffix | `CreateUserSchema` |
| TypeScript types | PascalCase | `User`, `TeamMembership` |

**Table names are always plural.** `users`, not `user`. Junction tables: `users_to_teams`.

---

## Database & Migrations

### Schema Rules

- Every table has `id` (integer auto-increment PK), `created_at`, `updated_at`
- No foreign key constraints at the DB level — enforce in application code. SQLite FKs are off by default and silently fail.
- Use `text` for all string columns — SQLite's `varchar` is an alias for `text` with no length enforcement.
- Store booleans as `integer` with `0`/`1` — SQLite has no native boolean.
- Store JSON as `text` with `jsonb` function support (SQLite 3.45+)

### Migration Conventions

1. Migrations live in `src/lib/db/migrations/`
2. Naming: `YYYYMMDD_HHMMSS_description.sql` — timestamp first, always sortable
3. Every migration is a transaction: wrap in `BEGIN; ... COMMIT;`
4. Migrations are immutable. Never edit a deployed migration. Create a new one.
5. The `migrate.ts` script records applied migrations in a `_migrations` table (auto-created)

### Migration Template

```sql
-- 20260115_143000_add_email_verified_to_users.sql
BEGIN;

ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0;

INSERT INTO _migrations (name, applied_at) VALUES ('20260115_143000_add_email_verified_to_users.sql', unixepoch());

COMMIT;
```

---

## Component Patterns

### Server Components (Default)

- Fetch data directly in the component via `db.query()`
- Pass data to Client Components as props — never pass setter functions
- Use `cache()` from React for deduplicated requests:

```tsx
import { cache } from "react";
import { db } from "@/lib/db";

const getUserById = cache(async (id: number) => {
  return db.query.users.findFirst({ where: (u, { eq }) => eq(u.id, id) });
});
```

### Client Components

- Mark with `"use client"` at the top
- Only when you need: `useState`, `useEffect`, browser APIs, forms with instant feedback
- Keep client components as leaves in the tree — push data fetching up to Server Components

### Forms

- Server Actions for mutations — no `fetch()` from client
- Use `useFormStatus()` for pending states
- Zod validation on the server action boundary:

```tsx
// Always validate at the server action boundary
const CreateProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function createProjectAction(formData: FormData) {
  const parsed = CreateProjectSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { error: parsed.error.flatten() };
  }
  // ... create in DB
}
```

---

## API Routes (`app/api/`)

- Use only for external webhooks, file uploads, or non-HTML responses
- Prefer Server Actions for internal mutations — they handle CSRF, streaming, and progressive enhancement
- API routes must validate with Zod, same schemas as Server Actions
- Return typed errors: `{ error: { code: "VALIDATION_ERROR", message: "..." } }`

### API Route Template

```ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const RequestSchema = z.object({
  email: z.string().email(),
});

export async function POST(req: NextRequest) {
  const body = await req.json();
  const parsed = RequestSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", issues: parsed.error.issues } },
      { status: 400 }
    );
  }

  // ... handler logic
  return NextResponse.json({ data: result });
}
```

---

## Authentication (Lucia)

### Session Flow

1. User submits credentials → Server Action
2. Verify password with `bcrypt` or `argon2`
3. Create session via `lucia.createSession(userId)`
4. Set session cookie via `lucia.createSessionCookie()`
5. On every request: validate session via `lucia.validateSession()` in layout
6. Attach user to context: `const user = validatedSession ? dbUser : null`

### Protected Routes

- Check session in the root layout, pass user down via React Context (client) or props (server)
- Redirect unauthenticated users in Server Components with `redirect("/login")`
- Do NOT protect routes via middleware — middleware runs on every request, including static assets

---

## Anti-Patterns (Don't Do This)

| Anti-Pattern | Why | What To Do Instead |
|-------------|-----|-------------------|
| `any` type | Defeats TypeScript's purpose | Use `unknown` + type guard, or proper Zod schema |
| Client-side `fetch` for internal APIs | Duplicates auth handling, no CSRF protection | Server Actions for mutations, Server Components for queries |
| Prisma in this stack | 50MB+ binary, slower queries, migration lock-in | Drizzle ORM — compiles to SQL, schema IS migration |
| `useEffect` for data fetching | Race conditions, no SSR, waterfalls | Fetch in Server Component, use `cache()` |
| Middleware for auth checks | Runs on every request including `_next/static` | Check session in layout, redirect there |
| `SELECT *` queries | Breaks when schema changes | Explicit column selection in Drizzle queries |
| `.env` in Docker image | Secrets leak to image layers | Mount `.env` at runtime, use secrets manager |
| Client-side environment variables for secrets | Exposed in browser bundle | Only `NEXT_PUBLIC_` prefix for truly public vars |
| No DB migrations in CI | Schema drift between environments | Run `migrate.ts` before app start in Dockerfile |

---

## Dev Commands

```bash
# Development
npm run dev                 # Start Next.js dev server (turbo mode)
npm run db:migrate          # Run pending migrations
npm run db:studio           # Drizzle Studio for local DB inspection
npm run db:seed             # Seed dev data (only in development!)

# Code quality
npm run typecheck           # tsc --noEmit
npm run lint                # next lint + eslint
npm run test                # vitest
npm run test:e2e            # playwright

# Production
npm run build               # next build (runs typecheck + lint)
npm start                   # next start (production server)
```

---

## Testing Strategy

| Test Type | Tool | Scope |
|-----------|------|-------|
| Unit | Vitest | Utility functions, Zod schemas, business logic |
| Component | `next-test` / `@testing-library/react` | Interactive client components |
| Integration | Vitest + `better-sqlite3` in `:memory:` | Server Actions with real DB |
| E2E | Playwright | Critical user flows: auth, payment, onboarding |

**Database testing rule:** Use `:memory:` database, run migrations in `beforeAll`, seed per test, clean up in `afterEach`. Never mock the database.

---

## Environment Variables

```bash
# Required
DATABASE_URL="file:./local.db"           # SQLite file path
SESSION_SECRET="min-32-char-random"      # Lucia session secret

# Optional
NEXT_PUBLIC_APP_URL="http://localhost:3000"
PORT=3000
```

**Rule:** `SESSION_SECRET` must be >= 32 characters. Generate with `openssl rand -hex 32`.

---

## Deployment Checklist

- [ ] `npm run typecheck` passes
- [ ] `npm run lint` passes
- [ ] `npm run test` passes
- [ ] Migrations are committed and tested on staging DB
- [ ] `SESSION_SECRET` is set in production (not in repo)
- [ ] `NODE_ENV=production` is set
- [ ] SQLite file is on persistent volume (not ephemeral container storage)
- [ ] Health check endpoint at `/api/health` returns 200

---

*Generated for Claude Code context. Last updated: 2026-06-29*
