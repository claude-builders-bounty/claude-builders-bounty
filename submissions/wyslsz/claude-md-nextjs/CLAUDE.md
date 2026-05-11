# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Drop this file into any greenfield Next.js 15 App Router + SQLite project.
> Claude Code will understand the stack, conventions, and boundaries without asking.

## Stack & Versions

- **Framework**: Next.js 15 (App Router, React Server Components by default)
- **Database**: SQLite via `better-sqlite3` (sync, no connection pool needed)
- **Migration**: Raw SQL files in `db/migrations/`, applied by a script
- **Auth**: `next-auth` v5 (Auth.js) with credentials + OAuth providers
- **Styling**: Tailwind CSS v4 + `shadcn/ui` components
- **Validation**: Zod v4 (both client and server)
- **TypeScript**: strict mode, no `any` without a comment explaining why

## Project Structure

```
src/
├── app/                    # Next.js App Router (RSC-first)
│   ├── (auth)/             # Route group: login, register, verify
│   ├── (dashboard)/        # Route group: authenticated pages
│   │   ├── layout.tsx      # Dashboard shell (sidebar + header)
│   │   └── settings/       # Nested routes follow folder convention
│   ├── api/                # Route handlers (REST endpoints)
│   └── layout.tsx          # Root layout (providers, fonts, metadata)
├── components/
│   ├── ui/                 # shadcn/ui base components (automatic)
│   ├── forms/              # Form components with Zod schemas
│   └── shared/             # Reusable across multiple routes
├── db/
│   ├── index.ts            # Database singleton (better-sqlite3)
│   ├── schema.ts           # TypeScript types derived from SQL schema
│   ├── migrations/         # Numbered SQL files: 001_init.sql, 002_add_x.sql
│   └── migrate.ts          # Migration runner (reads + applies .sql files)
├── lib/
│   ├── auth.ts             # next-auth config (providers, callbacks, adapter)
│   ├── db-helpers.ts       # Query wrappers, pagination, transaction helper
│   └── utils.ts            # Pure utility functions (no side effects)
├── actions/                # Server Actions (import 'use server')
│   └── settings.ts         # Group by domain, not by CRUD
└── hooks/                  # Client-side hooks (use client)
    └── use-debounce.ts     # One file per hook
```

**Why this structure**: Route groups keep auth/un-auth separated without URL prefix leaks. `db/` is isolated from the web layer — the app never imports SQL directly, only through `db/` helpers. Server Actions live in `actions/` because they're the RPC layer between client and server.

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files (components) | `kebab-case.tsx` | `user-profile.tsx` |
| Files (utilities) | `kebab-case.ts` | `format-currency.ts` |
| React components | `PascalCase` | `UserProfile` |
| Functions | `camelCase` | `getUserById()` |
| DB tables | `snake_case` plural | `user_settings` |
| DB columns | `snake_case` | `created_at` |
| Server Actions | `verbNoun` | `updateUserProfile()` |
| Zod schemas | `PascalCase + Schema` | `UserProfileSchema` |
| Route params | `[kebab-case]` | `[user-id]` |

**Why kebab-case for files**: Next.js file-system routing uses folder names as URL segments. Kebab-case maps directly to SEO-friendly URLs without transformation.

## Database Conventions

### Migrations
- Files: `db/migrations/001_descriptive_name.sql`
- Never edit a migration after it's been applied
- Every migration is wrapped in a transaction (the runner handles this)
- Include a `-- Down:` comment for reversibility, even if not automated

### Schema Design
- Every table has: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `created_at TEXT DEFAULT (datetime('now'))`, `updated_at TEXT DEFAULT (datetime('now'))`
- Foreign keys are enabled (`PRAGMA foreign_keys = ON`) — the db singleton sets this
- Use `TEXT` for dates (ISO 8601), `INTEGER` for booleans (0/1), `REAL` for decimals
- No JSON columns — normalize into separate tables (SQLite can't index JSON)

### Query Patterns
- All queries go through `db-helpers.ts` — never call `db.prepare()` directly in route handlers
- Use parameterized queries always: `db.prepare('SELECT * FROM users WHERE id = ?').get(id)`
- Pagination: `LIMIT ? OFFSET ?` with a wrapper that returns `{ data, total, page, pageSize }`

**Why no ORM**: SQLite is simple enough that raw SQL is more readable and predictable than an ORM. We use TypeScript types generated from the schema for type safety. No Prisma, no Drizzle — they add complexity without solving a problem we have with SQLite.

## Component Patterns

### Server vs Client Components
- Default to Server Components (no `'use client'` directive)
- Add `'use client'` only when you need: `useState`, `useEffect`, event handlers (`onClick`), browser APIs
- Data fetching happens in Server Components — pass data down as props
- Client components receive data, not fetch it

### Forms
```tsx
// Always: Server Action + useActionState + Zod validation
// File: src/actions/settings.ts
'use server'
export async function updateProfile(prev: State, formData: FormData) { ... }

// File: src/components/forms/profile-form.tsx
'use client'
import { useActionState } from 'react'
// Uses the server action directly
```

### Error Handling
- Server Actions return `{ error: string } | { success: true }` — never throw
- Use `error.tsx` boundaries for unexpected errors (one per route segment)
- Loading states: `loading.tsx` for route-level, `<Suspense>` for component-level

## Commands

```bash
npm run dev              # Next.js dev server (localhost:3000)
npm run build            # Production build
npm run start            # Production server
npm run db:migrate       # Apply pending migrations
npm run db:seed          # Seed development data
npm run db:studio        # Open Drizzle Studio (visual DB browser)
npm run lint             # ESLint + TypeScript check
npm run typecheck        # TypeScript only (faster than lint)
```

## What We Don't Do (And Why)

- **No ORM** — SQLite + raw SQL + TypeScript types is simpler and more predictable. ORMs obscure query performance.
- **No API routes for internal data** — Use Server Actions or `db-helpers.ts` directly in Server Components. REST endpoints are only for external consumers.
- **No `useEffect` for data fetching** — Data fetching happens in Server Components. `useEffect` is for browser-side effects only (event listeners, intervals, etc.).
- **No barrel exports (`index.ts` re-exporting everything)** — They cause tree-shaking problems and circular dependency risks. Import directly from the file.
- **No environment variables on the client without `NEXT_PUBLIC_`** — Next.js enforces this. Server-only secrets never reach the client.
- **No `any`** — Every `any` must have a comment explaining why proper typing is impossible (should be rare).
- **No inline styles** — Use Tailwind classes. Keeps the markup readable and consistent.
- **No `// @ts-ignore`** — Use `// @ts-expect-error` with a reason comment. It fails when the error is fixed, preventing stale suppressions.

## Anti-Patterns to Avoid

```tsx
// ❌ Don't fetch in client components
'use client'
function Profile() {
  const [data, setData] = useState(null)
  useEffect(() => { fetch('/api/profile').then(...) }, [])
}

// ✅ Fetch in server component, pass as props
async function ProfilePage() {
  const profile = await getUserProfile()
  return <ProfileForm initialData={profile} />
}
```

```tsx
// ❌ Don't use raw SQL in route handlers
export async function GET() {
  const db = getDb()
  return Response.json(db.prepare('SELECT * FROM users').all())
}

// ✅ Use db-helpers abstraction
export async function GET() {
  const users = await listUsers({ page: 1, pageSize: 20 })
  return Response.json(users)
}
```

```tsx
// ❌ Don't throw in Server Actions
export async function deleteUser(id: number) {
  await db.prepare('DELETE FROM users WHERE id = ?').run(id) // might throw
}

// ✅ Return structured result
export async function deleteUser(id: number): Promise<ActionResult> {
  try {
    await removeUser(id)
    return { success: true }
  } catch (e) {
    return { error: 'Failed to delete user' }
  }
}
```

## Fresh Project Verification

To verify Claude Code understands this template:

1. `npx create-next-app@latest test-project --typescript --tailwind --eslint --app`
2. `cd test-project && npm install better-sqlite3 zod next-auth@beta`
3. Copy this `CLAUDE.md` to the project root
4. Ask Claude Code: "Add a user settings page with a form to update display name"
5. Claude should:
   - Create `db/migrations/001_user_settings.sql`
   - Create `src/actions/settings.ts` with Zod validation
   - Create `src/components/forms/settings-form.tsx` using `useActionState`
   - Not create an API route, not use `useEffect` for data, not use an ORM
