# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> **This is an opinionated, production-ready guide for Claude Code.**
> Every rule here exists for a specific reason. If you're unsure why a rule exists, ask — don't skip it.

---

## Stack & Versions

| Tool | Version | Why |
|------|---------|-----|
| Next.js | 15 (App Router) | Server Components, streaming, built-in caching |
| TypeScript | 5.x | Strict mode only — no `any` |
| SQLite | via `better-sqlite3` or Turso | Zero-ops, single-file persistence; Turso for edge/multi-region |
| Tailwind CSS | 3.x | Utility-first, no CSS modules in new code |
| Zod | latest | All external input validated at the boundary |
| Drizzle ORM | latest | Type-safe SQL, explicit migrations, no magic |

---

## Folder Structure

```
app/
├── (auth)/               # Route group: login, register, forgot-password
│   ├── login/page.tsx
│   └── register/page.tsx
├── (dashboard)/          # Route group: authenticated pages
│   ├── layout.tsx        # Auth guard lives here
│   └── settings/page.tsx
├── api/                  # Route handlers only — no business logic here
│   └── webhooks/
├── layout.tsx            # Root layout: fonts, providers
└── page.tsx              # Landing page

components/
├── ui/                   # Pure presentational: Button, Input, Card, etc.
│   └── button.tsx
├── forms/                # Form components with react-hook-form
└── [feature]/            # Feature-scoped components (e.g., billing/, auth/)

lib/
├── db/
│   ├── index.ts          # DB connection singleton (better-sqlite3 or Turso)
│   ├── schema.ts         # Drizzle schema — single source of truth
│   └── migrations/       # SQL migration files, never edited after merge
├── auth/
│   ├── session.ts        # Session management (iron-session or lucia)
│   └── middleware.ts     # Edge-compatible auth check
├── validations/          # Zod schemas for all forms and API inputs
└── utils/                # Pure functions, no side effects

drizzle/
└── migrations/           # Drizzle-generated migration files
    └── 0001_init.sql

scripts/
└── seed.ts               # Dev seed data (never imported in app code)
```

**Rules:**
- `app/api/` handlers call `lib/` functions — they never contain SQL or business logic directly
- `components/ui/` components are stateless and have no data-fetching
- `lib/db/index.ts` exports a single `db` instance — never create a second connection

---

## Database / SQL / Migration Rules

### Connection

```typescript
// lib/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(process.env.DATABASE_URL ?? 'local.db');
sqlite.pragma('journal_mode = WAL');   // Required for concurrent reads
sqlite.pragma('foreign_keys = ON');    // Always enforce FK constraints

export const db = drizzle(sqlite, { schema });
```

**Why WAL?** Write-Ahead Logging allows concurrent reads during writes — critical for a web app.
**Why foreign_keys?** SQLite disables FK enforcement by default. This is a footgun.

### Schema

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id:        text('id').primaryKey(),          // Use CUID2, not UUID
  email:     text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
}, (t) => ({
  emailIdx: index('users_email_idx').on(t.email),
}));
```

**Rules:**
- All IDs use `cuid2` — never auto-increment integers for user-facing IDs
- All timestamps are stored as UNIX integers, not ISO strings
- Always add an index for columns used in `WHERE` or `JOIN` clauses
- Column names use `snake_case` in the DB; Drizzle maps them in TypeScript

### Migrations

```bash
# Generate a migration (after schema change)
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate
```

**Rules:**
- **Never edit a migration file after it has been committed and merged.** Create a new one.
- Migration files are append-only history — they document what happened to the DB
- Never run raw `ALTER TABLE` manually in production — always go through Drizzle
- Seed data goes in `scripts/seed.ts`, never in a migration file

---

## Component Patterns

### Server Components (default)

```tsx
// app/(dashboard)/settings/page.tsx
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { getSession } from '@/lib/auth/session';

export default async function SettingsPage() {
  const session = await getSession();
  const user = await db.query.users.findFirst({
    where: eq(users.id, session.userId),
  });

  return <SettingsForm user={user} />;
}
```

**Why:** Fetch data at the Server Component level. Never fetch in a `useEffect` when a Server Component can do it.

### Client Components

```tsx
'use client';

// Only mark as client when you need:
// - useState / useEffect
// - browser APIs (window, localStorage)
// - event listeners
// - third-party client-only libraries
```

**Rule:** Default to Server Components. Add `'use client'` only when you have a specific reason.

### Forms

```tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema } from '@/lib/validations/auth';

export function LoginForm() {
  const form = useForm({
    resolver: zodResolver(loginSchema),
  });
  // ...
}
```

**Rules:**
- All forms use `react-hook-form` + Zod schema validation
- The same Zod schema is used on both client and server — single source of truth
- Server Actions are preferred over API routes for form mutations

---

## Dev Commands

```bash
# Start dev server
npm run dev

# Run migrations
npx drizzle-kit migrate

# Generate new migration after schema change
npx drizzle-kit generate

# Seed the database
npx tsx scripts/seed.ts

# Type-check
npx tsc --noEmit

# Lint
npm run lint

# Format
npx prettier --write .
```

---

## What We Do

- ✅ **Server Components** for all data-fetching pages
- ✅ **Server Actions** for form submissions and mutations
- ✅ **Zod** for all input validation — at the API boundary and in forms
- ✅ **Drizzle** for all DB access — no raw SQL in application code
- ✅ **WAL mode + FK enforcement** on every SQLite connection
- ✅ **CUID2** for all primary keys
- ✅ **Route groups** `(auth)` and `(dashboard)` to separate concerns

---

## What We Don't Do (And Why)

| ❌ Anti-pattern | ✅ What to do instead | Why |
|-----------------|----------------------|-----|
| `any` in TypeScript | Proper types or `unknown` | Defeats the purpose of TypeScript |
| Raw SQL strings in app code | Drizzle query builder | SQL injection risk; no type safety |
| `useEffect` for data fetching | Server Components | Waterfall requests, worse UX |
| Auto-increment integer IDs | CUID2 | IDs become guessable/enumerable |
| Business logic in API routes | Dedicated `lib/` functions | Not testable, not reusable |
| Editing merged migrations | New migration file | Breaks reproducibility |
| Multiple DB connections | Single `db` singleton | SQLite only supports one writer |
| Storing timestamps as strings | UNIX integer timestamps | Sorting, comparison, and storage efficiency |
| Components in `app/` directory | `components/` directory | App dir is for routing only |
| `console.log` in production | Structured logger (pino) | Log noise, performance, no structured search |

---

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL=./local.db
SESSION_SECRET=<32-char-random-string>
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Production only
DATABASE_URL=<turso-connection-string>
TURSO_AUTH_TOKEN=<turso-token>
```

**Rule:** All env vars must be validated with Zod at startup in `lib/env.ts`. Never access `process.env` directly in components.

```typescript
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  SESSION_SECRET: z.string().min(32),
  NODE_ENV: z.enum(['development', 'production', 'test']),
});

export const env = envSchema.parse(process.env);
```

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `kebab-case` | `user-settings.tsx` |
| Components | `PascalCase` | `UserSettings` |
| Functions | `camelCase` | `getUserById` |
| DB columns | `snake_case` | `created_at` |
| DB tables | `snake_case`, plural | `users`, `blog_posts` |
| Env vars | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` |
| Types/Interfaces | `PascalCase` | `UserSession` |
| Zod schemas | `camelCase` + `Schema` suffix | `loginSchema` |

---

## Testing

```bash
# Unit tests
npx vitest

# Integration tests (uses test DB)
DATABASE_URL=:memory: npx vitest integration/
```

**Rules:**
- Unit tests live next to the file they test: `lib/utils/format.test.ts`
- Integration tests use an in-memory SQLite database — never the dev DB
- Always reset the DB between integration test runs

---

## Security Checklist

- [ ] All user input validated with Zod before use
- [ ] Session cookie uses `httpOnly`, `secure`, `sameSite: 'lax'`
- [ ] CSRF protection on all state-changing Server Actions
- [ ] No sensitive data in `NEXT_PUBLIC_` env vars
- [ ] Rate limiting on auth endpoints (`/api/auth/*`)
- [ ] SQL injection impossible (Drizzle query builder only)
