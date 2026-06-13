# Next.js 15 + SQLite SaaS — CLAUDE.md

## Stack & Versions

| Layer          | Choice                | Why                                                               |
|----------------|-----------------------|-------------------------------------------------------------------|
| Framework      | Next.js 15 (App Router) | RSC-first, stable Server Actions, Turbopack stable                |
| Database       | better-sqlite3 v11    | Synchronous — no async overhead for a single-file embedded DB     |
| Query builder  | Drizzle ORM (SQLite)  | Typed SQL, zero-runtime, <5% overhead vs raw. Not an ORM.         |
| Validation     | zod v3                | Single source of truth for forms, DB insert, API boundaries       |
| Auth           | next-auth v5 / Auth.js| App Router native, middleware-supported                           |
| Styling        | Tailwind CSS v4       | Utility-first, no runtime, tree-shakeable                         |
| Formatting     | Biome                 | Fastest formatter+linter, single config file                      |

**Node:** >= 20 (native `fs`, `URL`, and `tls` improvements required).
**Package manager:** pnpm (strict lockfile, faster than npm/yarn).

---

## Folder Structure

```
src/
├── app/                        # App Router — colocate by feature
│   ├── (auth)/                 # Route group — auth pages (login, register)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── (dashboard)/            # Route group — authenticated pages
│   │   ├── layout.tsx          # Dashboard layout (sidebar, header)
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   └── settings/
│   │       └── page.tsx
│   ├── api/                    # ONLY for external webhooks / 3rd-party callbacks
│   │   └── webhooks/
│   │       └── stripe/route.ts
│   ├── globals.css
│   ├── layout.tsx              # Root layout (fonts, providers)
│   └── page.tsx                # Landing / public page
│
├── components/                 # React components
│   ├── ui/                     # Atomic primitives (Button, Input, Card, Modal)
│   ├── forms/                  # Form components (LoginForm, SignupForm)
│   └── shared/                 # Domain-shared components (UserAvatar, NavLink)
│
├── lib/                        # Pure logic — NEVER import `next/*` here
│   ├── db/
│   │   ├── index.ts            # Single better-sqlite3 instance (singleton)
│   │   ├── schema.ts           # Drizzle schema definitions (source of truth)
│   │   ├── migrate.ts          # Migration runner script
│   │   └── migrations/
│   │       └── 0000_setup.sql  # Append-only migration files
│   ├── auth.ts                 # Auth.js config
│   ├── validations.ts          # zod schemas (shared between client + server)
│   └── utils.ts                # Pure helpers (formatDate, cn(), slugify)
│
├── actions/                    # Server Actions — one file per domain
│   ├── auth.actions.ts
│   ├── project.actions.ts
│   └── billing.actions.ts
│
├── hooks/                      # React hooks (client-side only)
│   ├── use-debounce.ts
│   └── use-media-query.ts
│
└── types/                      # Shared TypeScript types/interfaces
    └── index.ts
```

**Rules:**
- A `lib/` file MUST NOT import from `next/*` or `@/app/*` — it must be portable.
- A `components/` file MUST NOT import from `@/actions/*` directly — pass callbacks as props.
- A Route Handler (`app/api/*`) MUST only exist for external callbacks (webhooks, OAuth). Internal mutations use Server Actions.
- Colocate by feature, not by layer. `app/(dashboard)/settings/` owns its page + layout. Shared UI goes in `components/ui/`.

---

## SQL / Migration Conventions

### better-sqlite3 singleton

```ts
// lib/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(process.env.DATABASE_URL ?? 'data/app.db');
sqlite.pragma('journal_mode = WAL');       // performance: concurrent reads
sqlite.pragma('foreign_keys = ON');        // safety: enforce FKs
sqlite.pragma('busy_timeout = 5000');      // safety: avoid SQLITE_BUSY

export const db = drizzle(sqlite, { schema });
export { sqlite }; // raw access only in migrate.ts
```

### Migration strategy: Append-only SQL files

❌ **No auto-generated migration tools** (Drizzle Kit push, Prisma migrate).
✅ **Single SQL file per release, applied in order.**

```
lib/db/migrations/
├── 0001_add_teams.sql
├── 0002_add_subscriptions.sql
└── 0003_add_api_keys.sql
```

**Why:** SQLite schema changes are rarely reversible without data loss. Append-only gives you a linear, auditable history. Drizzle Kit's `push` encourages ad-hoc changes that never get reviewed.

**Migration file format:**
```sql
-- 0002_add_subscriptions.sql
-- Adds subscription plans and team subscriptions.

CREATE TABLE IF NOT EXISTS subscriptions (
  id         TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  team_id    TEXT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  plan       TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_subscriptions_team_id ON subscriptions(team_id);
```

**Rules:**
1. Every migration is `INSERT INTO __migrations` + raw SQL executed in a transaction.
2. Never modify a migration file after it's committed — write a new one.
3. Column types: `TEXT` for everything except integers and reals. SQLite has no native date type — store ISO 8601 strings.
4. All IDs are `TEXT` (UUID / random hex), never `INTEGER PRIMARY KEY AUTOINCREMENT` — prevents ID enumeration attacks in a SaaS.
5. Every table gets `created_at` and `updated_at` TEXT columns with `datetime('now')` defaults.
6. Use `REFERENCES` (not `FOREIGN KEY (...)` standalone) — it's clearer inline.
7. Index every FK column. SQLite does not auto-index FKs.

### Running migrations

```bash
pnpm db:migrate     # applies all pending migrations
pnpm db:seed        # seeds dev data
pnpm db:reset       # drop + migrate + seed (dev only)
```

In `package.json`:
```json
{
  "scripts": {
    "db:migrate": "tsx src/lib/db/migrate.ts",
    "db:seed": "tsx src/lib/db/seed.ts",
    "db:reset": "rm -f data/app.db && pnpm db:migrate && pnpm db:seed",
    "dev": "pnpm db:migrate && next dev --turbopack"
  }
}
```

---

## Component Patterns

### Server Components first

```tsx
// ✅ GOOD: Fetch in Server Component, pass data as props
export default async function ProjectList() {
  const projects = await db.query.projects.findMany({
    limit: 20,
    orderBy: (projects, { desc }) => desc(projects.createdAt),
  });
  return <ProjectListClient projects={projects} />;
}
```

```tsx
// ❌ BAD: Fetch in client component with useEffect
export default function ProjectList() {
  const [projects, setProjects] = useState([]);
  useEffect(() => { fetch('/api/projects').then(...); }, []);
  return <div>...</div>;
}
```

### Server Actions for mutations

```tsx
// actions/project.actions.ts
'use server';

import { z } from 'zod';
import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';

const CreateProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function createProject(formData: FormData) {
  const parsed = CreateProjectSchema.parse(Object.fromEntries(formData));
  await db.insert(projects).values({
    id: crypto.randomUUID(),
    name: parsed.name,
    description: parsed.description ?? null,
  });
  revalidatePath('/dashboard');
}
```

**Rules:**
- Server Actions go in `src/actions/*.actions.ts`, one file per domain.
- Every Server Action validates input with zod before touching the DB.
- Use `useActionState` + `useFormStatus` for loading states — no manual `isPending` state.
- Route Handlers (`app/api/*`) are ONLY for external callbacks. No internal `fetch('/api/...')`.

### Client components are leaf nodes

```tsx
// components/ui/Button.tsx — thin, presentational, testable
'use client';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
}

export function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  return (
    <button
      className={cn('rounded-lg px-4 py-2 font-medium', variantStyles[variant])}
      {...props}
    >
      {children}
    </button>
  );
}
```

**Pattern:** `"use client"` only in the leaf component that needs it (interactivity, context). Parent Server Components pass data via props.

---

## Dev Commands

```bash
pnpm dev              # Start dev server (auto-runs migrations)
pnpm build            # Production build (runs db:migrate first)
pnpm start            # Start production server
pnpm db:migrate       # Apply pending migrations
pnpm db:seed          # Seed development data
pnpm db:reset         # Delete DB, re-migrate, re-seed
pnpm lint             # Biome check
pnpm lint:fix         # Biome check + fix
pnpm typecheck        # tsc --noEmit (catches what Biome misses)
pnpm test             # Vitest (unit + integration)
```

---

## Patterns to Follow

1. **Drizzle queries over raw SQL** — typed, refactorable, no string interpolation bugs.
2. **One DB connection per process** — singleton pattern in `lib/db/index.ts`. SQLite doesn't benefit from connection pooling.
3. **Zod on every boundary** — Server Action input, webhook payloads, environment variables (`z.object({ DATABASE_URL: z.string() })`).
4. **Crypto.randomUUID() everywhere** — IDs are non-sequential, non-guessable. No autoincrement.
5. **Migration before dev** — `dev` script runs `db:migrate` automatically. Never start dev with a stale schema.
6. **WAL mode + busy_timeout** — set in the singleton constructor. Prevents `SQLITE_BUSY` in concurrent reads.
7. **Small Server Actions** — one action = one operation. Compose in the UI if you need multiple effects.
8. **Route groups for layouts** — `(auth)`, `(dashboard)` route groups keep layout logic separate from URL structure.

---

## Anti-Patterns to Avoid

### ❌ `async` every better-sqlite3 call
better-sqlite3 is **synchronous by design**. Wrapping it in `await` doesn't make it faster — it adds a microtask tick for zero benefit. SQLite runs in-process; I/O is synchronous. Don't pretend it's PostgreSQL.

### ❌ Prisma with SQLite
Prisma's SQLite adapter is slow (schema parsing overhead, binary engines), produces massive `node_modules`, and has poor migration ergonomics. Drizzle is 10-50x faster and compiles to raw SQL.

### ❌ API routes for internal mutations
```ts
// ❌ BAD
fetch('/api/projects', { method: 'POST', body: JSON.stringify({...}) });

// ✅ GOOD: Server Action
const result = await createProject(new FormData(event.target));
```
API routes add HTTP overhead, serialization, and a public surface area for operations that only your UI needs. Server Actions call the DB directly.

### ❌ SQLite in Vercel serverless functions
SQLite is a file-based database. Vercel's serverless runtime is ephemeral and read-only (except `/tmp`, which is per-instance). This means SQLite data **will be lost** and instances can't share state. Use SQLite ONLY if you self-host (Railway, Fly.io, Docker VPS) OR if it's a local development / single-tenant desktop tool. For serverless, use Turso (libsql — the hosted SQLite sibling) or a real DB.

### ❌ Multiple migration tools
Don't mix Drizzle Kit push, Prisma migrate, and raw SQL files. Pick one. This template uses raw SQL files in `lib/db/migrations/` — they're version-controlled, reviewable, and work the same in CI.

### ❌ `INTEGER PRIMARY KEY` for user-facing IDs
Autoincrement IDs leak data (user count, growth rate, sequential scanning). Every public-facing entity uses `TEXT PRIMARY KEY` with `crypto.randomUUID()` or `nanoid`.

### ❌ Raw SQL strings in components
```tsx
// ❌ BAD
const result = sqlite.prepare('SELECT * FROM users WHERE id = ?').get(id);

// ✅ GOOD
const user = await db.query.users.findFirst({ where: eq(users.id, id) });
```
Drizzle provides type safety, refactoring support, and prevents SQL injection even if you forget parameterization. Components should never import `better-sqlite3` directly — only through `lib/db`.

### ❌ Fetching in `useEffect` when Server Components could do it
If data is available at request time, fetch it in a Server Component. Client-side fetching should be reserved for real-time data, user-driven search, or infinite scroll.

---

## Enforcement

- **Linter:** Biome (`pnpm lint`) catches unused imports, unsafe `any`, and style issues.
- **Type checker:** `tsc --noEmit` (`pnpm typecheck`) catches shape mismatches and missing exports.
- **Migration review:** Every PR with a new `.sql` file in `lib/db/migrations/` gets a mandatory review. Schema changes are the highest-risk operation in a SaaS.
- **No `any`:** Type everything. If a third-party lib lacks types, create a `types/` module for it.
