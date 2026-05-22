# CLAUDE.md

## Stack And Versions

This project is a small production SaaS app built with:

- Next.js 15 App Router
- React Server Components by default
- TypeScript in strict mode
- SQLite through `better-sqlite3` for local/server deployments or Turso/libSQL for hosted SQLite
- Server Actions for trusted mutations
- Route Handlers only for external HTTP/API integrations
- Tailwind CSS and accessible, composable UI components

Optimize for boring, explicit server-side code. Prefer simple database queries, clear ownership boundaries, and easy deployability over framework cleverness.

## Common Commands

Use these commands unless the repository documents different ones:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
```

Before finishing a change, run the narrowest useful verification first, then broaden if the touched surface is shared:

```bash
npm run lint
npm run typecheck
npm test
```

Do not claim a migration, auth, billing, or permission change is done without testing the affected user path manually or with an integration test.

## Folder Structure

Use this structure for greenfield work:

```text
app/
  (marketing)/
  (app)/
  api/
  login/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  domain/
db/
  index.ts
  schema.ts
  migrations/
features/
  billing/
  organizations/
  projects/
  users/
lib/
  auth.ts
  env.ts
  errors.ts
  permissions.ts
  validators.ts
tests/
```

Rules:

- `app/` owns routing, layouts, loading states, and page composition.
- `features/<domain>/` owns business logic for one domain.
- `components/ui/` contains generic primitives only. No database calls, auth checks, or product-specific copy.
- `components/domain/` may compose UI for a specific product workflow but must still receive data through props.
- `db/` owns the SQLite connection, schema, and migrations.
- `lib/env.ts` is the only place that reads and validates environment variables directly.

## Server And Client Boundaries

Default to Server Components.

Use a Client Component only when it needs:

- browser state
- event handlers
- focus management
- optimistic interactions
- client-only libraries

Keep Client Components as leaf nodes. Fetch data in the server page, then pass the minimum serializable props down.

Do not import database clients, secrets, or server-only modules into Client Components. If a mutation is needed, use a Server Action or a Route Handler.

## Data Access Pattern

Database access belongs in feature-level query and mutation functions, not directly inside components.

Use this shape:

```text
features/projects/
  queries.ts
  mutations.ts
  validators.ts
  permissions.ts
```

Guidelines:

- `queries.ts` returns read models shaped for pages.
- `mutations.ts` performs writes inside transactions when more than one table changes.
- `validators.ts` contains Zod schemas shared by forms and Server Actions.
- `permissions.ts` exposes explicit checks such as `canReadProject` or `canInviteMember`.

Never hide permission checks inside generic helpers. Call them visibly from the page, action, or mutation entry point.

## SQLite Rules

SQLite is not Postgres. Write code that respects its strengths and constraints.

- Always enable foreign keys when opening a connection.
- Use transactions for multi-step writes.
- Keep writes short. Do not perform network calls inside a write transaction.
- Use ISO strings or integer epoch milliseconds for timestamps; pick one and keep it consistent.
- Prefer explicit indexes for foreign keys and high-cardinality filters.
- Avoid JSON blobs for data that must be queried, filtered, or permission-checked.
- Do not use floating point values for money. Store cents or minor units as integers.

For `better-sqlite3`, the connection should be process-local and reused. Do not create a new connection per request.

For Turso/libSQL, keep database calls server-side and treat network latency as part of the page budget.

## Migration Conventions

Migrations are append-only. Never edit a migration that has already been merged.

Naming:

```text
db/migrations/0001_initial.sql
db/migrations/0002_add_organizations.sql
db/migrations/0003_add_project_members.sql
```

Migration rules:

- Each migration must be deterministic and safe to run once.
- Include required indexes in the same migration as the table they support.
- Use `NOT NULL` with defaults only when the default is truly valid for old rows.
- For destructive changes, create a new table, copy data, verify shape, then swap.
- Keep seed/demo data out of migrations. Put seeds in a separate script.

Every schema change must include:

- migration file
- TypeScript schema/type update
- query/mutation update
- test or manual verification note

## Environment Variables

Read environment variables through `lib/env.ts`.

Validate on boot with a schema. Fail fast when a required variable is missing.

Use names like:

```text
DATABASE_URL
SESSION_SECRET
APP_URL
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
```

Never read `process.env` from random files. Never expose secrets through `NEXT_PUBLIC_` variables. Only public browser-safe values may use `NEXT_PUBLIC_`.

## Auth, Sessions, And Permissions

Authentication answers "who is this user?"

Authorization answers "can this user do this action?"

Keep them separate.

- Use one session helper, for example `requireUser()`, for pages and actions that need login.
- Check organization/project membership on every protected read and write.
- Do not rely on hidden form fields for ownership, price, role, or permission values.
- Derive sensitive values from the session and database.
- Mutations must re-check permissions even if the page already checked them.

For SaaS apps, most data should be scoped by `organizationId` or `workspaceId`. Queries that omit that scope are suspicious and should be reviewed.

## Server Actions

Use Server Actions for internal form submissions and product mutations.

Server Action rules:

- Validate input with Zod.
- Re-read the current user from the session.
- Re-check permissions inside the action.
- Return typed success/error results for expected validation failures.
- Throw only for unexpected infrastructure failures.
- Revalidate or redirect explicitly after successful writes.

Do not put raw database calls in inline page actions once the logic has more than one branch. Move it to `features/<domain>/mutations.ts`.

## Route Handlers

Use Route Handlers for:

- webhooks
- public API endpoints
- third-party integrations
- file upload callbacks

Route Handler rules:

- Verify webhook signatures before parsing trust-sensitive payloads.
- Keep response bodies small and explicit.
- Return stable error shapes.
- Do not use Route Handlers as a replacement for Server Actions inside the same app unless an external HTTP boundary is required.

## Component Patterns

Prefer small, named components with explicit props.

Good:

```tsx
type ProjectHeaderProps = {
  name: string;
  planName: string;
  canInviteMembers: boolean;
};
```

Avoid:

```tsx
type Props = {
  data: any;
};
```

Component rules:

- Use Server Components for data loading.
- Use Client Components for interaction islands.
- Keep forms close to the route that owns the workflow.
- Put reusable form fields in `components/forms/`.
- Put reusable design primitives in `components/ui/`.
- Do not create a global component until it has at least two real call sites.

## Error Handling

Expected user errors should be visible and recoverable.

Examples:

- invalid form input
- duplicate slug
- expired invite
- missing permission

Unexpected errors should be logged with enough context for debugging but without secrets.

Use a small app error type for domain failures:

```ts
type AppErrorCode =
  | "VALIDATION_ERROR"
  | "NOT_FOUND"
  | "FORBIDDEN"
  | "CONFLICT";
```

Do not leak SQL errors, tokens, stack traces, or third-party response bodies to the browser.

## Testing Rules

Prioritize tests around:

- permission boundaries
- billing state transitions
- database migrations
- Server Actions
- webhook verification
- multi-tenant data isolation

For simple presentational components, tests are optional unless the component encodes business rules.

When adding a bug fix, first add a regression test if the behavior can be reproduced locally.

## Performance Rules

- Avoid N+1 queries in dashboards and lists.
- Paginate lists that can grow beyond 50 rows.
- Keep page-level queries explicit.
- Use indexes for common filters like `organizationId`, `userId`, `slug`, `createdAt`.
- Do not fetch large records just to count or check existence.
- Prefer server-side filtering over client-side filtering for protected data.

## What We Do Not Do

- We do not put database calls in Client Components because secrets and server state must stay server-side.
- We do not edit merged migrations because deployed SQLite databases cannot safely forget history.
- We do not use `any` for API or action payloads because schema drift becomes invisible.
- We do not add broad abstractions before two or more real use cases prove the shape.
- We do not trust client-provided organization IDs, roles, prices, or user IDs.
- We do not use Route Handlers for ordinary internal form submissions when Server Actions fit better.
- We do not hide permission checks in generic data helpers because SaaS data leaks are usually scope bugs.
- We do not store money as floats because rounding errors become billing bugs.
- We do not introduce background jobs without documenting retry, idempotency, and failure behavior.

## Pull Request Expectations

Every PR should explain:

- what changed
- what user path is affected
- what database changes were made
- how it was tested
- what follow-up risk remains

For database, auth, billing, or permission changes, include the exact commands run and at least one manual verification note.

Keep PRs focused. If a change touches routing, schema, permissions, and UI all at once, explain why those parts must ship together.

## How Claude Should Work In This Repo

When asked to implement a feature:

1. Identify the route and feature domain.
2. Inspect existing schema, queries, mutations, and permission checks.
3. Make the smallest cohesive change.
4. Add or update tests for risky behavior.
5. Run the relevant checks.
6. Summarize changed files and remaining risk.

When uncertain, prefer a small explicit implementation over a generic framework. This codebase should stay easy for a small SaaS team to understand at 2 a.m.
