# CLAUDE.md — Opinionated Template for Next.js 15 + SQLite SaaS

> **Audience:** Claude Code (or any AI coding assistant) and human contributors.
> **Goal:** Make every important decision before the first commit so nobody — human or AI — wastes a turn asking "which ORM?", "where do migrations live?", or "is this a Server Component or a Client Component?".
> **Philosophy:** Opinionated beats flexible. A template that says "use better-sqlite3 with WAL mode" is more useful than one that says "use any database you like". This file is a *contract*: deviate from it and you are writing a different project.

---

## Table of contents

1. [Stack & versions](#1-stack--versions)
2. [Folder structure](#2-folder-structure)
3. [Naming conventions](#3-naming-conventions)
4. [SQL & migration conventions](#4-sql--migration-conventions)
5. [Component patterns (Server vs Client)](#5-component-patterns-server-vs-client)
6. [Data fetching & mutations](#6-data-fetching--mutations)
7. [Validation with Zod](#7-validation-with-zod)
8. [Styling rules](#8-styling-rules)
9. [TypeScript rules](#9-typescript-rules)
10. [Error handling](#10-error-handling)
11. [Logging](#11-logging)
12. [Testing with Vitest](#12-testing-with-vitest)
13. [Environment variables](#13-environment-variables)
14. [Security baseline](#14-security-baseline)
15. [Performance baseline](#15-performance-baseline)
16. [Git workflow](#16-git-workflow)
17. [Dev commands](#17-dev-commands)
18. [Patterns to follow](#18-patterns-to-follow)
19. [Anti-patterns to avoid](#19-anti-patterns-to-avoid)
20. [What we don't do (and why)](#20-what-we-dont-do-and-why)
21. [CHANGELOG format (Keep a Changelog)](#21-changelog-format-keep-a-changelog)
22. [Quick verification](#22-quick-verification)

---

## 1. Stack & versions

We pin major versions and let `^` cover patch + minor updates. Bumping a major version is a deliberate decision, not a side effect of `npm update`.

| Layer | Choice | Pinned | Why this and not the alternative |
|---|---|---|---|
| Framework | **Next.js 15** (App Router) | `^15.0.0` | App Router is the only Router still receiving new features. Pages Router is in maintenance. |
| Language | **TypeScript 5.5+** with `strict: true` | `^5.5.0` | JS in a SaaS is a liability: every refactor is a guessing game. |
| Runtime | **Node.js 20 LTS** | `>=20.0.0` | Required by Next 15 and better-sqlite3 prebuilt binaries. |
| Database | **better-sqlite3** (local) or **Turso** (hosted libSQL) | `^11.0.0` / `@libsql/client ^0.14.0` | See [§4](#4-sql--migration-conventions) for the full reasoning. |
| ORM | **None. Raw SQL via tagged template literals.** | n/a | See [§20](#20-what-we-dont-do-and-why) for the ORM rant. |
| Validation | **Zod 3** | `^3.23.0` | Single source of truth for runtime + compile-time types. |
| Styling | **Tailwind CSS 4** | `^4.0.0` | Utility classes ship ~10× less CSS than component libraries. |
| Forms | **react-hook-form** + `@hookform/resolvers/zod` | `^7.51.0` / `^3.9.0` | Smallest re-render footprint. Zod resolver reuses the same schemas. |
| Auth | **Auth.js (NextAuth v5)** or `oslo` + custom | `^5.0.0` | v5 plays nicely with App Router server actions. |
| Email | **Resend** | `^4.0.0` | Simplest API; React Email templates. |
| Background jobs | **In-process queue (better-sqlite3-backed)** for v1 | n/a | Postgres-backed queues (BullMQ) are overkill until you need horizontal scale. |
| Testing | **Vitest 2** | `^2.0.0` | Native ESM, 10× faster Jest cold start, Jest-compatible API. |
| E2E | **Playwright** | `^1.45.0` | First-class TS, multi-browser, no flake tax like Cypress. |
| Lint | **ESLint 9** (`eslint-config-next`) + **Prettier 3** | `^9.0.0` / `^3.3.0` | `next lint` ships sensible defaults; Prettier removes style debates from code review. |
| Package manager | **pnpm** | `^9.0.0` | Faster installs, strict peer-dep resolution, content-addressable store. |
| Container | **Docker** (multi-stage) | n/a | Local dev parity with production. |

**Rule:** every dependency is justified in the table above. If you want to add one, add a row first.

---

## 2. Folder structure

```
.
├── app/                          # Next.js App Router
│   ├── (marketing)/              # Route group: no auth, public pages
│   │   ├── page.tsx              # Landing page
│   │   ├── pricing/page.tsx
│   │   └── layout.tsx            # Marketing shell (minimal nav)
│   ├── (app)/                    # Route group: authenticated SaaS UI
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── loading.tsx       # Skeleton for streaming
│   │   │   └── error.tsx         # Route-level error boundary
│   │   ├── settings/
│   │   └── layout.tsx            # Authenticated shell (sidebar, user menu)
│   ├── (auth)/                   # Route group: sign-in, sign-up, etc.
│   │   ├── sign-in/page.tsx
│   │   └── sign-up/page.tsx
│   ├── api/                      # ONLY for webhooks + OAuth callbacks
│   │   └── webhooks/stripe/route.ts
│   ├── layout.tsx                # Root layout: <html>, fonts, providers
│   ├── error.tsx                 # Global error boundary
│   ├── not-found.tsx
│   └── globals.css               # Tailwind directives only
│
├── components/
│   ├── ui/                       # Primitive, reusable (Button, Input, Dialog)
│   │   ├── button.tsx
│   │   └── input.tsx
│   ├── forms/                    # Form compositions built on react-hook-form
│   │   └── sign-up-form.tsx
│   └── feature/                  # Feature-specific, NOT shared
│       └── billing/price-table.tsx
│
├── lib/
│   ├── db/
│   │   ├── client.ts             # better-sqlite3 singleton with WAL pragma
│   │   ├── migrations/           # Numbered SQL files (see §4)
│   │   │   ├── 0001_initial.sql
│   │   │   └── 0002_add_subscriptions.sql
│   │   ├── migrate.ts            # Migration runner (idempotent)
│   │   └── queries/              # One file per domain entity
│   │       ├── users.ts
│   │       └── subscriptions.ts
│   ├── auth/                     # Auth.js config + helpers
│   ├── validation/               # Zod schemas, exported and re-used
│   │   └── user.ts
│   ├── env.ts                    # Validated env via Zod
│   ├── logger.ts                 # Structured logger
│   └── http.ts                   # Typed fetch wrapper
│
├── actions/                      # Server Actions, one file per domain
│   ├── auth.ts
│   ├── users.ts
│   └── billing.ts
│
├── server/                       # Server-only utilities (cannot import from client)
│   ├── email/
│   └── queue/
│
├── types/                        # Shared type definitions
│   └── db.ts                     # Row types inferred from query return shapes
│
├── tests/
│   ├── unit/                     # Vitest
│   └── e2e/                      # Playwright
│
├── scripts/                      # One-off scripts (seed, db reset, etc.)
│   └── seed.ts
│
├── public/                       # Static assets
├── .env.example
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── vitest.config.ts
├── playwright.config.ts
├── Dockerfile
├── package.json
└── CLAUDE.md                     # ← you are here
```

**Why these groupings:**

- `app/` follows Next.js 15 conventions. Route groups `(name)/` let us share layouts without leaking URL segments. `(marketing)`, `(app)`, and `(auth)` each get their own `layout.tsx` with their own chrome.
- `components/ui` is **primitives** (Shadcn-style): presentational, no business logic. `components/feature` is **business UI** and is allowed to import server actions.
- `lib/db/queries/<entity>.ts` is the *only* place SQL is written. Components and actions import typed query functions. This makes it trivial to swap a query for a mock in tests.
- `actions/` is a flat folder of server actions. We don't nest them under features because Server Actions are public API of the app — they deserve a top-level home.
- `app/api/` exists **only** for Stripe webhooks, OAuth callbacks, and third-party integrations that POST to a URL. Internal mutations use Server Actions (§6).
- `tests/` is split `unit/` and `e2e/`. Vitest config picks up `tests/unit/**/*.test.ts`; Playwright config picks up `tests/e2e/**/*.spec.ts`.

**Anti-pattern in this structure:** `lib/utils.ts` is the junk drawer of every Next.js project. We forbid it. If you need a helper, put it in the file that uses it, or in a domain folder (`lib/billing/format-cents.ts`).

---

## 3. Naming conventions

| Thing | Convention | Example | Why |
|---|---|---|---|
| Files | `kebab-case.ts` | `user-profile.tsx` | Works on every OS, no case-sensitivity bugs in CI. |
| React components | `PascalCase` export, file is `kebab-case` | `Button` in `button.tsx` | Matches React community + ESLint defaults. |
| Functions | `camelCase` verbs | `getUserById`, `createSubscription` | Predictable grep. |
| Booleans | `is`, `has`, `should` prefix | `isAdmin`, `hasAccess` | Reads like English in conditionals. |
| Constants | `SCREAMING_SNAKE_CASE` for compile-time | `MAX_LOGIN_ATTEMPTS = 5` | Standard JS convention. |
| DB tables | `snake_case`, plural | `users`, `subscription_items` | SQL convention; matches generated SQL from Rails/Django. |
| DB columns | `snake_case` | `created_at`, `stripe_customer_id` | Avoids quoting hell. |
| TS types for rows | `PascalCase` + `Row` suffix | `UserRow`, `SubscriptionRow` | Distinguishes DB rows from DTOs. |
| API/Action input | `camelCase` | `emailAddress`, not `email_address` | Matches TypeScript/JSON, not SQL. |
| Env vars | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` | Standard. |
| Migrations | `NNNN_description.sql` | `0042_add_team_members.sql` | See §4. |

---

## 4. SQL & migration conventions

### 4.1 Why better-sqlite3 (and why no ORM)

**Decision:** Use `better-sqlite3` (Node addon) for local dev and `@libsql/client` for production (Turso). Write **raw SQL** in typed query functions. No Drizzle, no Prisma, no Kysely.

**Reasoning:**

1. **SQLite + ORM is friction you don't need.** An ORM adds a query builder, a schema DSL, a migration tool, a generation step, and a runtime abstraction — to wrap a database whose native query language is already the simplest in existence.
2. **Migrations are honest.** With raw SQL, a migration is the exact `CREATE TABLE` statement you'd write by hand. With an ORM, you write a DSL that *generates* SQL you never see, then debug by reading the generated output.
3. **SaaS queries get weird.** "Get all users whose subscription was canceled in the last 30 days but who logged in this week." That is one SQL query with a window function. The ORM version is six chained method calls that hide what's actually running.
4. **better-sqlite3 is the fastest SQLite driver in Node.** Synchronous API. No connection pool. No callback hell. Read latency for hot queries: ~50µs.
5. **WAL mode is a one-line pragma that doubles write throughput** and lets readers not block writers. There is no reason to ship without it.

**When to reconsider:** if you need MySQL/Postgres-specific features (full-text search with ranking, JSONB indexes, `RETURNING` for triggers), graduate to Postgres + Drizzle. Don't pre-optimize.

### 4.2 Migration rules

1. **Forward-only.** Never edit a migration after it has been applied to any environment. Add a new one.
2. **Numbered, zero-padded, four digits.** `0001_initial.sql`, `0002_add_users.sql`, `0042_…`. Numbers are sequential, never reused.
3. **One logical change per file.** Two unrelated `ALTER TABLE` statements → two migration files. Easier to bisect, easier to revert in dev.
4. **Idempotent where possible.** Use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`. Migrations should be safe to re-run on a partially-migrated database.
5. **Explicit `IF EXISTS` on drops.** `DROP TABLE IF EXISTS` in down-migrations only — and see rule 1: we don't write down-migrations.
6. **Track applied migrations in a `schema_migrations` table:**

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  version    INTEGER PRIMARY KEY,
  applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

7. **Migration runner is deterministic.** `lib/db/migrate.ts` reads `migrations/*.sql`, finds versions not in `schema_migrations`, applies them in order, inside a transaction per file. Refuses to start if a SQL file has a *lower* number than the highest applied version.
8. **No Prisma migrate, no Drizzle Kit, no Atlas.** They generate migrations from a DSL. We write the SQL directly. See [§19](#19-anti-patterns-to-avoid) for the rant.

### 4.3 Query function pattern

Every DB call is a named function in `lib/db/queries/<entity>.ts`. It takes plain values, returns typed rows.

```ts
// lib/db/queries/users.ts
import { db } from '@/lib/db/client';
import type { UserRow } from '@/types/db';

export function getUserById(id: string): UserRow | null {
  return db
    .prepare<[string], UserRow>('SELECT * FROM users WHERE id = ?')
    .get(id) ?? null;
}

export function createUser(input: { email: string; name: string }): UserRow {
  const stmt = db.prepare(`
    INSERT INTO users (id, email, name, created_at, updated_at)
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    RETURNING *
  `);
  return stmt.get(crypto.randomUUID(), input.email, input.name) as UserRow;
}
```

**Why this pattern:** components and Server Actions never write `db.prepare(...)` themselves. They call a named function. The function is the unit you test, the unit you mock, the unit you grep.

---

## 5. Component patterns (Server vs Client)

### 5.1 Default: Server Component

`app/**/page.tsx` and `app/**/layout.tsx` are Server Components **unless they need interactivity**. A Server Component:

- Runs on the server, sends HTML, no JS shipped.
- Can `import` from `lib/db/queries/*` directly. No HTTP roundtrip.
- Cannot use `useState`, `useEffect`, `onClick`, browser APIs.

### 5.2 When to add `'use client'`

Add the directive **only** when at least one of these is true:

1. The component uses `useState`, `useReducer`, or any other React hook.
2. The component attaches event handlers (`onClick`, `onChange`, `onSubmit`).
3. The component uses a browser-only API (`localStorage`, `IntersectionObserver`, `window`).
4. The component is a third-party UI library that demands client (most of them — Shadcn primitives are the exception).

If a component doesn't need any of these, **it must not have `'use client'`**. Period.

### 5.3 The composition pattern

A page is a Server Component. It fetches data and passes it as props to a small Client Component for the interactive bits.

```tsx
// app/(app)/billing/page.tsx — Server Component
import { getUserById } from '@/lib/db/queries/users';
import { getSubscription } from '@/lib/db/queries/subscriptions';
import { CancelButton } from '@/components/feature/billing/cancel-button';

export default async function BillingPage() {
  const user = await getUserById('current'); // assume auth helper
  const sub = await getSubscription(user!.id);
  return (
    <main>
      <h1>Billing</h1>
      <p>Plan: {sub!.plan}</p>
      <CancelButton subscriptionId={sub!.id} /> {/* only this is a client */}
    </main>
  );
}
```

```tsx
// components/feature/billing/cancel-button.tsx
'use client';
import { cancelSubscription } from '@/actions/billing';

export function CancelButton({ subscriptionId }: { subscriptionId: string }) {
  return (
    <form action={cancelSubscription.bind(null, subscriptionId)}>
      <button type="submit">Cancel</button>
    </form>
  );
}
```

**Why:** the page does no client-side data fetching (one less waterfall). The interactive piece is the smallest possible client island. HTML payload is small. First Contentful Paint is fast.

### 5.4 `'use client'` placement

`'use client'` is a **file-level** directive. Place it at the very top of the file, no imports above it. It applies to everything the file exports.

**Anti-pattern:** wrapping a whole page in `'use client'` to share one form hook. Extract the form, keep the page server-side.

---

## 6. Data fetching & mutations

### 6.1 Read path: Server Components fetch directly

```tsx
// page.tsx (Server)
import { getPosts } from '@/lib/db/queries/posts';
export default async function Page() {
  const posts = await getPosts();
  return <PostList posts={posts} />;
}
```

No `useEffect`, no SWR, no React Query. The component is rendered on the server with the data already in hand. The HTML response includes the rendered list.

### 6.2 Write path: Server Actions (not API routes)

For every internal mutation — create user, update settings, cancel subscription — use a **Server Action**, not a `POST /api/...` route.

```ts
// actions/billing.ts
'use server';
import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { getSession } from '@/lib/auth';
import { cancelSubscription } from '@/lib/db/queries/subscriptions';

const Input = z.object({ subscriptionId: z.string().uuid() });

export async function cancelSubscriptionAction(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');
  const parsed = Input.parse({ subscriptionId: formData.get('subscriptionId') });
  await cancelSubscription(parsed.subscriptionId);
  revalidatePath('/billing');
}
```

**Why Server Actions over API routes:**

- **Type-safe end to end.** A Server Action is a function. You call it from a form or a button. No `fetch`, no JSON serialization, no `any` slipping in.
- **Progressive enhancement.** `<form action={serverAction}>` works without JS. API routes don't.
- **No public surface area.** API routes are URLs; they get scraped, fuzzed, and indexed by Shodan. Server Actions are not routable.
- **Built-in CSRF protection.** Next 15 ties Server Actions to the build's action ID + origin check.

**When to still use `app/api/*`:** webhooks (Stripe POSTs to a URL), OAuth callbacks (the provider needs a redirect target), and anything a non-browser client must call.

### 6.3 Forms

Use `react-hook-form` + `zodResolver` for any non-trivial form (more than two fields, conditional fields, async validation).

```tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { SignUpSchema, type SignUpInput } from '@/lib/validation/user';
import { signUpAction } from '@/actions/auth';

export function SignUpForm() {
  const { register, handleSubmit, formState: { errors } } =
    useForm<SignUpInput>({ resolver: zodResolver(SignUpSchema) });
  return (
    <form onSubmit={handleSubmit(async (data) => await signUpAction(data))}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}
      <button type="submit">Sign up</button>
    </form>
  );
}
```

The schema is defined **once** in `lib/validation/user.ts` and reused on the server:

```ts
// lib/validation/user.ts
export const SignUpSchema = z.object({
  email: z.string().email(),
  password: z.string().min(12),
});
export type SignUpInput = z.infer<typeof SignUpSchema>;
```

**Why:** same validation rules on client and server. No "works in the form, blows up in the action" surprises.

---

## 7. Validation with Zod

- **Every external input has a Zod schema.** Form fields, Server Action args, API route bodies, webhook payloads, env vars.
- **Schemas live in `lib/validation/`.** One file per domain entity, named after the entity (`user.ts`, `billing.ts`).
- **The schema is the type.** `type X = z.infer<typeof XSchema>` — never duplicate the shape by hand.
- **Server Actions parse with `.parse()` (throws) or `.safeParse()` (returns result).** `.parse()` is fine because errors bubble to the nearest `error.tsx` boundary.

```ts
// actions/auth.ts
'use server';
import { SignUpSchema } from '@/lib/validation/user';

export async function signUpAction(raw: unknown) {
  const data = SignUpSchema.parse(raw); // throws ZodError on bad input
  // ...
}
```

**Why Zod over alternatives:**

- TypeScript inference is bidirectional: schema → type, no manual `interface User { ... }`.
- Composable: `z.object({ ... }).merge(...)`, `.partial()`, `.pick()`.
- Standardized error shape you can render uniformly.
- One library covers forms, server actions, env, and config validation.

---

## 8. Styling rules

- **Tailwind CSS 4 only.** No CSS-in-JS (no styled-components, no emotion, no vanilla-extract). No Sass, no LESS, no CSS modules.
- **`globals.css` contains only Tailwind directives:**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- **No `style={{ ... }}` inline objects** for static styles. Inline `style` is reserved for *dynamic* values that come from props (e.g. `style={{ width: `${progress}%` }}`).
- **Component variants via `cva` (class-variance-authority).** One component, named variants, typed props.
- **Dark mode via `class` strategy.** `darkMode: 'class'` in `tailwind.config.ts`. A small `<ThemeToggle />` flips the class on `<html>`.
- **Icons: `lucide-react`.** One icon set, tree-shaken, ~1KB per icon.

**Why no CSS-in-JS:** the App Router renders on the server. CSS-in-JS libraries that rely on runtime style injection either break (no DOM) or ship a runtime that costs you ~10KB gzipped of JS just to color a button. Tailwind compiles to a static stylesheet that the browser caches.

**Why no CSS Modules:** they reintroduce a naming and import layer with none of the design-token benefits of Tailwind.

---

## 9. TypeScript rules

`tsconfig.json` settings (non-negotiable):

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

- **`strict: true`** — non-negotiable. Every other flag is implied by it; we set them explicitly so the next dev doesn't wonder.
- **`noUncheckedIndexedAccess`** — `arr[0]` is `T | undefined`. Catches a whole class of off-by-one bugs at compile time.
- **`exactOptionalPropertyTypes`** — `{ x?: number }` is not assignable to `{ x?: number | undefined }`. Surfaces sloppy `undefined` handling.

### 9.1 The `any` rule

**`any` is forbidden.** Use:

- `unknown` when you genuinely don't know the shape, then narrow with Zod or type guards.
- A precise type inferred from a Zod schema.
- `Record<string, never>` for "this object should be empty".

If you reach for `any`, you are skipping a check that the type system is trying to do for you. `// eslint-disable-next-line` is not a solution; fix the type.

### 9.2 The `as` rule

Type assertions (`as Foo`) are restricted to:

1. **Test mocks:** `vi.mocked(fetch).mockResolvedValue(response as Response)`.
2. **Schema → row casts** that you have manually verified (rare, and add a comment).

`as any` is never acceptable. ESLint rule `@typescript-eslint/no-explicit-any` is set to `error`.

### 9.3 Imports

- **Use the `@/` path alias** for everything inside the project. No `../../../components/...` traversal.
- **Named exports only.** No default exports (except Next.js page/layout files, which require them).
- **Type-only imports use `import type`.** Keeps them out of the runtime bundle.

```ts
import { getUserById } from '@/lib/db/queries/users';
import type { UserRow } from '@/types/db';
```

---

## 10. Error handling

### 10.1 Boundaries

- `app/error.tsx` is the **global** error boundary. It catches anything that bubbles up.
- Each route can override with its own `app/<route>/error.tsx` to give a more specific recovery UI.
- `app/not-found.tsx` handles 404s. `app/global-error.tsx` handles errors in the root layout itself.

```tsx
// app/(app)/billing/error.tsx
'use client';
export default function BillingError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <p>Something went wrong loading billing.</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

### 10.2 Server Action errors

- Server Actions **throw** on error. They do not return `{ ok: false, error }` envelopes.
- `try`/`catch` belongs in the action only when you need to **recover** (e.g. retry a network call). For "this is a programmer error", throw.
- Thrown errors in Server Actions are caught by the nearest `error.tsx` boundary.

### 10.3 Logging errors

Every caught-and-swallowed error is logged with the structured logger (§11). The log includes:

- `level: 'error'`
- `error.message`
- `error.stack` (server-side only, never sent to the client)
- `context`: a short object describing the request (`{ userId, route, action }`)

---

## 11. Logging

- **One logger:** `lib/logger.ts` exports a thin wrapper around `pino` (production) and `console` (dev).
- **Structured JSON in production.** Readable pretty-print in dev.
- **No `console.log` in committed code.** ESLint rule `no-console: error` (with `dev` allowed via override).
- **Redact PII at the logger boundary.** The logger strips `email`, `password`, `token`, `cookie`, `authorization`. Don't rely on every call site to remember.

```ts
// lib/logger.ts
import pino from 'pino';
export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  redact: { paths: ['*.email', '*.password', '*.token', 'req.headers.authorization'], censor: '[REDACTED]' },
});
```

---

## 12. Testing with Vitest

### 12.1 Setup

- Vitest config: `vitest.config.ts` with `environment: 'node'` for unit, `environment: 'jsdom'` for component tests.
- One test file per source file: `foo.ts` → `foo.test.ts` next to it (or under `tests/unit/` mirroring the path).
- **Test names read as sentences:** `it('returns null when the user does not exist', ...)`.

### 12.2 What to test

| Layer | What to test | How |
|---|---|---|
| Pure functions | All branches, all edge cases | Direct call, no setup. |
| Query functions | SQL returns expected rows against a known fixture DB | `beforeEach` resets the in-memory SQLite (`':memory:'`). |
| Server Actions | Auth gating, validation, side effects | Mock the session; assert on returned data + DB state. |
| Components | Render output, form submission | `@testing-library/react` + `userEvent`. |
| E2E (Playwright) | One happy path per critical flow | Sign up, subscribe, cancel. Don't re-test what unit tests cover. |

### 12.3 Coverage

- We **do not** enforce a coverage percentage. Coverage is a lagging indicator; 100% coverage with bad tests is worse than 70% with good ones.
- Every bug fix lands with a test that reproduces the bug. PR review rejects bug fixes without a regression test.

### 12.4 Mocking

- Mock at the **module boundary**, not the network. Don't mock `better-sqlite3`; use `:memory:` and seed it.
- For external HTTP, use `msw` (Mock Service Worker). It runs the real `fetch` against a request handler, which catches more bugs than `vi.mock('fetch')`.

---

## 13. Environment variables

- **All env vars are validated at boot** via Zod. `lib/env.ts`:

```ts
import { z } from 'zod';
const Schema = z.object({
  DATABASE_URL: z.string().url(),
  AUTH_SECRET: z.string().min(32),
  RESEND_API_KEY: z.string().startsWith('re_'),
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
});
export const env = Schema.parse(process.env);
```

- **Importing `env` from `process.env` directly is forbidden.** ESLint rule `no-process-env: error`. Always go through the validated object.
- **`.env.example` ships with every var, no values.** CI fails if any var used in code is missing from `.env.example`.
- **No secrets in git history.** Use platform secret stores (Vercel env, Fly secrets, GitHub Actions secrets).

---

## 14. Security baseline

- **Authentication** on every authenticated route. `lib/auth/getSession()` returns `Session | null`. A `null` result in a `(app)/` route is a bug.
- **Authorization** is explicit. The user object from the session is not enough; you check `canAccess(user, resource)`. Don't leak by ID; leak by access check.
- **CSRF** is handled by Server Actions automatically; for raw form posts, use a double-submit cookie or SameSite=Strict.
- **Rate limiting** on every mutation. A 5-line in-memory token bucket for v1 (`lib/auth/rate-limit.ts`); swap for Redis-backed when you need multi-instance.
- **SQL injection:** we use parameterized queries **always**. `db.prepare('SELECT * FROM users WHERE id = ?')` — never string-concat user input.
- **XSS:** React escapes by default. Never `dangerouslySetInnerHTML`; if you must, sanitize with `DOMPurify` server-side first.
- **Headers:** set via `next.config.ts` `headers()`:

```ts
async headers() {
  return [{
    source: '/(.*)',
    headers: [
      { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self' 'nonce-{NONCE}'; ..." },
    ],
  }];
}
```

- **Dependencies:** `pnpm audit` in CI. Renovate or Dependabot for PR-based updates.

---

## 15. Performance baseline

- **No client-side data fetching for initial render.** Server Components do it.
- **Images via `next/image`.** Always. Provides lazy loading, responsive sizes, AVIF/WebP.
- **Fonts via `next/font`.** Self-hosted, no FOUT, no Google request.
- **Streaming:** use `<Suspense>` boundaries so slow queries don't block the page shell. `loading.tsx` files give you a skeleton for free.
- **Cache headers** on static assets (Next handles this). On API routes you care about caching, set `Cache-Control` explicitly.
- **DB indexes** on every column used in `WHERE`, `ORDER BY`, or `JOIN`. Add the index in the *same migration* as the table.
- **N+1 queries:** if you find yourself looping and querying, stop. Use a single `IN (...)` query and join client-side.
- **Bundle size:** the bundle is checked in CI with `@next/bundle-analyzer`. Regressions over 5% block the PR.

---

## 16. Git workflow

- **`main` is always deployable.** No commits to `main` directly.
- **Branch from `main`:** `feat/short-description`, `fix/short-description`, `chore/...`, `docs/...`.
- **Commit messages follow Conventional Commits:** `feat(billing): add cancel-subscription action`. This drives `release-please` and the CHANGELOG.
- **PRs require:** a green CI, one approval, and — for any non-trivial change — a CHANGELOG entry under `## [Unreleased]`.
- **Squash merge.** One commit per PR on `main`. PR title becomes the commit message; it must follow Conventional Commits.
- **No force-push to `main`.** No rewriting history of `main` once a PR is merged.

---

## 17. Dev commands

`package.json` scripts:

| Script | Command | Purpose |
|---|---|---|
| `dev` | `next dev` | Local dev server on `:3000`. |
| `build` | `next build` | Production build. |
| `start` | `next start` | Run the production build. |
| `lint` | `next lint` | ESLint over the project. |
| `lint:fix` | `next lint --fix` | Auto-fix what ESLint can. |
| `typecheck` | `tsc --noEmit` | TypeScript validation, no JS emitted. |
| `test` | `vitest run` | Unit tests, single run (CI mode). |
| `test:watch` | `vitest` | Unit tests, watch mode. |
| `test:e2e` | `playwright test` | End-to-end tests. |
| `test:e2e:ui` | `playwright test --ui` | Playwright UI mode for debugging. |
| `db:migrate` | `tsx lib/db/migrate.ts` | Apply pending migrations. |
| `db:reset` | `tsx scripts/reset-db.ts` | Drop, recreate, re-migrate, seed. **Destructive.** |
| `db:seed` | `tsx scripts/seed.ts` | Populate dev data. |
| `db:studio` | `npx @libsql/client-studio` (Turso) or `sqlite-web data.db` (local) | Browse the DB. |
| `format` | `prettier --write .` | Format the whole tree. |
| `format:check` | `prettier --check .` | CI mode. |
| `knip` | `knip` | Detect unused files, deps, exports. |
| `prepare` | `husky` | Install git hooks. |

**Typical dev loop:**

```bash
pnpm install
cp .env.example .env
pnpm db:migrate
pnpm db:seed
pnpm dev
```

In a second terminal:

```bash
pnpm test:watch
```

**Pre-commit hook (husky):** runs `lint-staged` (ESLint + Prettier on staged files) and `pnpm typecheck` on the whole tree.

**Pre-push hook:** runs `pnpm test`. If tests fail, push is blocked.

---

## 18. Patterns to follow

### 18.1 Colocate, then promote

A component used in two files lives in the second file until a third needs it, then it moves to `components/`. Don't pre-emptively create `components/ui/Button.tsx` before you have a Button.

### 18.2 Server Action per mutation, not per page

`actions/billing.ts` exports `createSubscriptionAction`, `cancelSubscriptionAction`, `updatePaymentMethodAction`. Each is independently importable, independently testable. Don't put five mutations in one mega-action with a `type` discriminator.

### 18.3 Validate at the edge

The first thing every Server Action does is parse its input with Zod. The first thing every `app/api/*/route.ts` does is parse the body. Inside the codebase, types are trusted; at the edge, they are not.

### 18.4 Idempotent operations

Mutations that can be retried (webhook handlers, "forgot password" emails) are **idempotent**. Check whether the operation has already been performed before performing it. Use a unique constraint or a `state` column.

### 18.5 Use transactions for multi-write operations

If a server action writes to two tables, both writes are in a single `db.transaction(() => { ... })()`. Half-applied state is a bug.

```ts
export function createUserWithProfile(userInput: UserInput, profileInput: ProfileInput) {
  return db.transaction(() => {
    const user = createUser(userInput);
    createProfile({ userId: user.id, ...profileInput });
    return user;
  })();
}
```

### 18.6 Small, named, exported query functions

See §4.3. Every query is a named function in `lib/db/queries/<entity>.ts`. No raw SQL in components. No raw SQL in Server Actions except for the simplest one-liner.

### 18.7 Constants in code, not config

Magic numbers (max login attempts, token TTLs) are named constants at the top of the file that uses them. They become config (env vars) only when they actually need to differ between environments.

### 18.8 Prefer composition over configuration

A `<Button variant="primary" />` is fine. A `<Button config={{ variant: 'primary', size: 'lg', theme: 'dark', icon: 'left' }} />` is not. Use `cva` for variants and let the consumer compose children for icon positioning.

### 18.9 Fail fast at boot

`lib/env.ts` parses env vars on import. If something is missing or wrong, the process exits with a clear message. Don't wait until the first request to discover that `RESEND_API_KEY` is unset.

### 18.10 PRs are small and reversible

A PR that touches 30 files is a PR that can't be reverted. Aim for <400 lines of diff, one logical change.

---

## 19. Anti-patterns to avoid

### 19.1 ORM (Prisma, Drizzle, Knex, TypeORM, Sequelize)

**Why bad for SaaS:** see §4.1. The query language is the abstraction. Wrapping a 50-year-old declarative language in a 2024 JS DSL gives you worse SQL, slower debugging, and a migration tool that you don't control.

**When to revisit:** Postgres-specific features (JSONB, partial indexes, `LISTEN/NOTIFY`). Then graduate the DB and reconsider.

### 19.2 `useEffect` for data fetching

**Why bad:** it runs after render, requires a loading state, runs on every dep change, can't be SSR'd, and creates waterfalls. Server Components fetch on the server during render. There is no equivalent on the client that isn't worse.

### 19.3 `pages/` directory (Pages Router)

**Why bad:** Pages Router is in maintenance. New features (Server Actions, streaming, RSC) are App Router only. New project, App Router, no debate.

### 19.4 Default exports (except Next.js page/layout)

**Why bad:** they break refactor tooling, make rename ambiguous (`Foo` vs `foo`), and allow two files in the same directory to export `default` with the same name. Named exports are greppable and refactor-safe.

### 19.5 `any`

**Why bad:** it disables the type system at exactly the point you need it most (the boundary you don't control). `unknown` forces a runtime check; `any` doesn't.

### 19.6 Inline styles for static values

**Why bad:** `style={{ color: 'red' }}` ships JS, can't be tree-shaken, breaks design tokens, can't be overridden by media queries. Use Tailwind classes.

### 19.7 API routes for internal mutations

**Why bad:** see §6.2. They lose type safety, lose progressive enhancement, gain a public URL.

### 19.8 `console.log` in production code

**Why bad:** unstructured, no levels, can't be filtered, no redaction, no correlation IDs. Use the logger.

### 19.9 Untyped env vars

**Why bad:** `process.env.DATABASE_URL` is `string | undefined`. The first DB call crashes with a confusing message at runtime. `env.DATABASE_URL` (after Zod parse) is `string` and crashes at boot with a clear message.

### 19.10 CSS-in-JS

**Why bad:** runtime cost on the server (or a 10KB runtime on the client), no static extraction, harder to cache, no design tokens. Tailwind is faster to write *and* faster at runtime.

### 19.11 Client-side `fetch` to your own API

**Why bad:** it's a Server Action with extra steps. Two serialization boundaries, two type systems, two error paths. Call the query function directly in a Server Component, or use a Server Action.

### 19.12 Indexing columns you don't query

**Why bad:** every index slows writes. A 10-column table with 8 indexes inserts ~5× slower than with 1. Add the index when the slow query shows up in a slow log, not preemptively.

### 19.13 Defaulting to `'use client'`

**Why bad:** every client directive ships JS to the browser. Default to Server. Add `'use client'` only when forced.

### 19.14 Migrations without indexes

**Why bad:** you'll add the index in a follow-up migration, but the original `CREATE TABLE` is already running in production without it, and now you have a hot table to index without downtime. Add indexes in the same migration as the table.

### 19.15 Edit a committed migration

**Why bad:** the local DB has the migration applied. Production has it applied. Your edit only affects future clones. Reproducible drift. Always add a new migration.

### 19.16 `Math.random()` for IDs

**Why bad:** collisions at scale, no sortability, guessable. Use `crypto.randomUUID()` (built-in) or ULIDs (`ulid` npm package, sortable).

### 19.17 `dangerouslySetInnerHTML`

**Why bad:** the prop name is the warning. If you must render HTML, sanitize with `DOMPurify` server-side first.

### 19.18 `as` for "fixing" a type error

**Why bad:** the type system is telling you something. `as` lies to it. The runtime behavior is unchanged, but you've removed the only thing that could have caught the bug at compile time. Use `unknown` + a type guard, or fix the underlying type.

### 19.19 Pulling `node_modules` into the repo

**Why bad:** it isn't, and never was, a thing. `pnpm install` from a lockfile.

### 19.20 Reading a row in a Server Component and passing the whole row to a Client Component

**Why bad:** Server-to-client serialization is expensive and leaks fields (e.g. `password_hash`). Pass only the fields the client needs.

---

## 20. What we don't do (and why)

- **No Redux / Zustand / Jotai / MobX.** Server Components are the store. If you need shared client state, lift it to a context provider at the root of a `(app)/` route group. Reach for `useState` first; reach for a store only when you have proven the state actually needs to be global.
- **No CSS-in-JS.** See §8.
- **No GraphQL.** A SaaS with a SQLite backend doesn't have a query-shape problem; it has an N+1 problem and a query-funneling problem. SQL in typed functions solves both without a new server.
- **No microservices.** You have one app, one DB. Splitting them before you have 10 engineers is the most expensive way to slow down development.
- **No `lodash`.** Modern JS + native array methods cover 95% of `lodash`. For the 5% that doesn't, import the specific function (`lodash.debounce`) and tree-shake the rest.
- **No moment.js / date-fns (for simple cases).** `Intl.DateTimeFormat` and `Intl.RelativeTimeFormat` cover 90% of date formatting with zero dependencies. Add `date-fns` only when you need time-zone math.
- **No axios.** `fetch` is in the standard library, has been for years, and works in Server Components. For retries/timeouts, a 20-line wrapper beats a 50KB dep.
- **No Swagger/OpenAPI generators.** Internal API is Server Actions, which are typed. External API (if you have one) gets a handwritten `docs/api.md` or a `tRPC` router — both better than a generated OAS file.
- **No Prettier config debates.** Default Prettier config. `printWidth: 80`, `singleQuote: true`, `trailingComma: 'all'`. Don't change them.
- **No custom webpack config.** Next 15 hides webpack behind `next.config.ts`. If you need a webpack tweak, justify it in the PR. Most "needed" webpack tweaks are resolvable with a different import.
- **No `useEffect(() => { document.title = ... }, [title])`.** Use Next 15's `metadata` export or the `useDocumentTitle` hook from a UI lib. Don't manage the document in effects.
- **No `any` and no `as` for "convenience".** See §9.
- **No Jest.** Vitest is faster, ESM-native, and Jest-compatible. Migration is a config change.
- **No default exports of components.** See §19.4.
- **No `pages/` directory.** See §19.3.

---

## 21. CHANGELOG format (Keep a Changelog)

This project follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and this file **adheres to [Semantic Versioning 2.0.0](https://semver.org/)**.

`CHANGELOG.md` lives at the repo root. It is the **human-readable** changelog (what changed and why), not a commit log.

### 21.1 Structure

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New cancel-subscription server action with idempotency guard.

### Changed
- Migrate auth from session cookies to JWT to support edge runtime.

### Deprecated
- `GET /api/users/:id` — use the new `getUserById` server action.

### Removed
- Drop the `legacy_session` table from `0009_drop_legacy.sql`.

### Fixed
- Plan downgrade no longer bills the previous plan's proration.

### Security
- Tighten CSP: remove `unsafe-inline` from `script-src` in production.

## [1.2.0] - 2026-07-14

### Added
- Team invites via email.
- Per-user audit log.

### Fixed
- Webhook handler now retries on 5xx (was: dropped the event).

[Unreleased]: https://github.com/owner/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/owner/repo/compare/v1.1.0...v1.2.0
```

### 21.2 Section rules

The seven Keep a Changelog section types, in the order they should appear:

1. `### Added` — new features.
2. `### Changed` — changes in existing functionality.
3. `### Deprecated` — soon-to-be removed features.
4. `### Removed` — now-removed features.
5. `### Fixed` — bug fixes.
6. `### Security` — vulnerability fixes (CVEs, hardening).

Use only the sections that have entries. Omit empty ones — never list `### Added` with nothing under it.

### 21.3 What goes in (and what doesn't)

- ✅ A user-facing change: a new button, a fixed bug, a new env var, a removed API.
- ✅ A breaking change: marked with `**BREAKING**:` prefix in the entry.
- ❌ Internal refactors that don't change behavior.
- ❌ Dependency bumps (those go in `pnpm-lock.yaml` and the release notes).
- ❌ Every commit (that's what `git log` is for).

### 21.4 Versioning

- **MAJOR** (`2.0.0`): breaking change to public API, schema, or Server Action signatures.
- **MINOR** (`1.3.0`): new feature, new Server Action, new migration that's purely additive.
- **PATCH** (`1.2.4`): bug fix, security fix, internal refactor.

The version is bumped in `package.json` by `release-please` based on Conventional Commits, in a release PR. The CHANGELOG entry is generated from PR titles in the same release PR.

### 21.5 Release process

1. Merge PRs into `main` with Conventional Commit titles.
2. `release-please` opens a release PR that bumps `package.json` and updates `CHANGELOG.md` under a new version heading.
3. Review the release PR. Edit entries for clarity if needed.
4. Merge the release PR. A GitHub Release is created with the same notes. The tag triggers deployment.

### 21.6 Anti-patterns in CHANGELOGs

- ❌ "Various improvements" — say what improved.
- ❌ Bumping a section to `## [1.2.0]` while still adding to it. Once released, the section is frozen.
- ❌ Editing old releases. They are historical record. If a fix was missed, add it under `[Unreleased]`.
- ❌ Putting `## [Unreleased]` below older releases. It always goes at the top.
- ❌ Mixing user-facing and internal entries. If a refactor shipped a user-facing fix, mention only the fix.

---

## 22. Quick verification

Use this section to verify that Claude Code (or any AI assistant) reads the CLAUDE.md correctly. The goal: zero clarifying questions on the first task.

### 22.1 Setup

```bash
# 1. Create a fresh Next.js 15 project
pnpm create next-app@latest test-claude-md --ts --app --tailwind --eslint --src-dir=false --import-alias="@/*"
cd test-claude-md

# 2. Drop this CLAUDE.md at the repo root
cp ../path/to/CLAUDE.md ./CLAUDE.md

# 3. Open the project in Claude Code
claude
```

### 22.2 Probe prompts (each should answer without asking a question)

Run each of these as the first message in a new session. A correctly-loaded CLAUDE.md should produce a complete, opinionated answer with no "which database?" / "where should I put migrations?" / "Server or Client?" questions.

| # | Prompt | Expected behavior |
|---|---|---|
| 1 | "Add a `posts` table with `id`, `title`, `body`, `author_id`, `created_at`. Wire it up so I can list and create posts." | Claude creates a numbered migration `000X_create_posts.sql` in `lib/db/migrations/`, adds indexes in the same file, creates `lib/db/queries/posts.ts` with `getPosts` and `createPost`, adds `actions/posts.ts` with a `createPostAction`, and a `app/(app)/posts/page.tsx` Server Component that renders a form posting to the action. **No API route. No ORM. No `'use client'` on the page.** |
| 2 | "I need a button that toggles a counter." | Claude writes a tiny Client Component with `'use client'`, `useState`, and an `onClick`. Does not turn the whole page into a client component. |
| 3 | "Validate that a user-submitted email is a real email before saving." | Claude adds a Zod schema in `lib/validation/user.ts` (`z.string().email()`), imports it in the Server Action, calls `.parse()` on the input. Does not write a regex by hand. |
| 4 | "Add a dark mode toggle." | Claude creates a `ThemeToggle` Client Component that flips the `class` attribute on `<html>`, persists the preference in `localStorage` (or a cookie), and uses `darkMode: 'class'` from the Tailwind config. Does not introduce styled-components. |
| 5 | "Migrate the `users` table to add a `phone_number` column." | Claude writes `00XX_add_phone_number_to_users.sql` (forward-only, idempotent with `IF NOT EXISTS`), updates the migration runner output, and confirms the running migration is forward-only. Does **not** edit the original `0001_initial.sql`. |
| 6 | "How do I log an error from a Server Action?" | Claude uses the structured logger from `lib/logger.ts`, includes a `context` object with `userId`, `route`, `action`, and notes that thrown errors bubble to the nearest `error.tsx` boundary. |
| 7 | "What's the policy on TypeScript `any`?" | Claude answers: forbidden. Use `unknown` + Zod or a type guard. No `// @ts-ignore`. No `as any`. |
| 8 | "I added a new env var. What do I do?" | Claude updates `lib/env.ts` to include the var in the Zod schema, adds it to `.env.example` with a comment, and notes the rule against reading `process.env` directly. |

### 22.3 Success criteria

The template works if, after pasting it into a new project:

- **Zero clarifying questions** on the first five tasks in the table above.
- **One consistent file layout** across all generated code (queries in `lib/db/queries/`, actions in `actions/`, components in `components/feature/...`).
- **No forbidden patterns** appear without explanation: no `useEffect` for data fetching, no API routes for internal mutations, no ORM import, no CSS-in-JS, no `any` type, no `'use client'` on Server-Component pages.

### 22.4 Failure modes (what it would look like if the template is broken)

- Claude asks "which database?" → §1 and §4 are not being read.
- Claude writes a Prisma migration → §4.2 and §20 are not being read.
- Claude wraps the page in `'use client'` → §5 is not being read.
- Claude uses `console.log` instead of the logger → §11 is not being read.
- Claude writes a down-migration → §4.2 rule 1 is not being read.
- Claude defaults to `any` → §9.1 is not being read.

If any of these appear in the first response, the CLAUDE.md is not being loaded by the assistant. Verify the file is at the project root and named `CLAUDE.md` (case-sensitive on Linux/macOS, irrelevant on Windows but matters in CI).

---

## Appendix A: Why this template exists in this exact form

Most "CLAUDE.md templates" you find online are collections of generic best practices. They read like an ESLint config — long, abstract, and forgettable. This template is different in three ways:

1. **Every rule has a reason.** If a rule doesn't have a justification in the prose, it was deleted during writing. Generic advice ("write clean code") is a placeholder, not a rule.
2. **It is opinionated.** The template says "use better-sqlite3", "use Zod", "use Vitest", "no ORM", "Tailwind only". It does not enumerate options. Options are the AI's job to evaluate; the template's job is to remove that evaluation from every session.
3. **It is verifiable.** §22 is a self-test. A CLAUDE.md that *looks* good but produces the wrong code is worse than one that looks opinionated.

When adapting this template for a different stack (Postgres, Vue, etc.), preserve the structure: every section is paired with a "why", and §22 is updated to reflect the new stack.

## Appendix B: License and reuse

This template is provided under the MIT license. You are encouraged to copy, modify, and redistribute it. If you improve it, please open a PR upstream so the next person benefits.

The Keep a Changelog format (§21) is © Olivier Lacan, used under CC BY 3.0.
