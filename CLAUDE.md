# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Use this as the default project memory for a production SaaS built with **Next.js 15 App Router**, **TypeScript**, **Tailwind**, and **SQLite** through either `better-sqlite3` for single-region deployments or **Turso/libSQL** for edge-friendly hosted SQLite.

## Stack and runtime

- Next.js 15 with the `app/` router only; do not add a legacy `pages/` tree.
- TypeScript strict mode. Treat `unknown` as a feature, not an annoyance.
- React Server Components by default; add `'use client'` only for interactivity, browser APIs, or client-side state.
- SQLite is the source of truth. Use `better-sqlite3` for local/server Node runtimes, or Turso/libSQL when the deployment target needs a remote database.
- Authentication, billing, email, and background jobs must be isolated behind service modules so the app can swap providers without rewriting route handlers.

Reason: this stack is fastest when server code stays boring, synchronous boundaries are obvious, and UI state does not leak into data mutation code.

## Expected folder structure

```text
app/
  (marketing)/             # public pages, no auth assumptions
  (app)/                   # authenticated product shell
  api/                     # route handlers, webhooks, integration callbacks
  layout.tsx
  page.tsx
components/
  ui/                      # small reusable primitives
  forms/                   # form components that call server actions
  charts/                  # browser-only visualizations
db/
  schema.sql               # complete canonical schema for new databases
  migrations/              # numbered, immutable SQL migrations
  queries/                 # typed query helpers; no raw SQL in components
  seed.ts                  # deterministic local/dev seed data
lib/
  auth/                    # session, currentUser(), permissions
  billing/                 # provider adapter + entitlement checks
  email/                   # transactional email templates and sender
  env.ts                   # validated environment variables
  errors.ts                # domain errors and UI-safe messages
  ids.ts                   # ID generation helpers
  logger.ts                # structured logging wrapper
server/
  actions/                 # server actions grouped by domain
  services/                # business operations; transactions live here
  jobs/                    # scheduled/background jobs
tests/
  unit/
  integration/
  fixtures/
```

Do not create catch-all folders like `utils/` or `helpers/`. If a name does not explain the domain boundary, it is too vague.

## Commands

Prefer `pnpm`. If the repo already uses npm/yarn/bun, follow the existing lockfile instead.

```bash
pnpm dev              # local Next.js app
pnpm lint             # eslint + Next lint rules
pnpm typecheck        # tsc --noEmit
pnpm test             # unit tests
pnpm test:integration # DB-backed tests
pnpm db:migrate       # apply pending SQL migrations
pnpm db:seed          # seed local database
pnpm build            # production build gate
```

Before claiming a task is done, run at minimum: `pnpm lint && pnpm typecheck && pnpm test`. If schema or query code changed, also run migrations against a disposable SQLite database.

## Naming conventions

- Components: `PascalCase.tsx`, e.g. `InvoiceStatusBadge.tsx`.
- Server actions: verb-first files, e.g. `createWorkspace.ts`, `inviteMember.ts`.
- Query helpers: noun or read intent, e.g. `workspaceQueries.ts`, `listInvoicesForWorkspace()`.
- Mutating service functions: explicit verbs, e.g. `provisionWorkspace()`, `cancelSubscription()`.
- Database tables: singular snake_case, e.g. `workspace`, `workspace_member`, `billing_event`.
- IDs: opaque text IDs with prefixes where useful, e.g. `usr_`, `org_`, `inv_`. Do not expose autoincrement integers in URLs.
- Environment variables: `SCREAMING_SNAKE_CASE`, read only through `lib/env.ts`.

Reason: predictable names let Claude Code jump to the right layer without asking whether a function is UI, data access, or business logic.

## Database and migration rules

1. `db/schema.sql` describes the latest full schema for bootstrapping a new database.
2. `db/migrations/NNNN_description.sql` files are append-only after merge.
3. A migration must be safe to run exactly once and must not depend on local seed data.
4. Every table must have `created_at` and, when mutable, `updated_at`.
5. Use `CHECK` constraints for domain enums instead of trusting TypeScript alone.
6. Enable foreign keys on every SQLite connection: `PRAGMA foreign_keys = ON`.
7. Wrap multi-table writes in an explicit transaction in `server/services/*`.
8. Keep raw SQL inside `db/queries` or migrations. Components and route handlers must not embed SQL.
9. Do not silently catch constraint errors. Convert them to typed domain errors in the service layer.
10. Never generate migrations by editing production data manually; write the SQL and a rollback note in the PR description.

Preferred query pattern:

```ts
// db/queries/workspaceQueries.ts
export async function getWorkspaceBySlug(slug: string) {
  return db.prepare(`
    SELECT id, name, slug, plan, created_at
    FROM workspace
    WHERE slug = ?
  `).get(slug);
}
```

Reason: SQLite rewards simple, explicit SQL. Hiding it behind a generic abstraction usually makes migrations and performance worse.

## App Router patterns

- Fetch data in Server Components when rendering read-only pages.
- Use Server Actions for form submissions that mutate local app data.
- Use Route Handlers for external callbacks, webhooks, file uploads, and public API endpoints.
- Validate every boundary with a schema library such as Zod: form data, search params, webhook payloads, and environment variables.
- Keep redirects and cache invalidation close to the mutation that requires them.
- Use `revalidatePath()` or `revalidateTag()` deliberately; do not scatter revalidation across components.

## Component rules

- Components in `components/ui` must be dumb, accessible, and provider-agnostic.
- Components in `components/forms` may know about server actions but not SQL or billing provider SDKs.
- Client components receive serializable props only. Do not pass database rows with `Date`, `BigInt`, or custom classes directly.
- If a component needs `useEffect`, first ask whether the data belongs in a Server Component instead.
- Use optimistic UI only when rollback behavior is obvious and tested.

## Server action rules

Every server action should follow this shape:

1. Authenticate and load `currentUser()`.
2. Validate input.
3. Authorize against workspace/project membership.
4. Call one service function.
5. Revalidate or redirect.
6. Return UI-safe errors only.

Do not put business rules directly in `app/` files. `app/` orchestrates HTTP and rendering; `server/services` owns decisions.

## Authentication and authorization

- Authentication answers “who is this?”; authorization answers “can they do this here?”. Keep them separate.
- Put membership and role checks in `lib/auth/permissions.ts` or a domain service.
- Do not trust workspace IDs from forms or URLs without verifying membership.
- Prefer deny-by-default helpers such as `requireWorkspaceRole(userId, workspaceId, ['owner'])`.
- Session lookup should be cached per request where safe, but authorization checks must remain explicit at mutation points.

## Billing and webhooks

- Treat billing provider webhooks as eventually consistent events, not direct UI commands.
- Store raw webhook event IDs and ignore duplicates.
- Entitlements should be computed from local database state, not by calling the provider on every request.
- Keep provider-specific payload parsing in `lib/billing/providerName.ts`.
- Tests must cover duplicate webhook delivery and out-of-order events.

## Error handling

- Throw domain errors from services, e.g. `new DomainError('WORKSPACE_SLUG_TAKEN')`.
- Map domain errors to human messages at the UI boundary.
- Log unexpected errors with request context, but never log secrets, session tokens, API keys, or full webhook payloads.
- Do not return stack traces from server actions or route handlers.

## Testing expectations

- Unit test pure functions and permission logic.
- Integration test services that write to SQLite using a temporary database file.
- Route handlers need tests for status codes, validation failures, and auth failures.
- Server actions need tests for validation, authorization, and cache/redirect behavior where practical.
- Add a regression test for every bug fix before or with the fix.

SQLite test setup should create a fresh temporary database, apply `schema.sql` plus migrations, and enable foreign keys before each test suite.

## Anti-patterns to avoid

- Do not add Prisma just because it is familiar. SQLite-first SaaS code is clearer with explicit SQL unless the project already uses an ORM.
- Do not perform writes from React Client Components through ad-hoc fetch calls when a Server Action fits.
- Do not keep business logic in route handlers.
- Do not store money as floating point. Use integer cents or provider minor units.
- Do not add global mutable singletons for request-specific data.
- Do not mix marketing pages and authenticated app shell in the same route group.
- Do not create migrations that rewrite large tables without explaining lock time and backup strategy.
- Do not read `process.env` throughout the codebase; centralize validation in `lib/env.ts`.

## Definition of done

A change is complete only when:

- The code follows the layer boundaries above.
- New or changed behavior has tests.
- Migrations are included and documented when schema changes.
- `pnpm lint`, `pnpm typecheck`, `pnpm test`, and relevant DB tests pass.
- The PR description includes screenshots or logs for user-visible changes.
- Secrets, tokens, local database files, and generated caches are not committed.

When uncertain, choose the smaller change with clearer boundaries. A SaaS codebase becomes hard to maintain when every feature invents its own route, query, and permission pattern.
