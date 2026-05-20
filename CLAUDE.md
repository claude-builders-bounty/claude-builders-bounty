# Next.js 15 App Router + SQLite SaaS Instructions

Use this file as the default project memory for a greenfield SaaS built with
Next.js 15 App Router, TypeScript, SQLite, and server-first React patterns. The
goal is a small, durable application that can move quickly without drifting into
framework or database habits that make SQLite painful later.

## Stack And Versions

- Next.js 15 with the App Router under `app/`.
  Reason: App Router gives server components, route handlers, layouts, metadata,
  streaming, and server functions without a parallel `pages/` tree.
- React 19 through the version bundled by Next.js 15.
  Reason: do not pin React separately unless a dependency requires it.
- TypeScript with `strict: true`.
  Reason: SaaS bugs usually come from unclear data shapes, nullable session
  state, and unchecked request payloads.
- SQLite through `better-sqlite3` for single-node deployments or Turso/libSQL
  for remote and replicated deployments.
  Reason: keep the SQL shape portable and avoid an ORM migration lock-in.
- Drizzle or plain SQL migrations are allowed; Prisma is not the default.
  Reason: SQLite features, indexes, transactions, and generated columns should
  remain visible in review.
- Tailwind CSS is allowed for styling, but UI behavior must not depend on class
  name string construction that hides state.

## Default Dev Commands

Use one package manager per project. Prefer `pnpm`; use `npm` only if the lock
file is already `package-lock.json`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
pnpm db:studio
pnpm build
```

Expected scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx src/db/migrate.ts",
    "db:studio": "drizzle-kit studio"
  }
}
```

If a command is missing, add the script instead of telling the user to run a
one-off command. Reason: agents repeat documented commands reliably.

## Folder Structure

Create this structure first and keep new code inside the nearest existing
boundary:

```text
app/
  (marketing)/
    page.tsx
  (app)/
    layout.tsx
    dashboard/page.tsx
  api/
    webhooks/stripe/route.ts
  actions/
    billing.ts
    profile.ts
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  layout/
src/
  auth/
    session.ts
    permissions.ts
  db/
    client.ts
    schema.ts
    migrate.ts
    queries/
  env.ts
  lib/
    dates.ts
    ids.ts
    result.ts
  services/
    billing/
    mail/
tests/
  unit/
  integration/
drizzle/
  migrations/
```

Rules:

- `app/` owns routes, route handlers, layouts, loading states, and server
  actions that are route-specific.
  Reason: route behavior should be visible beside the route.
- `src/services/` owns business workflows such as billing, invitations, and
  email.
  Reason: services are reusable from route handlers, server actions, and jobs.
- `src/db/queries/` owns reusable database reads and writes.
  Reason: SQL belongs in a reviewable database layer, not scattered through UI.
- `components/ui/` contains generic components only.
  Reason: domain logic in generic UI turns every change into a cross-app risk.
- Keep tests beside the behavior type: pure logic in `tests/unit`, database or
  route behavior in `tests/integration`.

## Naming Conventions

- Files and folders use kebab-case: `billing-summary.tsx`.
  Reason: route paths and imports stay readable on case-sensitive systems.
- React components use PascalCase exports: `BillingSummary`.
  Reason: component names are easy to distinguish in stack traces.
- Server actions end with `Action`: `updateProfileAction`.
  Reason: callers can see that the function crosses a network boundary.
- Database query functions start with the operation: `getUserById`,
  `insertSubscription`, `updateWorkspaceName`.
  Reason: query intent is visible at call sites.
- Zod schemas end with `Schema`: `updateProfileSchema`.
  Reason: validation objects are not confused with inferred TypeScript types.
- Inferred types end with `Input`, `Row`, `View`, or `DTO`.
  Reason: each suffix describes where the data is safe to use.

## Environment Rules

All environment variables are declared in `src/env.ts` and validated at startup.
Never read `process.env` directly outside that file.

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_").optional()
});

export const env = envSchema.parse(process.env);
```

Reasons:

- Missing secrets should fail on boot, not during the first checkout.
- Public variables must be intentionally prefixed with `NEXT_PUBLIC_`.
- Tests can override one module instead of patching global process state.

## SQLite And Migration Conventions

SQLite is the source of truth. Treat migrations as product code.

- Every schema change gets a numbered migration committed under
  `drizzle/migrations/`.
  Reason: production databases must advance through reviewed steps.
- Migrations are append-only after review.
  Reason: editing shipped migrations breaks existing databases.
- Prefer `TEXT` identifiers generated by the app with stable prefixes:
  `usr_`, `org_`, `sub_`, `evt_`.
  Reason: IDs become self-describing in logs and support tickets.
- Store timestamps as ISO-8601 UTC text.
  Reason: ordering stays lexical and values remain portable across SQLite
  adapters.
- Use `INTEGER NOT NULL DEFAULT 0` for booleans.
  Reason: SQLite has no separate boolean storage class.
- Add foreign keys and enable enforcement when opening the database.
  Reason: SQLite requires `PRAGMA foreign_keys = ON` per connection.
- Add indexes for every foreign key and for the left side of every common
  dashboard filter.
  Reason: SaaS pages degrade first on tenant-scoped list queries.
- Use transactions for any operation that writes more than one table.
  Reason: billing, invites, and workspace updates must not partially succeed.
- Do not use `SELECT *` in app queries.
  Reason: adding a column must not silently change payload size or leak data.

Example database client boundary:

```ts
import Database from "better-sqlite3";
import { env } from "@/src/env";

export const db = new Database(env.DATABASE_URL);
db.pragma("foreign_keys = ON");
db.pragma("journal_mode = WAL");
```

## Query Rules

- Validate input before it reaches SQL.
  Reason: SQL parameterization prevents injection, but validation prevents bad
  business states.
- Always scope tenant data by `workspace_id`.
  Reason: almost every SaaS data leak starts with a missing tenant predicate.
- Return plain objects from query helpers.
  Reason: server components and actions should not depend on database driver
  row classes.
- Write focused query helpers instead of generic repositories.
  Reason: SQLite performance comes from knowing the exact SQL being run.

Example:

```ts
export function getWorkspaceProjects(workspaceId: string) {
  return db
    .prepare(
      `select id, name, status, updated_at
       from projects
       where workspace_id = ?
       order by updated_at desc
       limit 100`
    )
    .all(workspaceId);
}
```

## App Router Patterns

- Default to server components.
  Reason: data fetching stays close to the route and reduces client JavaScript.
- Add `"use client"` only for event handlers, browser APIs, local interactive
  state, or client-only libraries.
  Reason: client boundaries are bundle boundaries.
- Keep route `page.tsx` files as orchestrators.
  Reason: pages should load data and compose components, not contain all UI.
- Use route groups for product areas: `(marketing)`, `(auth)`, `(app)`.
  Reason: layouts and auth rules differ by area without changing URLs.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` where the route needs its
  own state.
  Reason: user-facing fallback behavior should be route-specific.
- Use route handlers for webhooks and third-party callbacks.
  Reason: request signature handling belongs at the HTTP edge.

## Server Actions And Mutations

- Put route-specific actions in `app/actions/` or beside the route.
  Reason: actions are part of the route contract.
- Every action returns a typed result instead of throwing for expected failures.
  Reason: forms need validation messages, not generic error boundaries.
- Every action validates input with Zod.
  Reason: browser forms and programmatic callers are both untrusted.
- Every action checks session and authorization inside the action.
  Reason: client-side checks are only UX, not security.
- Revalidate the smallest affected path or tag.
  Reason: broad revalidation hides stale-data bugs and wastes work.

Example result type:

```ts
export type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; fieldErrors?: Record<string, string[]> };
```

## Component Patterns

- Keep components small and named after the domain surface:
  `WorkspaceSwitcher`, `InvoiceTable`, `InviteMemberForm`.
  Reason: names should help reviewers navigate behavior quickly.
- Split data loading from display.
  Reason: display components become reusable in loading, empty, and test states.
- Do not pass raw database rows into client components.
  Reason: client props are a serialization and privacy boundary.
- Forms use server actions for mutations unless the interaction needs optimistic
  client state.
  Reason: most SaaS writes are simpler and safer when they stay server-owned.
- UI components accept explicit props, not entire domain objects.
  Reason: this avoids accidental exposure of hidden fields.

## Authentication And Authorization

- Centralize session lookup in `src/auth/session.ts`.
- Centralize permission checks in `src/auth/permissions.ts`.
- Check authorization in server actions, route handlers, and query helpers that
  touch tenant data.
- Do not trust workspace IDs supplied by the client without checking membership.

Reason: route middleware can redirect users, but it cannot prove that a specific
record belongs to the current principal.

## Error Handling

- Use typed action results for expected validation and permission errors.
- Use `notFound()` when a missing record should look identical to an
  unauthorized record.
- Log unexpected errors on the server with request context, never secrets.
- Do not expose raw database errors to the client.

Reason: SaaS users need actionable messages, while attackers should not receive
schema or tenant details.

## Testing Rules

- Unit test pure utilities and validation schemas.
- Integration test database queries against a temporary SQLite database.
- Test server actions with mocked sessions and real validation.
- Add at least one test for every migration that changes constraints or
  indexes.
- Include one smoke test note for new project-memory files explaining how the
  instructions were checked.

Reason: SQLite apps often pass UI checks while failing at migration or
transaction boundaries.

## Patterns To Follow

- Server-first pages with thin client islands.
  Reason: dashboards load faster and expose less data to the browser.
- Explicit SQL with named query helpers.
  Reason: review is faster when data access is concrete.
- Small actions that validate, authorize, mutate, and revalidate.
  Reason: each mutation has one auditable path.
- Tenant-first data model: every user-owned resource has `workspace_id`.
  Reason: multi-tenant safety is easier to enforce from the schema up.
- Append-only migrations.
  Reason: production data needs a linear history.

## Anti-Patterns To Avoid

- Do not create a `pages/` directory.
  Reason: two routers create duplicate conventions and confusing data flow.
- Do not put database calls inside client components.
  Reason: database access belongs on the server and should never be bundled.
- Do not use generic `any` or unvalidated `FormData`.
  Reason: bad input should be rejected before it reaches business logic.
- Do not use `SELECT *`.
  Reason: response shape must be intentional.
- Do not create a catch-all repository abstraction.
  Reason: it hides SQL, transactions, and tenant filters.
- Do not store dates as local time strings.
  Reason: billing and audit logs require unambiguous UTC values.
- Do not read secrets in components.
  Reason: component boundaries can move between server and client over time.
- Do not add a custom Next.js server.
  Reason: the built-in router, route handlers, and deployment adapters cover
  the normal SaaS surface.
- Do not handle Stripe webhooks in a server action.
  Reason: webhooks need raw request bodies and signature verification.
- Do not use global mutable state for the current user or workspace.
  Reason: server rendering can interleave requests.

## When Asked To Build A Feature

Follow this order:

1. Identify route, data model, and permission boundary.
2. Add or update the migration.
3. Add query helpers with tenant scoping.
4. Add validation schemas and server action or route handler.
5. Compose server components and minimal client components.
6. Add unit or integration tests at the changed boundary.
7. Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build`.

If details are missing, make the smallest production-safe assumption and note it
in the PR. Do not pause for generic questions when the schema, route, and user
flow are already implied by the request.
