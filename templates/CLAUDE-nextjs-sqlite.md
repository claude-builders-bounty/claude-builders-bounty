# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> Drop this file into the root of any greenfield SaaS project built with Next.js 15 App Router and SQLite. Claude Code will read it automatically and follow these conventions without asking clarifying questions.

---

## Stack & Versions

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 15.x |
| Runtime | Node.js | ≥ 20 |
| Database | SQLite | via `better-sqlite3` or `@libsql/client` (Turso) |
| ORM / Query | `drizzle-orm` | latest |
| Styling | Tailwind CSS v4 | |
| Auth | `next-auth` (Auth.js v5) | |
| Validation | Zod | |
| Package Manager | pnpm | ≥ 9 |
| Linting | Biome | (replaces ESLint + Prettier) |

**Why these choices:**
- `better-sqlite3` is synchronous and fast for single-process SaaS; swap to `@libsql/client` when you need Turso edge deployment — the Drizzle dialect change is one line
- Drizzle over Prisma: lighter bundle, explicit SQL, better TypeScript inference, no runtime codegen
- Biome over ESLint+Prettier: single tool, 10-100x faster, same output quality

---

## Folder Structure

```
├── src/
│   ├── app/                    # App Router (file-based routing)
│   │   ├── (auth)/             # Route group: login, register, forgot-password
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── register/
│   │   │       └── page.tsx
│   │   ├── (dashboard)/        # Route group: authenticated app pages
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   ├── settings/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx     # Dashboard shell (sidebar, header)
│   │   ├── api/                # API routes (edge-compatible where possible)
│   │   │   └── trpc/           # tRPC or standard REST handlers
│   │   │       └── route.ts
│   │   ├── layout.tsx          # Root layout (providers, fonts, metadata)
│   │   ├── page.tsx            # Landing page
│   │   └── not-found.tsx
│   ├── components/             # React components
│   │   ├── ui/                 # Primitive UI (buttons, inputs, modals) — shadcn/ui style
│   │   ├── layout/             # Structural (Header, Sidebar, Footer)
│   │   └── features/           # Feature-specific (e.g., BillingForm, UserTable)
│   ├── db/                     # Database layer
│   │   ├── schema.ts           # Drizzle table definitions
│   │   ├── migrations/         # Drizzle migration files (auto-generated)
│   │   ├── client.ts           # Drizzle client singleton (prevents connection leaks)
│   │   └── seed.ts             # Development seed data
│   ├── lib/                    # Shared utilities
│   │   ├── auth.ts             # next-auth config
│   │   ├── utils.ts            # cn() helper, formatters
│   │   └── constants.ts        # App-wide constants
│   ├── hooks/                  # Custom React hooks
│   │   └── use-current-user.ts
│   ├── actions/                # Server Actions (mutations)
│   │   ├── user-actions.ts
│   │   └── billing-actions.ts
│   └── types/                  # TypeScript type definitions
│       └── index.ts
├── public/                     # Static assets
├── tests/                      # Test files (co-located `*.test.tsx` also OK)
├── drizzle.config.ts           # Drizzle Kit config
├── biome.json                  # Linter/formatter config
├── next.config.ts              # Next.js config
└── package.json
```

**Naming conventions:**
- **Files:** kebab-case for everything (`user-table.tsx`, `use-current-user.ts`)
- **Components:** PascalCase for exports, kebab-case for files (`UserTable` in `user-table.tsx`)
- **Server Actions:** `*-actions.ts` suffix, named exports like `updateUserProfile`
- **DB schema:** singular table names in Drizzle (`user`, `subscription`), not plural

**Why route groups `(auth)` and `(dashboard)`:**
They let you apply different layouts without nesting URL segments. `/dashboard/settings` not `/dashboard/dashboard/settings`.

---

## SQL & Migration Conventions

### Drizzle Schema Rules

```typescript
// db/schema.ts — ALWAYS use this pattern
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const user = sqliteTable('user', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull().unique(),
  name: text('name'),
  role: text('role', { enum: ['user', 'admin'] }).default('user').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp_ms' })
    .notNull()
    .default(sql`(unixepoch() * 1000)`),
  updatedAt: integer('updated_at', { mode: 'timestamp_ms' })
    .notNull()
    .default(sql`(unixepoch() * 1000)`),
});
```

**Rules:**
1. **Every table has** `id` (UUID text), `createdAt`, `updatedAt`
2. **Use `text` for UUIDs**, not integer — SQLite integers overflow at 2^53
3. **`$defaultFn(() => crypto.randomUUID())`** — generate IDs in JS, not DB
4. **Timestamps as `timestamp_ms` integers** — SQLite has no native datetime type
5. **`enum` via `text` with `enum` option** — not a separate enum table (SQLite has no ENUM)
6. **Never use raw SQL in queries** — always go through Drizzle. Exception: `sql`` tagged templates for complex expressions

### Migration Workflow

```bash
# After editing db/schema.ts:
pnpm db:generate   # generates migration file
pnpm db:migrate    # applies to local DB
pnpm db:push       # dev shortcut (no migration file, direct push)
```

**Rules:**
- **Production:** always `generate` → review the migration file → `migrate`
- **Development:** `push` is fine for throwaway changes
- **Never edit migration files manually** — Drizzle generates them deterministically
- **Commit migration files** — they are part of the codebase history

---

## Component Patterns

### Server vs Client Components

```typescript
// ✅ Server Component (default) — for data fetching, layout, SEO
export default async function DashboardPage() {
  const user = await getCurrentUser();  // server action / DB call
  return <DashboardShell user={user} />;
}

// ✅ Client Component — for interactivity
'use client';
export function UserPreferences() {
  const [name, setName] = useState('');
  return <input value={name} onChange={e => setName(e.target.value)} />;
}
```

**Rules:**
1. **Default to Server Components** — only add `'use client'` when you need `useState`, `useEffect`, event handlers
2. **Keep `'use client'` at the leaves** — the boundary component is client, its children can be server
3. **Server Actions go in `src/actions/`**, not inline in components
4. **Pass data down as props**, don't fetch the same data in multiple components

### Data Fetching Pattern

```typescript
// ✅ Good: server component fetches, passes to client component
export default async function UsersPage() {
  const users = await db.select().from(user);
  return <UserTable users={users} />;  // UserTable is 'use client'
}
```

**Never do this:**
```typescript
// ❌ Bad: client component fetches data
'use client';
export function UsersPage() {
  const [users, setUsers] = useState([]);
  useEffect(() => { fetch('/api/users')... }, []);
}
```

**Why:** Server components eliminate waterfalls, improve TTFB, and work without JavaScript on the client.

---

## Dev Commands

```bash
pnpm dev           # Start Next.js dev server (localhost:3000)
pnpm build         # Production build
pnpm start         # Start production server
pnpm lint          # Biome lint + check
pnpm lint:fix      # Biome fix
pnpm db:generate   # Generate Drizzle migration from schema changes
pnpm db:migrate    # Apply migrations
pnpm db:push       # Push schema to DB (dev only, no migration file)
pnpm db:studio     # Open Drizzle Studio (GUI for DB browsing)
pnpm db:seed       # Seed development database
pnpm test          # Run test suite
```

---

## What We Don't Do (and Why)

| Anti-pattern | Why we avoid it | What we do instead |
|-------------|----------------|-------------------|
| **Prisma ORM** | Heavy runtime, codegen step, slow cold starts | Drizzle — explicit, typed, no codegen |
| **ESLint + Prettier** | Two tools, slow, config conflicts | Biome — single tool, 50x faster |
| **Client-side data fetching** | Waterfalls, no SSR, worse UX | Server Components + Server Actions |
| **Plural table names** | Inconsistent with Drizzle conventions | Singular: `user`, not `users` |
| **Integer primary keys** | Predictable IDs, enumeration risk | UUID via `crypto.randomUUID()` |
| **`.env` in repo** | Secrets leak | `.env.local` in `.gitignore`, `.env.example` committed |
| **Inline SQL strings** | No type safety, SQL injection risk | Drizzle query builder everywhere |
| **Prop drilling past 3 levels** | Unmaintainable | Server component composition or React context |
| **`any` type** | Defeats TypeScript | `unknown` + narrowing, or proper type definition |

---

## Auth Rules

- **All `(dashboard)` routes require authentication** — enforce in `(dashboard)/layout.tsx`
- **API routes under `/api/*` check session explicitly** — don't rely on route-level auth
- **Use `next-auth` with SQLite adapter** — `@auth/drizzle-adapter`
- **Session strategy: `database`** (not JWT) — so you can revoke sessions
- **Role check: `user.role === 'admin'`** — no complex permission system until you need it

---

## Error Handling

- **Server Actions return `{ success: boolean; error?: string; data?: T }`** — never throw to the client
- **API routes use `NextResponse.json({ error }, { status })`** — consistent error shape
- **`not-found.tsx`** at root and per route group — different 404s for auth vs public areas
- **`error.tsx`** for route-level error boundaries — catch rendering errors, not data errors
