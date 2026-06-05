# CLAUDE.md — Next.js 15 + SQLite SaaS Template

This file is the source of truth for Claude Code when working on a Next.js 15
App Router project with SQLite (better-sqlite3 or Turso). Paste it at the
root of a greenfield project; Claude Code will work without asking clarifying
questions.

---

## Stack

- **Framework:** Next.js 15 App Router (React 19, Server Components)
- **Language:** TypeScript (strict)
- **DB:** better-sqlite3 (local) or Turso (libSQL/HTTP, prod)
- **ORM:** Drizzle ORM with `drizzle-kit` for migrations
- **Styling:** Tailwind CSS v4 (no CSS-in-JS, no Sass)
- **Auth:** Auth.js v5 (next-auth@beta) with email magic-link
- **Validation:** Zod (server + client)
- **Package manager:** pnpm (lockfile committed)

## Versions to pin

```
"next": "15.x",
"react": "19.x",
"typescript": "5.6+",
"drizzle-orm": "0.36+",
"drizzle-kit": "0.28+",
"@auth/core": "0.37+",
"tailwindcss": "4.x",
"zod": "3.23+"
```

---

## Folder structure

```
app/                   # App Router routes
  (marketing)/         # Public marketing pages (no auth)
  (app)/               # Authenticated app routes
  api/                 # Route handlers
components/
  ui/                  # Primitive UI (Button, Input, Modal)
  features/            # Feature-specific (UserMenu, InvoiceTable)
lib/
  db/                  # Drizzle schema + client + migrations
  auth/                # Auth.js config
  validation/          # Zod schemas (re-exported by API + forms)
  utils/               # Pure functions (cn, format, etc.)
drizzle/               # Generated SQL migrations (committed!)
```

### Naming conventions

| What | Convention | Example |
|---|---|---|
| Files | `kebab-case.tsx` | `user-menu.tsx` |
| Components | `PascalCase` | `UserMenu` |
| Functions | `camelCase` | `getUserById` |
| DB tables | `snake_case`, plural | `users`, `invoice_items` |
| DB columns | `snake_case` | `created_at`, `user_id` |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_URL` |
| Routes | `kebab-case` | `/api/webhooks/stripe` |
| Constants | `SCREAMING_SNAKE` | `MAX_UPLOAD_SIZE` |

---

## Database

### Schema (`lib/db/schema.ts`)

- One file per domain area (`schema/users.ts`, `schema/invoices.ts`)
- Re-exported from `lib/db/schema/index.ts`
- **Always** include `id`, `created_at`, `updated_at`
- Use `text` UUIDs, not auto-increment integers
- Foreign keys always `NOT NULL` + `references(...).onDelete('cascade')`

```ts
// Good
export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull().unique(),
  created_at: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updated_at: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
})

// Bad — no updated_at, integer id, no cascade
export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email'),
})
```

### Migrations

- **Always** commit migration files in `drizzle/`
- Migration name: `NNNN_descriptive_name.sql` (auto-generated)
- **Never** edit a committed migration — add a new one instead
- `pnpm db:generate` → `pnpm db:migrate` (local), `pnpm db:migrate:prod` (Turso)
- Schema changes go in a single PR with the migration, never split

### Queries

- Use Drizzle's typed query builder, **never** raw SQL
- All queries in Server Actions or Route Handlers, never in components
- Use `db.select().from(table).where(eq(...))` not template strings

---

## Components

- **Server Components by default** — only add `"use client"` when you need state/effects/event handlers
- Co-locate component + types in the same file until ~300 lines
- Use `cn()` helper (clsx + tailwind-merge) for conditional classes
- **No barrel files** (`index.ts` re-exports) — they break tree-shaking in Next 15
- Component props type: `ComponentProps<typeof Component>` not duplicated interfaces

### Forms

- Use `react-hook-form` + `@hookform/resolvers/zod`
- Zod schema is the source of truth — server action validates with the same schema
- Use `<form action={serverAction}>` not `onSubmit` handlers

---

## API

### Route Handlers (`app/api/.../route.ts`)

- **Always** validate input with Zod
- Return typed responses, never `any`
- Use proper HTTP status codes (201 create, 204 delete, 400 validation, 401 auth, 403 forbidden, 404 not found, 409 conflict, 500 server)
- Errors: `{ error: { code: 'STRING_CODE', message: 'human readable' } }`

```ts
// Good
export async function POST(req: Request) {
  const body = await req.json()
  const parsed = CreateUserSchema.safeParse(body)
  if (!parsed.success) {
    return Response.json({ error: { code: 'INVALID_INPUT', message: parsed.error.message } }, { status: 400 })
  }
  // ...
}

// Bad — no validation, returns string
export async function POST(req: Request) {
  const body = await req.json()
  const user = await db.insert(users).values(body)
  return Response.json('ok')
}
```

### Server Actions

- Mark with `"use server"` at top of file
- Always return `{ ok: true, data } | { ok: false, error }`
- Use for mutations, not reads (reads go in Server Components)
- Validate with Zod, throw on invalid (caught by error boundary)

---

## Patterns we follow

1. **One source of truth** — schema, types, validation all from Zod + Drizzle
2. **Server-first** — only add `"use client"` when truly needed
3. **Type everything** — no `any`, no `as unknown as X` escape hatches
4. **Validate at boundaries** — every API entry point validates with Zod
5. **Errors are typed** — return discriminated unions, not throws (except at top level)
6. **Migrations are append-only** — never edit committed migrations
7. **Env vars validated at startup** — fail fast on missing config
8. **Webhooks verify signatures** — never trust inbound payloads blindly
9. **Rate limit public endpoints** — use `@upstash/ratelimit` or similar

## Anti-patterns to avoid

| Anti-pattern | Why |
|---|---|
| Raw SQL via `db.run()` | Loses type safety, bypasses migrations |
| `useEffect` for data fetching | Use Server Components |
| `localStorage` for auth tokens | XSS-stealable, use httpOnly cookies |
| Inline event handlers in client components | Server Actions are cleaner |
| `dangerouslySetInnerHTML` | Almost always a bug, use `react-dom/server` |
| Catch-all `try/catch` that swallows | Log + rethrow or return typed error |
| Storing money as floats | Use integer cents |
| `as const` chains > 3 levels | Use Zod schema or explicit type |
| Magic numbers in components | Extract to named const |
| `console.log` in committed code | Use proper logger (pino, etc.) |
| Default exports everywhere | Named exports for tree-shaking |
| Mutating props in components | Props are read-only, derive new state |

## What we don't do (and why)

- **No Redux/Zustand** — Server Components + Server Actions cover our state needs
- **No CSS modules** — Tailwind only, single styling system
- **No Express/Fastify custom server** — Next.js API routes are enough
- **No `getServerSideProps`** — App Router uses `async` Server Components
- **No GraphQL** — REST + Server Actions cover our needs without the complexity
- **No microservices** — monolith until we have 10+ engineers
- **No `any`** — TypeScript strict mode, no escape hatches
- **No `package-lock.json`** — pnpm uses `pnpm-lock.yaml`
- **No barrel files** — explicit imports are clearer and tree-shake better

---

## Dev commands

```bash
pnpm dev               # Start dev server (http://localhost:3000)
pnpm build             # Production build
pnpm start             # Start production server
pnpm lint              # ESLint
pnpm typecheck         # tsc --noEmit
pnpm test              # Vitest
pnpm test:e2e          # Playwright
pnpm db:generate       # Generate migration from schema diff
pnpm db:migrate        # Run migrations (local SQLite)
pnpm db:migrate:prod   # Run migrations (Turso)
pnpm db:studio         # Drizzle Studio (visual DB editor)
pnpm format            # Prettier
```

## Git conventions

- Branch: `feat/`, `fix/`, `chore/`, `refactor/` prefix
- Commit: Conventional Commits (`feat:`, `fix:`, `chore:`)
- PR: link to issue, include screenshot/recording for UI changes
- Squash-merge by default, preserve conventional commit title

## When in doubt

- Server Component first
- Validate with Zod at every API boundary
- Type everything, escape hatches discouraged
- Read the [Next.js 15 docs](https://nextjs.org/docs) before guessing
- Ask: "would a new hire understand this without explanation?" If no, refactor.
