# CLAUDE.md — Next.js 15 + SQLite SaaS

> This file tells Claude Code how to work in this codebase.
> Every rule exists because we got burned without it.

---

## Stack & Versions

- **Framework**: Next.js 15 (App Router only — no Pages Router, ever)
- **Runtime**: Node.js 20 LTS
- **Language**: TypeScript 5.x — strict mode, no `any` escapes
- **Database**: SQLite via `better-sqlite3` (local dev) / Turso `@libsql/client` (production)
- **ORM**: None. Raw SQL with typed helpers. ORMs hide the query plan and make migrations unpredictable on SQLite.
- **Auth**: `next-auth` v5 (Auth.js) with database sessions (not JWT — JWTs can't be revoked)
- **Styling**: Tailwind CSS 4 — no CSS modules, no styled-components
- **Package manager**: pnpm (lockfile committed, no `npm` / `yarn`)
- **Validation**: `zod` for all external input (API bodies, form data, search params)
- **Testing**: Vitest (unit/integration), Playwright (e2e)

---

## Dev Commands

```bash
pnpm dev              # Start dev server on :3000
pnpm build            # Production build — fails on type errors
pnpm lint             # ESLint + strict TS checks
pnpm test             # Vitest — run unit and integration tests
pnpm test:e2e         # Playwright — run end-to-end tests
pnpm db:migrate       # Apply pending migrations (better-sqlite3)
pnpm db:seed          # Seed dev data — idempotent, safe to re-run
pnpm db:reset         # Drop and recreate local DB, then seed
pnpm db:studio        # Open Drizzle Studio or Turso shell for inspection
```

---

## Folder Structure

```
src/
├── app/                        # Next.js App Router (routes only)
│   ├── (auth)/                 # Route group: login, register, forgot-password
│   ├── (dashboard)/            # Route group: authenticated app pages
│   ├── api/                    # API routes — thin wrappers that call services
│   │   └── webhooks/           # Stripe, auth callbacks — no auth middleware
│   ├── layout.tsx              # Root layout — providers, fonts, metadata
│   └── global-error.tsx        # Top-level error boundary
├── components/
│   ├── ui/                     # Primitives: Button, Input, Dialog, Card
│   └── [feature]/              # Feature-scoped: billing/, settings/, projects/
├── lib/
│   ├── db/
│   │   ├── client.ts           # DB connection — singleton, one file
│   │   ├── schema.ts           # Table type definitions (TypeScript interfaces)
│   │   ├── migrations/         # Numbered SQL files: 0001_create_users.sql
│   │   └── queries/            # One file per entity: users.ts, projects.ts
│   ├── auth/                   # Auth config + helpers
│   ├── validators/             # Zod schemas — shared between client and server
│   └── utils.ts                # Pure functions only — no side effects, no imports from Next.js
├── hooks/                      # Client-side React hooks
├── types/                      # Shared TypeScript types (not DB types — those live in schema.ts)
└── config/                     # Environment config, feature flags, constants
```

### Rules for this structure

- **`app/` contains ONLY route files**: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, `route.ts`. No components, no utilities, no hooks. If you're adding a helper function in `app/`, move it to `lib/`.
- **One route file = one default export**. No named exports from page files.
- **API routes are thin**. The `route.ts` handler validates input, calls a service, returns a response. Business logic never lives in `route.ts`.
- **Feature folders in `components/`** match route groups. `components/billing/` feeds `app/(dashboard)/billing/`.
- **`lib/db/queries/`** is the only place that touches the database. Components and routes never import `client.ts` directly.

---

## SQL / Migration Conventions

### File naming

```
src/lib/db/migrations/
├── 0001_create_users.sql
├── 0002_create_projects.sql
├── 0003_add_projects_archived_at.sql
└── 0004_create_invoices.sql
```

- **Numbered prefix, zero-padded to 4 digits**. No timestamps — they cause merge conflicts and are unreadable.
- **Name describes the change**: `create_X`, `add_X_Y`, `drop_X`, `alter_X_Y`. Not `update_schema` or `fix_stuff`.
- **Every migration is idempotent**. Use `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (SQLite 3.35+).
- **Migrations only go forward**. No down migrations. If you need to undo, write a new migration that reverts.

### SQL style

```sql
-- Table names: plural, snake_case
CREATE TABLE IF NOT EXISTS invoices (
  -- PKs: always 'id', text type for ULIDs/UUIDs, never autoincrement
  id            TEXT PRIMARY KEY NOT NULL,
  -- FKs: singular_table_id
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount_cents  INTEGER NOT NULL,           -- money in cents, never floats
  status        TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','sent','paid','void')),
  -- Timestamps: always _at suffix, always UTC, stored as ISO 8601 text
  created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- Indexes: idx_table_column(s)
CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
```

### Non-negotiable DB rules

1. **No `AUTOINCREMENT`**. SQLite's `AUTOINCREMENT` has performance overhead and prevents row ID reuse. Use ULID strings (`01HYX...`) — they sort chronologically, are globally unique, and don't leak row count.
2. **Money is INTEGER cents**. `amount_cents INTEGER NOT NULL`. Never store money as REAL/FLOAT. `$19.99` = `1999`.
3. **Timestamps are ISO 8601 TEXT in UTC**. Not Unix epochs, not locale strings. `2025-03-15T09:30:00Z`.
4. **All FKs have `ON DELETE` behavior**. Explicitly set `CASCADE`, `SET NULL`, or `RESTRICT`. No implicit defaults.
5. **Enable WAL mode in client.ts**. `PRAGMA journal_mode=WAL;` — without this, SQLite blocks concurrent reads during writes.
6. **Enable foreign keys**. `PRAGMA foreign_keys=ON;` — SQLite disables FK enforcement by default.
7. **Run migrations at startup** in dev. In production, run as a deploy step before the app starts.
8. **Use prepared statements** for all queries. Never concatenate user input into SQL strings.

### Query file pattern

```typescript
// src/lib/db/queries/users.ts
import { db } from '../client';
import type { User, NewUser } from '../schema';

const findById = db.prepare<{ id: string }, User>(
  'SELECT * FROM users WHERE id = ?'
);

const create = db.prepare<NewUser, void>(
  'INSERT INTO users (id, email, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)'
);

export const usersQueries = {
  findById: (id: string): User | undefined => findById.get({ id }),
  create: (user: NewUser): void => create.run(user),
  // ...
} as const;
```

---

## Component Patterns

### Server Components by default

Every component is a Server Component unless it needs interactivity. If you're adding `'use client'` ask yourself: does this really need client-side JS?

```
Needs 'use client':        Does NOT need 'use client':
- onClick handlers         - Fetching data
- useState / useEffect     - Reading searchParams
- useRouter                - Conditional rendering
- Browser APIs             - Displaying formatted dates
- Form with client state   - <form> with Server Actions
```

### File naming

- **Components**: `PascalCase.tsx` — `InvoiceTable.tsx`, `PricingCard.tsx`
- **Hooks**: `camelCase.ts` prefixed with `use` — `useDebounce.ts`, `useInvoice.ts`
- **Utilities**: `camelCase.ts` — `formatCurrency.ts`, `parseDate.ts`
- **Types**: `camelCase.ts` — types are exported, not files. One `types/` file can export many types.
- **Route files**: always lowercase Next.js conventions — `page.tsx`, `layout.tsx`, `loading.tsx`

### Server Actions

```typescript
// src/app/(dashboard)/projects/actions.ts
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { projectsQueries } from '@/lib/db/queries/projects';
import { createProjectSchema } from '@/lib/validators/projects';

export async function createProject(formData: FormData) {
  const parsed = createProjectSchema.safeParse({
    name: formData.get('name'),
    description: formData.get('description'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await projectsQueries.create({
    id: generateUlid(),
    ...parsed.data,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  });

  revalidatePath('/projects');
  return { success: true };
}
```

### Error handling pattern

- **Server Actions** return `{ error: ... }` or `{ success: ... }` — never throw.
- **API routes** return proper HTTP status codes. `400` for validation, `401` for unauthed, `404` for missing, `500` for unexpected.
- **DB queries** wrap in try/catch at the service layer, not in the query file.
- **Global error boundary** (`global-error.tsx`) catches unhandled exceptions and shows a fallback UI.

### Form pattern

Use native `<form>` with Server Actions. No `e.preventDefault()`, no `fetch` calls for mutations. Client state only for optimistic UI.

```tsx
// Simple form — Server Action, no client JS
export default function NewProjectPage() {
  return (
    <form action={createProject}>
      <Input name="name" required />
      <SubmitButton />
    </form>
  );
}
```

### Data fetching

- **Server Components** fetch data directly — no `useEffect`, no `useSWR` for initial load.
- **Revalidation** via `revalidatePath()` or `revalidateTag()` in Server Actions — not time-based.
- **No client-side fetching for mutations**. Use Server Actions.
- **Client-side polling** only for real-time features (notifications, live updates). Use `useSWR` with a refresh interval, not `setInterval` + `fetch`.

---

## What We Don't Do (and Why)

### No Pages Router

The `pages/` directory does not exist. App Router is the only routing system. Mixing routers causes hydration bugs, doubles the bundle, and splits the mental model.

### No ORM (Drizzle, Prisma, Knex)

SQLite is simple enough that raw SQL with typed helpers is more predictable. ORMs add a query planner on top of SQLite's query planner, making performance opaque. Migrations are just `.sql` files — no codegen step, no migration lock tables, no ORM version coupling.

### No `any` types

`any` disables the type checker for everything it touches. Use `unknown` and narrow, or define a proper type. The only exception: third-party library type workarounds, which must have a `// eslint-disable-next-line` comment with a linked issue.

### No barrel exports (`index.ts`)

Barrel files (`components/index.ts` that re-exports everything) break tree-shaking, slow down IDE autocomplete, and create circular dependency chains. Import directly from the file: `import { Button } from '@/components/ui/Button'`.

### No relative imports

Always use the `@/` path alias. `import { db } from '@/lib/db/client'` — not `import { db } from '../../../lib/db/client'`. Relative paths break when files move and are hard to scan visually.

### No `useEffect` for data fetching

`useEffect` fetch calls cause waterfalls, layout shift, and require loading state management. Server Components fetch on the server with zero client JS. If you're writing `useEffect(() => { fetch(...) }, [])`, you're doing it wrong.

### No `REAL` / `FLOAT` for money

Floating-point arithmetic produces rounding errors (`0.1 + 0.2 !== 0.3`). All monetary values are stored as integer cents and formatted at the display layer.

### No environment variables in components

Components do not read `process.env` directly. Environment config lives in `src/config/env.ts` and is validated with Zod at startup. If a config value is missing, the app crashes immediately — not when a user hits the affected feature.

### No default exports (except route files)

Named exports are greppable, refactor-friendly, and prevent naming drift. Route files (`page.tsx`, `layout.tsx`, `route.ts`) use default exports because Next.js requires it. Everything else uses named exports.

### No `console.log` in committed code

Use a structured logger (`pino` or similar) that outputs JSON in production. `console.log` has no level, no timestamp, no structure, and is invisible in log aggregators.

---

## Path Aliases

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL=file:./dev.db                    # Local SQLite path
# DATABASE_URL=libsql://your-db.turso.io      # Turso production URL
# DATABASE_AUTH_TOKEN=your-turso-token         # Turso auth (production only)
AUTH_SECRET=generate-with-openssl-rand-base64-32
AUTH_URL=http://localhost:3000
NEXT_PUBLIC_APP_URL=http://localhost:3000       # Only NEXT_PUBLIC_ vars reach the client
```

All env vars are validated in `src/config/env.ts` using Zod:

```typescript
// src/config/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  AUTH_URL: z.string().url(),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

---

## Git Conventions

- **Branch names**: `feat/description`, `fix/description`, `chore/description`
- **Commit messages**: imperative mood, lowercase, no period. `add invoice export endpoint`, not `Added invoice export endpoint.`
- **One concern per commit**. Migration + feature code = two commits, not one.
- **Never commit `.env.local`**, `dev.db`, or `node_modules/`.

---

## Performance Rules

1. **SQLite: one writer at a time**. WAL mode allows concurrent reads, but writes still serialize. Batch writes in transactions.
2. **Add indexes for every `WHERE` and `JOIN` column**. SQLite doesn't auto-index FKs.
3. **Use `loading.tsx`** for every route segment that fetches data. Instant navigation, no white screens.
4. **Images go through `next/image`**. No raw `<img>` tags — they skip optimization and break LCP.
5. **Dynamic imports** (`next/dynamic`) for heavy client components (charts, editors, maps). Don't load a 200KB chart library on every page.

---

## Security Checklist

- [ ] All user input validated with Zod before touching the DB
- [ ] All SQL queries use prepared statements (never string concatenation)
- [ ] Auth middleware on every protected route group
- [ ] CSRF protection on all mutations (Server Actions handle this automatically)
- [ ] Rate limiting on auth endpoints and public APIs
- [ ] `Content-Security-Policy` headers configured in `next.config.ts`
- [ ] No secrets in client-side code (only `NEXT_PUBLIC_` vars reach the browser)
