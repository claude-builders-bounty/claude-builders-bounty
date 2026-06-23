# CLAUDE.md — Project Instructions for Claude Code

This document provides comprehensive guidance for working with this Next.js + SQLite SaaS application. Read this file in full before making any changes to the codebase.

---

## Overview

This is a SaaS web application built with:

- **Next.js 14+** (App Router) — React framework with server-side rendering, API routes, and file-based routing
- **SQLite** via **better-sqlite3** — Embedded database for zero-config, single-file persistence
- **TypeScript** — Strict type safety across the entire stack
- **Tailwind CSS** — Utility-first styling with the `cn()` helper for conditional classes

The app is designed for simple deployment (single-process, no external database server) while supporting multi-tenant SaaS patterns.

---

## Getting Started

### Prerequisites

- Node.js 20+ (LTS recommended)
- npm, yarn, or pnpm

### Initial Setup

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your values (see Environment Variables section)

# Initialize the database and run migrations
npm run db:migrate

# (Optional) Seed sample data
npm run db:seed

# Start development server
npm run dev
```

The app runs at `http://localhost:3000`. The database file is created at `./data/app.db` (relative to project root).

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_PATH` | No | Path to SQLite file (default: `./data/app.db`) |
| `NEXTAUTH_SECRET` | Yes | Secret for session encryption. Generate with `openssl rand -base64 32` |
| `NEXTAUTH_URL` | Yes | Canonical URL (e.g., `http://localhost:3000` in dev) |
| `STRIPE_SECRET_KEY` | Yes | Stripe API key for billing |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |

Never commit `.env.local` or any file containing secrets.

---

## Project Structure

```
├── app/                        # Next.js App Router (pages & layouts)
│   ├── (auth)/                 # Auth-related routes (login, signup, forgot-password)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/            # Authenticated dashboard routes
│   │   ├── layout.tsx          # Dashboard shell with sidebar
│   │   ├── page.tsx            # Dashboard home
│   │   └── settings/
│   │       └── page.tsx
│   ├── (marketing)/            # Public-facing pages (home, pricing, about)
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── api/                    # API route handlers
│   │   ├── auth/[...nextauth]/
│   │   │   └── route.ts
│   │   ├── webhooks/
│   │   │   └── stripe/
│   │   │       └── route.ts
│   │   └── v1/                 # Versioned API endpoints
│   │       ├── users/
│   │       │   └── route.ts
│   │       └── organizations/
│   │           └── route.ts
│   ├── layout.tsx              # Root layout (providers, fonts, global styles)
│   └── globals.css             # Tailwind directives and CSS custom properties
│
├── lib/                        # Shared utilities (no React components)
│   ├── db/
│   │   ├── index.ts            # Database connection singleton
│   │   ├── schema.ts           # Table definitions and types
│   │   ├── migrations/         # SQL migration files (001_initial.sql, etc.)
│   │   └── queries/
│   │       ├── users.ts        # User-related queries
│   │       └── organizations.ts
│   ├── auth.ts                 # Auth configuration and helpers
│   ├── stripe.ts               # Stripe client setup
│   ├── utils.ts                # General utilities (cn(), formatDate, etc.)
│   └── validations/            # Zod schemas for input validation
│       ├── user.ts
│       └── organization.ts
│
├── components/                 # Reusable UI components
│   ├── ui/                     # Primitive components (Button, Input, Modal)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── forms/                  # Form components with validation
│   │   └── login-form.tsx
│   └── layouts/                # Layout components (Sidebar, Header, etc.)
│       ├── sidebar.tsx
│       └── header.tsx
│
├── hooks/                      # Custom React hooks
│   ├── use-user.ts
│   └── use-debounce.ts
│
├── types/                      # Shared TypeScript type definitions
│   ├── index.ts
│   └── api.ts                  # API request/response types
│
├── data/                       # Runtime data (gitignored)
│   └── app.db                  # SQLite database file
│
├── public/                     # Static assets
│   └── images/
│
├── scripts/                    # CLI scripts (db:migrate, db:seed, etc.)
│   ├── migrate.ts
│   └── seed.ts
│
├── tests/                      # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── tailwind.config.ts          # Tailwind configuration
├── tsconfig.json               # TypeScript configuration
├── next.config.ts              # Next.js configuration
├── package.json
└── CLAUDE.md                   # ← This file
```

### Key Architectural Decisions

1. **Route Groups**: Parenthesized folders like `(auth)`, `(dashboard)`, `(marketing)` group related routes without affecting the URL path. Each group has its own layout.

2. **API Versioning**: All public API endpoints are under `/api/v1/` to allow future versioning without breaking clients.

3. **Database Singleton**: `lib/db/index.ts` exports a single `better-sqlite3` instance. Never create multiple connections. In development, use a module-level variable to survive Next.js hot reloads:

   ```typescript
   // lib/db/index.ts
   import Database from 'better-sqlite3';
   import path from 'path';

   const globalForDb = globalThis as unknown as { db: Database.Database };

   export const db = globalForDb.db ?? new Database(
     process.env.DATABASE_PATH ?? path.join(process.cwd(), 'data', 'app.db'),
     { verbose: process.env.NODE_ENV === 'development' ? console.log : undefined }
   );

   if (process.env.NODE_ENV !== 'production') globalForDb.db = db;

   // Enable WAL mode for better concurrent read performance
   db.pragma('journal_mode = WAL');
   db.pragma('foreign_keys = ON');
   ```

4. **Multi-tenancy**: The app uses a shared-database, shared-schema model. Most tables include an `organization_id` column. All queries must filter by the current user's organization. Middleware injects the org context.

---

## Coding Standards

### General Rules

- **TypeScript strict mode** is enabled. No `any` types — use `unknown` and narrow with type guards.
- Use **named exports** everywhere. Default exports are only allowed for Next.js page/layout files (required by the framework).
- Prefer **`const` assertions** and literal types over enums. Use `as const` objects when a set of values is needed.
- All async functions must have explicit return types (e.g., `Promise<User | null>`).
- Use **early returns** to reduce nesting. Prefer guard clauses at the top of functions.
- Maximum function length: ~50 lines. If longer, extract helpers.

### File Naming

| Type | Convention | Example |
|---|---|---|
| React components | kebab-case `.tsx` | `user-avatar.tsx` |
| Utility/helper files | kebab-case `.ts` | `format-date.ts` |
| Test files | `*.test.ts` or `*.test.tsx` | `user-avatar.test.tsx` |
| E2E test files | `*.spec.ts` | `login.spec.ts` |
| SQL migrations | `NNN_description.sql` | `001_initial_schema.sql` |
| Route handlers | Always `route.ts` | (Next.js convention) |
| Page components | Always `page.tsx` | (Next.js convention) |

### Component Patterns

```typescript
// ✅ DO: Define prop types as an interface
interface UserAvatarProps {
  user: User;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function UserAvatar({ user, size = 'md', className }: UserAvatarProps) {
  return (
    <div className={cn('rounded-full', sizeClasses[size], className)}>
      {/* ... */}
    </div>
  );
}

// ❌ DON'T: Use inline prop types or default exports
export default function UserAvatar({ user, size = 'md' }: any) {
```

### Server vs. Client Components

- **Default to Server Components**. Only add `'use client'` when the component needs interactivity (event handlers, hooks, browser APIs).
- Server Components can directly call `lib/db/` queries. Client Components cannot.
- When a Client Component needs data, fetch it in a parent Server Component and pass as props, or use a server action.

```typescript
// app/(dashboard)/page.tsx  — Server Component (no directive needed)
import { getOrganizations } from '@/lib/db/queries/organizations';
import { OrganizationList } from '@/components/organization-list';

export default async function DashboardPage() {
  const orgs = await getOrganizations();  // Direct DB call — OK in server component
  return <OrganizationList organizations={orgs} />;
}
```

### Styling with Tailwind

- Use the `cn()` utility (from `lib/utils.ts`) for conditional/merged classes. It wraps `clsx` + `tailwind-merge`.
- Extract repeated patterns into component variants using `class-variance-authority` (CVA).
- Do not use inline styles. Use Tailwind classes exclusively.
- Follow the design tokens in `tailwind.config.ts` — do not hardcode arbitrary values (`w-[347px]`) unless truly necessary.

```typescript
import { cn } from '@/lib/utils';

// ✅ DO
<button className={cn('px-4 py-2 rounded-md', variant === 'primary' && 'bg-blue-600', className)}>

// ❌ DON'T: string concatenation or template literals for classes
<button className={`px-4 py-2 rounded-md ${variant === 'primary' ? 'bg-blue-600' : ''}`}>
```

### Database and Query Patterns

- **Always use parameterized queries**. Never interpolate user input into SQL strings.
- **Use transactions** for multi-step writes:
  ```typescript
  const createOrgWithOwner = db.transaction((orgName: string, userId: string) => {
    const org = db.prepare('INSERT INTO organizations (name) VALUES (?)').run(orgName);
    db.prepare('UPDATE users SET organization_id = ? WHERE id = ?').run(org.lastInsertRowid, userId);
    return org;
  });
  ```
- **Migration files** are plain SQL in `lib/db/migrations/`. Each migration runs exactly once, tracked in a `_migrations` table. Never modify an already-applied migration — create a new one.
- Prefer `RETURNING *` over separate SELECT after INSERT/UPDATE.
- Define Zod schemas in `lib/validations/` for all API inputs. Validate before touching the database.

### Error Handling

- Use the `AppError` class (from `lib/errors.ts`) for application errors with HTTP status codes.
- API routes should return structured error responses:
  ```typescript
  return NextResponse.json(
    { error: { code: 'NOT_FOUND', message: 'Organization not found' } },
    { status: 404 }
  );
  ```
- Never expose internal error details (stack traces, SQL errors) to the client in production.
- Use `try/catch` in server actions and log errors server-side.

### Naming Conventions

| Context | Convention | Example |
|---|---|---|
| Components | PascalCase | `UserProfile` |
| Functions/hooks | camelCase | `useCurrentUser` |
| Constants | UPPER_SNAKE_CASE | `MAX_FILE_SIZE` |
| Database tables | snake_case, plural | `user_sessions` |
| Database columns | snake_case | `created_at`, `organization_id` |
| API endpoints | kebab-case | `/api/v1/organizations` |
| CSS/Tailwind classes | kebab-case (standard) | `bg-blue-600` |

---

## Testing

### Stack

- **Unit & Integration**: Vitest + Testing Library
- **E2E**: Playwright
- **API Testing**: Vitest with supertest or direct fetch against `next-server`

### Running Tests

```bash
# Unit and integration tests
npm test

# Unit tests only (watch mode)
npm run test:watch

# E2E tests (requires running dev server)
npm run test:e2e

# Coverage report
npm run test:coverage
```

### Test File Organization

- Unit tests live **next to the file they test**: `lib/utils.ts` → `lib/utils.test.ts`
- Integration tests go in `tests/integration/`
- E2E tests go in `tests/e2e/`

### Writing Tests

```typescript
// lib/utils.test.ts
import { describe, it, expect } from 'vitest';
import { cn } from './utils';

describe('cn', () => {
  it('merges tailwind classes without conflicts', () => {
    expect(cn('px-4', 'px-8')).toBe('px-8');
  });

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'extra')).toBe('base extra');
  });
});
```

### Database Testing

- Use an **in-memory SQLite database** for tests. The test setup file creates a fresh `:memory:` database and runs all migrations before each test suite.
- Never run tests against the production or development database.
- Seed test data in `beforeEach` or `beforeAll` hooks. Clean up in `afterEach`.

```typescript
import Database from 'better-sqlite3';

let db: Database.Database;

beforeEach(() => {
  db = new Database(':memory:');
  db.pragma('foreign_keys = ON');
  // Run migrations
  runMigrations(db);
});

afterEach(() => {
  db.close();
});
```

---

## Database Migrations

### Creating a Migration

1. Create a new file: `lib/db/migrations/NNN_description.sql`
2. Use sequential numbering (001, 002, ...). Never reuse or modify applied numbers.
3. Each migration must be **idempotent-safe at creation time** (use `CREATE TABLE IF NOT EXISTS`).
4. Include both up and down migrations as comments, but the runner only executes the up direction.

```sql
-- lib/db/migrations/002_add_billing_fields.sql
-- Up migration

ALTER TABLE organizations ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE organizations ADD COLUMN subscription_status TEXT DEFAULT 'trialing'
  CHECK (subscription_status IN ('trialing', 'active', 'past_due', 'canceled'));

CREATE INDEX idx_organizations_stripe ON organizations(stripe_customer_id);
```

### Running Migrations

```bash
npm run db:migrate        # Apply all pending migrations
npm run db:migrate:status # Show which migrations have been applied
npm run db:reset          # Drop and recreate database (DESTRUCTIVE — dev only)
```

---

## Common Commands

```bash
# Development
npm run dev              # Start dev server (http://localhost:3000)
npm run build            # Production build
npm run start            # Start production server
npm run lint             # Run ESLint
npm run lint:fix         # Auto-fix ESLint issues
npm run typecheck        # Run tsc --noEmit (type checking without emitting)

# Database
npm run db:migrate       # Run pending migrations
npm run db:seed          # Seed with sample data
npm run db:reset         # Drop, recreate, migrate, and seed (dev only)
npm run db:studio        # Open database inspector (if configured)

# Testing
npm test                 # Vitest (unit + integration)
npm run test:e2e         # Playwright E2E tests
npm run test:coverage    # Coverage report

# Code Quality
npm run format           # Prettier format all files
npm run format:check     # Check formatting without writing
```

---

## Deployment

### Production Build

```bash
npm run build
npm run start
```

### Deployment Checklist

1. Set all required environment variables (see table above).
2. Ensure `DATABASE_PATH` points to a persistent volume (SQLite file must survive restarts).
3. Run `npm run db:migrate` before starting the app.
4. Set `NODE_ENV=production`.
5. Use a process manager (PM2, systemd, or container orchestration) — the app is a single long-running Node process.

### SQLite in Production

- Enable WAL mode (done in `lib/db/index.ts` by default).
- Set `busy_timeout` to avoid lock contention: `db.pragma('busy_timeout = 5000')`.
- Back up the database file regularly. Use `.backup` command or `sqlite3 data/app.db ".backup data/app.db.bak"`.
- SQLite works well for single-server deployments with moderate write loads. For horizontal scaling, consider migrating to PostgreSQL.

### Static Assets

- `public/` files are served by Next.js at the root URL path.
- Images should be optimized via `next/image`. Do not serve raw large images.
- Set `Cache-Control` headers for static assets in `next.config.ts`.

---

## Common Pitfalls

### 1. Using `'use client'` unnecessarily
Server Components are the default. Adding `'use client'` to a component makes it and all its children client-rendered, which increases bundle size and prevents direct database access. Only use it when you need interactivity.

### 2. N+1 query patterns
Don't call a database query inside a loop. Use `IN` clauses or JOINs:
```typescript
// ❌ BAD: N+1 queries
for (const user of users) {
  user.org = db.prepare('SELECT * FROM organizations WHERE id = ?').get(user.organization_id);
}

// ✅ GOOD: Single query with JOIN
const usersWithOrgs = db.prepare(`
  SELECT users.*, organizations.name as org_name
  FROM users
  LEFT JOIN organizations ON users.organization_id = organizations.id
`).all();
```

### 3. Forgetting `organization_id` in queries
Every multi-tenant query must filter by `organization_id`. This is a security-critical requirement. Missing this filter exposes data across tenants. Consider using a query builder or helper that auto-injects the filter.

### 4. Mutating database in GET requests
GET requests (page loads, `GET` API routes) must be read-only. All writes must go through POST/PUT/PATCH/DELETE handlers or Server Actions.

### 5. Importing from wrong paths
Use the `@/` path alias (maps to project root). Never use relative imports that go up more than one directory:
```typescript
// ✅
import { db } from '@/lib/db';
import { Button } from '@/components/ui/button';

// ❌
import { db } from '../../../lib/db';
```

### 6. Storing SQLite file inside the Next.js source directory
The database file must be in `./data/` (gitignored), not inside `app/` or `lib/`. Next.js watches source files for hot reload, and a changing `.db` file causes issues.

### 7. Not handling database busy state
SQLite uses file-level locking. Under concurrent writes, you may get `SQLITE_BUSY` errors. The `busy_timeout` pragma (set in `lib/db/index.ts`) mitigates this, but long-running transactions should be avoided.

### 8. Committing secrets or database files
Ensure `.env.local`, `data/`, and `*.db` files are in `.gitignore`. Never commit API keys, database files, or session secrets.

---

## Adding a New Feature (Checklist)

When adding a new feature, follow this order:

1. **Create migration** if new tables/columns are needed → `lib/db/migrations/`
2. **Define types** in `types/` or alongside the schema → `lib/db/schema.ts`
3. **Write Zod validation schemas** → `lib/validations/`
4. **Implement database queries** → `lib/db/queries/`
5. **Build API route** (if needed) → `app/api/v1/`
6. **Build Server Action** (for form submissions) → `app/(dashboard)/actions.ts`
7. **Build UI components** → `components/`
8. **Build page** → `app/(dashboard)/feature/page.tsx`
9. **Write tests** — unit for queries/validation, integration for API, E2E for critical flows
10. **Update this document** if the feature introduces new patterns or conventions

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `next` | Framework (App Router, SSR, API routes) |
| `react` / `react-dom` | UI library |
| `typescript` | Type checking |
| `better-sqlite3` | SQLite driver (synchronous, fast) |
| `tailwindcss` | Utility-first CSS |
| `clsx` + `tailwind-merge` | Conditional class merging (`cn()` helper) |
| `class-variance-authority` | Component variant patterns |
| `zod` | Runtime schema validation |
| `next-auth` | Authentication (sessions, OAuth) |
| `stripe` | Billing and subscriptions |
| `vitest` | Unit/integration testing |
| `@testing-library/react` | Component testing |
| `playwright` | E2E testing |
| `eslint` + `prettier` | Code formatting and linting |

---

## Getting Help

- Check existing patterns in the codebase before writing new code. When in doubt, follow an existing example.
- Run `npm run typecheck` and `npm run lint` before committing.
- If a migration fails, check `npm run db:migrate:status` for the state. Never modify an applied migration.
- For SQLite-specific questions, refer to the [SQLite documentation](https://www.sqlite.org/lang.html) and [better-sqlite3 API](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md).
