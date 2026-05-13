# CLAUDE.md — Next.js 15 + SQLite SaaS

This is the working contract for Claude Code in this repository. Treat it as the first source of truth when making implementation decisions.

## Stack and Versions

- Framework: Next.js 15 App Router.
- Language: TypeScript in strict mode.
- Runtime: Node.js for server work; do not assume Edge runtime when using SQLite.
- Database: SQLite via `better-sqlite3` for local/single-node deployments or Turso/libSQL for remote SQLite.
- Styling: Tailwind CSS plus small, typed React components.
- Validation: Zod at every boundary that accepts untrusted input.
- Testing: unit tests for pure logic; integration tests for database writes and server actions.

Reason: this stack is fast to ship, but SQLite has sharp edges around runtime choice, migrations, and concurrent writes. Optimize for clear boundaries over clever abstractions.

## Repository Shape

Use this structure unless the project already has a stronger convention:

```txt
app/
  (marketing)/              # public pages
  (app)/                    # authenticated product UI
  api/                      # route handlers only when HTTP is required
  layout.tsx
  page.tsx
components/
  ui/                       # generic presentational components
  product/                  # domain-specific UI
lib/
  auth/                     # auth/session helpers
  db/                       # connection, migrations, schema helpers
  domain/                   # business rules with no React imports
  env.ts                    # typed environment parsing
  server/                   # server-only orchestration
migrations/
  0001_init.sql
  0002_add_billing_tables.sql
scripts/
  migrate.ts
  seed.ts
  check-env.ts
tests/
  unit/
  integration/
types/
```

Rules:

- `lib/domain/*` must not import React, Next.js request objects, or database clients. It should be easy to test.
- `app/*` can compose UI and server actions, but should not contain long business workflows.
- `components/ui/*` must be reusable and data-light. Put product assumptions in `components/product/*`.
- `lib/db/*` is the only place that opens a SQLite/Turso connection.

## Development Commands

Prefer these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:seed": "tsx scripts/seed.ts",
    "check": "pnpm typecheck && pnpm lint && pnpm test && pnpm build"
  }
}
```

Before claiming a task is complete, run the smallest relevant gate. For feature work, default to `pnpm check`. If a gate cannot run, explain exactly why.

## Environment and Config

Create `lib/env.ts` and parse environment variables once:

```ts
import { z } from "zod";

const Env = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
});

export const env = Env.parse(process.env);
```

Rules:

- Never read `process.env` deep inside feature code.
- Never log secrets, full database URLs, auth tokens, or session cookies.
- Add new env vars to `.env.example` with safe placeholder values.

Reason: central parsing turns config failures into startup failures instead of runtime mysteries.

## SQLite and Migration Conventions

### Migration files

- Store migrations in `migrations/`.
- Name them with a zero-padded sequence and a verb phrase: `0003_create_invoices.sql`.
- Migrations are append-only after merge. Never edit a migration that may have run in any environment.
- Prefer explicit SQL over magical schema sync.

### Schema rules

- Every table has an `id` primary key, `created_at`, and `updated_at` unless there is a strong reason not to.
- Use `TEXT` for UUIDs, public IDs, emails, and external references.
- Use integer cents/sats/smallest units for money. Never store money as floating point.
- Store timestamps as ISO-8601 text or integer epoch milliseconds; pick one per project and document it.
- Add indexes in the same migration that introduces the query path.
- Enable foreign keys on every SQLite connection: `PRAGMA foreign_keys = ON;`.

### Query rules

- Use parameterized statements only.
- Keep SQL close to the repository function that owns the data shape.
- Repository functions return typed domain objects, not raw database rows.
- Wrap multi-step writes in transactions.

Example repository shape:

```ts
export async function createWorkspace(input: CreateWorkspaceInput): Promise<Workspace> {
  const parsed = CreateWorkspaceInput.parse(input);
  return db.transaction(() => {
    const workspace = insertWorkspace(parsed);
    insertAuditEvent({ type: "workspace.created", workspaceId: workspace.id });
    return workspace;
  })();
}
```

Reason: SQLite is reliable when writes are explicit. Hidden writes across helpers create lock and consistency bugs.

## App Router Patterns

- Default to Server Components for data fetching and page composition.
- Use Client Components only for browser state, forms that need client interactivity, charts, and widgets.
- Keep `"use client"` files small and leaf-level.
- Use route handlers for external HTTP integrations, webhooks, or public APIs.
- Use server actions for first-party form mutations when they improve clarity.
- Revalidate intentionally after mutations using `revalidatePath` or `revalidateTag`.

Do not fetch internal API routes from Server Components. Call the server/domain function directly.

Reason: internal HTTP calls add latency, duplicate validation paths, and make auth harder to reason about.

## Server Actions

Server action checklist:

1. Validate input with Zod.
2. Resolve the current session/server identity.
3. Authorize the specific resource, not just "logged in".
4. Execute one domain operation.
5. Revalidate affected paths/tags.
6. Return a small typed result for the UI.

Never trust hidden form fields for ownership, price, role, or permission checks.

## Component Patterns

- Components receive already-shaped props. They do not know database row names.
- Avoid boolean prop soup. Use explicit variants: `variant="primary" | "secondary" | "danger"`.
- Keep data fetching out of generic UI components.
- Co-locate small component tests near complex components or under `tests/unit`.
- Accessibility is part of done: labels for controls, semantic buttons/links, keyboard-safe dialogs.

Reason: a SaaS codebase grows by copy-paste. Good component seams stop copy-paste from becoming architecture.

## API and Webhook Patterns

Route handlers must:

- Validate request bodies and query params.
- Return typed JSON with stable error shapes.
- Authenticate before doing work.
- Verify webhook signatures before parsing business payloads.
- Be idempotent for external events.

Use this error shape:

```ts
return Response.json({ error: { code: "invalid_input", message: "Invalid request" } }, { status: 400 });
```

Do not leak stack traces or vendor payloads in production responses.

## Auth and Authorization

- Separate authentication from authorization.
- Check ownership or role at the data boundary before every read/write.
- Prefer scoped helper functions: `requireWorkspaceRole(workspaceId, ["owner", "admin"])`.
- Audit sensitive changes: billing, team membership, permissions, exports, destructive actions.

Reason: most SaaS bugs are not login bugs; they are "user can touch another user's resource" bugs.

## Testing Strategy

Test pyramid:

- Unit: domain rules, formatting, validation, permission decisions.
- Integration: SQLite migrations, repository functions, server actions with mocked auth.
- E2E only for critical flows: signup, checkout, primary product action.

SQLite test rules:

- Use a temporary database per integration test file or reset all tables between tests.
- Run migrations in tests; do not maintain a separate test schema.
- Test failed migrations and rollback-sensitive paths when changing schema.

Add regression tests for every bug fix.

## Error Handling and Observability

- Use typed expected errors for validation/authorization/business conflicts.
- Let unexpected errors crash the request and be captured by the platform logger.
- Log event names and IDs, not raw PII or secrets.
- Include correlation IDs for long workflows.

For background jobs, store durable state: `queued`, `running`, `succeeded`, `failed`, `retry_after`, `last_error_code`.

## Background Jobs

For small SaaS apps, start with database-backed jobs before adding queues:

- `jobs` table with status, payload JSON, attempts, `run_after`, and timestamps.
- Worker script processes jobs in small batches.
- Every job handler is idempotent.
- Use exponential backoff and a max attempts policy.

Do not hide critical work inside fire-and-forget promises in route handlers or server actions.

Reason: serverless/lambda lifetimes are not durable. If the response returns, unfinished promises may die.

## Security Rules

- No raw SQL string interpolation.
- No dynamic redirects without allowlists.
- No trusting client-provided prices, roles, limits, or ownership.
- No secrets in client components, bundled code, logs, or screenshots.
- Rate-limit auth, invite, export, and expensive generation endpoints.
- Escape or sanitize user-provided HTML; prefer Markdown with a strict renderer.

## Performance Rules

- Avoid N+1 queries in Server Components. Batch by IDs.
- Paginate list pages from the start.
- Add indexes before shipping filters/sorts used by real pages.
- Keep client bundles small by pushing data shaping to server components.
- Use streaming/suspense for slow secondary panels, not for the primary action path.

## What We Do Not Do

- We do not create generic service layers that only pass arguments through. They hide ownership and add no value.
- We do not call internal API routes from server-side code. Direct function calls are simpler and safer.
- We do not mutate database schema from application startup. Migrations are deliberate and reviewable.
- We do not store money in floats. Small rounding bugs become real financial bugs.
- We do not put `"use client"` at page level unless the whole page is truly interactive.
- We do not swallow errors with `catch {}`. If recovery is intentional, record the reason.
- We do not add dependencies for one helper function unless the dependency reduces real risk.

## Definition of Done

A change is done when:

- It matches this file or explains a deliberate exception.
- Input validation and authorization are present at the boundary.
- Migrations are included and tested when schema changes.
- Relevant tests pass.
- `pnpm typecheck` and the relevant build/test gate pass.
- Documentation or `.env.example` is updated when behavior/config changes.
- The PR description states the user-facing change, the risk, and the verification run.
