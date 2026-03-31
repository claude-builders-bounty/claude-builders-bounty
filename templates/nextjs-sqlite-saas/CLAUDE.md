# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated conventions for building a SaaS application with Next.js 15 App Router and SQLite. Every rule has a reason.

## Stack & Versions

| Technology       | Version  | Notes                                    |
|------------------|----------|------------------------------------------|
| Next.js          | 15.x     | App Router, Server Components by default |
| TypeScript       | 5.x      | Strict mode enabled                      |
| SQLite           | 3.x      | Via better-sqlite3, single-file DB       |
| Tailwind CSS     | 4.x      | Utility-first styling                    |
| Auth             | next-auth v5 or lucia-auth | Session-based preferred   |
| Node.js          | 20.x LTS | Required for Next.js 15                  |
| Package manager  | npm      | Lock file committed                      |

## Project Structure

```
src/
  app/                    # App Router — pages, layouts, route handlers
    (auth)/               # Auth group: /login, /register, /forgot-password
      login/
        page.tsx
      register/
        page.tsx
      layout.tsx          # Auth-specific layout (centered card)
    (dashboard)/          # Protected group: requires auth
      settings/
        page.tsx
      page.tsx            # Dashboard home
      layout.tsx          # Sidebar + nav layout
    api/                  # Route handlers (POST/GET/PUT/DELETE)
      webhooks/
        stripe/
          route.ts
    layout.tsx            # Root layout — html, body, providers
    page.tsx              # Landing page
  components/             # Shared React components (PascalCase filenames)
    ui/                   # Design primitives: Button, Input, Card, Badge
    forms/                # Form components: LoginForm, SettingsForm
    layout/               # Layout parts: Sidebar, Header, Footer
  db/
    schema.sql            # Source of truth for all tables
    migrations/           # Numbered SQL files: 001_init.sql, 002_add_users.sql
    index.ts              # DB singleton — one connection for the process
    seed.ts               # Dev seed data
  lib/                    # Shared utilities, organized by domain
    auth.ts               # Auth helpers (getSession, requireAuth)
    db.ts                 # Query helpers (re-exports from db/index.ts)
    email.ts              # Email sending utilities
    stripe.ts             # Stripe client + helpers
    validation.ts         # Zod schemas for input validation
  types/                  # TypeScript type definitions
    db.ts                 # Row types matching SQL schema
    api.ts                # API request/response types
  middleware.ts           # Next.js middleware — auth redirects
next.config.ts
tailwind.config.ts
tsconfig.json
```

**Why this structure:**
- Route groups `(auth)` and `(dashboard)` share layouts without affecting URL paths.
- `db/schema.sql` as a single source of truth prevents drift between code and database.
- `lib/` is organized by domain, not by abstraction level. `lib/auth.ts` is discoverable; `utils/helpers.ts` is not.
- `types/` mirrors data sources (db rows, API shapes) rather than arbitrary groupings.

## Naming Conventions

| Thing             | Convention          | Example                         | Reason                                  |
|-------------------|---------------------|---------------------------------|-----------------------------------------|
| Files (components)| PascalCase          | `UserCard.tsx`                  | Matches the component name inside       |
| Files (lib)       | kebab-case          | `send-email.ts`                 | Consistent with Node.js ecosystem       |
| SQL tables        | snake_case plural   | `team_members`                  | SQL standard, avoids quoting            |
| SQL columns       | snake_case          | `created_at`, `user_id`         | SQL standard                            |
| SQL indexes       | idx_table_column    | `idx_users_email`               | Instantly identifies table and column   |
| TS interfaces     | PascalCase          | `TeamMember`                    | TypeScript convention                   |
| TS variables      | camelCase           | `teamMember`                    | JavaScript convention                   |
| Environment vars  | SCREAMING_SNAKE     | `DATABASE_PATH`                 | Universal convention                    |
| Route handlers    | HTTP verb functions | `export async function POST()`  | Next.js 15 convention                   |

## SQL & Migration Conventions

### Schema is the source of truth

The file `db/schema.sql` contains the complete current schema. It should always be possible to create the database from scratch using this file alone. Migrations are for incremental changes to existing databases.

### Migration rules

1. Migrations are numbered SQL files: `001_init.sql`, `002_add_teams.sql`, `003_add_billing.sql`
2. Each migration runs inside a transaction (BEGIN/COMMIT)
3. Migrations only go forward — never edit a migration that has been committed to main
4. Each migration file has a comment header describing what it does and why

```sql
-- Migration: 002_add_teams.sql
-- Purpose: Add team support for multi-tenant billing
-- Date: 2026-03-15

BEGIN;

CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_teams_slug ON teams(slug);
CREATE INDEX idx_teams_owner_id ON teams(owner_id);

COMMIT;
```

### Query rules

- **Always** use parameterized queries with `?` placeholders. Never concatenate user input.
- Use the `db.prepare()` pattern from better-sqlite3 for type-safe, reusable statements.
- Keep queries close to where they are used. A `getUser(id)` function in `lib/auth.ts` is better than a generic `db.query()` wrapper.

```typescript
// Good: parameterized, close to usage
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId) as User | undefined;

// Bad: string concatenation (SQL injection risk)
const user = db.prepare(`SELECT * FROM users WHERE id = ${userId}`).get();

// Bad: generic wrapper that hides the query
const user = dbHelper.findOne('users', { id: userId });
```

### Foreign keys

- Always define `ON DELETE` behavior: `CASCADE` for owned resources, `SET NULL` for optional references.
- Enable foreign keys at connection time: `PRAGMA foreign_keys = ON;`

### SQLite-specific

- Use `TEXT` for dates, stored as ISO 8601 (`datetime('now')`). SQLite has no native date type.
- Use `INTEGER PRIMARY KEY AUTOINCREMENT` for auto-incrementing IDs.
- Use `WAL` mode for concurrent reads: `PRAGMA journal_mode = WAL;`
- Database file location: set via `DATABASE_PATH` env var, default `./data/app.db`

## Component Patterns

### Server Components by default

Every component is a React Server Component unless it needs interactivity. This is not a suggestion — it is the default behavior of Next.js 15 App Router.

```typescript
// Server Component (default) — no directive needed
// Can directly query the database, read files, call APIs
export function UserList() {
    const users = db.prepare('SELECT * FROM users').all() as User[];
    return (
        <ul>
            {users.map(user => <li key={user.id}>{user.name}</li>)}
        </ul>
    );
}
```

### When to use 'use client'

Add `'use client'` only when the component needs:
- Event handlers (onClick, onChange, onSubmit)
- React hooks (useState, useEffect, useRef)
- Browser APIs (window, document, localStorage)
- Third-party client libraries (e.g., a chart library)

```typescript
'use client';

// Client Component — interactive form
import { useState } from 'react';

export function SearchBar({ onSearch }: { onSearch: (q: string) => void }) {
    const [query, setQuery] = useState('');
    return (
        <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onSearch(query)}
        />
    );
}
```

### Props pattern

Define the props interface directly above the component, not inline. Named export, not default.

```typescript
// Good
interface UserCardProps {
    user: User;
    showEmail?: boolean;
}

export function UserCard({ user, showEmail = false }: UserCardProps) {
    return (/* ... */);
}

// Bad: inline props, default export
export default function UserCard({ user, showEmail }: { user: User; showEmail?: boolean }) {
    return (/* ... */);
}
```

### Component colocation

- Route-specific components live next to their page: `app/(dashboard)/settings/SettingsForm.tsx`
- Shared components live in `src/components/`
- If a component is used by 2+ routes, move it to `src/components/`

## Dev Commands

```bash
npm run dev          # Start Next.js dev server (port 3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint check
npm run typecheck    # TypeScript check (tsc --noEmit)
npm run db:migrate   # Run pending SQL migrations
npm run db:seed      # Insert dev seed data
npm run db:reset     # Drop and recreate DB from schema.sql + seed
npm run test         # Run tests
```

### Package.json scripts

```json
{
    "scripts": {
        "dev": "next dev",
        "build": "next build",
        "start": "next start",
        "lint": "next lint",
        "typecheck": "tsc --noEmit",
        "db:migrate": "tsx db/migrate.ts",
        "db:seed": "tsx db/seed.ts",
        "db:reset": "tsx db/reset.ts",
        "test": "vitest"
    }
}
```

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_PATH=./data/app.db          # SQLite file path
NEXTAUTH_SECRET=random-32-chars      # Auth encryption key
NEXTAUTH_URL=http://localhost:3000   # Canonical app URL
STRIPE_SECRET_KEY=sk_test_...        # Stripe server key
STRIPE_WEBHOOK_SECRET=whsec_...      # Stripe webhook signature
```

**Rules:**
- `.env.local` is gitignored. Always.
- `.env.example` is committed with placeholder values and comments.
- Access env vars through a typed config file (`lib/config.ts`), not `process.env` scattered everywhere.

```typescript
// lib/config.ts
export const config = {
    databasePath: process.env.DATABASE_PATH || './data/app.db',
    auth: {
        secret: process.env.NEXTAUTH_SECRET!,
        url: process.env.NEXTAUTH_URL || 'http://localhost:3000',
    },
    stripe: {
        secretKey: process.env.STRIPE_SECRET_KEY!,
        webhookSecret: process.env.STRIPE_WEBHOOK_SECRET!,
    },
} as const;
```

## Error Handling

- Route handlers return proper HTTP status codes with JSON bodies.
- Use Next.js `error.tsx` boundary files for page-level errors.
- Use Next.js `not-found.tsx` for 404 pages.
- Log errors server-side with context (user ID, request path). Do not expose internal errors to clients.

```typescript
// app/api/users/route.ts
export async function GET(request: Request) {
    try {
        const users = db.prepare('SELECT id, name FROM users').all();
        return Response.json(users);
    } catch (error) {
        console.error('Failed to fetch users:', error);
        return Response.json({ error: 'Internal server error' }, { status: 500 });
    }
}
```

## Testing

- Use Vitest for unit and integration tests.
- Test files live next to the code they test: `lib/auth.test.ts`
- Use a separate test database: `DATABASE_PATH=./data/test.db`
- Reset the test database before each test suite.

## What We Don't Do (and Why)

| Rule                                    | Reason                                                              |
|-----------------------------------------|---------------------------------------------------------------------|
| No ORM (Prisma, Drizzle, Knex)         | SQLite is simple. Raw SQL is clearer, faster, and has zero abstraction cost. ORMs add complexity without proportional benefit at this scale. |
| No `src/utils/` catchall directory      | Catchall directories become dumping grounds. Use domain-specific locations: `lib/auth.ts`, `lib/email.ts`. Every file should be discoverable by what it does. |
| No barrel exports (`index.ts` re-exports) | Barrel files cause circular dependency issues, make tree-shaking harder, and obscure where things actually live. Import directly from the source file. |
| No default exports                      | Named exports are greppable, refactor-friendly, and prevent silent renaming bugs. `import { UserCard }` is clearer than `import Whatever`. |
| No relative imports beyond `../`        | Deep relative paths (`../../../lib/auth`) are fragile and unreadable. Use the `@/` alias: `import { getSession } from '@/lib/auth'`. |
| No global state or context providers    | Server Components cannot use context. Use database queries, search params, and cookies for state. Client-side state should be local to the component that needs it. |
| No `any` type                           | Defeats the purpose of TypeScript. Use `unknown` and narrow, or define proper types. |
| No `.env` committed to git              | Security risk. Use `.env.example` with placeholder values instead. |
| No API routes for data Server Components can fetch | If a Server Component can query the DB directly, there is no reason to add an API route as a middleman. API routes are for client-side fetches, webhooks, and external integrations. |
| No CSS Modules or styled-components     | Tailwind CSS is the styling solution. One approach, zero decisions about CSS methodology. |
