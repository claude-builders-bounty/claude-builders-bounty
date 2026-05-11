# CLAUDE.md - Next.js 15 + SQLite SaaS

You are working in a production SaaS codebase built with Next.js 15 App Router,
TypeScript, SQLite, and React Server Components. Follow these rules without
asking for clarifying questions unless a requested product behavior is genuinely
ambiguous.

## Stack And Versions

- Runtime: Node.js 22 LTS.
  Reason: Next.js 15 and modern SQLite clients work best on a current LTS
  runtime with stable Web APIs.
- Framework: Next.js 15 App Router with TypeScript in strict mode.
  Reason: App Router gives clear server/client boundaries, and strict TypeScript
  catches data-shape drift before it reaches production.
- UI: React 19 Server Components by default, Client Components only where
  browser state, effects, or event handlers are required.
  Reason: most SaaS screens are data-heavy and render faster when server-first.
- Database: SQLite through `better-sqlite3` for local/single-node deployments or
  Turso/libSQL for hosted edge-style deployments.
  Reason: both keep SQL explicit while avoiding an ORM layer that hides query
  costs in a small SaaS project.
- Validation: Zod at every external boundary.
  Reason: route handlers, forms, and webhooks receive untrusted input.
- Styling: Tailwind CSS plus small local components.
  Reason: greenfield SaaS teams move faster with shared primitives than with a
  large component framework they must fight later.
- Testing: Vitest for unit tests, Playwright for end-to-end flows that cross
  auth, billing, or persistence boundaries.
  Reason: fast local unit tests protect business logic, while browser tests
  protect revenue-critical workflows.

## Project Structure

Use this structure for a new project:

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
  api/
    webhooks/
      stripe/
        route.ts
  layout.tsx
  error.tsx
  not-found.tsx
components/
  ui/
  forms/
  layout/
db/
  client.ts
  migrations/
  queries/
features/
  accounts/
    actions.ts
    components/
    queries.ts
    schemas.ts
    types.ts
  billing/
lib/
  auth.ts
  env.ts
  result.ts
scripts/
  migrate.ts
tests/
  e2e/
  unit/
```

Rules:

- Put route-owned pages under `app/`, reusable UI under `components/`, and
  product behavior under `features/<domain>/`.
  Reason: App Router files stay thin, and domain logic remains testable without
  rendering a page.
- Keep SQL access in `db/queries/` or `features/<domain>/queries.ts`.
  Reason: query ownership is visible and reviewable.
- Keep Zod schemas next to the feature that owns the input.
  Reason: validation changes usually belong to the same domain as the UI and
  mutation logic.
- Do not create catch-all `utils.ts` files.
  Reason: generic utility files become hidden dependency hubs.

## Naming Conventions

- Components use PascalCase file names, such as `AccountSwitcher.tsx`.
  Reason: React component imports stay visually distinct from functions.
- Server Actions are named with a verb and `Action` suffix, such as
  `createWorkspaceAction`.
  Reason: the name makes mutation and server execution obvious at call sites.
- Query functions start with `get`, `list`, `find`, or `count`.
  Reason: reads are easy to scan during review.
- Mutation functions start with `create`, `update`, `delete`, `archive`, or
  `restore`.
  Reason: side effects must be explicit.
- Zod schemas end in `Schema`, inferred types end in `Input` or `Payload`.
  Reason: runtime validators and TypeScript-only types should not be confused.
- Database tables use plural snake_case names, such as `workspaces` and
  `workspace_members`.
  Reason: SQL stays conventional and easy to inspect outside TypeScript.
- TypeScript files use kebab-case except React component files.
  Reason: route files and libraries remain consistent with Next.js conventions.

## Database And Migrations

- Every schema change must be represented by a numbered SQL migration in
  `db/migrations/`, for example `0004_add_workspace_members.sql`.
  Reason: production SQLite databases need deterministic, reviewable upgrades.
- Migrations are append-only after merge.
  Reason: editing an applied migration breaks existing deployments.
- Each migration must run inside a transaction unless SQLite forbids it for the
  operation.
  Reason: partial schema changes can corrupt application assumptions.
- Include both the table/index change and any required backfill in the same
  migration when the app needs them together.
  Reason: deploys should not require manual data repair.
- Prefer explicit SQL over query builders for core SaaS data.
  Reason: SQL is the contract reviewers and operators can understand directly.
- Add indexes for foreign keys, high-cardinality filters, and ordered dashboard
  lists at the time the query is introduced.
  Reason: SaaS list pages become slow before anyone remembers to revisit them.
- Use `TEXT` ISO timestamps for application-created timestamps unless the
  project already standardizes on Unix milliseconds.
  Reason: ISO strings are readable in SQLite shells and logs.
- Never concatenate user input into SQL.
  Reason: SQLite is still vulnerable to injection; use prepared statements.

Example migration:

```sql
BEGIN;

CREATE TABLE workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workspaces_slug ON workspaces(slug);

COMMIT;
```

## Data Access Pattern

Use a small database client and feature-owned query modules.

```ts
// db/client.ts
import Database from "better-sqlite3";

export const db = new Database(process.env.DATABASE_PATH ?? "local.db");
db.pragma("foreign_keys = ON");
```

```ts
// features/workspaces/queries.ts
import { db } from "@/db/client";

export function getWorkspaceBySlug(slug: string) {
  return db
    .prepare(
      "SELECT id, name, slug, created_at AS createdAt FROM workspaces WHERE slug = ?",
    )
    .get(slug);
}
```

Rules:

- Map snake_case database columns to camelCase at the query boundary.
  Reason: UI and feature code should use normal TypeScript naming.
- Return narrow records instead of `SELECT *`.
  Reason: data exposure remains intentional and refactors are easier.
- Keep transactions inside the feature mutation that owns the workflow.
  Reason: transaction scope should match the business invariant.

## Server Actions And Route Handlers

- Use Server Actions for form submissions initiated by first-party UI.
  Reason: they keep form logic close to the route and avoid unnecessary API
  surface area.
- Use route handlers for webhooks, third-party callbacks, public API endpoints,
  and polling endpoints.
  Reason: external callers need explicit HTTP contracts.
- Validate all action and route input with Zod before reading or writing the
  database.
  Reason: TypeScript does not validate runtime requests.
- Return typed result objects instead of throwing for expected user errors.
  Reason: forms need predictable error rendering.
- Throw only for unexpected system failures.
  Reason: operational errors should reach logging and error boundaries.
- Call `revalidatePath` or `revalidateTag` after successful mutations that
  affect rendered data.
  Reason: App Router caches can otherwise show stale SaaS state.

Server Action shape:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";

const createWorkspaceSchema = z.object({
  name: z.string().min(2).max(80),
});

export async function createWorkspaceAction(formData: FormData) {
  const parsed = createWorkspaceSchema.safeParse({
    name: formData.get("name"),
  });

  if (!parsed.success) {
    return { ok: false, error: "Enter a workspace name." } as const;
  }

  // Call a feature mutation here.
  revalidatePath("/dashboard");
  return { ok: true } as const;
}
```

## Component Patterns

- Start every page as a Server Component.
  Reason: server-first pages reduce client JavaScript and simplify data loading.
- Add `"use client"` only at leaf components that need local state, effects, or
  event handlers.
  Reason: accidental client boundaries make database and server modules
  unavailable.
- Keep page files as orchestration: load data, choose layout, pass props.
  Reason: deeply nested page logic is hard to reuse and test.
- Use composition over configuration objects for UI variants.
  Reason: JSX composition is easier to inspect than large prop-driven switches.
- Put form state and optimistic UI in client leaf components, not in page files.
  Reason: pages should remain server-rendered and cache-aware.
- Keep shared UI primitives in `components/ui/` and product-specific UI in
  `features/<domain>/components/`.
  Reason: reusable design primitives and business UI evolve at different speeds.

## Environment And Configuration

- Read environment variables only through `lib/env.ts`.
  Reason: a single validated env module makes missing secrets fail fast.
- Do not read `process.env` directly in features or components.
  Reason: scattered env reads make tests and deploys unpredictable.
- Separate server-only secrets from public `NEXT_PUBLIC_` values.
  Reason: client bundles expose public variables to users.

Example:

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_PATH: z.string().default("local.db"),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

## Auth, Accounts, And Billing

- Model SaaS tenancy around `users`, `workspaces`, and `workspace_members`.
  Reason: even single-user products usually need teams later.
- Check membership on the server before every workspace read or mutation.
  Reason: client-side navigation guards are not authorization.
- Store Stripe or billing provider IDs in a dedicated billing table.
  Reason: billing identifiers are integration state, not user profile data.
- Make webhook handlers idempotent.
  Reason: billing providers retry events and may deliver them out of order.

## Dev Commands

Use these commands unless the project defines stricter equivalents:

```bash
npm run dev          # start Next.js locally
npm run build        # production build and type checks
npm run lint         # lint code
npm run test         # unit tests
npm run test:e2e     # Playwright tests
npm run db:migrate   # apply SQLite migrations
npm run db:studio    # open a database viewer when configured
```

Rules:

- Run `npm run build` before any PR that touches routing, server actions, env,
  or database code.
  Reason: Next.js catches server/client boundary errors during build.
- Run the narrowest relevant test first, then the full affected suite.
  Reason: fast feedback preserves momentum without skipping safety.
- Do not add dependencies without explaining why the standard stack cannot solve
  the problem.
  Reason: small SaaS projects are easier to maintain with fewer moving parts.

## Patterns To Follow

- Prefer boring SQL, simple TypeScript functions, and explicit feature folders.
  Reason: maintainers can review business behavior quickly.
- Keep business invariants in server-side mutations.
  Reason: UI checks improve usability but cannot enforce correctness.
- Use optimistic UI only after the server path is correct.
  Reason: optimistic flows should not hide broken persistence.
- Prefer server-side pagination for tables and audit logs.
  Reason: SaaS data grows beyond client-side arrays quickly.
- Add empty states, loading states, and permission-denied states for dashboard
  pages.
  Reason: SaaS users spend most of their time inside edge cases.

## Anti-Patterns To Avoid

- Do not put database calls in Client Components.
  Reason: database modules are server-only and secrets must not reach the client.
- Do not use `SELECT *` in product queries.
  Reason: accidental columns become accidental API surface.
- Do not edit old migrations after they are merged.
  Reason: deployed databases cannot replay rewritten history.
- Do not store money as floating-point numbers.
  Reason: billing amounts need integer cents or provider-native decimal strings.
- Do not create generic `api.ts`, `helpers.ts`, or `utils.ts` dumping grounds.
  Reason: unclear ownership slows every future change.
- Do not introduce a global state library for server data.
  Reason: App Router and server rendering already own most data freshness.
- Do not catch and ignore errors in Server Actions or webhooks.
  Reason: hidden failures become lost revenue or broken accounts.
- Do not ask before choosing standard file locations from this document.
  Reason: this template exists to make greenfield decisions consistent.

## Default Response Behavior For Claude Code

When implementing a change:

1. Locate the feature folder or create one using the structure above.
2. Add or update migrations before code that depends on new tables or columns.
3. Validate inputs with Zod at the action or route boundary.
4. Keep the first implementation server-first.
5. Add tests for business logic, migrations, or revenue-critical flows.
6. Report which commands were run and any commands that could not be run.

If a task conflicts with this template, explain the conflict and choose the
smallest change that preserves the SaaS architecture.
