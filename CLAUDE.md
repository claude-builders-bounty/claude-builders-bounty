<!-- markdownlint-disable MD013 -->

# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

You are working in a production SaaS application built with Next.js 15 App Router, React 19, TypeScript, SQLite, Drizzle ORM, Tailwind CSS, shadcn/ui, and Auth.js. Treat this file as the operating contract for Claude Code and keep every change aligned with it.

## Stack and version assumptions

- Runtime: Node.js 22 LTS or newer.
- Package manager: pnpm 10; do not switch to npm, Yarn, or Bun unless the lockfile already proves the project uses one of them.
- Framework: Next.js 15 with App Router only. Prefer Server Components and Server Actions by default.
- Language: TypeScript in strict mode. Do not introduce `any` unless a boundary cannot be typed and the reason is documented inline.
- Database: SQLite through Drizzle ORM.
  - Local/dev default: `better-sqlite3` file database at `./data/dev.db`.
  - Hosted/serverless option: Turso/libSQL using `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`.
- Auth: Auth.js with database-backed sessions unless the existing app explicitly uses JWT sessions.
- Styling: Tailwind CSS plus shadcn/ui primitives. Do not add another component framework.
- Validation: Zod for all external input, form payloads, webhooks, and environment variables.

Reason: these choices keep a small SaaS easy to run locally while staying deployable to common Node hosting and Turso.

## Canonical project structure

Use this structure for greenfield work. If the repository already has equivalent directories, follow the existing names instead of creating duplicates.

```text
app/
  (marketing)/                 Public landing and content pages
  (app)/                       Authenticated product routes
  api/                         Route handlers for webhooks and integration endpoints
  layout.tsx                   Root layout, providers, metadata
  globals.css                  Tailwind base styles only
components/
  ui/                          shadcn/ui generated primitives
  forms/                       Reusable form components
  layout/                      Navigation, shell, sidebars, headers
  marketing/                   Landing page components
  features/<feature>/          Feature-specific presentational components
server/
  actions/                     Server Actions grouped by feature
  auth/                        Auth.js config, guards, session helpers
  db/
    index.ts                   Database client factory
    schema.ts                  Drizzle table definitions
    migrations/                Generated SQL migrations
    queries/                   Read-model functions
  services/                    Business workflows that coordinate DB + external APIs
  validators/                  Zod schemas shared by actions and route handlers
lib/
  env.ts                       Typed environment parser
  utils.ts                     Pure utilities only; no database or network access
emails/                        Transactional email templates
scripts/                       One-off maintenance scripts, seed scripts
tests/
  unit/                        Pure unit tests
  integration/                 DB-backed tests using temporary SQLite files
  e2e/                         Playwright flows when present
```

Reasons:

- `app/` stays focused on routing and rendering.
- `server/` marks code that must never be imported by Client Components.
- `components/features/<feature>/` prevents a flat component dump.
- `server/db/queries/` centralizes reads so authorization and filtering are reviewable.

## Development commands

Use the existing scripts if they differ, but greenfield projects should expose these commands:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:integration
pnpm db:generate
pnpm db:migrate
pnpm db:studio
pnpm build
```

Expected script meanings:

```json
{
  "dev": "next dev",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:integration": "vitest run tests/integration",
  "db:generate": "drizzle-kit generate",
  "db:migrate": "drizzle-kit migrate",
  "db:studio": "drizzle-kit studio",
  "build": "next build"
}
```

Before opening a PR, run at minimum:

```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

If database schema, queries, or Server Actions changed, also run:

```bash
pnpm db:generate && pnpm test:integration
```

## Environment variables

All environment variables must be parsed in `lib/env.ts` with Zod. Never read `process.env` directly outside that file except in Next.js config files.

Required baseline:

```ts
DATABASE_URL="file:./data/dev.db"
AUTH_SECRET="development-only-change-me"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

Turso option:

```ts
TURSO_DATABASE_URL="libsql://..."
TURSO_AUTH_TOKEN="..."
```

Rules:

- Prefix only browser-safe values with `NEXT_PUBLIC_`.
- Do not log secrets, tokens, cookies, or raw OAuth payloads.
- Add new variables to `.env.example` in the same PR as the code that uses them.

Reason: typed env parsing fails fast during boot and prevents accidental secret exposure.

## Database and migration rules

### Schema ownership

- Define all tables in `server/db/schema.ts` or split by domain under `server/db/schema/*.ts` and re-export from `schema.ts`.
- Use singular table object names and plural SQL table names:
  - `user` object -> `users` table
  - `subscription` object -> `subscriptions` table
- Every business table must include:
  - `id` as a stable text ID generated in application code.
  - `createdAt` and `updatedAt` integer timestamps or ISO text timestamps, consistently across the app.
- Use explicit indexes for foreign keys, lookup slugs, tenant IDs, and status fields used in dashboards.

### Migration workflow

- Never hand-edit generated migrations unless fixing a generator bug. If edited, explain why in the PR body.
- Never change an already-applied migration. Create a new migration instead.
- Migrations must be safe for existing production data:
  - Add nullable columns first.
  - Backfill in a script or follow-up migration.
  - Only then add `not null` or stricter constraints when SQLite supports it safely.
- Do not use destructive migration steps (`DROP TABLE`, `DROP COLUMN`, mass deletes) without a clearly named backup/export step.

### Query conventions

- Put reusable reads in `server/db/queries/<feature>.ts`.
- Put writes behind Server Actions or service functions, not inside Client Components.
- Always include tenant/user ownership filters in queries for authenticated data.
- Use transactions for multi-row writes that must succeed or fail together.
- Return plain serializable objects from query functions, not ORM internals.

Reason: SQLite is reliable for SaaS workloads, but schema changes and tenant filtering must be boring, explicit, and reviewable.

## App Router conventions

- Prefer Server Components. Add `"use client"` only when state, effects, browser APIs, or event handlers are required.
- Fetch database data in Server Components or query helpers; do not fetch internal API routes from server-side code.
- Use Route Handlers in `app/api/**/route.ts` only for external HTTP boundaries such as webhooks, public API endpoints, or third-party callbacks.
- Keep `page.tsx` thin:
  - parse `searchParams`
  - call query helpers
  - compose feature components
- Put mutations in `server/actions/<feature>.ts` with `"use server"` at the file top.
- After successful mutations, call `revalidatePath` or `revalidateTag` for affected pages.
- Use `notFound()` for missing resources and `redirect()` for access flows.

Reason: Server Components reduce client JavaScript and Server Actions keep mutations close to authorization and validation.

## Server Action pattern

Every Server Action must follow this order:

1. Authenticate and authorize.
2. Parse and validate input with Zod.
3. Run the smallest necessary transaction or service call.
4. Revalidate affected paths/tags.
5. Return a typed success/error result safe for the client.

Example shape:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireUser } from "@/server/auth/guards";
import { db } from "@/server/db";

const updateProjectSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1).max(80),
});

export async function updateProjectAction(input: unknown) {
  const user = await requireUser();
  const data = updateProjectSchema.parse(input);

  await db.transaction(async (tx) => {
    // Include user/tenant ownership checks in the write predicate.
  });

  revalidatePath("/app/projects");
  return { ok: true as const };
}
```

Do not return stack traces, database errors, or provider responses to the browser.

## Component patterns

- Server Components own data loading.
- Client Components own interaction only.
- Keep shadcn/ui files in `components/ui/` close to generated upstream shape; wrap them elsewhere instead of heavily modifying them.
- Name components by domain intent, not visual placement:
  - Good: `ProjectBillingCard`, `InviteMemberDialog`
  - Avoid: `RightBox`, `Form2`, `NewModal`
- Forms should use Zod schemas shared with the Server Action where practical.
- Empty, loading, and error states are part of the feature, not afterthoughts.
- Accessibility is required: label inputs, use semantic buttons/links, preserve focus behavior in dialogs.

Reason: this split makes hydration boundaries obvious and keeps reusable UI from accumulating business logic.

## Authentication and authorization

- Use `requireUser()` for authenticated routes/actions and `getOptionalUser()` only where anonymous access is valid.
- Authorization must happen on the server for every read and write involving private data.
- Never trust client-provided `userId`, `organizationId`, role, price, quota, or plan values.
- Use role/permission helpers instead of scattering string comparisons through pages.
- For multi-tenant SaaS, every tenant-scoped query must include both resource ID and tenant membership constraints.

Reason: UI checks are helpful for experience but do not protect data.

## API route and webhook rules

- Validate method, headers, body size, and payload schema.
- For webhooks, verify the provider signature before parsing business data.
- Make webhook handlers idempotent using provider event IDs.
- Return minimal error responses; log structured server-side context without secrets.
- Keep route handlers thin by delegating business logic to `server/services/`.

## Testing expectations

Use Vitest for unit and integration tests. Use Playwright only for browser flows that cannot be covered cheaper.

Test priorities:

1. Zod validators for edge cases and invalid input.
2. Query helpers with a temporary SQLite database.
3. Server Actions for authorization, validation, and revalidation behavior.
4. Critical billing/auth/webhook service flows.
5. One happy-path smoke test for the main app shell if Playwright exists.

Integration test rules:

- Each test file owns a temporary SQLite database.
- Do not depend on a developer's local `data/dev.db`.
- Seed only the rows needed for the test.
- Assert authorization boundaries, not just successful paths.

## Naming conventions

- Files and folders: kebab-case except Next.js reserved files (`page.tsx`, `layout.tsx`, `route.ts`).
- React components: PascalCase.
- Server Actions: verb-noun with `Action` suffix, e.g. `createProjectAction`.
- Query helpers: `getProjectById`, `listProjectsForUser`, `countActiveSeats`.
- Zod schemas: noun plus `Schema`, e.g. `createProjectSchema`.
- Drizzle table objects: singular nouns, e.g. `project`, `subscription`.
- Database columns: camelCase in TypeScript; generated SQL may use snake_case only if the project already does.

## Pull request checklist

Before submitting:

- [ ] The change follows the existing package manager and lockfile.
- [ ] `pnpm lint` passes.
- [ ] `pnpm typecheck` passes.
- [ ] `pnpm test` passes.
- [ ] `pnpm build` passes for app or framework changes.
- [ ] Migrations are generated and included when schema changes.
- [ ] `.env.example` and docs are updated for new configuration.
- [ ] New or changed private data paths include authorization tests.
- [ ] UI changes include loading, empty, and error states where relevant.

## Anti-patterns to avoid

- Adding `"use client"` to a layout or high-level page just to fix a child interaction. Instead, isolate a small Client Component.
- Fetching `/api/*` from Server Components. Call the underlying server function directly.
- Reading `process.env` throughout the codebase. Use the typed env module.
- Building SQL strings with interpolation. Use Drizzle query builders or parameterized SQL.
- Applying migrations by editing production data manually without a script.
- Hiding TypeScript errors with `as any`, `// @ts-ignore`, or broad casts.
- Creating generic `utils` that perform database, auth, or network work.
- Trusting hidden form fields for ownership, price, quota, role, or plan decisions.
- Returning raw provider payloads or stack traces to the client.
- Installing large dependencies for a problem already solved by the stack.

## When uncertain

- Preserve the existing architecture over introducing a new pattern.
- Choose explicit, typed, boring code over clever abstractions.
- Ask for clarification in the PR when a product decision is ambiguous, but still keep the code safe and reversible.
- Prefer a small complete slice with tests over a broad partial rewrite.
