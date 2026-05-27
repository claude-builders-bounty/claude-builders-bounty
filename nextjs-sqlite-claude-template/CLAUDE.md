# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated, production-ready. Every rule has a reason. Drop this into any greenfield Next.js 15 App Router + SQLite project and Claude Code knows exactly how to work.

## Stack & Versions

- **Next.js 15** (App Router, React 19, Server Components by default)
- **SQLite** via `better-sqlite3` (synchronous, fast, zero-config — no Turso/libSQL unless you need edge replication)
- **TypeScript** strict mode
- **Tailwind CSS** for styling (utility-first = no naming debates)
- **No ORM** — raw SQL with a thin typed wrapper (see SQL conventions)

## Folder Structure

```
src/
├── app/                    # Next.js App Router — routes live here
│   ├── layout.tsx          # Root layout (metadata, fonts, providers)
│   ├── page.tsx            # Home page (server component)
│   ├── (auth)/             # Route group — auth pages, no layout shared
│   ├── (dashboard)/        # Route group — authenticated pages
│   │   ├── layout.tsx      # Dashboard shell (sidebar, nav)
│   │   └── settings/       # Nested route
│   └── api/                # API routes (route.ts files)
├── components/             # Shared UI components
│   ├── ui/                 # Primitives (Button, Input, Card) — shadcn-style
│   └── [feature]/          # Feature-specific components
├── lib/
│   ├── db.ts               # DB connection + typed query helpers
│   ├── auth.ts             # Auth logic (session, middleware)
│   └── utils.ts            # Pure utility functions
├── migrations/             # SQL migration files (see conventions)
├── types/                  # Shared TypeScript types
└── tests/                  # Vitest tests (co-locate with source when possible)
```

**Why this structure**: App Router colocation means `page.tsx`, `layout.tsx`, and `loading.tsx` live together. Feature components stay near their routes. No `pages/` directory — we're App Router only.

## Commands

```bash
npm run dev           # Next.js dev server
npm run build         # Production build
npm run start         # Production server
npm run lint          # ESLint + TypeScript check
npm run test          # Vitest (unit + integration)
npm run db:migrate    # Run pending migrations
npm run db:seed       # Seed development data
npm run db:studio     # Open Drizzle Studio (if using) or sqlite viewer
```

## SQL / Migration Conventions

### Database layer (`src/lib/db.ts`)

```typescript
import Database from 'better-sqlite3';

const db = new Database(process.env.DATABASE_PATH || './data/app.db');

// Enable WAL mode for concurrent reads in production
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

export default db;
```

**Rules**:
1. **Migrations are numbered SQL files** in `migrations/`: `001_create_users.sql`, `002_add_sessions.sql`. Never edit a migration after it's applied — create a new one.
2. **Use a migration runner** (simple script, not an ORM): read `migrations/`, track applied ones in a `_migrations` table, apply new ones in order.
3. **Foreign keys always ON** — enforced at the connection level.
4. **No raw SQL in components or API routes** — queries go through typed helper functions in `lib/db.ts` or dedicated `lib/[domain].ts` files.
5. **Use prepared statements** for all queries — better-sqlite3 is synchronous, so prepared statements give type safety + performance for free.

```typescript
// lib/users.ts — example typed query layer
import db from './db';

const getUserById = db.prepare('SELECT * FROM users WHERE id = ?');
const insertUser = db.prepare(
  'INSERT INTO users (email, name) VALUES (@email, @name)'
);

export function findUser(id: number) {
  return getUserById.get(id) as User | undefined;
}
```

**Why NOT an ORM**: better-sqlite3 is already a thin, fast layer. An ORM adds abstraction that makes debugging, optimization, and migration harder. Typed prepared statements give 90% of the DX with 0% of the magic.

## Component Patterns

### 1. Server Components are the default

```tsx
// app/(dashboard)/page.tsx — Server Component by default
import { findUser } from '@/lib/users';
import { auth } from '@/lib/auth';

export default async function DashboardPage() {
  const session = await auth();       // reads cookie, no useEffect
  const user = findUser(session.userId);  // sync SQL, no fetch/axios
  return <DashboardShell user={user} />;
}
```

**Why**: Server Components let you `await` data directly. No `useEffect`, no loading states for initial data, no API route indirection for your own database.

### 2. Client Components are the exception — mark them explicitly

```tsx
'use client';
// Only use for: event handlers, useState/useEffect, browser APIs, context consumers
```

### 3. Data mutations go through Server Actions

```tsx
// app/(dashboard)/settings/actions.ts
'use server';
import { updateUser } from '@/lib/users';
import { revalidatePath } from 'next/cache';

export async function updateName(formData: FormData) {
  const session = await auth();
  updateUser(session.userId, { name: formData.get('name') as string });
  revalidatePath('/dashboard/settings');
}
```

**Why**: Server Actions = no API route boilerplate, progressive enhancement (works without JS), automatic CSRF protection.

### 4. Loading + Error boundaries are mandatory

Every route group gets `loading.tsx` (skeleton) and `error.tsx` (error recovery). No exceptions.

## What We Don't Do (And Why)

| Anti-pattern | Why we avoid it |
|---|---|
| `useEffect` for data fetching | Server Components fetch data. `useEffect` fetches = double render + waterfall |
| API routes calling our own database | Unnecessary network hop. Server Components + Server Actions talk to DB directly |
| `any` type | TypeScript strict mode. If you need `any`, write a proper type or use `unknown` |
| Environment variables in client code | Prefix client-safe vars with `NEXT_PUBLIC_`. Everything else stays server-only |
| Barrel exports (`index.ts` re-exporting everything) | Kills tree-shaking, slows HMR, obscures dependencies. Import directly from the source file |
| ORMs (Prisma, Drizzle) | Adds build steps, codegen, and abstraction for a DB that doesn't need it. Typed prepared statements are sufficient |
| `.env` committed to git | Use `.env.example` with dummy values. Real secrets go in your deployment platform |
| `fetch` to call your own backend | Server Components can import and call functions directly. `fetch` = unnecessary serialization + network |

## Testing

- **Vitest** for unit + integration tests
- Database tests use a **temporary SQLite file** (not mock — SQLite is fast enough for real tests)
- Test files co-located: `lib/users.test.ts` next to `lib/users.ts`
- One `describe` per exported function, one `it` per behavior

## First-Time Setup for a New Project

```bash
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app
cd my-saas
npm install better-sqlite3
npm install -D vitest @types/better-sqlite3
mkdir -p src/lib src/migrations src/components/ui data
echo "DATABASE_PATH=./data/app.db" > .env.local
```
