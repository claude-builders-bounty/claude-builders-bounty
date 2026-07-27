# CLAUDE.md

## Stack & Versions

- **Framework:** Next.js 15 (App Router, React 19, Server Components)
- **Language:** TypeScript 5.x strict mode
- **Database:** SQLite via Turso (libsql) for production, `better-sqlite3` for dev/testing
- **ORM:** Drizzle ORM — schema-first, lightweight, no code generation step
- **Auth:** NextAuth.js v5 (Auth.js) with credential + OAuth providers
- **Styling:** Tailwind CSS v4 + `clsx` for conditional classes
- **Validation:** Zod — share schemas between server actions and client forms
- **Hosting:** Vercel (or any Node.js server); Turso for edge-replicated DB

## Folder Structure

```
src/
  app/                  # Next.js App Router (file-based routing)
    (auth)/             # Route group: login, signup, forgot-password
    (dashboard)/        # Route group: authenticated pages
    api/                # API route handlers
  components/
    ui/                 # shadcn/ui primitives (Button, Input, Dialog...)
    forms/              # Form components (one file per form, colocated with action)
    layout/             # Shell layout components (Sidebar, Header, Shell)
  lib/
    db/
      schema.ts         # Drizzle table definitions
      index.ts          # DB client singleton
      migrations/       # Drizzle-generated SQL migrations
    auth.ts             # NextAuth config + callbacks
    auth/               # Auth helpers (getSession, requireAuth)
    validations.ts      # Shared Zod schemas
  server/
    actions/            # Server actions (one file per domain: users.ts, projects.ts)
    queries/            # Read queries (cached where possible)
  hooks/                # Client hooks (useFormState wrappers, optimistic-update hooks)
  types/                # Shared TypeScript types
drizzle.config.ts       # Drizzle Kit config
```

**Rule:** One file, one concern. A server action file handles one domain's mutations. A form component handles one form. No `utils.ts` dumpster.

## Database Conventions

### Schema Design
- Table names: `snake_case`, plural (`users`, `project_members`)
- Column names: `snake_case`
- Every table gets `id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID())`
- Every table gets `createdAt` and `updatedAt` timestamps
- Use `text` for enums, not Drizzle `pgEnum` — keeps it portable to Turso/libsql
- Foreign keys explicit with `.references(() => table.column)`

### Migrations
- **Never edit an existing migration file.** Create a new one.
- Run `drizzle-kit generate` after schema changes, `drizzle-kit migrate` to apply
- Migrations run at startup via `db:migrate` script, not at request time
- Check migration file into git — it's source of truth

### Query Patterns
- Server Components: query directly (no API layer)
- Server Actions: use `db.transaction()` for writes that touch multiple tables
- Client: never import `db/` directly — go through server actions
- Don't use raw SQL unless Drizzle can't express the query (rare)

## Component Patterns

### Server vs Client
- Default to Server Components. Add `"use client"` only when you need: `useState`, `useEffect`, `onClick`, browser APIs, or context
- Pass data as props from Server parent → Client child. Don't fetch in Client components
- Server Actions for mutations. No `fetch('/api/...')` from client components — import the action directly

### Form Pattern (canonical)
```tsx
// src/components/forms/create-project.tsx
"use client"
import { useActionState } from "react"
import { createProject } from "@/server/actions/projects"

const initialState = { error: null, success: false }

export function CreateProjectForm() {
  const [state, action, pending] = useActionState(createProject, initialState)
  // render form, use state.error for validation messages
}
```

### Data Display
- Server Component fetches data, passes to presentational Client wrapper for interactivity
- `Suspense` boundaries at the page level, not wrapping every component
- Loading states: skeleton UI (not spinners) for content areas

## Naming Conventions

- **Files:** `kebab-case.tsx` for components, `kebab-case.ts` for utilities
- **Components:** `PascalCase` default export, one component per file (except UI primitives that export variants)
- **Functions:** `camelCase` — `getUserById()`, `createProject()`
- **Server actions:** verb-first — `createProject`, `updateUser`, `deleteMember`
- **Route params:** `[entityId]` not `[id]` when multiple params exist

## Dev Commands

```bash
npm run dev          # next dev --turbo
npm run build        # next build
npm run db:generate  # drizzle-kit generate (after schema changes)
npm run db:migrate   # drizzle-kit migrate (apply pending migrations)
npm run db:studio    # drizzle-kit studio (GUI at localhost:4983)
npm run check        # tsc --noEmit + eslint + prettier --check
npm run test         # vitest run
```

## What We Don't Do (And Why)

- **No API routes for internal data.** Server Components and Server Actions eliminate this layer. API routes only for external consumers (webhooks, public API).
- **No `useEffect` for data fetching.** It causes waterfalls and double-renders. Server Components or Server Actions instead.
- **No ORM that needs code generation.** Prisma's codegen step breaks CI too often and the generated client is massive. Drizzle is zero-build.
- **No barrel exports (`index.ts` re-exporting everything).** They make tree-shaking unpredictable and confuse import resolution. Import from the source file.
- **No environment variables in client components without `NEXT_PUBLIC_` prefix.** The convention is enforced by Next.js; we just never need client-side env vars — keep secrets on the server.
- **No `any` types.** Unknown shapes get `unknown` with a Zod parse. Legacy data gets a gradual type with explicit `// TODO: type after migration`.
- **No inlining SQL migrations in application code.** Migrations are separate .sql files. Application code reads the current schema, not the migration history.
