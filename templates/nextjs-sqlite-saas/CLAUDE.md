# CLAUDE.md - Next.js 15 App Router + SQLite SaaS

This file is the operating guide for a greenfield SaaS built with Next.js 15,
TypeScript, React 19, SQLite, and Drizzle ORM. Follow these rules unless the
user explicitly changes the stack.

## Stack And Versions

- Next.js 15 App Router in `src/app`. Reason: App Router keeps routing, layouts,
  Server Components, Server Actions, and Route Handlers in one model.
- React 19 with Server Components by default. Reason: most SaaS screens are
  data-heavy and should not ship client JavaScript unless they need interaction.
- TypeScript in strict mode. Reason: database rows, form payloads, and auth state
  must be checked before runtime.
- SQLite through Drizzle ORM. Use `better-sqlite3` for a local file database and
  Turso/libSQL for hosted SQLite. Reason: one schema model can support both local
  development and hosted production.
- Node.js runtime for routes and Server Actions that touch SQLite. Reason:
  `better-sqlite3` is not Edge-compatible and Turso clients still need explicit
  server-only boundaries.
- Tailwind CSS plus small local UI primitives. Reason: a SaaS starter needs
  consistent screens without forcing a component marketplace dependency.

## Project Structure

Use this structure unless a file already exists in a different conventional
location:

```text
src/
  app/
    (app)/
      dashboard/
        page.tsx
      settings/
        page.tsx
      layout.tsx
    (auth)/
      sign-in/
        page.tsx
      sign-up/
        page.tsx
    api/
      webhooks/
        route.ts
    actions/
      organizations.ts
      users.ts
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
    navigation/
  db/
    schema.ts
    migrate.ts
    seed.ts
    migrations/
  lib/
    auth/
      session.ts
    db/
      client.ts
      queries/
    env.ts
    validators/
  tests/
```

Rules and reasons:

- Keep route UI in `src/app` and reusable UI in `src/components`. Reason: route
  files should explain navigation, not become component libraries.
- Keep database schema in `src/db/schema.ts` and query helpers in
  `src/lib/db/queries`. Reason: schema changes and business reads have different
  review risks.
- Keep mutations in Server Actions under `src/app/actions` unless they are public
  APIs or webhooks. Reason: in-app forms should use App Router invalidation
  instead of ad-hoc API calls.
- Keep auth helpers under `src/lib/auth`. Reason: session parsing and permission
  checks must be shared by pages, actions, and route handlers.

## Naming Conventions

- Route segments use kebab-case: `billing-history`, `team-members`. Reason:
  URLs should be stable and readable.
- React components use PascalCase: `TeamMemberTable.tsx`. Reason: component
  imports stay visually distinct from utilities.
- Server-only modules use nouns plus context: `session.ts`, `client.ts`,
  `organizations.ts`. Reason: call sites should read like product behavior.
- Server Actions use verb phrases: `createOrganization`, `inviteMember`,
  `updateBillingEmail`. Reason: every mutation should be auditable by intent.
- Database tables use plural snake_case: `organizations`, `organization_members`.
  Columns use snake_case: `created_at`, `owner_id`. Reason: SQL stays consistent
  across SQLite tooling and logs.

## Dev Commands

Prefer these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx src/db/migrate.ts",
    "db:seed": "tsx src/db/seed.ts",
    "test": "vitest run"
  }
}
```

Run `npm run typecheck` and `npm run build` before claiming a feature is done.
Reason: SQLite and Server Component mistakes often pass local navigation but fail
at build time.

## Environment Rules

- Read environment variables through `src/lib/env.ts`. Reason: missing
  `DATABASE_URL`, auth secrets, and webhook secrets should fail in one place.
- Do not read `process.env` inside Client Components. Reason: client bundles
  cannot safely contain server secrets.
- Use `.env.local` for local values and never commit it. Commit `.env.example`
  with placeholder values. Reason: new developers need setup hints without
  leaking credentials.

Example `src/lib/env.ts`:

```ts
import 'server-only'

function requireEnv(name: string) {
  const value = process.env[name]
  if (!value) throw new Error(`Missing required environment variable: ${name}`)
  return value
}

export const env = {
  databaseUrl: requireEnv('DATABASE_URL'),
  sessionSecret: requireEnv('SESSION_SECRET'),
}
```

## Database Client Rules

- Import `server-only` in every DB client module. Reason: SQLite credentials and
  file handles must never enter a browser bundle.
- Initialize DB clients lazily with a getter. Reason: `next build` can evaluate
  modules before runtime-only configuration is available.
- Keep transactions short. Reason: SQLite allows many readers but only one writer.
- Enable WAL for local `better-sqlite3` databases. Reason: WAL improves concurrent
  reads during development and background jobs.

Example pattern:

```ts
import 'server-only'
import { drizzle } from 'drizzle-orm/better-sqlite3'
import Database from 'better-sqlite3'
import { env } from '@/lib/env'

let db: ReturnType<typeof drizzle> | null = null

export function getDb() {
  if (!db) {
    const sqlite = new Database(env.databaseUrl)
    sqlite.pragma('journal_mode = WAL')
    db = drizzle(sqlite)
  }
  return db
}
```

## SQL And Migration Conventions

- Generate migrations with `npm run db:generate`; apply them with
  `npm run db:migrate`. Reason: schema history must be reproducible.
- Migrations are append-only after merge. Reason: edited migrations break deployed
  databases and teammate environments.
- Use expand-and-contract for risky changes: add nullable column, backfill, switch
  reads/writes, then enforce constraints in a later migration. Reason: SQLite has
  limited `ALTER TABLE` behavior and production data needs a rollback path.
- Every tenant-owned table has `organization_id`, `created_at`, and `updated_at`.
  Reason: SaaS queries must be scoped and auditable.
- Add indexes for foreign keys and common filters in the same migration as the
  table or column. Reason: SQLite will not save slow dashboard queries later.
- Never run raw destructive SQL from application code. Reason: schema changes
  belong in reviewed migrations, not request handlers.
- For deletes, prefer soft delete columns such as `deleted_at` when user-facing
  history or billing records are involved. Reason: SaaS data usually has audit
  and support requirements.

## Component Patterns

- Server Components fetch data and compose pages. Reason: dashboards should render
  with minimal client JavaScript.
- Client Components are leaf components for stateful widgets only: dialogs,
  menus, tabs, comboboxes, optimistic buttons. Reason: pushing `'use client'` too
  high turns the app into a slower SPA.
- Pass plain serializable props from Server Components to Client Components.
  Reason: functions, database rows with custom prototypes, and secrets cannot
  cross the server/client boundary safely.
- Use forms plus Server Actions for authenticated in-app mutations. Reason:
  validation, mutation, and revalidation stay together.
- Use Route Handlers for webhooks, external APIs, file uploads, and integrations.
  Reason: those call sites need HTTP semantics and status codes.

Server Action pattern:

```ts
'use server'

import { revalidatePath } from 'next/cache'
import { getSession } from '@/lib/auth/session'
import { createOrganizationRow } from '@/lib/db/queries/organizations'

export async function createOrganization(formData: FormData) {
  const session = await getSession()
  if (!session.userId) throw new Error('Unauthorized')

  const name = String(formData.get('name') ?? '').trim()
  if (name.length < 2) throw new Error('Organization name is too short')

  await createOrganizationRow({ ownerId: session.userId, name })
  revalidatePath('/dashboard')
}
```

## Data Access Rules

- Query helpers must receive explicit IDs from the authenticated session. Reason:
  multi-tenant data leaks happen when helpers infer scope.
- Do not return raw auth secrets, tokens, or password hashes from query helpers.
  Reason: Server Component props can be passed further than intended.
- Validate all form and route inputs before DB writes. Reason: SQLite type
  affinity is permissive and will store bad data unless the app refuses it.
- Use transactions for multi-step writes. Reason: partial writes create billing,
  membership, and invitation inconsistencies.

## Authentication And Authorization

- Treat authentication as identity and authorization as a separate check. Reason:
  logged-in users are not automatically allowed to access every organization.
- Put permission helpers next to session helpers, for example
  `requireOrganizationRole(userId, organizationId, 'admin')`. Reason: every
  mutation should state the permission it needs.
- Re-check authorization inside Server Actions and Route Handlers. Reason: hidden
  buttons are not a security boundary.
- Store sessions in httpOnly cookies. Reason: Client Components should not read or
  manipulate session tokens.

## Error, Loading, And Empty States

- Add `loading.tsx` for slow dashboard segments. Reason: users need immediate
  feedback while Server Components resolve data.
- Add `error.tsx` around account, billing, and integration areas. Reason: one
  failed integration call should not blank the whole app.
- Empty states must include the next action, not explanation text only. Reason:
  SaaS users are usually trying to complete setup.

## Patterns To Follow

- Prefer Server Components for reads, Server Actions for app mutations, Route
  Handlers for external HTTP integrations.
- Keep DB access behind query helpers.
- Keep forms progressively enhanced with real `<form>` elements.
- Revalidate exact paths after mutations with `revalidatePath`.
- Use optimistic UI only after the server mutation path is correct.
- Add tests for query helpers and permission checks before UI-only tests.

## Anti-Patterns To Avoid

- Do not put `'use client'` in `layout.tsx` or page-level components unless the
  whole route is truly interactive. Reason: it forces unnecessary client bundles.
- Do not import `better-sqlite3`, Turso clients, or Drizzle clients from Client
  Components. Reason: the browser cannot run those modules and must not see DB
  credentials.
- Do not create migrations by editing the production database manually. Reason:
  teammates and deployments cannot reproduce the change.
- Do not use API routes for every form submission. Reason: Server Actions already
  provide the App Router mutation path with cache invalidation.
- Do not write SQL strings inline across components. Reason: scattered SQL makes
  tenant scoping and review harder.
- Do not skip `organization_id` filters in SaaS queries. Reason: this is the most
  common path to cross-tenant data exposure.
- Do not catch errors only to return `null`. Reason: silent failures produce
  empty dashboards and hide data integrity problems.

## Before Finishing Any Task

1. Run `npm run typecheck`.
2. Run `npm run build`.
3. If DB schema changed, run `npm run db:generate` and `npm run db:migrate` on a
   disposable local database.
4. Confirm changed routes have loading, error, and empty states where relevant.
5. State which commands were run and which were not run.

If a command is missing from the project, add the script or explicitly explain why
it is not applicable.
