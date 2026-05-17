# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> **Purpose:** This file gives Claude Code everything it needs to contribute to this
> project without asking clarifying questions. Every rule below has a concrete
> reason — this is not generic advice. It encodes hard-won lessons from shipping
> real SaaS products.

---

## Stack & Locked Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js **15** (App Router) | Stable caching semantics, partial prerendering opt-in, React 19 |
| Language | TypeScript **strict** | `strict: true` in tsconfig. No exceptions. |
| Styling | Tailwind CSS **v4** | Vite-native, CSS-first config, no `tailwind.config.ts` needed |
| Database | SQLite via **better-sqlite3** | Synchronous API = no connection pooling drama. Single-file DB. |
| ORM | **Drizzle ORM** | Type-safe, SQL-like, no codegen step, `.sql` migration output |
| Auth | **NextAuth.js v5** (Auth.js) | Edge-compatible, middleware-based, session in JWT or DB |
| Validation | **Zod** | Parse, don't validate. Use everywhere user input enters the system. |
| Testing | **Vitest** + **Playwright** | Vitest for unit/integration, Playwright for E2E |
| Package manager | **pnpm** | Strict, fast, disk-efficient. Do not use npm or yarn. |

---

## Project Structure

```
project-root/
├── app/                        # App Router. File system IS the router.
│   ├── (marketing)/            # Route group — no layout nesting impact
│   │   ├── page.tsx            #   / (landing page)
│   │   └── layout.tsx          #   Marketing shell (light header, no sidebar)
│   ├── (dashboard)/            # Route group — authenticated area
│   │   ├── layout.tsx          #   Auth check + sidebar + user menu
│   │   ├── dashboard/
│   │   │   └── page.tsx        #   /dashboard
│   │   └── settings/
│   │       └── page.tsx        #   /settings
│   ├── api/                    # ONLY for external consumers (webhooks, OAuth)
│   │   └── webhooks/
│   │       └── stripe/
│   │           └── route.ts    #   /api/webhooks/stripe
│   ├── error.tsx               # Global error boundary
│   ├── global-error.tsx        # Root error (replaces root layout on crash)
│   ├── layout.tsx              # Root layout: <html>, <body>, providers
│   ├── not-found.tsx           # Global 404
│   └── loading.tsx             # Global loading skeleton
├── components/                 # Shared UI components
│   ├── ui/                     #   shadcn/ui primitives (Button, Input, Card…)
│   └── [feature]/              #   Feature-specific shared components
├── lib/                        # Pure utilities — NO React imports allowed
│   ├── db/                     #   Database
│   │   ├── index.ts            #     Singleton DB connection
│   │   ├── schema.ts           #     Drizzle schema definitions
│   │   └── migrations/         #     Generated .sql migration files
│   ├── auth.ts                 #   NextAuth.js config
│   ├── auth-middleware.ts      #   Middleware auth logic (edge-safe subset)
│   ├── validations.ts          #   Zod schemas — one file, co-located
│   └── utils.ts                #   String/date/number helpers
├── hooks/                      # Client-side React hooks (useX)
├── drizzle.config.ts           # Drizzle Kit config
├── drizzle/                    # Drizzle Kit output (migrations + meta)
├── middleware.ts               # Next.js middleware (root-level, edge runtime)
├── playwright.config.ts
├── vitest.config.ts
├── tailwind.config.ts          # Only if overriding v4 defaults
├── tsconfig.json               # strict: true
└── package.json
```

### Structure Rules (with reasons)

1. **Use route groups `(name)`** to separate marketing vs. dashboard layouts.
   *Why:* Different auth requirements, different shells. Avoids a rats-nest of
   conditional rendering in a single layout.

2. **No `src/` directory.** Next.js 15 works perfectly without it.
   *Why:* Extra nesting adds no value for App Router projects. Flatter = faster
   to navigate.

3. **`components/` is for shared UI only.** Page-specific components live
   **co-located** inside their route segment.
   *Why:* Co-location makes it obvious what a page depends on. Deleting a route
   deletes its components. No dead code archaeology later.

4. **`lib/` must not import React or 'use client'.** It is pure TypeScript.
   *Why:* Forces a clean boundary. Lib functions work in Server Components,
   middleware, scripts, and tests without issue.

5. **One Zod schemas file: `lib/validations.ts`.**
   *Why:* Tiny files create import hell. A single validation file stays under
   300 lines for most SaaS projects. Split only when it genuinely hurts.

---

## Database & Migrations

### Connection (Singleton)

```ts
// lib/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(process.env.DATABASE_PATH ?? './data.db');
sqlite.pragma('journal_mode = WAL');  // Concurrent reads during writes
sqlite.pragma('foreign_keys = ON');   // Enforce FK constraints

export const db = drizzle(sqlite);
```

- **Always enable WAL mode.** SQLite default journal mode blocks readers
  during writes. WAL allows concurrent reads — critical for serverless-ish
  Next.js where multiple requests hit the same DB.
- **Always enable foreign keys.** SQLite disables them by default. Without
  this, CASCADE deletes silently fail.
- **Use a singleton.** Don't re-create the DB connection on every import.
  Next.js hot-reloads modules in dev — without a singleton you leak file
  handles.

### Schema Conventions

```ts
// lib/db/schema.ts — Example
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id:           text('id').primaryKey(),             // ULID, not auto-increment
  email:        text('email').notNull().unique(),
  name:         text('name').notNull(),
  avatarUrl:    text('avatar_url'),
  createdAt:    integer('created_at', { mode: 'timestamp' }).notNull()
                  .$defaultFn(() => new Date()),
  updatedAt:    integer('updated_at', { mode: 'timestamp' }).notNull()
                  .$defaultFn(() => new Date()),
});
```

**Rules:**

- **Table names: plural, snake_case** (`users`, `team_members`).
  *Why:* SQL convention. Matches generated SQL, avoids quoting in raw queries.

- **Column names: camelCase in TypeScript, snake_case in SQL.**
  *Why:* TypeScript convention in code, SQL convention on disk. Drizzle maps
  automatically — use the `name` property for the SQL column.

- **Primary keys: ULID strings, not auto-increment integers.**
  *Why:* ULIDs are sortable by time, URL-safe, and safe to expose publicly
  (no enumeration attacks). They also survive DB merges. Use
  `import { ulid } from 'ulid'`.

- **Timestamps: integer with `mode: 'timestamp'`.** Drizzle converts to JS Date
  automatically. *Why:* SQLite has no native datetime type. Integer unix
  timestamps avoid string-format ambiguity and timezone bugs.

- **Use `$defaultFn`, not `$default`** (uppercase F). The lowercase version is
  deprecated in Drizzle and silently breaks on some query types.

- **Index every column used in WHERE on hot paths.**
  *Why:* SQLite query planning is simple — without indexes, large tables
  degrade to full scans. Add indexes for: foreign keys, email lookups,
  slug lookups, date range queries.

### Migration Workflow

```bash
# 1. Edit lib/db/schema.ts
# 2. Generate migration SQL
pnpm db:generate   # runs: drizzle-kit generate

# 3. Review the generated .sql in lib/db/migrations/
# 4. Apply migrations (runs on app start)
pnpm db:migrate    # runs: drizzle-kit migrate

# 5. NEVER edit generated .sql files by hand.
#    If you need custom SQL, write a separate manual migration.
```

- **Migrations run automatically on server start**, not as a separate deploy
  step. *Why:* SQLite is a single file. No migration pipeline needed. Less
  deployment ceremony.
- **Generated migrations live in `lib/db/migrations/`**, checked into git.
- **Never use `drizzle-kit push` in production.** `push` silently drops and
  recreates columns. `generate` + `migrate` forces you to review the SQL diff.

---

## Component Patterns

### Server Components are the DEFAULT

Every component starts as a Server Component. Add `'use client'` only when
you need one of: `useState`, `useEffect`, `onClick`, `useContext`, browser APIs.

```tsx
// ✅ GOOD: Server Component — async, reads DB directly
// app/dashboard/page.tsx
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export default async function DashboardPage() {
  const allUsers = await db.select().from(users);
  return <UserList users={allUsers} />;
}
```

```tsx
// ✅ GOOD: Client Component — clearly separated, minimal
// components/dashboard/copy-button.tsx
'use client';
export function CopyButton({ text }: { text: string }) {
  return <button onClick={() => navigator.clipboard.writeText(text)}>Copy</button>;
}
```

```tsx
// ❌ BAD: Marking a whole page 'use client' for one button
'use client';  // Unnecessary — kills all server-side benefits
export default function DashboardPage() { /* ... */ }
```

**The rule:** Push `'use client'` as deep as possible. A page with 98%
server-rendered content and a 2-line interactive widget should have exactly
one small Client Component import — not a client page.

### Data Fetching

- **Fetch in Server Components, never in Client Components.**
  *Why:* Server Components can be async. They read directly from the DB
  (no API layer). No loading spinners for initial data. No `useEffect` +
  `fetch` + `useState` tango.

- **For mutations, use Server Actions.**
  *Why:* No API route boilerplate. Progressive enhancement — forms work before
  JS loads. Automatic CSRF protection.

```tsx
// app/(dashboard)/settings/actions.ts
'use server';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { updateProfileSchema } from '@/lib/validations';

export async function updateProfile(formData: FormData) {
  const data = updateProfileSchema.parse(Object.fromEntries(formData));
  await db.update(users).set(data).where(eq(users.id, data.userId));
  revalidatePath('/settings');
}
```

- **API routes (`route.ts`) ONLY for external consumers:** webhooks, OAuth
  callbacks, public REST APIs for 3rd parties. *Why:* Server Actions replace
  internal API routes. Less code, better types, no CORS headaches.

### Suspense Boundaries

Every async page gets a `loading.tsx` sibling. For granular loading, wrap
slow components in `<Suspense>`:

```tsx
// app/(dashboard)/dashboard/page.tsx
import { Suspense } from 'react';
import { RecentActivity, RecentActivitySkeleton } from './recent-activity';
import { Stats, StatsSkeleton } from './stats';

export default function DashboardPage() {
  return (
    <div className="grid gap-6">
      <Suspense fallback={<StatsSkeleton />}>
        <Stats />
      </Suspense>
      <Suspense fallback={<RecentActivitySkeleton />}>
        <RecentActivity />
      </Suspense>
    </div>
  );
}
```

- **Streaming by default.** Next.js 15 App Router streams Suspense boundaries
  automatically. Fast data renders first; slow data fills in. No config needed.

---

## Naming Conventions

| What | Convention | Example |
|------|------------|---------|
| Files (components) | kebab-case | `user-avatar.tsx`, `billing-form.tsx` |
| Files (utilities) | kebab-case | `format-currency.ts`, `send-email.ts` |
| React Components | PascalCase | `UserAvatar`, `BillingForm` |
| Functions | camelCase | `getUserById`, `formatCurrency` |
| Server Actions files | `actions.ts` | `app/(dashboard)/settings/actions.ts` |
| Zod schemas | camelCase, suffixed `Schema` | `updateProfileSchema` |
| Database tables | plural, snake_case | `users`, `team_members` |
| Route parameters | `[slug]` dynamic, `[...catch]` catch-all | `app/blog/[slug]/page.tsx` |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_PATH`, `STRIPE_SECRET_KEY` |

**Why kebab-case for files?** Case-insensitive filesystems (macOS, Windows).
`UserAvatar.tsx` and `useravatar.tsx` are the same file on macOS but different
in git on Linux. Kebab-case eliminates this entire class of bug.

---

## Auth Conventions (NextAuth.js v5)

```ts
// lib/auth.ts — Server-side auth
import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  callbacks: {
    session: ({ session, token }) => ({
      ...session,
      user: { ...session.user, id: token.sub! },
    }),
  },
});
```

```ts
// middleware.ts — Route protection (edge-safe)
export { auth as middleware } from '@/lib/auth-middleware';
export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*'],
};
```

**Rules:**

- **Never call `auth()` inside a try/catch.** The auth function throws
  `AuthError` on invalid sessions. Let error boundaries handle it.
- **Use `auth()` (server-side) for page-level checks, `useSession()` only for
  client-only UI** (e.g., avatar in a dropdown).
- **Protect routes via middleware `matcher`, not per-page checks.**
  *Why:* Middleware runs at the edge before layout rendering. No flash of
  unauthenticated content.
- **Extend the session to include `user.id`** via the `session` callback.
  *Why:* You need the user ID for DB queries. The default session only
  includes name/email/image.

---

## Middleware

```ts
// middleware.ts — Root-level, edge runtime
import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth-middleware';

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isDashboard = req.nextUrl.pathname.startsWith('/dashboard');

  if (isDashboard && !isLoggedIn) {
    return NextResponse.redirect(new URL('/login', req.url));
  }
  return NextResponse.next();
});

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

- **Keep middleware thin.** No DB queries, no heavy imports.
  *Why:* Middleware runs on every request at the edge. A slow middleware
  degrades every page. Auth checks only.
- **Use `matcher` to exclude static assets and API routes** from middleware.
  *Why:* Every matched request runs the middleware function. Wasted compute.

---

## Error Handling

### error.tsx (per-segment error boundaries)

```tsx
// app/(dashboard)/error.tsx
'use client';
export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 p-8">
      <h2 className="text-lg font-semibold">Something went wrong</h2>
      <p className="text-muted-foreground text-sm">
        {error.message || 'An unexpected error occurred.'}
      </p>
      <button onClick={() => reset()}>Try again</button>
    </div>
  );
}
```

- **Every route group gets an `error.tsx`.**
- **`error.tsx` must be a Client Component** (needs `reset()` which uses state).
- **Don't leak stack traces to users.** Show `error.message` only. The
  `error.digest` is a server-side lookup key — don't render it.
- **Use `notFound()` for 404s.** Call `notFound()` inside Server Components when
  a resource doesn't exist. Next.js renders the nearest `not-found.tsx`.

### Server Action Errors

```ts
// Return structured errors, don't throw in Server Actions
'use server';
export async function updateProfile(formData: FormData) {
  try {
    const data = updateProfileSchema.parse(Object.fromEntries(formData));
    await db.update(users).set(data).where(eq(users.id, data.userId));
    revalidatePath('/settings');
    return { success: true as const };
  } catch (error) {
    if (error instanceof ZodError) {
      return { success: false as const, errors: error.flatten().fieldErrors };
    }
    throw error; // Re-throw unexpected errors — error.tsx handles them
  }
}
```

- **Return `{ success, errors }` from Server Actions, don't throw.**
  *Why:* Thrown errors in Server Actions don't give the form component
  field-level error information. Return types let the client render inline
  validation messages.

---

## Testing

```bash
# Unit tests (lib functions, Zod schemas, utils)
pnpm test              # vitest run
pnpm test:watch        # vitest --watch

# E2E tests (Playwright)
pnpm test:e2e          # playwright test
pnpm test:e2e:ui       # playwright test --ui
```

**Rules:**

- **Test utilities in `lib/` with Vitest.** Pure functions, no mocking needed.
  Fast, deterministic.
- **Test Server Actions with Vitest + a test SQLite database.**
  Create a `:memory:` DB for each test run.
- **E2E tests with Playwright** for critical user flows (sign-up, checkout,
  dashboard load). Don't E2E test everything — it's slow and flaky.
- **No snapshot tests.** They break on every intentional change and trains
  developers to blindly update snapshots. Assert specific values instead.

---

## Dev Commands

```bash
# === Daily workflow ===
pnpm dev                # next dev --turbo (Turbopack enabled)
pnpm build              # next build (type-check + optimize)
pnpm start              # next start (production server on port 3000)
pnpm lint               # next lint (ESLint)
pnpm typecheck          # tsc --noEmit (types only, no build)

# === Database ===
pnpm db:generate        # drizzle-kit generate (create migration SQL)
pnpm db:migrate         # drizzle-kit migrate (apply pending migrations)
pnpm db:studio          # drizzle-kit studio (visual DB browser at :4983)
pnpm db:push            # drizzle-kit push (DANGER: only for prototyping)

# === Testing ===
pnpm test               # vitest run (unit + integration)
pnpm test:watch         # vitest --watch
pnpm test:e2e           # playwright test
pnpm test:coverage      # vitest run --coverage

# === Quality ===
pnpm format             # prettier --write .
pnpm format:check       # prettier --check .
pnpm lint:fix           # next lint --fix
pnpm check              # tsc --noEmit && next lint && prettier --check .
```

**Always run `pnpm check` before committing.** *Why:* Catches type errors,
lint issues, and formatting in one command. Block broken commits at the
developer's machine, not in CI.

---

## Patterns to Follow

### 1. Zod-First Data Flow

```
User Input → Zod.parse() → Typed Data → DB Query → Typed Response → UI
```

Never trust `FormData.get()` returns. Parse everything through Zod before it
touches the database.

### 2. Optimistic UI for Mutations

```tsx
// Use useOptimistic + Server Actions for instant feedback
'use client';
import { useOptimistic } from 'react';
import { toggleTodo } from './actions';

export function TodoList({ todos }: { todos: Todo[] }) {
  const [optimisticTodos, addOptimistic] = useOptimistic(
    todos,
    (state, id: string) => state.map(t => t.id === id ? { ...t, done: !t.done } : t)
  );
  // ... render optimisticTodos
}
```

### 3. Route-Specific Layouts

Each route group gets its own `layout.tsx`. Don't abuse a single root layout
with conditional rendering — that's how layout shift bugs are born.

### 4. CSS via Tailwind Utility Classes Only

No CSS modules, no `styles/` directory, no CSS-in-JS. Tailwind v4's
`@apply` in `app/globals.css` is the single exception for complex repeated
patterns (e.g., `.card`).

### 5. Environment Variables in `env.ts`

```ts
// lib/env.ts — Coerce and validate at import time
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_PATH: z.string().default('./data.db'),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

**Validate environment variables at app startup.** *Why:* Catching a missing
`AUTH_SECRET` on app start beats debugging cryptic auth failures at runtime.

---

## Anti-Patterns (What We Don't Do)

### ❌ API Routes for Internal Data Fetching
```ts
// DON'T: Create /api/users to fetch from a Server Component
// DO: Import the DB directly in the Server Component
```
*Why:* Adds network latency, serialization overhead, and an extra layer to
maintain. The DB is on the same machine — just query it.

### ❌ `useEffect` for Data Fetching
```tsx
// DON'T: useEffect + useState + fetch
// DO: Async Server Component OR React Query for client-side refetches
```
*Why:* Waterfall rendering: mount → fetch → re-render. Server Components
eliminate this entirely. For client refetches (search, polling), use TanStack
Query.

### ❌ Barrel Exports (`index.ts` Re-exporting Everything)
```ts
// DON'T: components/ui/index.ts re-exporting 40 components
// DO: Import directly: import { Button } from '@/components/ui/button'
```
*Why:* Barrel files defeat tree-shaking, slow down Fast Refresh in dev, and
create circular dependency traps. Next.js 15's bundler handles direct imports
perfectly.

### ❌ `any` or `as` TypeScript Escape Hatches
```ts
// DON'T: const data = await db.all('SELECT * FROM users') as User[];
// DO: Use Drizzle's typed query API: await db.select().from(users);
```
*Why:* `any` and `as` are lies we tell the compiler. They rot over time.
Drizzle is fully typed — use it.

### ❌ Raw SQL Strings in Route Handlers
```ts
// DON'T: db.exec(`INSERT INTO users (name) VALUES ('${name}')`);
// DO: Use Drizzle OR parameterized queries
```
*Why:* SQL injection. Always. Even for internal tools — you'll copy-paste it
into user-facing code someday.

### ❌ Mixing Auth Logic in Layouts
```tsx
// DON'T: const session = await auth(); if (!session) redirect('/login');
//       inside a layout.tsx
// DO: Protect routes via middleware matcher; use auth() in pages for authorization
```
*Why:* Layouts don't re-render on navigation. Auth state changes (logout,
session expiry) won't trigger a redirect. Middleware runs on every request.

### ❌ `process.env` Directly in Components
```ts
// DON'T: const apiKey = process.env.STRIPE_SECRET_KEY;
// DO: import { env } from '@/lib/env';
```
*Why:* No validation, no default values, no type safety. One typo and you
ship with an undefined API key. Validate once in `env.ts`.

---

## CI / Pre-Commit

```yaml
# .github/workflows/ci.yml
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm lint
      - run: pnpm format:check
      - run: pnpm test
      - run: pnpm build
```

**CI runs on every PR. Merge only when green.** No exceptions for "minor"
changes — formatting is checked in CI, not negotiated.

---

## File Creation Template

When implementing new features, create files in this order:

```
1. lib/db/schema.ts           — Add/modify Drizzle tables
2. pnpm db:generate           — Generate migration SQL
3. lib/validations.ts         — Add Zod schemas for the feature
4. app/[route]/actions.ts     — Write Server Actions (mutations)
5. app/[route]/page.tsx       — Server Component that queries DB
6. app/[route]/loading.tsx    — Loading skeleton
7. app/[route]/error.tsx      — Error boundary
8. components/[feature]/      — Client Components for interactivity
```

*Why this order:* Types first. Data layer before UI. Validation before
mutation. Loading and error handling before you declare "done."

---

## Questions Claude Code Should Ask

If Claude Code encounters ambiguity that this file doesn't cover, it should
ask about:

1. **Business logic specifics** (e.g., "Should a user be able to delete their
   account if they have active subscriptions?")
2. **Design system choice** (e.g., "Are we using shadcn/ui, Radix primitives,
   or custom components?")
3. **Auth provider selection** (e.g., "Google only, or email/password too?")
4. **Deployment target** (e.g., "Vercel, Docker on VPS, or other?")
5. **Multi-tenancy** (e.g., "Single team or multi-workspace?")

Everything else — structure, naming, tooling, patterns — is answered here.
