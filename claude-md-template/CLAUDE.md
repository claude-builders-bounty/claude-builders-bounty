# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework:** Next.js 15 (App Router, Turbopack)
- **Language:** TypeScript 5.x (strict mode)
- **Database:** SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM:** Drizzle ORM (not Prisma — Prisma's SQLite support has poor edge compatibility and no `libsql` driver)
- **Auth:** NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **Styling:** Tailwind CSS v4
- **Packaging:** pnpm (not npm/yarn — faster, disk-efficient, strict)

## Dev Commands

```bash
pnpm dev          # Next.js 15 dev server on :3000
pnpm build        # Production build
pnpm lint         # ESLint + Prettier
pnpm test         # Vitest (not Jest — faster ESM-native)
pnpm db:generate  # Generate Drizzle migrations
pnpm db:migrate   # Apply pending migrations
pnpm db:seed      # Seed database with sample data
pnpm db:studio    # Open Drizzle Studio GUI
pnpm typecheck    # tsc --noEmit (separate from build)
```

## Folder Structure

```
src/
├── app/                    # App Router pages (route groups)
│   ├── (auth)/             # Auth pages (login, register)
│   ├── (dashboard)/        # App pages behind auth wall
│   │   └── _layout.tsx     # Auth check wrapper
│   ├── api/                # Route handlers
│   │   └── trpc/           # if using tRPC
│   └── globals.css
├── components/
│   ├── ui/                 # Primitive UI (Button, Input, Card...)
│   ├── forms/              # Form components (react-hook-form wrappers)
│   └── layout/             # Navigation, sidebar, header
├── lib/
│   ├── db/                 # Database layer
│   │   ├── schema/         # Drizzle schema files (one per domain)
│   │   ├── migrations/     # Auto-generated migration files
│   │   ├── index.ts        # Drizzle client singleton
│   │   └── seed.ts         # Seed data
│   ├── auth/               # Auth.js configuration
│   ├── email/              # Transactional email (Resend)
│   └── utils.ts            # Shared utilities
├── actions/                # Server Actions (colocated by domain)
│   ├── users.ts
│   └── billing.ts
└── styles/
```

### Why this structure

- **`lib/` groups pure logic** — testable without React. Schema, DB, auth, email don't belong in components.
- **`actions/` is a flat directory** — one file per domain module, not nested. Server Actions are thin orchestrators that call `lib/` functions. If an action exceeds 50 lines, extract logic into `lib/`.
- **`components/ui/` is separated from business components** — primitives never import from `actions/` or `lib/db/`. This prevents circular dependencies and keeps the UI kit portable.
- **Route groups `(auth)` and `(dashboard)` enforce auth boundaries at the layout level** — you never have to check auth inside a page component.

## Naming Conventions

| Artifact        | Convention                    | Example                  |
|-----------------|-------------------------------|--------------------------|
| Files           | `kebab-case`                  | `user-settings.tsx`      |
| Components      | `PascalCase`                  | `UserSettingsForm`       |
| Functions       | `camelCase`                   | `getUserById()`          |
| DB Schema       | `snake_case` (columns), `PascalCase` (tables) | `users.id`, `usersTable` |
| Server Actions  | `verbNoun`, camelCase         | `updateUserEmail`        |
| API Routes      | `kebab-case`                  | `/api/stripe/webhook`    |

## SQL / Migration Conventions

### Rules

1. **Every migration must be reversible.** If `up` creates a table, `down` drops it. Drizzle generates both automatically — never manually edit migrations.
2. **Schema files are the source of truth.** Never modify migration files directly. Change `schema/` → run `db:generate` → apply.
3. **Foreign keys are implicit in SQLite.** SQLite has foreign key parsing, but Drizzle relationships handle joins at the ORM level. Use `relations()` in schema, not raw FK constraints.
4. **Timestamps are stored as ISO 8601 text.** SQLite has no native datetime type. Use `text('created_at').default(sql\`(current_timestamp)\`)`.
5. **Index every foreign key column.** SQLite doesn't auto-index FKs. `createIndex().on(usersTable, { columns: [usersTable.createdBy] })`.
6. **Seed data represents realistic production states.** 3 users with different roles, 50+ sample records. Not "hello world" seeds.

### Anti-patterns to avoid

- ❌ Raw SQL in migrations (breaks Drizzle's idempotency tracking)
- ❌ `ALTER TABLE ADD COLUMN` for nullable columns in SQLite (SQLite doesn't support `ADD COLUMN IF NOT EXISTS` — use Drizzle's `alterTable` helper)
- ❌ Storing JSON in text columns without Drizzle's `text({ mode: 'json' })` — you lose type safety

## Component Patterns

### 1. Server Components by default

```tsx
// ✅ Preferred — fetch data in Server Component, pass down
export default async function DashboardPage() {
  const projects = await getProjectsForUser(userId)
  return <ProjectList projects={projects} />
}
```

**Why:** Less client JS, direct DB access without API endpoints, streaming via `loading.tsx`.

### 2. Client Components only when you need interactivity

```tsx
'use client'
// Only add 'use client' when using: useState, useEffect, onClick, onSubmit,
// browser APIs, or React context providers
```

**Allowed use cases:** forms, modals, toasts, drag-and-drop, real-time subscriptions, chart libraries.

### 3. Form pattern

```tsx
// Server Action + useActionState — no client-side validation library needed for basic forms
export function UpdateEmailForm() {
  const [state, action, pending] = useActionState(updateUserEmail, null)
  return (
    <form action={action}>
      <input name="email" type="email" required />
      {state?.error && <p className="text-red-500">{state.error}</p>}
      <Button disabled={pending}>Save</Button>
    </form>
  )
}
```

**Why:** No Zod form schema duplication. Server Actions validate once on the server using your API types. Zero client JS for validation.

### 4. Error boundaries

- `error.tsx` at every route group level — never a global catch-all.
- Each error boundary shows a "retry" button and logs to Sentry.
- `not-found.tsx` for 404s — don't throw errors for missing resources, use `notFound()`.

## Auth Pattern

### Session fetching

```tsx
// ✅ Correct: session is fetched once in a layout, passed down
const session = await auth()
if (!session) redirect('/login')

// ❌ Wrong: never call auth() inside individual page components
// ❌ Wrong: never use useSession() in Server Components
```

### Protected API routes

Route handlers check `auth()` at the top and return 401 immediately — don't let unauthenticated requests hit your database.

## What We Don't Do (And Why)

| Don't | Reason |
|-------|--------|
| ❌ Use `any` or `as` casts | TypeScript strict mode exists for a reason. If you fight types, extract and validate. |
| ❌ Embed API keys in `.env.local` | Use `process.env` only at the edge (server load). Better: use a secrets manager or `.env` tracked by infra. |
| ❌ Create a `utils/` directory | It becomes a junk drawer. Every util belongs to a domain module in `lib/`. |
| ❌ Use `redux` or `zustand` for server state | React Server Components + Server Actions eliminate the need for client-side query state. For shared client state (theme, toasts), use React Context with `useOptimistic`. |
| ❌ Write raw HTML in JSX | Every element must use Tailwind classes. No inline `<style>` tags. No CSS modules (they negate Tailwind's design system). |
| ❌ Store files on the server filesystem | Use S3/R2. Heroku-style filesystem storage doesn't scale and breaks deploys. |
| ❌ Commit `drizzle.config.ts` changes accidentally | Generated migrations belong in git. Config does not. |

## Testing Strategy

- **Vitest** for unit tests (pure functions in `lib/`)
- **Playwright** for E2E (auth flows, CRUD, billing)
- **No testing-library** for component rendering — Server Components are tested by E2E, pure functions by unit tests. Client component tests add maintenance cost with little value in a Next.js App Router project.

## Environment Variables

```
# Required
DATABASE_URL=file:./data/dev.db        # SQLite path (dev)
TURSO_DATABASE_URL=libsql://...         # Turso URL (prod)
TURSO_AUTH_TOKEN=...                    # Turso token (prod)
AUTH_SECRET=...                         # NextAuth secret
AUTH_GITHUB_ID=...                      # GitHub OAuth
AUTH_GITHUB_SECRET=...                  # GitHub OAuth
RESEND_API_KEY=...                      # Transactional email

# Optional
NEXT_PUBLIC_POSTHOG_KEY=...             # Analytics
NEXT_PUBLIC_SENTRY_DSN=...              # Error tracking
```

## Key Dependencies

```json
{
  "dependencies": {
    "next": "^15",
    "react": "^19",
    "@auth/core": "^0.37",
    "next-auth": "^5",
    "drizzle-orm": "^0.36",
    "@libsql/client": "^0.14",
    "better-sqlite3": "^11",
    "resend": "^4",
    "tailwindcss": "^4"
  },
  "devDependencies": {
    "drizzle-kit": "^0.28",
    "vitest": "^2",
    "playwright": "^1",
    "@types/better-sqlite3": "^7"
  }
}
```
