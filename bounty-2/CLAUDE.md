# CLAUDE.md — Next.js 15 + SQLite SaaS

> Drop this file into any greenfield Next.js 15 App Router + SQLite project.
> Every rule below exists because we learned the hard way what happens without it.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | App Router is the default. Pages Router is legacy. |
| UI | React | 19.x | Server Components, `use()`, Actions — all require 19. |
| Language | TypeScript | 5.x | Non-negotiable. `any` is banned outside prototype spikes. |
| Database | better-sqlite3 (local) / Turso (prod) | latest | Same SQL dialect, zero ORM overhead, embedded or edge-deployed. |
| Styling | Tailwind CSS | 4.x | Utility-first, zero runtime cost, ships only used classes. |
| Auth | next-auth / Auth.js | 5.x | Server-side sessions, App Router native. |

**Rule:** Pin exact versions in `package.json`. Why: `^` drift broke production once. Never again.

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router — routes only
│   ├── (auth)/             # Route group: auth pages (no URL prefix)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/        # Route group: authenticated area
│   │   ├── layout.tsx      # Shared sidebar/header for dashboard
│   │   ├── page.tsx        # / → dashboard home
│   │   └── settings/
│   ├── api/                # Route handlers (REST, not tRPC)
│   │   └── health/
│   ├── layout.tsx          # Root layout — fonts, providers
│   └── globals.css
├── components/
│   ├── ui/                 # Generic, reusable primitives (Button, Dialog, Input)
│   └── features/           # Domain-specific compositions (UserTable, PricingCard)
├── db/
│   ├── migrations/         # Numbered .sql files
│   ├── schema.ts           # Typed query helpers (not an ORM)
│   ├── client.ts           # Database connection singleton
│   └── seed.ts             # Dev seed data
├── lib/
│   ├── auth.ts             # Auth config & helpers
│   ├── errors.ts           # Typed error classes
│   ├── validators.ts       # Zod schemas — single source of truth for shapes
│   └── utils.ts            # Pure functions only (formatDate, cn(), etc.)
└── types/
    └── index.ts            # Shared TypeScript types, not Zod-inferred
```

**Rules:**

1. **`app/` contains only routes and layouts.** Why: Mixing business logic into route files creates 800-line monsters that are impossible to test.

2. **Route groups use `()` folders for shared layouts, not URL segments.** Why: `(dashboard)` gives you a sidebar without polluting the URL with `/dashboard/`.

3. **`components/ui/` is framework-level. `components/features/` is product-level.** Why: When you swap Button, you touch one folder. When you refactor pricing, you touch the other. Separation of concerns by rate of change.

4. **`lib/` is pure logic. No React imports.** Why: If `lib/validators.ts` imports React, it's in the wrong place. Pure functions are testable functions.

5. **Colocate test files: `login-form.test.tsx` next to `login-form.tsx`.** Why: `__tests__/` directories become graveyards nobody maintains. Proximity = accountability.

---

## SQL & Migration Conventions

### Migrations

```
db/migrations/
├── 001-create-users.sql
├── 002-create-projects.sql
├── 003-add-user-avatar.sql
```

**Rules:**

1. **Zero-padded 3-digit prefix, kebab-case description.** Why: `001` sorts correctly up to 999 migrations. No `v1`, no dates, no timestamps.

2. **Every migration is forward-only.** Why: Down migrations are a lie — they rarely account for data transformations. Use backups instead.

3. **One logical change per migration.** Why: `003-add-user-avatar-and-rename-email-column.sql` is two migrations. Split them so `git blame` tells a story.

4. **Migrations must be idempotent where possible.** Use `CREATE TABLE IF NOT EXISTS`. Why: Dev environments crash mid-migration. Don't make it worse.

### Query Patterns

```typescript
// ✅ DO: Prepared statements via typed helpers
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(userId) as User | undefined;

// ❌ DON'T: String interpolation
db.exec(`SELECT * FROM users WHERE id = ${userId}`); // SQL injection
```

```typescript
// db/client.ts — singleton pattern
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'data', 'app.db');

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');       // Why: WAL = concurrent reads during writes
    _db.pragma('foreign_keys = ON');        // Why: SQLite doesn't enforce FK by default
  }
  return _db;
}
```

**Rules:**

1. **Always use prepared statements.** Why: Performance (query plan caching) AND security (parameterization). Not negotiable.

2. **No ORM. No query builder. Raw SQL only.** Why: Prisma adds 30s to cold starts and generates N+1 queries. Drizzle is better but still an abstraction over SQL you'll fight. You know SQL. Write SQL.

3. **WAL mode, always.** Why: Default journal mode locks the entire DB on write. WAL allows concurrent reads. Essential for any SaaS with more than one user.

4. **Foreign keys ON, always.** Why: SQLite ignores FK constraints by default. Without this pragma, your "relationships" are decorative.

5. **Type assertions on query results.** Use `as User`, not runtime validation at the DB boundary. Why: Zod validation belongs at the API/request boundary. The DB layer should be fast and trust its own schema.

---

## Component Patterns

### Server Components by Default

```typescript
// app/(dashboard)/page.tsx — this is a Server Component
import { getDb } from '@/db/client';
import { ProjectList } from '@/components/features/project-list';

export default async function DashboardPage() {
  const projects = getDb().prepare('SELECT * FROM projects WHERE user_id = ?').all(userId);
  return <ProjectList projects={projects} />;
}
```

```typescript
// components/features/project-list.tsx — also a Server Component
interface ProjectListProps {
  projects: Project[];
}

export function ProjectList({ projects }: ProjectListProps) {
  return (
    <ul>
      {projects.map(p => <li key={p.id}>{p.name}</li>)}
    </ul>
  );
}
```

**Rules:**

1. **Server Components are the default. Only add `'use client'` when you need:**
   - `useState`, `useEffect`, `useReducer`
   - Browser APIs (`window`, `localStorage`, `intersectionObserver`)
   - Event handlers (`onClick`, `onChange`)

   Why: Server Components ship zero JS. A page that renders static data should send zero client bundle.

2. **Never `'use client'` at the page/layout level.** Push interactivity down. Why: A `'use client'` page makes the entire tree client-rendered, defeating the purpose of RSC.

3. **Data fetching belongs in Server Components or Server Actions.** Why: Client-side `fetch` means loading spinners, waterfall requests, and stale data. Server Components fetch at render time on the server — no waterfall.

4. **Colocate related files:**
   ```
   components/features/
   └── pricing-card/
       ├── pricing-card.tsx
       ├── pricing-card.test.tsx
       └── pricing-card.stories.tsx   (if using Storybook)
   ```
   Why: A component is a folder, not a scattered set of imports across 3 directories.

---

## Server Actions

```typescript
// app/(dashboard)/settings/actions.ts
'use server';

import { getDb } from '@/db/client';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';

const UpdateNameSchema = z.object({
  name: z.string().min(1).max(100),
});

export async function updateName(formData: FormData) {
  const { name } = UpdateNameSchema.parse({ name: formData.get('name') });
  // TODO: get userId from session
  
  getDb().prepare('UPDATE users SET name = ? WHERE id = ?').run(name, userId);
  revalidatePath('/settings');
}
```

**Rules:**

1. **Server Actions live in `actions.ts` files colocated with their route.** Why: Actions are route-specific business logic. Putting them in `lib/` creates a junk drawer.

2. **Always validate with Zod at the action boundary.** Why: `formData.get()` returns `string | null`. Never trust it. Zod gives you typed output and error messages.

3. **`revalidatePath` after mutations.** Why: SQLite is synchronous — the data is already updated. But Next.js caches the rendered RSC output. You must tell it to re-render.

4. **Never return UI from actions.** Return data or throw. Why: Actions should be callable from anywhere (forms, buttons, programmatic). UI coupling makes them single-use.

---

## Dev Commands

```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "migrate": "node -e \"require('./db/migrate').run()\"",
    "seed": "tsx db/seed.ts",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "check": "npm run typecheck && npm run lint"
  }
}
```

**Rules:**

1. **`npm run dev` uses Turbopack.** Why: Fast refresh < 100ms vs Webpack's 2-3s. Only disable if Turbopack breaks something specific.

2. **`npm run build` must pass with zero warnings.** Why: Warnings in CI become invisible. Make them errors now or they'll bite in prod.

3. **`npm run migrate` is separate from `npm run build`.** Why: Migrations modify data. Builds should be stateless. Combining them means failed migrations = failed deploys = downtime.

4. **`npm run check` runs before every commit.** Why: Catching type errors in CI is 10 minutes too late.

---

## Naming Conventions

| What | Convention | Example | Why |
|---|---|---|---|
| Files & folders | `kebab-case` | `user-profile.tsx`, `api-key-row.tsx` | Consistent with Next.js conventions and URL segments. |
| Components (exports) | `PascalCase` | `export function UserProfile()` | React convention. Dev tools display the PascalCase name. |
| Functions / utilities | `camelCase` | `export function formatDate()` | JavaScript convention. |
| Constants | `UPPER_SNAKE` | `const MAX_RETRY = 3` | Visually distinct from variables. |
| CSS classes | Via Tailwind | `className="flex items-center gap-2"` | No custom class names. Tailwind utilities only. |
| Environment variables | `UPPER_SNAKE` | `DATABASE_URL`, `AUTH_SECRET` | 12-factor app convention. |
| Route params | `camelCase` | `{ userId }` from `[userId]` | Next.js generates them this way. |
| Database columns | `snake_case` | `created_at`, `user_id` | SQL convention. Different from JS = easy to spot boundary. |

**Rule:** If you're unsure, match the prevailing convention in the file you're editing. Why: Consistency within a file matters more than global consistency.

---

## Anti-Patterns (What We Don't Do)

### ❌ No Prisma / Drizzle / Any ORM
**Why:** ORMs add cold-start overhead, generate surprising queries, and create a second "language" to learn. We know SQL. We write SQL. The `db/client.ts` file with prepared statements is 30 lines and does everything we need.

### ❌ No SWR / React Query by Default
**Why:** Server Components eliminate the need for client-side data fetching in most cases. Only add a data-fetching library when you genuinely need polling, optimistic updates, or offline support. Premature caching layers create stale-data bugs.

### ❌ No CSS-in-JS (styled-components, Emotion, Stitches)
**Why:** Runtime CSS-in-JS adds 5-15KB to the JS bundle, causes SSR hydration mismatches, and is unnecessary when Tailwind exists. If you need dynamic styles, use inline `style={{ }}`.

### ❌ No `useEffect` for Data Fetching
**Why:** This is the #1 React anti-pattern. Use Server Components for initial data, Server Actions for mutations, and `use()` for suspense-based loading. `useEffect` + `fetch` creates loading flicker, race conditions, and waterfall requests.

### ❌ No Default Exports for Components
```typescript
// ❌ DON'T
export default function UserProfile() {}

// ✅ DO
export function UserProfile() {}
```
**Why:** Named exports enable fast refresh reliability, better IDE navigation ("Find All References"), and prevent name drift between file and export.

### ❌ No Barrel Files (`index.ts` re-exporting everything)
**Why:** Barrel files defeat tree-shaking, slow down builds, and create circular dependency traps. Import directly: `import { Button } from '@/components/ui/button'`.

### ❌ No `any` in Production Code
**Why:** `any` opts out of TypeScript's entire value prop. Use `unknown` and narrow, or define a proper type. Prototyping? Fine. Shipping? No.

### ❌ No `@ts-ignore` / `@ts-expect-error` Without a Linked Issue
**Why:** Suppressed errors become permanent errors. If you must suppress, add `// TODO(#123): fix this after upgrading X` so it has an expiry.

### ❌ No `console.log` in Production
**Why:** `console.log` in server code logs to stdout in production. Use a structured logger or remove it. Pre-commit hooks should catch this.

### ❌ No Middleware for Data Fetching
**Why:** Next.js middleware runs on the edge runtime — it can't access `better-sqlite3`. Use middleware only for auth redirects and header manipulation. Fetch data in Server Components.

---

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL=file:./data/app.db          # local: file path | prod: libsql://...
AUTH_SECRET=                             # generate: openssl rand -base64 32
AUTH_URL=http://localhost:3000           # OAuth callback URL
```

**Rule:** All env vars must have a fallback or a startup check. Why: Silent `undefined` in prod leads to "cannot read property of undefined" at 3 AM.

```typescript
// lib/env.ts
export const env = {
  DATABASE_URL: process.env.DATABASE_URL ?? 'file:./data/app.db',
  AUTH_SECRET: assertEnv('AUTH_SECRET'),
} as const;

function assertEnv(key: string): string {
  const value = process.env[key];
  if (!value) throw new Error(`Missing env var: ${key}`);
  return value;
}
```

---

## Git Conventions

1. **Conventional commits:** `feat:`, `fix:`, `chore:`, `docs:`. Why: Changelog generation and semantic versioning.

2. **Small, atomic commits.** One logical change per commit. Why: Bisect works. Revert is surgical. Code review is fast.

3. **No `--no-verify` commits.** Why: The pre-commit hooks exist because something broke without them.

---

## Quick Reference

```
# New feature checklist
1. Create migration: db/migrations/0XX-describe-change.sql
2. Run npm run migrate
3. Add types to types/index.ts
4. Build Server Component in app/
5. Extract interactivity to components/features/ with 'use client'
6. Add Server Action in route-level actions.ts
7. Validate inputs with Zod in lib/validators.ts
8. npm run check passes
9. Commit: feat: short description
```

---

*This file is the source of truth for how this project works. When in doubt, read this first. When this file is wrong, update it.*
