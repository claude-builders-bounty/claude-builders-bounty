# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this as the operating guide for a greenfield SaaS built with Next.js 15 App Router, TypeScript, Tailwind, and SQLite via either `better-sqlite3` for local/serverful deploys or Turso/libSQL for hosted SQLite.

## Stack

- Next.js 15 App Router, React Server Components by default.
- TypeScript strict mode. Avoid `any`; use `unknown` plus narrowing when input shape is external.
- SQLite as the source of truth. Use `better-sqlite3` for single-node apps, Turso/libSQL when distributed reads or hosted DB are required.
- Tailwind CSS for styling. Keep component APIs small; avoid theme abstractions until repeated.
- Server Actions for simple mutations. Route Handlers only for webhooks, public API endpoints, file uploads, or third-party callbacks.

## Project structure

```txt
src/
  app/                  # routes, layouts, loading/error boundaries
    (marketing)/         # public pages
    (app)/               # authenticated product pages
    api/                 # route handlers only when HTTP API is required
  components/
    ui/                  # reusable primitives: Button, Input, Dialog
    feature/             # feature-level composed components
  db/
    index.ts             # DB connection + typed query helpers
    schema.sql           # canonical schema snapshot
    migrations/          # numbered SQL migrations
  lib/
    auth.ts              # auth/session helpers
    env.ts               # environment validation
    validators.ts        # shared zod schemas
  server/
    actions/             # server actions grouped by feature
    queries/             # read-only DB queries grouped by feature
  types/                 # shared TS types that are not inferred elsewhere
```

Why: routes stay thin, DB code stays server-only, and business logic does not leak into UI components.

## Naming conventions

- Files and folders: kebab-case (`billing-settings.tsx`, `create-invoice.ts`).
- React components: PascalCase exports from kebab-case files.
- Server Actions: verb-first names (`createProject`, `updateWorkspaceName`).
- Query functions: read-first names (`getProjectById`, `listWorkspaceMembers`).
- DB tables: plural snake_case (`users`, `workspace_members`).
- DB columns: snake_case (`created_at`, `workspace_id`).
- TypeScript objects returned to UI: camelCase. Convert at DB boundary, not inside components.

## SQLite and migration rules

- Every schema change gets a numbered migration: `0001_initial.sql`, `0002_add_billing.sql`.
- Migrations are append-only after merge. Never edit a migration already applied by another environment.
- `schema.sql` must match the result of all migrations. Update it in the same PR as migrations.
- Always enable foreign keys when opening a connection: `PRAGMA foreign_keys = ON`.
- Use `INTEGER PRIMARY KEY` for local numeric IDs or `TEXT PRIMARY KEY` for public IDs. Never expose autoincrement IDs in URLs if enumeration matters.
- Store timestamps as ISO-8601 UTC text (`created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`) unless epoch math is a proven need.
- Use transactions for multi-step writes. Partial writes are bugs.
- Add indexes for every foreign key and common lookup path before shipping the feature.
- Do not use SQLite as a queue for long-running jobs unless a single-process worker is guaranteed.

## Data access patterns

- DB modules must be server-only. Add `import 'server-only'` in `src/db/index.ts`, `src/server/queries/*`, and mutation modules that touch secrets or DB.
- Components never execute raw SQL. Components call query functions or receive data from route-level server components.
- Validate all external input with zod before writing to DB: form submissions, route handler JSON, webhook payloads, search params used in queries.
- Prefer prepared statements. Never concatenate user input into SQL strings.
- Keep query return types explicit at module boundaries so UI code is not coupled to raw DB rows.

Example boundary:

```ts
// src/server/queries/projects.ts
import 'server-only'
import { db } from '@/db'

export type ProjectSummary = {
  id: string
  name: string
  createdAt: string
}

export function listProjectsForUser(userId: string): ProjectSummary[] {
  return db
    .prepare(`
      SELECT p.id, p.name, p.created_at AS createdAt
      FROM projects p
      JOIN project_members pm ON pm.project_id = p.id
      WHERE pm.user_id = ?
      ORDER BY p.created_at DESC
    `)
    .all(userId) as ProjectSummary[]
}
```

## Component patterns

- Default to Server Components. Add `'use client'` only for state, effects, browser APIs, or event handlers.
- Client Components should be leaves, not entire pages, unless the page is genuinely interactive.
- Pass serializable props from server to client. No DB handles, Dates, class instances, functions, or secrets.
- Keep forms progressively simple: HTML form + Server Action first; client-side form libs only when UX requires complex local state.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` for route states instead of custom global spinners everywhere.
- Co-locate one-off components with the route. Promote to `components/feature` only after reuse is real.

## Server Actions

- Server Actions must authenticate, authorize, validate, mutate inside a transaction when needed, then revalidate or redirect.
- Never trust hidden form fields for ownership. Use the session plus DB lookup.
- Return small typed errors for expected validation failures; throw for unexpected failures.
- Call `revalidatePath` or `revalidateTag` immediately after writes that affect rendered data.

Template:

```ts
'use server'

import { revalidatePath } from 'next/cache'
import { z } from 'zod'
import { requireUser } from '@/lib/auth'
import { db } from '@/db'

const schema = z.object({ name: z.string().trim().min(1).max(80) })

export async function createProject(input: unknown) {
  const user = await requireUser()
  const data = schema.parse(input)

  const projectId = crypto.randomUUID()
  db.transaction(() => {
    db.prepare('INSERT INTO projects (id, name, owner_id) VALUES (?, ?, ?)')
      .run(projectId, data.name, user.id)
    db.prepare('INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)')
      .run(projectId, user.id, 'owner')
  })()

  revalidatePath('/projects')
  return { ok: true, projectId }
}
```

## Environment and configuration

- Read environment variables in one module: `src/lib/env.ts`.
- Validate env at startup with zod. Fail fast if required values are missing.
- Never read `process.env` throughout the app; import `env` instead.
- Keep `.env.example` current and secret-free.

## Auth and authorization

- Authentication answers “who is this user?” Authorization answers “may this user touch this row?” Do both in every mutation.
- Put ownership checks next to the DB write, not only in UI routing.
- For multi-tenant data, every query must include tenant/workspace scope unless intentionally global.
- Prefer deny-by-default roles: `owner`, `admin`, `member`, `viewer`.

## Testing and verification

- For DB code, test against a temporary SQLite database with migrations applied.
- Test migrations by applying them from empty DB and by applying the new migration to the previous schema.
- For Server Actions, test validation, authorization failure, and successful mutation.
- Before marking work done, run: typecheck, lint, unit tests, and a local production build.

Expected commands:

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

If these scripts do not exist yet, add them before the feature that needs them.

## What we do not do

- No generic repository/service layers around every table. They hide SQL without adding safety in small SaaS apps.
- No premature client state managers. Server Components plus URL/search params cover most SaaS screens.
- No raw SQL in components or Server Actions when a query helper would make authorization reusable.
- No silent migration edits after merge. Create a corrective migration instead.
- No fake “temporary” `any` in request parsing. External input is where type safety matters most.
- No broad cache invalidation by habit. Revalidate the smallest path or tag that changed.
- No secrets in `NEXT_PUBLIC_*`. Anything public is visible to users.

## Done definition

A change is done only when:

1. Data ownership is enforced server-side.
2. Inputs are validated at the boundary.
3. SQLite migration and `schema.sql` are in sync if schema changed.
4. UI states cover loading, empty, success, and expected errors.
5. Typecheck, lint, tests, and build pass or the PR clearly documents an unrelated upstream failure.
