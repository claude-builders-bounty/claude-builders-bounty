# Project

Next.js 15 SaaS with SQLite. App Router only, no Pages Router.

## Stack

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **Database:** SQLite via better-sqlite3 (sync, no ORM)
- **Auth:** Auth.js v5
- **Styling:** Tailwind CSS 4
- **Package manager:** pnpm

## Folder Structure

```
src/
  app/                    # App Router pages and layouts
    (auth)/               # Auth route group (login, register)
    (dashboard)/          # Authenticated route group
      layout.tsx          # Dashboard layout with sidebar/nav
    api/                  # API routes
    layout.tsx            # Root layout
    page.tsx              # Landing page
  components/
    ui/                   # Reusable primitives (button, input, card)
    [feature]/            # Feature-specific components
  lib/
    db.ts                 # Database connection singleton
    db/
      schema.sql          # Full schema, single source of truth
      migrations/         # Numbered: 001-create-users.sql, 002-add-teams.sql
      queries/            # Named query files grouped by entity
        users.ts
        teams.ts
    auth.ts               # Auth.js config
    utils.ts              # Pure utility functions
  types/                  # Shared TypeScript types (no enums, use const objects)
```

## Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm lint         # ESLint
pnpm typecheck    # tsc --noEmit
pnpm db:migrate   # Run pending migrations
pnpm db:seed      # Seed dev data
```

## Database Rules

**Schema:** `lib/db/schema.sql` is the canonical schema. Every table lives there. When you need to understand the data model, read this file.

**Migrations:** Numbered SQL files in `lib/db/migrations/`. Always forward-only, never edit an existing migration. Name format: `NNN-description.sql`. Each migration is idempotent -- wrap DDL in `CREATE TABLE IF NOT EXISTS` or check existence before altering.

**Queries:** Write raw SQL in `lib/db/queries/`. One file per entity. Each export is a function that takes the db instance and params, runs a prepared statement, returns typed results. No query builders, no ORMs.

```typescript
// lib/db/queries/users.ts
import { db } from '@/lib/db';

export function getUserById(id: string) {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id) as User | undefined;
}

export function createUser(email: string, name: string) {
  return db.prepare('INSERT INTO users (id, email, name) VALUES (?, ?, ?)').run(crypto.randomUUID(), email, name);
}
```

**Connection:** Single `db` export from `lib/db.ts`. Uses better-sqlite3 with WAL mode enabled. Never create a second connection.

```typescript
// lib/db.ts
import Database from 'better-sqlite3';
import path from 'path';

const db = new Database(path.join(process.cwd(), 'data', 'app.db'));
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

export { db };
```

## Component Patterns

**Server Components by default.** Only add `'use client'` when you need interactivity (event handlers, hooks, browser APIs). If a component just renders data, it's a Server Component.

**Naming:** PascalCase files for components (`UserCard.tsx`), kebab-case for routes and directories. Component files export a single default component matching the filename.

**Data fetching:** Fetch in Server Components or Route Handlers. Never fetch from Client Components directly -- pass data down as props or use Server Actions.

**Server Actions:** Put mutations in the component file or a colocated `actions.ts`. Always validate input with zod. Always revalidate the path or tag after mutation.

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { createUser } from '@/lib/db/queries/users';

const schema = z.object({ email: z.string().email(), name: z.string().min(1) });

export async function signupAction(formData: FormData) {
  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten().fieldErrors };
  createUser(parsed.data.email, parsed.data.name);
  revalidatePath('/dashboard');
}
```

**Forms:** Use native `<form action={serverAction}>` with `useActionState` for pending/error states. No `onSubmit` + `fetch` patterns.

**Loading states:** Use `loading.tsx` files in route segments. Use `<Suspense>` with fallbacks for component-level loading. Never show a blank screen.

**Error handling:** Use `error.tsx` boundary files. Log errors server-side, show user-friendly messages client-side.

## API Routes

Use Route Handlers (`app/api/`) for webhook receivers and external integrations only. Internal data mutations use Server Actions, not API routes.

All Route Handlers return `NextResponse.json()`. Always set appropriate status codes. Validate request bodies with zod.

## Styling

Tailwind only. No CSS modules, no styled-components, no inline style objects. Use `cn()` utility (clsx + twMerge) for conditional classes:

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## TypeScript

- Strict mode, no `any`. Use `unknown` and narrow.
- No enums. Use `as const` objects with derived types.
- Infer return types, don't annotate them unless the function is exported from a library file.
- Shared types go in `types/`. Component prop types are colocated.

## What We Don't Do

**No ORM.** Prisma, Drizzle, etc. add abstraction that hides what's happening. Raw SQL in prepared statements is faster, more predictable, and easier to debug with SQLite.

**No `useEffect` for data fetching.** Server Components and Server Actions handle all data. If you're reaching for useEffect to load data, you're fighting the framework.

**No barrel exports.** No `index.ts` files that re-export everything from a directory. Import directly from the source file. Barrel exports break tree-shaking and make it harder to trace dependencies.

**No relative imports.** Use the `@/` path alias for everything. `import { db } from '@/lib/db'` not `import { db } from '../../lib/db'`.

**No client-side state management libraries.** No Redux, Zustand, Jotai for server data. URL search params + Server Components handle most state. For local UI state, `useState` is fine.

**No `.env.local` in the repo.** Use `.env.example` with dummy values. Document every env var with a comment.
