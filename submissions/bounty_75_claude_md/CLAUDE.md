# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude Code exactly how this project is structured and what conventions to follow.
Every rule here exists for a reason. Do not deviate without asking first.

---

## Stack & Versions

| Tool | Version | Why |
|------|---------|-----|
| Next.js | 15 (App Router) | Server Components reduce client JS; layouts compose cleanly |
| React | 19 | Concurrent features, use() hook for async data |
| TypeScript | 5.x strict mode | Catch DB shape mismatches at compile time |
| SQLite | via `better-sqlite3` | Synchronous API fits Next.js route handlers; zero infra |
| Drizzle ORM | latest | Type-safe queries, migration-first, no magic |
| Tailwind CSS | 4.x | Utility-first; no CSS files to maintain |
| Zod | 3.x | Runtime validation at API boundaries |
| Auth | `lucia` or `better-auth` | Lightweight, no vendor lock-in |
| Testing | Vitest + Playwright | Fast unit tests, real browser E2E |

---

## Folder Structure

```
src/
  app/                     # Next.js App Router pages and layouts
    (auth)/                # Route group — auth pages (login, register)
      login/page.tsx
      register/page.tsx
    (dashboard)/           # Route group — protected routes
      layout.tsx           # Session check lives here
      dashboard/page.tsx
    api/                   # Route handlers (never put business logic here)
      auth/[...route]/
      webhooks/
    layout.tsx             # Root layout: fonts, providers
    page.tsx               # Landing page

  components/
    ui/                    # Primitive, reusable components (Button, Input, Modal)
    features/              # Domain components (UserCard, InvoiceTable)
    layouts/               # Page-level structural components

  lib/
    db/
      index.ts             # Single DB connection export
      schema.ts            # ALL Drizzle table definitions in one file
      migrations/          # Generated migration SQL files (never edit manually)
    auth/
      session.ts           # Session read/write helpers
    validators/            # Zod schemas — one file per domain entity
    utils/                 # Pure functions, no side effects

  server/                  # Server-only business logic
    actions/               # Next.js Server Actions — form submissions, mutations
    queries/               # Database read functions

  types/
    index.ts               # Shared TypeScript types (NOT database types — those come from Drizzle)
```

**Rules:**
- `server/` is never imported by client components. Use the `"server-only"` package.
- `components/ui/` contains zero business logic and zero DB imports.
- Route handlers in `api/` call `server/queries/` or `server/actions/`. Never raw SQL in route handlers.

---

## Database & Migration Conventions

### Schema

All tables are defined in `src/lib/db/schema.ts`. One file. Do not split.

```ts
// Example table — follow this exact pattern
export const users = sqliteTable("users", {
  id:        text("id").primaryKey(),           // CUID2, generated at app level
  email:     text("email").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().default(sql`(unixepoch())`),
});
```

**ID convention:** Use `cuid2` (import `createId` from `@paralleldrive/cuid2`). Never auto-increment integers for user-facing IDs. Never UUIDs (too long, ugly in URLs).

**Timestamps:** Always `integer` with `mode: "timestamp"`. Always use Unix epoch default. Always include both `createdAt` and `updatedAt`.

**Soft deletes:** Use `deletedAt: integer(...).default(null)` — never hard delete user data.

### Migrations

```bash
# Create a new migration after changing schema.ts
npx drizzle-kit generate

# Apply all pending migrations
npx drizzle-kit migrate
```

- Never edit migration files after they are committed.
- One schema change per migration. Do not batch unrelated changes.
- Migration files are named `0001_description.sql` — the description must be meaningful.
- Run migrations as part of the deployment process, not inside application code.

### Query Rules

- All queries live in `src/server/queries/`. Named exports, one file per entity.
- Never write raw SQL strings in queries — use Drizzle's query builder.
- Exception: complex aggregations can use `db.run(sql`...`)` but must be annotated with `// raw-sql: reason`.
- Always return typed results — never `any`.
- Paginate with `limit` + `cursor` (keyset), not `OFFSET`. Offset pagination breaks at scale.

---

## Component Patterns

### Server Components by default

Every component is a Server Component unless it needs interactivity. Add `"use client"` only when:
- Using `useState`, `useEffect`, or other React hooks
- Attaching event listeners
- Using browser APIs

**Wrong:**
```tsx
"use client"
export default async function UserList() { ... }  // async + "use client" doesn't make sense
```

**Right:**
```tsx
// Server Component — no directive needed
export default async function UserList() {
  const users = await getUsers();
  return <ul>{users.map(u => <UserRow key={u.id} user={u} />)}</ul>;
}
```

### Data fetching

Fetch data in Server Components or Server Actions. Never `fetch()` to your own API from the client — call the server function directly.

```ts
// Wrong: client calling its own API
const res = await fetch("/api/users");

// Right: call server query directly in a Server Component
const users = await getUsers();
```

### Forms and mutations

Use Next.js Server Actions for all form submissions.

```tsx
// src/server/actions/user.ts
"use server"
export async function updateUser(formData: FormData) {
  const parsed = updateUserSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };
  await db.update(users).set(parsed.data).where(eq(users.id, parsed.data.id));
  revalidatePath("/dashboard");
}
```

Validate with Zod before touching the DB. Always return `{ error }` or `{ data }` — never throw from Server Actions.

### Loading and error states

Use `loading.tsx` and `error.tsx` files in route segments. Do not handle loading/error state manually in page components.

---

## Dev Commands

```bash
# Start dev server
npm run dev

# Type check (run before committing)
npm run typecheck

# Run unit tests
npm run test

# Run E2E tests (requires dev server running)
npm run test:e2e

# Generate Drizzle migration after schema change
npm run db:generate

# Apply pending migrations
npm run db:migrate

# Open Drizzle Studio (visual DB browser)
npm run db:studio

# Build for production
npm run build

# Lint
npm run lint
```

`package.json` scripts map to:
```json
{
  "typecheck": "tsc --noEmit",
  "db:generate": "drizzle-kit generate",
  "db:migrate": "drizzle-kit migrate",
  "db:studio": "drizzle-kit studio"
}
```

---

## What We Don't Do (and Why)

| We don't do this | We do this instead | Why |
|---|---|---|
| `pages/` directory | `app/` directory | We're on Next.js 15 App Router — no mixing |
| `getServerSideProps` / `getStaticProps` | Server Components + `fetch()` with cache options | App Router handles caching declaratively |
| Prisma | Drizzle ORM | Drizzle is lighter, SQL-first, better SQLite support |
| UUID primary keys | CUID2 | Shorter, URL-safe, time-sortable |
| `OFFSET` pagination | Cursor-based (keyset) pagination | OFFSET degrades at scale |
| Raw SQL in route handlers | `server/queries/` | Keeps route handlers thin; queries are testable |
| `useState` + `useEffect` for server data | Server Components | Avoids client/server data duplication |
| `any` type | Drizzle inferred types + Zod | Type safety is the entire point |
| Hard delete | Soft delete (`deletedAt`) | User data is precious; hard deletes are irreversible |
| `.env` in version control | `.env.example` only | Secrets never touch git |
| `console.log` in production | Structured logging or nothing | Logs are noise unless they're searchable |
| Multiple DB connection files | Single `src/lib/db/index.ts` | One connection, easy to mock in tests |
| Business logic in components | `server/actions/` and `server/queries/` | Components render; servers compute |

---

## Environment Variables

Required in `.env.local`:

```bash
# Database
DATABASE_URL="./dev.db"          # Relative path for local dev; absolute path in production

# Auth
AUTH_SECRET="..."                # 32+ random bytes — generate with: openssl rand -base64 32

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

Never commit real values. The `.env.example` file is the source of truth for required variables.

---

## TypeScript Rules

- `strict: true` in `tsconfig.json`. No exceptions.
- No `// @ts-ignore` unless accompanied by a comment explaining why and a ticket reference.
- No `as any`. If you need to cast, cast to the most specific type possible.
- Import types with `import type { ... }` to avoid accidental runtime imports.
- Infer DB types from Drizzle: `type User = typeof users.$inferSelect`

---

## Testing Philosophy

- Unit test pure functions in `src/lib/` — these have no side effects and are easy to test.
- Integration test Server Actions with a real (in-memory) SQLite DB.
- E2E test critical user flows only: signup, login, core feature, payment.
- Do not test implementation details. Test observable behavior.
- A test that needs to be updated every time the code changes is a bad test.

---

## Git Conventions

- Branch naming: `feat/short-description`, `fix/issue-id-description`, `chore/what`
- Commit style: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- PRs are squash-merged. The PR title becomes the commit message — write it well.
- Never commit directly to `main`. Always use a PR.
- CI must pass (typecheck + tests) before merge. No exceptions.
