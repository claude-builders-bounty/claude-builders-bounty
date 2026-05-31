# CLAUDE.md - Next.js 15 + SQLite SaaS

## Stack & Versions
- Next.js 15 App Router with TypeScript.
- React Server Components by default; Client Components only for browser state, event handlers, effects, or browser APIs.
- SQLite via `better-sqlite3` for local or single-node apps, or Turso/libSQL when remote edge access is required.
- SQL migrations are source-controlled and deterministic. Runtime schema mutation is not allowed.

Why: this stack is fast to ship, easy to reason about, and avoids premature distributed-system complexity.

## Project Structure
```text
app/                    # route segments, layouts, pages, server actions
app/(marketing)/        # public pages
app/(app)/              # authenticated product UI
components/             # shared UI components
components/ui/          # primitive reusable components
lib/                    # framework-agnostic app utilities
lib/db/                 # db client, queries, migration helpers
lib/auth/               # auth/session helpers
lib/validators/         # zod schemas and input validation
server/                 # server-only workflows and integrations
migrations/             # ordered SQL migration files
tests/                  # unit/integration tests
```

Keep route-local components beside the route. Promote to `components/` only after reuse is real.

## Dev Commands
Use these unless the project README says otherwise:
```bash
npm run dev          # start local app
npm run build        # production build gate
npm run lint         # lint gate
npm run typecheck    # TypeScript gate
npm test             # tests
npm run db:migrate   # apply migrations
npm run db:studio    # optional DB browser if configured
```

If a command is missing, inspect `package.json` and use the closest available script. Do not invent dependencies without asking.

## Naming Conventions
- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts` and only in Client Components or client modules.
- Server actions: `actions.ts` inside the route or feature folder.
- Query functions: `getUserById`, `listInvoicesForOrg`, `createCheckoutSession`.
- SQL migration files: `0001_create_users.sql`, `0002_add_billing_tables.sql`.
- Environment variables: `UPPER_SNAKE_CASE`; document every required variable in `.env.example`.

Why: predictable names reduce search time and make Claude useful without extra clarification.

## SQL And Migration Rules
- All schema changes go in `migrations/` as numbered SQL files.
- Never edit an already-applied migration. Add a new migration instead.
- Every table has:
  - `id` primary key, either text UUID/ULID or integer, but consistent across the app.
  - `created_at` default timestamp.
  - `updated_at` when the row is mutable.
- Foreign keys are explicit and indexed.
- Use transactions for multi-step writes.
- Validate inputs before SQL. Parameterize all queries; never interpolate user input into SQL strings.
- Do not use `SELECT *` in application queries; return only fields the caller needs.

Why: SQLite is reliable when schema and writes are disciplined. Loose migrations create production pain.

## Data Access Pattern
- Keep raw SQL in `lib/db/queries/*` or feature-local `queries.ts`.
- Server Components may call read queries directly.
- Mutations happen through server actions or server-only service functions.
- Return typed domain objects, not driver-specific row shapes.
- Convert `Date`, money, and enum-like values at the boundary.

## Component Patterns
- Prefer Server Components for data fetching and initial render.
- Client Components should be small islands for interactivity.
- Forms use server actions for simple mutations; use API routes only when third-party webhooks, non-form clients, or streaming APIs require them.
- Keep loading and error states route-local with `loading.tsx` and `error.tsx`.
- Use accessible primitives: labels for inputs, semantic buttons and links, keyboard-reachable dialogs.

## Auth And Tenancy
- Treat auth/session lookup as server-only.
- Every organization-scoped query must filter by `org_id` or equivalent tenant key.
- Do not trust client-provided user IDs, roles, prices, or plan names.
- Authorization checks live beside the server action or query, not only in UI.

## Payments And Billing
- Webhooks must be idempotent. Store provider event IDs.
- Never trust client-side price or plan data.
- Keep billing state in local tables derived from provider webhooks.
- Log enough to debug failed webhook handling without storing secrets.

## Testing Expectations
Before claiming done, run the smallest meaningful gate:
1. `npm run typecheck` if present.
2. `npm run lint` if present.
3. `npm test` if present.
4. `npm run build` for route, component, or DB changes.
5. For migrations, apply them to a disposable SQLite database.

If a gate cannot run, state exactly why.

## What We Do Not Do, And Why
- No ORM unless the project already uses one. Raw SQL is clearer for small SaaS apps and easier to review.
- No schema changes from application startup. Migrations must be explicit and reviewable.
- No broad Client Component wrappers. They destroy Server Component benefits.
- No hidden global mutable state for request data. It breaks concurrent rendering assumptions.
- No secrets in code, tests, logs, screenshots, or docs.
- No optimistic security: UI hiding is not authorization.
- No premature queues, microservices, or event sourcing. SQLite SaaS should stay boring until scale proves otherwise.

## Claude Workflow Rules
- Read `package.json`, existing migrations, and route structure before editing.
- Make the smallest coherent change.
- Preserve existing style unless it conflicts with this file.
- For risky DB, auth, or billing changes, explain the plan before editing.
- After changes, summarize files changed, validation run, and any known follow-up.
