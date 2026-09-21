# CLAUDE.md — Next.js 15 + SQLite SaaS Project

This file defines the mandatory conventions for this codebase. Every rule has a reason. Follow them without exception.

---

## 1. Stack & Versions

| Layer | Choice | Version | Reason |
|-------|--------|---------|--------|
| Framework | Next.js | 15.x (App Router) | Server Components by default, streaming, React 19 ready |
| Language | TypeScript | 5.x | Strict mode; catches bugs at compile time |
| Database | SQLite (better-sqlite3) | 9.x / 11.x | Zero-config, file-based, fast for OLTP; Turso for prod sync |
| ORM / Query Builder | **None** — raw SQL | — | Full control, no abstraction leaks, simpler debugging |
| Migrations | Custom timestamped files | — | Explicit, reviewable, no magic |
| Auth | NextAuth.js (Auth.js) | 5.x (beta) | Edge-compatible, multiple providers, session handling |
| Validation | Zod | 3.x | Schema-first, TypeScript inference |
| Styling | Tailwind CSS | 4.x | Utility-first, no runtime, built-in design tokens |
| Testing | Vitest + Playwright | Latest | Fast unit, reliable e2e |
| Linting | Biome | 1.x | Fast, all-in-one (lint + format) |
| Package Manager | pnpm | 9.x | Fast, disk-efficient, strict peer deps |

**Non-negotiable:** No Prisma, Drizzle, or Supabase client. No `next-auth` v4. No CSS Modules or Styled Components.

---

## 2. Folder Structure

```
├── app/                          # Next.js App Router (server components by default)
│   ├── (auth)/                   # Route group: auth pages (login, register, reset)
│   ├── (dashboard)/              # Route group: protected dashboard layout + pages
│   ├── (marketing)/              # Route group: public marketing pages
│   ├── api/                      # API routes (thin controllers only)
│   │   └── v1/                   # Versioned API
│   ├── globals.css               # Tailwind v4 @import "tailwindcss" + custom CSS vars
│   ├── layout.tsx                # Root layout: providers, fonts, metadata
│   └── page.tsx                  # Landing page (marketing)
├── components/                   # Shared UI components
│   ├── ui/                       # Primitive, reusable (Button, Input, Card, etc.)
│   ├── forms/                    # Form-specific (Field, Select, DatePicker)
│   ├── layout/                   # Layout chrome (Header, Sidebar, Footer)
│   └── features/                 # Feature-specific composites (UserAvatar, BillingCard)
├── lib/                          # Core utilities, singletons, config
│   ├── db/                       # Database layer
│   │   ├── index.ts              # Singleton connection (better-sqlite3)
│   │   ├── migrations/           # Migration runner + files
│   │   │   ├── 0001_initial_schema.sql
│   │   │   └── 0002_add_billing.sql
│   │   ├── queries/              # One file per domain: users.sql.ts, subscriptions.sql.ts
│   │   └── transactions.ts       # Explicit transaction helper
│   ├── auth.ts                   # Auth.js config (callbacks, adapters)
│   ├── validation/               # Zod schemas (export types from schemas)
│   ├── utils.ts                  # Pure helpers (cn, formatCurrency, etc.)
│   └── constants.ts              # App-wide enums, limits, config
├── hooks/                        # React hooks (useDebounce, useLocalStorage)
├── types/                        # Global type exports (from Zod, DB, API)
├── middleware.ts                 # Auth protection, locale, security headers
├── scripts/                      # CLI scripts (db:migrate, db:seed, generate:types)
├── tests/                        # Unit + integration (Vitest)
│   ├── db/                       # DB tests with temp file
│   └── components/               # Component tests
├── e2e/                          # Playwright e2e tests
├── .github/workflows/            # CI: lint, typecheck, test, build
├── biome.json                    # Biome config (lint + format)
├── tailwind.config.ts            # Tailwind v4 config (if needed beyond CSS)
├── tsconfig.json                 # Strict TS config
├── package.json
├── pnpm-lock.yaml
└── CLAUDE.md                     # This file
```

**Rules:**
- **No `src/` prefix** — Next.js 15 expects `app/` at root.
- **Route groups `(...)`** for layout separation, not URL segments.
- **`lib/db/queries/*.sql.ts`** — One file per domain. Named exports: `getUserById`, `createSubscription`, etc.
- **`components/ui/`** — Primitives only. No business logic. No server components.
- **`components/features/`** — Composites that may be server components (fetch data internally).
- **`scripts/`** — All DB operations (migrate, seed, studio) are scripts, not npm lifecycle hooks.

---

## 3. Database: SQL & Migration Conventions

### Connection (`lib/db/index.ts`)
```ts
import Database from 'better-sqlite3'
import { resolve } from 'node:path'

const dbPath = process.env.DB_PATH ?? resolve(process.cwd(), 'data/app.db')
export const db = new Database(dbPath)
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')
db.pragma('busy_timeout = 5000')
```

### Migration Rules
1. **File naming:** `NNNN_descriptive_name.sql` (4-digit zero-padded sequence).
2. **One statement per file** — or multiple in a single transaction block.
3. **Up only.** No down migrations. Fix forward with a new migration.
4. **Run via script:** `pnpm db:migrate` (runs in order, tracks applied in `_migrations` table).
5. **Review every migration** — raw SQL is visible, no ORM magic.

### Query File Pattern (`lib/db/queries/users.sql.ts`)
```ts
import { db } from '../index'
import type { User, NewUser } from '@/types/db'

export function getUserById(id: string): User | undefined {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id) as User | undefined
}

export function createUser(input: NewUser): User {
  const stmt = db.prepare(`
    INSERT INTO users (id, email, password_hash, role, created_at)
    VALUES (@id, @email, @passwordHash, @role, @createdAt)
    RETURNING *
  `)
  return stmt.get(input) as User
}

export function updateUserEmail(id: string, email: string): User {
  return db.prepare('UPDATE users SET email = ? WHERE id = ? RETURNING *').get(email, id) as User
}
```

### Conventions
- **Parameter style:** Named (`@param`) for 3+ params, positional (`?`) for 1-2.
- **Always `RETURNING *`** on writes — avoids extra SELECT.
- **Types from `types/db.ts`** — Generated from schema (see `scripts/generate:types`).
- **No dynamic SQL construction** — Use `?`/`@` params always.
- **Transactions:** Use `lib/db/transactions.ts` helper for multi-statement atomicity.

---

## 4. Component Patterns

### Server Components by Default
- **All components in `app/` are Server Components** unless `'use client'` is at top.
- **Client components only for:** Interactivity (forms, modals, charts), browser APIs, `useSearchParams`, `usePathname`.
- **Push client boundaries down** — wrap smallest subtree possible.

### Component Structure
```tsx
// components/ui/Button.tsx
import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:pointer-events-none disabled:opacity-50',
          {
            'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'primary',
            'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
            'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
            'bg-destructive text-destructive-foreground hover:bg-destructive/90': variant === 'destructive',
            'h-8 px-3 text-xs': size === 'sm',
            'h-10 px-4 py-2': size === 'md',
            'h-12 px-8 text-lg': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'
```

### Patterns to Follow
| Pattern | Rule |
|---------|------|
| **Compound components** | Use `Slot` pattern (Radix-style) for flexible composition |
| **Variant props** | Single `variant` + `size` props, not boolean soup (`isPrimary`, `isLarge`) |
| **Forward refs** | Always `forwardRef` on primitives; `displayName` for debugging |
| **Server-first data fetching** | Fetch in Server Component, pass data as props to client children |
| **Form handling** | `react-hook-form` + Zod resolver; server actions for mutations |
| **Error boundaries** | Wrap feature sections, not whole app |
| **Loading/Empty states** | Define in the component that owns the data fetch |

### Naming
- **Files:** PascalCase for components (`UserCard.tsx`), kebab-case for utils (`format-date.ts`).
- **Exports:** Named exports for components, default only for pages/layouts.
- **Props interfaces:** `ComponentNameProps` (e.g., `ButtonProps`).
- **Types:** `User`, `NewUser`, `UserUpdate` — suffix by operation.

---

## 5. API Routes (`app/api/v1/`)

- **Thin controllers only** — Validate, call query functions, return JSON.
- **No business logic in route handlers** — Logic lives in `lib/db/queries/`.
- **Standard response shape:**
```ts
// Success
{ data: T, error: null }
// Error
{ data: null, error: { code: string, message: string, details?: unknown } }
```
- **Status codes:** 200 (OK), 201 (Created), 400 (Validation), 401 (Unauth), 403 (Forbidden), 404 (Not Found), 500 (Server).
- **Auth:** Use `getServerSession` from `next-auth` in route handlers.
- **Rate limiting:** Apply via middleware or Upstash Redis (if needed).

---

## 6. Dev Commands

```bash
# Development
pnpm dev                    # Next.js dev server (turbopack)
pnpm db:studio              # Better-sqlite3 CLI (sqlite3 data/app.db)

# Database
pnpm db:migrate             # Run pending migrations
pnpm db:seed                # Seed development data
pnpm db:reset               # Drop + migrate + seed (dev only)
pnpm generate:types         # Generate TypeScript types from schema

# Quality
pnpm lint                   # Biome lint
pnpm format                 # Biome format
pnpm typecheck              # tsc --noEmit
pnpm test                   # Vitest (unit + integration)
pnpm test:e2e               # Playwright

# Build
pnpm build                  # Production build
pnpm start                  # Production server
```

**Never run** `next build` or `next start` directly — use `pnpm build` / `pnpm start`.

---

## 7. What We Don't Do (and Why)

| Anti-Pattern | Why |
|--------------|-----|
| **ORM (Prisma, Drizzle, etc.)** | Adds abstraction layer, hides SQL, migration drift, cold-start penalty. Raw SQL is transparent and fast. |
| **Client Components by default** | Increases bundle, hydration cost, complexity. Server Components are the default in Next.js 15. |
| **Barrel exports (`index.ts` re-exports)** | Obscures dependency graph, slows HMR, causes circular deps. Import from source file directly. |
| **`any` type** | Defeats TypeScript. Use `unknown` + narrowing, or generate types from DB/Zod. |
| **Magic strings for routes** | Use `app/routes.ts` with route constants or `next/link` href directly. |
| **Global state libraries (Zustand, Redux, Jotai)** | Server Components + URL state + React Context (sparingly) cover 95% of cases. |
| **CSS-in-JS / CSS Modules** | Tailwind v4 is zero-runtime, composable, and design-token-native. |
| **`try/catch` in query functions** | Let errors bubble. Handle at API route / Server Action boundary with typed error response. |
| **Async components in `app/` without `Suspense`** | Always wrap async boundaries in `<Suspense fallback={<Skeleton />}>` at the layout level. |
| **Direct `better-sqlite3` calls in components** | All DB access through `lib/db/queries/`. Components receive data as props. |
| **Env vars in client code** | Only `NEXT_PUBLIC_*` exposed. Server-only secrets stay in `lib/` and API routes. |
| **Committing `data/app.db`** | `.gitignore` includes `data/`. DB is generated via migrations + seed. |
| **Skipping migrations in CI** | CI runs `pnpm db:migrate` on temp DB before tests. |

---

## 8. Authentication & Authorization

- **Auth.js v5** with `credentials` + `github`/`google` providers.
- **Session strategy:** `database` (stored in SQLite `sessions` table).
- **Roles:** `user`, `admin` (stored on `users.role`).
- **Middleware (`middleware.ts`):**
  - Protects `/dashboard/*`, `/api/v1/*` (except public endpoints).
  - Redirects unauthenticated to `/login?callbackUrl=...`.
  - Adds security headers (CSP, HSTS, etc.).
- **Server Components:** Use `auth()` from `next-auth` (React 19 `async` support).
- **Server Actions:** Verify session + role before mutation.

---

## 9. Validation & Type Safety

- **Zod schemas in `lib/validation/`** — One file per domain.
- **Infer types:** `export type UserInput = z.infer<typeof userInputSchema>`.
- **Validate at boundaries:** API routes, Server Actions, Form submissions.
- **Never validate in UI components** — They receive already-validated data.

---

## 10. Testing Strategy

| Layer | Tool | Scope |
|-------|------|-------|
| Unit | Vitest | Pure functions, Zod schemas, utils, query functions (with temp DB) |
| Integration | Vitest | API routes (via `next-test-api-route-handler`), Server Actions |
| E2E | Playwright | Critical user flows: signup, login, subscription, dashboard |

**DB tests:** Use `:memory:` or temp file per test file. `scripts/test-db.ts` sets up schema.

---

## 11. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `file:./data/app.db` (dev) / `libsql://...` (Turso prod) |
| `AUTH_SECRET` | Yes | `openssl rand -base64 32` |
| `GITHUB_CLIENT_ID` / `SECRET` | No | OAuth provider |
| `GOOGLE_CLIENT_ID` / `SECRET` | No | OAuth provider |
| `STRIPE_SECRET_KEY` | Yes (billing) | Stripe server key |
| `STRIPE_WEBHOOK_SECRET` | Yes (billing) | Stripe webhook verification |
| `NEXT_PUBLIC_APP_URL` | Yes | `http://localhost:3000` / `https://app.example.com` |

**Never commit `.env`.** Use `.env.example` as template.

---

## 12. Deployment Checklist

- [ ] `pnpm build` passes (no type errors, no lint warnings)
- [ ] `pnpm test` + `pnpm test:e2e` pass
- [ ] Migrations run against production DB (Turso / SQLite volume)
- [ ] `AUTH_SECRET` rotated, not reused from dev
- [ ] CSP headers allow only required origins
- [ ] Rate limiting configured (Upstash / edge middleware)
- [ ] Backups scheduled for SQLite file / Turso replicas
- [ ] Health check endpoint (`/api/health`) returns 200

---

## 13. Quick Reference: File → Responsibility

| Path | Responsibility |
|------|----------------|
| `lib/db/queries/*.sql.ts` | All SQL reads/writes |
| `lib/db/migrations/*.sql` | Schema changes |
| `lib/validation/*.ts` | Input schemas + inferred types |
| `components/ui/*.tsx` | Design system primitives |
| `components/features/*.tsx` | Business-logic composites |
| `app/(dashboard)/**/page.tsx` | Server Components fetching + composing |
| `app/api/v1/**/route.ts` | Validation → query → response |
| `middleware.ts` | Auth guard, headers, redirects |
| `scripts/*.ts` | DB ops, type generation, one-off tasks |

---

**End of CLAUDE.md** — This file is the single source of truth for AI and human contributors. Update it when conventions change.