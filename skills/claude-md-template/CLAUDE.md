# CLAUDE.md — Next.js 15 + SQLite SaaS Template

> Drop this file into any greenfield Next.js + SQLite SaaS project.
> Claude Code will read it on every session and follow these conventions.

---

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server Components by default, minimal client JS |
| Language | TypeScript 5.x strict | No `any` — use `unknown` + type guards |
| Database | SQLite via Turso (prod) / better-sqlite3 (local) | Single-file dev DB, edge-replicated in prod |
| ORM | Drizzle ORM | Type-safe, lightweight, SQL-like — no runtime overhead |
| Auth | NextAuth v5 (Auth.js) | Session-based, no JWT in cookies |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, copy-paste components |
| Testing | Vitest + Testing Library | Fast, ESM-native, no Jest legacy baggage |
| Linting | ESLint flat config + Prettier | Enforced on pre-commit via lefthook |
| Package Manager | pnpm | Fast, strict, deterministic |

**Pinned versions** — no `^` or `~` in `package.json`. Every dependency is locked.
Upgrade intentionally: `pnpm update --interactive`.

---

## Folder Structure

```
/
├── app/                      # Next.js App Router
│   ├── (marketing)/          # Route group — public pages
│   │   ├── page.tsx          # Landing page
│   │   └── pricing/
│   ├── (dashboard)/          # Route group — authenticated
│   │   ├── layout.tsx        # Dashboard shell with sidebar
│   │   └── settings/
│   ├── api/                  # Route handlers
│   │   ├── webhooks/
│   │   └── trpc/             # tRPC API (if used)
│   ├── layout.tsx            # Root layout — html/body/providers
│   └── globals.css
├── components/
│   ├── ui/                   # shadcn primitives (Button, Input, Dialog)
│   ├── layout/               # Navbar, Sidebar, Footer
│   └── features/             # Domain-specific (BillingCard, UsageChart)
├── db/
│   ├── schema.ts             # Drizzle schema — single source of truth
│   ├── migrations/           # Auto-generated, never edit manually
│   └── index.ts              # DB client singleton
├── lib/
│   ├── auth.ts               # NextAuth config
│   ├── utils.ts              # Generic helpers (cn, formatCurrency)
│   └── validations/          # Zod schemas — one per domain
├── server/
│   ├── actions/              # Server Actions (form submissions, mutations)
│   └── queries/              # Read-only DB queries (reusable in RSC + Actions)
├── hooks/                    # Custom React hooks (useMediaQuery, useDebounce)
├── types/                    # Shared TypeScript types (not Zod — raw types)
├── public/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                  # Playwright if needed
├── drizzle.config.ts
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── CLAUDE.md                 # This file
```

**Rules:**
- Route groups `(folder)` for layout scoping — never nest routes more than 3 levels deep
- `components/ui/` is append-only — import shadcn, don't modify primitives
- `server/actions/` files export one action each: `createBillingPortal.ts`
- `server/queries/` are pure functions that return data — no side effects
- No barrel exports (`index.ts` re-exports) outside of `db/` and `lib/`

---

## Coding Standards

### TypeScript

- `strict: true` — no exceptions
- No `any`. Use `unknown` + narrowing, or `Record<string, unknown>` for objects
- No type assertions (`as`) unless interfacing with untyped libraries — add a comment explaining why
- Prefer `interface` for object shapes, `type` for unions/intersections/utility types
- Enums → `as const` objects. See: `const PLANS = ['free', 'pro', 'enterprise'] as const`
- Zod schemas in `lib/validations/` — derive types from them: `type UserInput = z.infer<typeof userSchema>`

### React & Components

- Server Components by default — only add `"use client"` when you need interactivity (onClick, useState, useEffect)
- Component files: `PascalCase.tsx` → `UsageChart.tsx`
- One component per file, named export preferred: `export function UsageChart()`
- Props type defined inline or above the function — never imported from another file
- No prop drilling beyond 2 levels — use composition or Context
- Loading states: use `Suspense` + `loading.tsx`, not manual `isLoading` flags
- Error handling: use `error.tsx` boundary files, not try/catch in components

### API Design (Route Handlers)

- Every handler returns typed JSON: `NextResponse.json<ApiResponse<T>>(data)`
- Validate input with Zod before touching the DB
- Auth check at the top — throw 401 early, not deep in the logic
- Rate limit per endpoint using `@upstash/ratelimit` or middleware
- Never expose internal IDs — use UUIDs or slugs in public APIs
- Error format: `{ error: { code: string, message: string } }`

### Server Actions

- Prefix with `"use server"` at the top of the file
- Accept FormData or validated object — never raw JSON body
- Return `{ success: boolean, data?: T, error?: string }` — never throw to the client
- Revalidate paths after mutations: `revalidatePath('/dashboard')`

---

## Database Conventions

### Schema (Drizzle)

```typescript
// db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'
import { createId } from '@paralleldrive/cuid2'

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(createId),
  email: text('email').notNull().unique(),
  plan: text('plan', { enum: ['free', 'pro', 'enterprise'] }).notNull().default('free'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$onUpdateFn(() => new Date()),
})
```

**Rules:**
- IDs: CUID2 (`@paralleldrive/cuid2`) — shorter than UUID, sortable, URL-safe
- Timestamps: `integer` with `{ mode: 'timestamp' }` — store as epoch ms
- No foreign key constraints in schema — enforce at app level (SQLite FK enforcement is weak)
- Column names: `snake_case` in DB, `camelCase` in TS (Drizzle maps automatically)
- Enums: `text('column', { enum: [...] })` — validated at compile time
- No `defaultNow()` — use `$defaultFn(() => new Date())` for consistency

### Migrations

- Generate: `pnpm db:generate` (runs `drizzle-kit generate`)
- Apply: `pnpm db:migrate` (runs `drizzle-kit migrate`)
- **Never edit generated migration files** — if schema is wrong, fix `schema.ts` and regenerate
- Local dev: `pnpm db:push` for quick iteration (skips migration files)
- Every migration gets a meaningful name: `0003_add_usage_tracking.sql`
- Run migrations in CI before tests

### Queries

```typescript
// server/queries/getUser.ts
import { db } from '@/db'
import { users } from '@/db/schema'
import { eq } from 'drizzle-orm'

export async function getUserByEmail(email: string) {
  return db.select().from(users).where(eq(users.email, email)).get()
}
```

- One query per file in `server/queries/`
- Use `.get()` for single results, `.all()` for lists
- Always filter with `eq`, `and`, `or` — never interpolate SQL strings
- No raw SQL unless absolutely necessary — add a comment if you do

---

## Testing Strategy

### Unit Tests (`tests/unit/`)

- Test pure logic: validators, formatters, utility functions
- Naming: `functionName.test.ts` next to source, or in `tests/unit/`
- Mock external dependencies (DB, APIs) with `vi.mock()`
- No mocking of React components — that's what integration tests are for

### Integration Tests (`tests/integration/`)

- Server Actions: call the action, assert DB state + return value
- API Routes: use `next-test-api-route-handler` or direct fetch to local server
- Use a test database: `TEST_DB_URL=file:./test.db` in `.env.test`
- Seed data in `beforeEach`, clean in `afterEach`

### E2E Tests (`tests/e2e/`)

- Only for critical paths: signup → onboarding → billing
- Playwright with `@playwright/test`
- Run in CI, not on every commit (slow)

### Commands

```bash
pnpm test              # Run all unit + integration
pnpm test:watch        # Watch mode
pnpm test:e2e          # Playwright
pnpm test:coverage     # With v8 coverage
```

---

## Deployment

### Environment Variables

```
# .env.local (never commit)
DATABASE_URL=file:./local.db          # Local SQLite
DATABASE_URL=libsql://...             # Turso (prod)
NEXTAUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000    # Override in prod
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

- `.env.example` committed with placeholder values — document every required var
- No secrets in code, ever. No exceptions.

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
steps:
  - pnpm install --frozen-lockfile
  - pnpm lint
  - pnpm typecheck
  - pnpm db:generate    # Verify migrations compile
  - pnpm test
  - pnpm build
```

### Production Deploy

- Platform: Vercel (zero-config for Next.js)
- DB: Turso (SQLite at the edge, libSQL driver)
- Migrations: run via `postinstall` script or Vercel build step
- Preview deploys: every PR gets a URL — test before merging

---

## Common Commands

```bash
# Development
pnpm dev                # Start dev server (localhost:3000)
pnpm build              # Production build
pnpm start              # Start production server

# Database
pnpm db:push            # Push schema changes (dev only)
pnpm db:generate        # Generate migration SQL
pnpm db:migrate         # Apply migrations
pnpm db:studio          # Drizzle Studio (visual DB editor)

# Code Quality
pnpm lint               # ESLint
pnpm lint:fix           # ESLint with auto-fix
pnpm format             # Prettier
pnpm typecheck          # tsc --noEmit

# Testing
pnpm test               # Unit + integration
pnpm test:watch         # Watch mode
pnpm test:e2e           # Playwright

# Shadcn UI
pnpx shadcn@latest add button    # Add a component
```

---

## Error Handling Patterns

### Server Actions

```typescript
'use server'

export async function updateUserPlan(formData: FormData) {
  try {
    const input = updatePlanSchema.parse({
      plan: formData.get('plan'),
    })

    const session = await auth()
    if (!session?.user) {
      return { success: false, error: 'Unauthorized' }
    }

    await db.update(users)
      .set({ plan: input.plan })
      .where(eq(users.id, session.user.id))

    revalidatePath('/dashboard')
    return { success: true, data: { plan: input.plan } }
  } catch (error) {
    if (error instanceof ZodError) {
      return { success: false, error: 'Invalid input' }
    }
    console.error('[updateUserPlan]', error)
    return { success: false, error: 'Something went wrong' }
  }
}
```

### API Route Handlers

```typescript
import { NextResponse } from 'next/server'
import { ZodError } from 'zod'

export async function POST(req: Request) {
  try {
    const session = await auth()
    if (!session) {
      return NextResponse.json(
        { error: { code: 'UNAUTHORIZED', message: 'Sign in required' } },
        { status: 401 }
      )
    }

    const body = createItemSchema.parse(await req.json())
    const item = await createItem(body)

    return NextResponse.json({ data: item }, { status: 201 })
  } catch (error) {
    if (error instanceof ZodError) {
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: error.errors[0].message } },
        { status: 400 }
      )
    }

    console.error('[POST /api/items]', error)
    return NextResponse.json(
      { error: { code: 'INTERNAL', message: 'Internal server error' } },
      { status: 500 }
    )
  }
}
```

### Client Error Boundaries

```typescript
// app/(dashboard)/error.tsx
'use client'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="text-muted-foreground text-sm mt-1">{error.message}</p>
        <button onClick={reset} className="mt-4 underline">
          Try again
        </button>
      </div>
    </div>
  )
}
```

---

## What We Don't Do (And Why)

| ❌ Never | Why |
|----------|-----|
| ORM `select *` on large tables | Fetch only what you need — explicit columns |
| Client-side data fetching for initial load | Use RSC — client fetches are for real-time updates only |
| `any` type | Defeats the entire point of TypeScript |
| CSS modules + Tailwind mixed | Pick one. We picked Tailwind. |
| Default exports | Named exports are greppable and refactor-safe |
| `useEffect` for data fetching | Use RSC + Server Actions — `useEffect` is for DOM/subscription side effects |
| Nested ternaries | Readability matters — use if/else or early returns |
| Inline styles | Use Tailwind classes — consistent, themeable, purged in prod |
| Storing passwords in DB | Use NextAuth + OAuth — password auth is an anti-pattern for SaaS |
| Direct DB access in components | Always go through `server/queries/` or `server/actions/` |
| Editing migration files | Fix schema → regenerate — migrations are immutable |
| `console.log` in production code | Use a logger or remove — `console.error` is fine for server errors |

---

## Quick Reference for Claude Code

When working in this repo:

1. **Read before writing** — check existing patterns in the area you're editing
2. **Server Components first** — only add `"use client"` when you need interactivity
3. **Validate everything** — Zod schemas at every boundary (API, forms, server actions)
4. **Types from Zod** — `z.infer<typeof schema>` is the source of truth
5. **One file, one purpose** — queries in `server/queries/`, actions in `server/actions/`
6. **Test the happy path + one edge case** — don't write 20 test cases for a simple function
7. **pnpm, not npm** — lock file is pnpm-lock.yaml
8. **Error boundaries** — every route group needs `error.tsx` and `loading.tsx`
