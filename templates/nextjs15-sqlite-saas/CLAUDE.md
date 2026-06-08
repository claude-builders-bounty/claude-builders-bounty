# CLAUDE.md

This file is the operating manual for Claude Code in this repository. Treat it as project policy unless a human explicitly overrides it.

## Stack And Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode. Do not introduce `any` unless the boundary is genuinely untyped and the type is narrowed immediately.
- SQLite as the source of truth:
  - Use `better-sqlite3` for local, embedded, synchronous access.
  - Use Turso/libSQL only when the deployment target requires remote SQLite.
- Server-first SaaS architecture:
  - Server Components for data reads.
  - Server Actions or Route Handlers for writes and webhooks.
  - Client Components only for browser state, forms that need interactivity, and UI primitives.
- Authentication, billing, and email providers are replaceable adapters. Keep provider-specific code at the edge of the app.

Reason: this stack is fast when data access stays close to the server boundary. Most bugs in Next.js SaaS apps come from mixing browser state, database writes, and provider SDKs in the same component.

## Non-Negotiable Working Rules

1. Read the relevant files before editing.
2. Prefer a small, complete vertical change over a broad refactor.
3. Keep database changes explicit, reversible where possible, and covered by tests.
4. Never expose secrets to Client Components, logs, browser bundles, screenshots, or generated docs.
5. Do not silently change public routes, billing behavior, auth rules, or migration history.
6. If a requirement is ambiguous, make the safest reasonable assumption, state it in the PR, and keep the change easy to revise.

Reason: SaaS projects fail more often from accidental contract changes than from missing abstractions.

## Project Structure

Use this structure for greenfield work:

```txt
app/
  (marketing)/
    page.tsx
    pricing/page.tsx
  (app)/
    dashboard/page.tsx
    settings/page.tsx
  api/
    webhooks/
      stripe/route.ts
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  layout/
db/
  client.ts
  migrations/
  queries/
  schema.ts
features/
  auth/
  billing/
  onboarding/
  organizations/
  users/
lib/
  config/
  errors/
  server/
  validation/
tests/
  fixtures/
  integration/
  unit/
```

Rules:

- `app/` owns routing, metadata, layouts, loading states, and route-level composition.
- `features/<domain>/` owns domain workflows and UI that is not generic.
- `components/ui/` contains reusable primitives only. Do not put business logic there.
- `db/queries/` contains named database functions. Do not scatter SQL across components.
- `lib/server/` is server-only infrastructure. Add `import 'server-only'` to modules that must never enter a client bundle.
- `lib/config/` parses environment variables once and exports typed config.

Reason: route files should be easy to scan. Domain complexity belongs in features and database query modules, not in page components.

## Naming Conventions

- Files:
  - Components: `PascalCase.tsx`
  - Hooks: `useThing.ts`
  - Server actions: `actions.ts`
  - Database queries: `thing.queries.ts`
  - Validation schemas: `thing.schema.ts`
  - Tests: `thing.test.ts` or `thing.spec.ts`
- Components:
  - `ThingPage` for route-level composition.
  - `ThingForm` for interactive forms.
  - `ThingTable` for tabular data.
  - `ThingEmptyState` for empty states.
- Database functions:
  - `getThingById`
  - `listThingsForUser`
  - `createThing`
  - `updateThing`
  - `deleteThing`
- Booleans:
  - Use `is`, `has`, `can`, or `should`.
  - Example: `canManageBilling`, not `billingAccess`.

Reason: predictable names reduce the amount of context Claude and humans need to hold while changing the app.

## Dev Commands

Prefer these commands unless the repository defines different scripts:

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm run test
npm run test:integration
npm run db:migrate
npm run db:rollback
npm run db:studio
```

Before opening a PR, run the smallest useful checks:

```bash
npm run typecheck
npm run lint
npm run test
```

Run `npm run build` when touching routes, layouts, server/client boundaries, metadata, or environment config.

Reason: typecheck catches contract mistakes, lint catches framework boundary mistakes, tests catch behavior, and build catches Next.js runtime assumptions.

## Environment And Config

- Keep `.env.example` current.
- Read environment variables only through `lib/config/env.ts`.
- Validate env with a schema before exporting values.
- Use separate variables for public and secret config:
  - `NEXT_PUBLIC_*` only for values safe to ship to the browser.
  - Everything else stays server-only.
- Do not add fallback dummy secrets in production code.

Example:

```ts
import 'server-only'
import { z } from 'zod'

const EnvSchema = z.object({
  DATABASE_URL: z.string().min(1),
  SESSION_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().optional()
})

export const env = EnvSchema.parse(process.env)
```

Reason: typed config fails early and prevents secrets from leaking into client bundles.

## SQLite And Migration Conventions

### Database Access

- Open the SQLite connection in `db/client.ts`.
- Export a single database handle or factory. Do not create ad hoc connections.
- For `better-sqlite3`, enable WAL mode and foreign keys during initialization.
- For Turso/libSQL, keep the client async and isolate differences behind query functions.

Example:

```ts
import 'server-only'
import Database from 'better-sqlite3'

export const db = new Database(process.env.DATABASE_URL ?? 'local.db')

db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')
```

Reason: WAL improves local concurrency; foreign keys prevent impossible SaaS states such as orphaned memberships.

### Schema Rules

- Every table has:
  - `id TEXT PRIMARY KEY`
  - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
  - `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
- Use ISO timestamp strings unless the project already standardizes on Unix milliseconds.
- Use `TEXT` for IDs, enums, and JSON blobs.
- Use `INTEGER` for booleans with `0` and `1`.
- Use foreign keys with explicit `ON DELETE` behavior.
- Add indexes for every foreign key and every common list filter.
- Do not use floating point for money. Store cents or provider integer amounts.

Reason: SQLite is permissive. Strong conventions prevent subtle data bugs.

### Migration Rules

- Migrations live in `db/migrations/` and are numbered monotonically:

```txt
0001_create_users.sql
0002_create_organizations.sql
0003_add_billing_customer_id.sql
```

- Never edit a migration that has shipped. Add a new migration.
- Each migration must be safe to run once and recorded in a migrations table.
- Prefer additive migrations:
  - Add nullable column.
  - Backfill.
  - Add constraint or not-null check in a later migration when needed.
- Destructive migrations require a comment explaining data loss and a backup plan.
- Keep seed data separate from migrations.

Reason: production databases are historical artifacts. Rewriting history breaks deploys and local reproducibility.

### Query Rules

- Put SQL in `db/queries/*.queries.ts`.
- Use prepared statements for `better-sqlite3`.
- Validate untrusted input before calling query functions.
- Return plain objects, not database driver rows with unknown shapes.
- Keep transactions explicit for multi-step writes.

Example:

```ts
export function createOrganization(input: CreateOrganizationInput) {
  return db
    .prepare(
      `INSERT INTO organizations (id, name, owner_id)
       VALUES (@id, @name, @ownerId)
       RETURNING id, name, owner_id AS ownerId`
    )
    .get(input)
}
```

Reason: central query modules make permissions, transactions, and tests much easier to reason about.

## App Router Patterns

- Fetch data in Server Components whenever possible.
- Keep route files thin:
  - parse route params
  - call a feature-level loader
  - render feature components
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` deliberately.
- Use `generateMetadata` for pages with dynamic SEO needs.
- Use `revalidatePath` or `revalidateTag` after mutations that affect cached reads.
- Do not call server actions from random utility modules. Keep them near the route or feature that owns the workflow.

Reason: App Router is most maintainable when data ownership is visible at route boundaries.

## Component Patterns

### Server Components

- Default to Server Components.
- Server Components may import query functions and server-only modules.
- Server Components must not use hooks, browser APIs, event handlers, or local state.

### Client Components

Add `'use client'` only when the component needs:

- `useState`, `useEffect`, or browser APIs.
- Event handlers.
- Client-side form state.
- Focus management, animations, or interactive UI primitives.

Keep Client Components small and pass serializable props from Server Components.

Reason: every Client Component increases bundle size and moves logic away from the database boundary.

### Forms

- Use server actions for simple mutations.
- Use a validation schema for all writes.
- Return typed action states for user-facing errors.
- Disable submit buttons while pending.
- Show optimistic UI only when rollback is straightforward.

Reason: forms are where auth, validation, and persistence meet. They need explicit state.

## Authentication And Authorization

- Authentication proves who the user is.
- Authorization decides what the user can do.
- Do not mix them.
- Every write must check authorization on the server.
- Do not trust organization IDs, role IDs, prices, or user IDs from the browser.
- Centralize permission checks in feature modules such as `features/organizations/permissions.ts`.

Reason: hiding UI controls is not access control. Server-side permission checks are mandatory.

## Billing Rules

- Treat billing provider webhooks as the source of truth for subscription state.
- Verify webhook signatures before reading event bodies.
- Store provider IDs and normalized local state.
- Never grant paid access only because a checkout session was created.
- Money uses integers in the smallest currency unit.
- Billing changes should be idempotent.

Reason: checkout redirects are user-controlled; signed webhooks are provider-controlled.

## Error Handling

- Use typed domain errors for expected failures.
- Convert domain errors to user-facing messages at the UI boundary.
- Let unexpected errors reach `error.tsx` or observability.
- Do not log secrets, full tokens, cookies, or raw webhook payloads.
- Include enough context to debug: user ID, organization ID, route, and operation.

Reason: useful logs help production support; excessive logs create privacy and security risk.

## Testing Policy

Write tests at the level where the risk lives:

- Unit tests for pure helpers, validation, permissions, and query mappers.
- Integration tests for database queries, migrations, server actions, and webhooks.
- Route or component tests for critical user flows.

SQLite test rules:

- Use a temporary database per test file or transaction rollback per test.
- Run migrations before integration tests.
- Test foreign key behavior and important indexes when schema changes.
- Include one regression test for every fixed bug.

Reason: tests should protect behavior and data integrity, not implementation details.

## Security Checklist

Before shipping auth, billing, database, upload, or webhook changes:

- Server-side authorization exists for every write.
- Inputs are validated before database calls.
- Secrets stay out of Client Components.
- Webhook signatures are verified.
- SQL uses prepared statements or parameterized queries.
- File uploads validate type, size, and ownership.
- Redirect targets are relative or allowlisted.
- Rate limits exist for expensive or abuse-prone endpoints.

Reason: SaaS security bugs usually appear at integration boundaries.

## Performance Rules

- Avoid N+1 query patterns in pages and lists.
- Add indexes when adding list filters or joins.
- Paginate unbounded lists.
- Keep Client Component props small and serializable.
- Do not import large provider SDKs into shared UI modules.
- Use `Suspense` for slow independent panels.

Reason: SQLite is fast, but unbounded reads and oversized client bundles are not.

## What We Do Not Do

- Do not put database calls in Client Components.
  - Reason: it leaks server concerns and often secrets.
- Do not create a generic `utils.ts` dumping ground.
  - Reason: ownership disappears and dependencies sprawl.
- Do not edit old migrations.
  - Reason: existing databases cannot replay changed history.
- Do not store money as floats.
  - Reason: rounding errors become billing bugs.
- Do not add `use client` to a whole page to fix one interactive widget.
  - Reason: it ships unnecessary JavaScript and weakens server boundaries.
- Do not catch errors just to return `null`.
  - Reason: silent failures make production incidents harder to diagnose.
- Do not rely on middleware alone for authorization.
  - Reason: middleware is coarse-grained; writes still need resource-level checks.
- Do not introduce new dependencies without checking bundle impact, maintenance status, and whether the platform already solves the problem.
  - Reason: dependencies become long-term operational surface area.

## PR Expectations

Every PR should explain:

- What changed.
- Why this approach was chosen.
- What commands were run.
- Whether migrations were added.
- Any production or rollout risk.

For database changes, include:

- Migration filename.
- Rollback or mitigation plan.
- New indexes and why they are needed.
- Tests covering the migration or affected query.

Reason: reviewers need operational context, not just a diff.

## Claude Behavior In This Repository

When working here:

- Start by identifying the route, feature, and database tables involved.
- State assumptions briefly when they affect behavior.
- Prefer existing patterns over new abstractions.
- Keep generated code idiomatic TypeScript.
- After edits, run the narrowest relevant checks first, then broader checks if needed.
- If you cannot run a check, say exactly why and what should be run next.

When asked to implement a feature:

1. Inspect routes and feature modules.
2. Inspect schema and migrations.
3. Add or update validation.
4. Implement server-side behavior.
5. Add minimal UI.
6. Add focused tests.
7. Run checks.

Reason: this order prevents polished UI from hiding broken data or permissions.

