# CLAUDE.md — Next.js 15 + SQLite SaaS Template

> **Purpose:** This file is the source of truth for working in this codebase. Read it before touching anything. Update it when the team agrees to change how we work.

---

## Stack & Versions

We pin exact versions. No `latest`, no `^`, no `~`. Floating versions cause production incidents.

| Package | Version | Why |
|---------|---------|-----|
| Node.js | 22.x LTS | Fast refresh is stable. 23.x has edge-case bugs with App Router. |
| Next.js | 15.x | App Router is no longer experimental. Server Components by default. |
| React | 19.x | Ships with Next.js 15. Don't upgrade React independently. |
| SQLite | via `better-sqlite3` | Synchronous API = simpler code. Drizzle ORM for type safety. |
| Drizzle ORM | 0.40.x | Zero runtime overhead. Generates migrations. Plays nice with TypeScript. |
| Tailwind CSS | 4.x | CSS-first config. No `tailwind.config.js` overhead. |
| TypeScript | 5.7.x | Strict mode on. Nulls are not undefined. |

**Runtime:** Node.js process (not Vercel Edge, not Cloudflare Workers). We use the Node.js adapter for deployment flexibility.

---

## Project Structure

```
/
├── src/
│   ├── app/                    # Next.js App Router pages + layouts
│   │   ├── (auth)/             # Route group: authentication pages
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/        # Route group: authenticated app pages
│   │   │   ├── layout.tsx       # Shell: sidebar, header, auth guard
│   │   │   └── [orgSlug]/       # Multi-tenant org scope
│   │   │       ├── settings/
│   │   │       └── billing/
│   │   ├── api/                # Route Handlers only — no Express-style routers
│   │   │   ├── auth/
│   │   │   └── webhooks/
│   │   ├── layout.tsx          # Root layout (fonts, providers)
│   │   └── page.tsx            # Landing/marketing → redirects to /dashboard
│   │
│   ├── components/
│   │   ├── ui/                 # Primitive UI components (Button, Input, Card)
│   │   │   └── *.tsx
│   │   ├── forms/              # Form components bound to schemas
│   │   │   └── *.tsx
│   │   └── features/           # Business-domain components (InvoiceList, UserMenu)
│   │       └── */              # One folder per feature: components + tests
│   │
│   ├── lib/
│   │   ├── db/                 # Database layer
│   │   │   ├── index.ts        # Single exported db client instance
│   │   │   ├── schema/         # Drizzle schema files — one per domain
│   │   │   │   ├── users.ts
│   │   │   │   ├── organizations.ts
│   │   │   │   └── subscriptions.ts
│   │   │   └── migrations/     # Drizzle-generated SQL migrations
│   │   ├── auth.ts             # Session management (lucia or iron-session)
│   │   ├── rate-limit.ts       # In-memory rate limiter for API routes
│   │   └── validators.ts       # Zod schemas shared across client/server
│   │
│   └── types/                  # Global TypeScript types (not auto-generated)
│       └── index.ts
│
├── drizzle.config.ts           # Drizzle config — points to migrations/ folder
├── tailwind.config.ts          # Tailwind 4 uses CSS-first; this enables TS intellisense
├── next.config.ts              # Next.js config (no .js)
└── .env.local                  # Local secrets — NEVER commit
```

### Why route groups `(auth)` and `(dashboard)`?

Because they share layouts but have **zero** URL path overlap. `(auth)/login` is `/login`, `(dashboard)/settings` is `/settings`. Route groups don't affect URLs — they organize code. This keeps `app/` from becoming a flat list of 30 folders.

### One schema file per domain, not one big `schema.ts`

When your team has 50 tables in one file, every PR becomes a merge conflict nightmare. One file per domain = smaller diffs, easier reviews, clearer ownership.

---

## Naming Conventions

### Files

| Thing | Convention | Example |
|-------|------------|---------|
| React Components | PascalCase | `UserProfile.tsx` |
| Utilities / hooks | camelCase | `useUserProfile.ts`, `formatCurrency.ts` |
| Drizzle schema | camelCase | `userProfiles.ts` (not `UserProfiles.ts`) |
| Database tables | snake_case | `user_profiles` (Drizzle handles the mapping) |
| Route files | kebab-case | `user-profiles.tsx` (URLs are `/user-profiles`) |
| Environment variables | SCREAMING_SNAKE | `DATABASE_URL`, `AUTH_SECRET` |
| API route files | kebab-case + route.ts | `user-profiles/route.ts` |

**Why snake_case for DB tables?** SQLite is case-insensitive but tooling (Drizzle, SQLite Studio) defaults to snake_case. Consistency with the broader SQLite ecosystem > fighting the tooling.

**Why kebab-case for route files?** URLs are `/user-profiles`, not `/userProfiles`. The file should match the URL so `grep -r user-profiles` finds the route file.

### Variables

- Prefix with type for ambiguous things: `userId: string`, `planId: string` — both `string`, both in scope. `userId` and `planId` are unambiguous.
- `is`/`has`/`should` for booleans: `isLoading`, `hasPermission`, `shouldRedirect`.
- No Hungarian notation: `strName` is garbage. TypeScript has types.

### React Component Patterns

```tsx
// ✅ DO: Colocate Props interface with the component
export function UserProfile({ userId }: { userId: string }) {
  return <div>{userId}</div>;
}

// ✅ DO: Explicit return type for complex components
export async function UserProfile({ userId }: { userId: string }): Promise<JSX.Element> {
  const user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  if (!user) notFound();
  return <div>{user.name}</div>;
}

// ❌ DON'T: Props interface in a separate file unless it's reused in 3+ places
```

---

## SQL & Migration Conventions

### The Golden Rule: Migrations are Code

Every schema change goes through a migration. **Never mutate the database manually in production.** If you need a hotfix, write a migration, test it locally, ship it with the deploy.

### Migration Workflow

```bash
# 1. Change your schema in src/lib/db/schema/
pnpm db:generate        # Drizzle generates migration from schema diff

# 2. Review the generated SQL in src/lib/db/migrations/
#    If the SQL looks wrong, fix the schema — not the migration file

pnpm db:migrate         # Apply to local database
pnpm db:studio          # Inspect DB with Drizzle Studio (optional)
```

### Schema File Rules

```typescript
// ✅ DO: Add createdAt/updatedAt to every table
export const users = sqliteTable('users', {
  id: text('id').primaryKey(),       // UUID, not auto-increment
  email: text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`CURRENT_TIMESTAMP`),
  updatedAt: integer('updated_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`CURRENT_TIMESTAMP`),
});

// ✅ DO: Use text() for IDs, not integer(). UUIDs are portable across databases.
export const organizations = sqliteTable('organizations', {
  id: text('id').primaryKey(),
  slug: text('slug').notNull().unique(),   // For URL routing: /acme-corp
  // ...
});
```

### What We Don't Do in SQL

- **No foreign key constraints at the DB level.** SQLite's FK enforcement is optional and has edge cases. Enforce referential integrity in application code (Drizzle relations + service layer).
- **No `ALTER TABLE` for adding columns with defaults in migration.** SQLite doesn't support `ALTER TABLE ADD COLUMN` with non-constant defaults on existing tables. Use a workaround migration.
- **No triggers.** Business logic in application code is debuggable. Triggers in SQLite are invisible to ORMs and hard to test.
- **No raw SQL in Route Handlers.** Use Drizzle queries. Raw SQL is an attack surface.

### Indexes

```typescript
// ✅ DO: Add indexes for columns you query with WHERE
export const sessions = sqliteTable('sessions', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id),
  expiresAt: integer('expires_at', { mode: 'timestamp' }).notNull(),
});

// ✅ DO: Composite indexes for multi-column queries
export const userOrganizations = sqliteTable('user_organizations', {
  userId: text('user_id').notNull(),
  orgId: text('org_id').notNull(),
}, (table) => ({
  // This covers: WHERE userId = ? AND orgId = ? (common in RBAC)
  userOrgIdx: index('user_org_idx').on(table.userId, table.orgId),
}));
```

---

## Component Patterns

### Server Components by Default

Every component is a Server Component unless it needs:
1. `use client` directive (event handlers, state)
2. Browser-only APIs (localStorage, navigator)
3. Real-time subscriptions (WebSockets)

```tsx
// ✅ Default: Server Component
export default async function UserList() {
  const users = await db.select().from(usersTable);
  return (
    <ul>
      {users.map(u => <li key={u.id}>{u.email}</li>)}
    </ul>
  );
}

// ✅ When you need interactivity: Client Component
'use client';
import { useState } from 'react';
export function Counter({ initialCount }: { initialCount: number }) {
  const [count, setCount] = useState(initialCount);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

**Why?** Server Components reduce JavaScript bundle size. Your landing page might ship 0 KB of JS if all components are server-rendered.

### Passing Data: Props, Not Context

```tsx
// ✅ DO: Pass data as props
async function Dashboard({ user }: { user: User }) {
  return <UserStats stats={user.stats} />;
}

// ❌ DON'T: Use React Context for server-fetched data
// Context is for client-side global state (theme, auth status, cart).
// Server data comes through component trees as props.
```

### Error Handling

```tsx
// ✅ DO: Use Next.js error.tsx for route-level errors
// app/(dashboard)/error.tsx
'use client';
export function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <p>Something went wrong: {error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}

// ✅ DO: Use notFound() for 404s
import { notFound } from 'next/navigation';
if (!user) notFound();
```

---

## What We DON'T Do

### No "just add a package" for solved problems

| Problem | Our Solution | Why |
|---------|--------------|-----|
| Auth from scratch | `lucia` + `arctic` | Battle-tested. Don't build your own JWT signing. |
| File uploads | Upload to S3/R2, store URL in DB | Don't store blobs in SQLite. SQLite is for structured data. |
| Background jobs | `inngest` or `trigger.dev` | SQLite is not a job queue. |
| Full-text search | SQLite FTS5 extension | Already built in. Don't add Elasticsearch. |
| Real-time | Server-Sent Events (SSE) | Simple, works with App Router. WebSockets require separate infrastructure. |

### No Mixing Server and Client Fetching

```tsx
// ❌ DON'T: Client fetches then passes to Server Component
'use client';
const data = await fetch('/api/users');  // Client-side API call

// ❌ DON'T: Server Component uses SWR/React Query
// Server Components run on the server. React Query is for client-side data caching.
```

### No `.env.production` or `.env.staging`

We have **two** env files: `.env.local` (local, never committed) and `.env.example` (documented template). All other environment variables come from the deployment platform (Vercel, Railway, Fly.io). This prevents credential drift between local and production.

### No API Routes for Internal Mutations

If a Server Component needs to write data, call the service layer directly — don't go through an HTTP round-trip:

```tsx
// ✅ DO: Direct service call from Server Component
import { createOrganization } from '@/lib/services/organizations';
export default async function CreateOrgPage() {
  await createOrganization({ name: 'Acme', slug: 'acme' });
  redirect('/dashboard/acme');
}

// ❌ DON'T: HTTP redirect to API route for internal writes
// Extra network hop, extra latency, extra attack surface.
```

API Routes are for **external consumers** (webhooks, third-party integrations, mobile apps). Internal mutations use direct service calls.

### No `console.log` in Production Code

```typescript
// ✅ DO: Use structured logging for production
import { logger } from '@/lib/logger';
logger.info('User created', { userId: user.id, orgId: org.id });

// ❌ DON'T: console.log everywhere
// console.log doesn't go to structured logging systems (Datadog, Sentry).
// It also frequently leaks sensitive data.
```

### No In-Memory Caching for User Data

```typescript
// ❌ DON'T: Module-level cache for user data
const userCache = new Map();
export async function getUser(id: string) {
  if (userCache.has(id)) return userCache.get(id);
  const user = await db.query.users.findFirst({ where: eq(users.id, id) });
  userCache.set(id, user);
  return user;
}

// SQLite + Next.js hot reload = cache pollution, stale data, memory leaks.
// If you need caching, use a dedicated cache (Redis, cloudflare cache, etc.)
```

---

## Development Commands

```bash
pnpm dev          # Start dev server at localhost:3000
pnpm build        # Production build (runs type check first)
pnpm start        # Start production server
pnpm lint         # ESLint (runs on pre-commit via husky)
pnpm typecheck    # tsc --noEmit

# Database
pnpm db:generate  # Generate migration from schema changes
pnpm db:migrate   # Apply pending migrations
pnpm db:studio    # Drizzle Studio (GUI for SQLite)
pnpm db:seed      # Run seed script (if exists)

# Testing
pnpm test         # Vitest unit tests
pnpm test:e2e     # Playwright E2E tests
```

### Pre-commit Hooks

We use Husky + lint-staged:
- `pnpm lint` on changed `.ts`/`.tsx` files
- `pnpm typecheck` on the full project

If lint fails, the commit is rejected. No exceptions.

---

## Deployment

**Build:** `pnpm build` produces a Node.js server, not a static export.

**Environment variables required:**
```
DATABASE_URL=file:./data/app.db   # SQLite file path (relative to project root)
AUTH_SECRET=<32-byte-hex-string>  # Use `openssl rand -hex 32`
```

**Recommended platforms:** Railway, Fly.io, Render — any platform that supports persistent disk storage for SQLite.

**NOT recommended:** Vercel Hobby (no persistent filesystem). Vercel Pro works if you use `DATABASE_URL` pointing to a managed SQLite provider (Turso, Cloudflare D1).

---

## Why SQLite?

SQLite is not a toy database. It handles 100K+ row tables with sub-millisecond reads. For a SaaS with <10K concurrent users, SQLite is likely faster than PostgreSQL because there's no network round-trip to a separate database server.

The constraint that forces good habits:
- No `SELECT *` on large tables (every query hits disk)
- No N+1 queries (each query is slow enough that you notice)
- Simple backup strategy (copy the `.db` file)

If you outgrow SQLite, the migration path to Turso (libSQL) or PostgreSQL (via Drizzle) is straightforward.

---

## Contributing to this Template

If you disagree with a rule here, open an issue. This is a opinionated template — "I'm not sure about X" is not a PR. "I think we should do Y instead of X because Z" is a PR.

The goal is a template that a team of 3-10 engineers can use without having to make the same 20 decisions on every new project.
