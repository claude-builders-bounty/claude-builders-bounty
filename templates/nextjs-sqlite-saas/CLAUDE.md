# CLAUDE.md

This file gives Claude Code the project rules for a production SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and server-first React.

## Stack And Versions

- Next.js 15 with App Router. Use route groups, server components, server actions, and route handlers from the `app/` directory.
- React 19. Prefer server components; add `"use client"` only for interactive UI state, browser APIs, or client-only libraries.
- TypeScript in strict mode. Avoid `any`; model request, database, and UI data explicitly.
- SQLite through one adapter: `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted SQLite. Do not mix adapters in app code.
- SQL migrations live in the repository and are reviewed like application code because schema drift is a production bug.
- Styling may use Tailwind CSS, CSS Modules, or the project's existing system. Do not introduce a second styling system without a reason.

Reason: the stack rules keep runtime, rendering, database, and styling choices predictable so Claude Code can make implementation decisions without first rediscovering the architecture.

## Folder Structure

Use this structure for greenfield work:

```text
app/
  (marketing)/
  (auth)/
  (dashboard)/
  api/
components/
  ui/
  forms/
  layout/
db/
  migrations/
  queries/
  schema.ts
  client.ts
lib/
  auth/
  env.ts
  errors.ts
  validation/
server/
  actions/
  services/
  jobs/
tests/
  unit/
  integration/
```

- `app/` owns routing, layouts, loading states, error boundaries, metadata, and route handlers.
- `components/ui/` contains reusable primitives without business logic.
- `components/forms/` contains form shells and client-side interaction only; validation and writes stay server-side.
- `db/client.ts` owns database connection creation. Import database clients from there only so runtime behavior is consistent.
- `db/queries/` contains SQL access functions. UI and server actions must not inline SQL.
- `server/services/` contains business workflows that coordinate validation, authorization, and database queries.
- `server/actions/` contains thin server actions that parse inputs, call services, and return typed results.
- `lib/env.ts` validates environment variables at startup because missing secrets should fail early.

Reason: these boundaries prevent React files from accumulating database, authorization, and workflow logic that should be reviewed and tested separately.

## Naming Conventions

- Routes use lowercase segment names: `app/(dashboard)/settings/page.tsx`.
- Components use PascalCase file names: `BillingSummary.tsx`.
- Server actions use verb-first names: `createWorkspace`, `updateSubscription`, `deleteInvite`.
- Query functions name the entity and intent: `getUserByEmail`, `listWorkspaceMembers`, `insertAuditEvent`.
- Database tables use `snake_case` plural nouns: `users`, `workspaces`, `workspace_members`.
- IDs are text UUIDs unless the project has a clear reason for integer primary keys.
- TypeScript types mirror domain nouns: `Workspace`, `WorkspaceMember`, `InvoiceStatus`.

Reason: consistent names let Claude Code infer where new files belong and reduce accidental duplicates like `memberService`, `workspaceMembersService`, and `teamUserService`.

## Dev Commands

Use these commands unless the project package manager already defines equivalent scripts:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:migrate
npm run db:studio
```

- Run `lint`, `typecheck`, and relevant tests before opening a PR because App Router mistakes often compile but fail at runtime.
- Run migrations locally before testing a page that reads new columns.
- If a command is missing, add it to `package.json` instead of documenting a one-off command in chat.

Reason: common commands make every branch reproducible for humans, Claude Code, and CI instead of relying on hidden local shell history.

## SQL And Migration Conventions

- Every schema change gets a migration in `db/migrations/` with a timestamp prefix such as `202605120915_add_workspace_members.sql`.
- Migrations must be append-only after merge. Add a new migration to fix a mistake because editing applied migrations breaks deployed databases.
- Prefer explicit SQL over ORM magic. SQLite is small and predictable; hidden query generation makes performance and locking harder to reason about.
- Wrap multi-step writes in transactions. SaaS state changes often touch audit logs, memberships, and billing records together.
- Add indexes in the same migration as the query that needs them. Document the lookup in a SQL comment when it is not obvious.
- Always include `created_at` and `updated_at` for mutable tables. Use UTC ISO strings or integer epoch milliseconds consistently.
- Never use `SELECT *` in app queries. Column lists keep API contracts stable when tables grow.
- Never run destructive migrations automatically in production. Drops, truncates, and large backfills need a documented rollout plan.
- Foreign keys must be enabled for local SQLite connections. In `better-sqlite3`, run `PRAGMA foreign_keys = ON` during client initialization.

Reason: SQLite is reliable when schema changes are explicit; migration discipline prevents local success from turning into production data loss.

## Database Access Patterns

- Keep SQL in `db/queries/`. Server components, actions, and route handlers call query functions or services.
- Validate external input before it reaches SQL. Use a schema validator in `lib/validation/` and pass typed values to query functions.
- Query functions return domain objects, not raw driver rows with unclear nullability.
- Handle unique constraint conflicts intentionally. Return a typed conflict result rather than surfacing driver-specific errors to UI.
- For Turso/libSQL, keep network database calls out of hot rendering paths when possible. Cache read-only data with Next.js caching primitives where product requirements allow it.
- For `better-sqlite3`, do not open a new connection per request. Reuse the shared client from `db/client.ts`.

Reason: centralizing database access makes authorization, transactions, caching, and driver-specific behavior visible in review.

## App Router Patterns

- Default to server components for pages and data fetching. They reduce client bundle size and keep secrets on the server.
- Use route handlers in `app/api/` only for external integrations, webhooks, or non-React clients. Internal form mutations should use server actions.
- Put `loading.tsx`, `error.tsx`, and `not-found.tsx` near the route segment they protect.
- Use `generateMetadata` for dynamic metadata when it depends on route params or database records.
- Keep layouts stable. Do not fetch user-specific volatile data in the root layout if it forces unnecessary re-rendering.
- Use `revalidatePath` or `revalidateTag` after mutations that change visible server-rendered data.

Reason: App Router works best when server-rendered data, cache invalidation, and client interactivity are intentionally separated.

## Component Patterns

- Server components pass serializable props into client components. Do not pass database clients, class instances, functions, or secrets.
- Client components own interaction state only: toggles, menus, optimistic UI, controlled inputs, and browser APIs.
- Forms should use progressive enhancement. The form submits to a server action and still has clear pending, success, and error states.
- Shared UI primitives do not import from `db/`, `server/`, or `app/api/`.
- Prefer composition over prop explosions. If a component needs many unrelated booleans, split it.
- Keep accessibility built in: labels for inputs, keyboard reachable menus, visible focus states, and semantic buttons.

Reason: component boundaries keep the client bundle small and make SaaS screens easier to scan, test, and reuse.

## Auth And Authorization

- Authentication answers "who is this user?" Authorization answers "can this user do this action?" Keep both checks explicit.
- Perform authorization in services or query helpers close to the data being accessed, not only in UI conditionals.
- Never trust `workspaceId`, `userId`, or role values sent from the client. Resolve permissions from the session and database.
- For dashboard pages, fetch the current user/session in a server boundary and pass only safe fields to client components.
- Audit sensitive writes such as role changes, billing updates, exports, and destructive deletes.

Reason: SaaS bugs often become tenant isolation bugs, so permission checks must live near the server-side data they protect.

## Error Handling

- Use typed result objects for expected failures: validation errors, conflicts, missing records, and permission denials.
- Throw only for unexpected failures. Unexpected exceptions should reach an error boundary or centralized logger.
- Do not leak SQL, token, or provider error messages into user-facing UI.
- Empty states are not errors. Render useful empty states for first-run SaaS flows.

Reason: clear error categories let users recover from expected failures while preserving useful signal for developers.

## Testing Rules

- Unit test pure helpers, validation schemas, and query mappers.
- Integration test database queries against a temporary SQLite database with migrations applied.
- Test server actions at the service layer. UI tests should not be the only coverage for data writes.
- Add regression tests for every migration that changes constraints, nullability, or authorization-sensitive queries.
- Snapshot tests are acceptable only for stable serialization output, not broad UI trees.

Reason: the highest-risk behavior in this stack lives at service, query, migration, and authorization boundaries, not in static page markup.

## Patterns To Follow

- Create thin routes, thin server actions, and thicker services. This keeps routing concerns separate from business decisions.
- Keep environment reads in `lib/env.ts`. This makes tests easier and avoids scattered `process.env` checks.
- Use transactions for workflows that must either fully succeed or fully fail.
- Prefer explicit cache invalidation after writes. Stale dashboard data causes support issues.
- Keep generated types and migration output committed when the project uses code generation.

Reason: these patterns optimize for durable SaaS behavior under repeated edits rather than one-off demo code.

## Anti-Patterns To Avoid

- Do not put SQL directly inside React components. It makes rendering, testing, and authorization harder to audit.
- Do not add `"use client"` at the top of a page just to use one interactive child. Move the interactive part into a small client component.
- Do not mutate data in server components during render. Use server actions, route handlers, or background jobs.
- Do not edit old migrations after they have shipped. Production databases cannot replay your git history.
- Do not swallow database errors and return `null`. Missing data, denied access, and broken queries need different handling.
- Do not use global mutable objects for request-specific user/session state. Server concurrency will eventually expose the bug.
- Do not duplicate schema constants between SQL and TypeScript without a single source of truth or tests.

Reason: each anti-pattern hides state, ownership, or data-contract changes in a place reviewers and Claude Code are likely to miss.

## PR Checklist

- The change follows the folder boundaries above.
- New data writes have validation, authorization, and transaction handling where needed.
- Schema changes include a migration and any required indexes.
- UI changes include loading, empty, and error states.
- `lint`, `typecheck`, tests, and migrations were run locally or the PR explains why they were not.
