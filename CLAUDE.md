# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the project memory for a greenfield SaaS app built with Next.js 15 App Router, React 19, TypeScript, SQLite, and either `better-sqlite3` for local-first apps or Turso/libSQL for hosted SQLite.

## Stack and Runtime

- Framework: Next.js 15 App Router with TypeScript in strict mode.
- UI: React 19 Server Components by default; Client Components only for browser state, effects, forms with client-side interactivity, or third-party browser-only libraries.
- Database: SQLite through a tiny data-access layer. Use `better-sqlite3` for single-node deployments and `@libsql/client` for Turso/serverless deployments.
- Styling: Tailwind CSS plus small, composable components. Prefer semantic HTML before custom widgets.
- Auth: session cookies stored server-side or signed HttpOnly cookies. Never store JWTs in localStorage.
- Validation: `zod` at every trust boundary: route handlers, server actions, webhook payloads, and environment variables.
- Package manager: `pnpm` unless the repository already chose another manager.

Reason: this stack keeps the app simple, typed end-to-end, and deployable without introducing a separate database server before the product needs one.

## Project Structure

Use this structure unless the existing repository already has a clear convention:

```text
app/
  (marketing)/              # public pages and SEO content
  (app)/                    # authenticated product shell
  api/                      # route handlers for webhooks or external clients
  login/                    # auth entry points
components/
  ui/                       # reusable primitives: Button, Input, Dialog
  app/                      # product-specific components
  forms/                    # form components and field groups
db/
  client.ts                 # SQLite/libSQL connection factory
  schema.ts                 # table names, SQL snippets, row types
  migrations/               # numbered SQL migrations
  queries/                  # small query modules grouped by domain
lib/
  auth/                     # session, password, permission helpers
  env.ts                    # zod-validated environment variables
  errors.ts                 # typed app errors and user-safe messages
  utils.ts                  # pure shared helpers only
server/
  actions/                  # server actions grouped by feature
  services/                 # business workflows; calls db/queries
hooks/                      # client hooks only
tests/
  unit/
  integration/
  fixtures/
```

Reason: `app/` stays focused on routing and rendering, while `server/` and `db/` keep business logic testable without a browser.

## Naming Conventions

- Files and folders: kebab-case for routes and components (`billing-settings.tsx`).
- React components: PascalCase exports (`BillingSettings`).
- Server actions: verb-first names ending in `Action` (`createWorkspaceAction`).
- Query functions: verb-first names that name the entity (`getUserByEmail`, `insertWorkspace`).
- Database tables: snake_case plural nouns (`users`, `workspace_members`).
- Database columns: snake_case (`created_at`, `workspace_id`).
- TypeScript types: domain-specific names (`WorkspaceMemberRow`, `CreateInvoiceInput`). Avoid vague `Data`, `Info`, or `Payload` unless scoped.

Reason: matching SQL naming to SQLite conventions and TypeScript naming to JS conventions avoids constant translation confusion.

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
    "db:migrate": "tsx db/migrate.ts",
    "db:studio": "sqlite-web ./data/app.db"
  }
}
```

Before declaring work complete, run:

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

If a command is missing, add it rather than skipping verification.

## Environment Rules

- All environment variables must be declared and validated in `lib/env.ts` with `zod`.
- Never read `process.env` directly outside `lib/env.ts`.
- Split server-only secrets from public values. Public values must start with `NEXT_PUBLIC_`.
- Provide `.env.example` with safe placeholders, never real secrets.

Reason: centralized env validation fails fast during boot and prevents secret leakage into client bundles.

## SQLite and Migration Rules

- Every schema change gets a numbered SQL file in `db/migrations/`:
  - `0001_initial.sql`
  - `0002_add_billing_tables.sql`
- Migrations must be append-only after merge. Do not edit old migrations except before the PR lands.
- Include `created_at` and `updated_at` on user-owned tables.
- Use `TEXT` UUID/ULID primary keys unless there is a clear reason for integer IDs.
- Enable foreign keys on every connection: `PRAGMA foreign_keys = ON`.
- Use transactions for multi-step writes.
- Add indexes for every foreign key and for every column used in frequent `WHERE`, `JOIN`, or `ORDER BY` clauses.
- Prefer explicit SQL over heavy ORM abstractions. If using Drizzle, keep generated schema and migrations in sync.
- Store booleans as `INTEGER NOT NULL DEFAULT 0` and convert at the boundary.
- Store timestamps as ISO-8601 UTC text unless the project already standardizes on Unix milliseconds.

Reason: SQLite is reliable when schema changes are explicit, transactional, and easy to audit.

## Data Access Pattern

Do not query the database from React components or route files directly. Use this flow:

1. `app/**` route/page/server action receives input.
2. `zod` validates input.
3. `server/services/**` applies business rules.
4. `db/queries/**` performs SQL.
5. The caller maps database rows into UI-safe objects.

Example:

```ts
// db/queries/workspaces.ts
export async function getWorkspaceBySlug(slug: string) {
  return db.prepare("SELECT * FROM workspaces WHERE slug = ?").get(slug)
}

// server/services/workspaces.ts
export async function requireWorkspace(slug: string, userId: string) {
  const workspace = await getWorkspaceBySlug(slug)
  if (!workspace) throw new NotFoundError("Workspace not found")
  await assertWorkspaceMember(workspace.id, userId)
  return workspace
}
```

Reason: this makes permissions and business rules reusable across pages, actions, and APIs.

## Server Component Rules

- Pages are Server Components unless they need browser APIs.
- Fetch data in Server Components and pass minimal serializable props to Client Components.
- Do not pass database rows containing secrets or internal flags to Client Components.
- Use `Suspense` for slow panels and `error.tsx` for route-level failures.
- Use `cache()` only for request-safe reads. Do not cache user-specific permission checks globally.

Reason: Server Components reduce client JavaScript and keep secrets on the server.

## Server Actions and Forms

- Validate all `FormData` with a schema before using it.
- Return typed action states for expected validation errors.
- Throw only for unexpected failures.
- Revalidate the narrowest path or tag after writes.
- Check authorization inside the action, not only in the UI.

Example action result:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; fieldErrors?: Record<string, string>; message: string }
```

Reason: users need clear form errors, and attackers can call server actions without using the UI.

## Component Patterns

- Keep `components/ui/*` generic and free of business logic.
- Keep feature components near their domain under `components/app/*` or the route segment.
- Prefer composition over boolean prop explosions. If a component has more than three display modes, split it.
- Use accessible primitives for dialogs, menus, popovers, and tabs.
- Every interactive control needs a visible label or `aria-label`.
- Loading states should preserve layout dimensions to avoid page jumps.

Reason: SaaS UIs change quickly; small accessible components survive redesigns better.

## Auth and Authorization

- Authentication answers “who is this?” Authorization answers “can they do this?” Keep them separate.
- Every workspace-scoped query must include `workspace_id` or pass through a service that verifies membership.
- Never trust client-supplied `user_id`, `workspace_id`, role, price, or plan data.
- Passwords, if used, must be hashed with `argon2id` or `bcrypt` with current cost settings.
- Session cookies must be `HttpOnly`, `Secure` in production, `SameSite=Lax`, and rotated on login.

Reason: most SaaS security bugs are missing tenant checks or trusting client-provided identity data.

## API Route Rules

- Use route handlers only for external clients, webhooks, file uploads, or integrations that cannot use server actions.
- Validate method, params, query, headers, and body.
- Return stable JSON error shapes:

```json
{ "error": { "code": "invalid_input", "message": "Email is required" } }
```

- Verify webhook signatures before parsing business data.
- Avoid leaking stack traces or raw database errors.

Reason: predictable APIs are easier to test and safer for third-party integrations.

## Testing Rules

- Unit test pure helpers, validators, and query mappers.
- Integration test server actions, route handlers, and database queries against a temporary SQLite database.
- Add regression tests for every bug fix.
- Do not mock the database for query tests; use a temp DB and run migrations.
- Use factories in `tests/fixtures/` instead of copying object literals across tests.

Reason: SQLite makes integration tests cheap; use that advantage.

## Error Handling

- Create typed errors in `lib/errors.ts`: `NotFoundError`, `ForbiddenError`, `ValidationError`, `ConflictError`.
- Convert typed errors into user-safe messages at the route/action boundary.
- Log unexpected errors with context, but never log secrets, tokens, cookies, or full payment payloads.
- Prefer explicit empty states over throwing when a user simply has no data yet.

Reason: typed errors keep UX predictable and logs useful without exposing sensitive data.

## Performance Rules

- Avoid N+1 query loops. Fetch related records in batches.
- Use pagination for tables and activity feeds from the start.
- Add indexes in the same PR that adds a query needing them.
- Keep Client Components small; do not move a whole page to the client for one dropdown.
- Use `next/image` for remote images and define allowed domains.

Reason: SQLite handles SaaS workloads well when queries are indexed and pages do not ship unnecessary JavaScript.

## What We Do Not Do

- Do not introduce Prisma by default. Reason: migrations and generated clients add weight; explicit SQL is clearer for SQLite-first apps.
- Do not store auth tokens, sessions, or feature flags in localStorage. Reason: XSS turns localStorage into credential exfiltration.
- Do not put business logic in React components. Reason: it becomes untestable and duplicated across API/actions/pages.
- Do not create a generic `utils` dumping ground. Reason: domain-specific modules are easier to delete and refactor.
- Do not add background job infrastructure before there is a real asynchronous workflow. Reason: cron plus a table is often enough early on.
- Do not add global state for server data. Reason: Server Components and URL state should handle most data flow.
- Do not silently catch errors. Reason: hidden failures become data corruption or support tickets.
- Do not edit old migrations after merge. Reason: deployed databases cannot replay history differently.

## PR Checklist

Before opening a PR, confirm:

- [ ] Inputs are validated with `zod`.
- [ ] Authorization is checked on the server.
- [ ] Database changes include a migration and relevant indexes.
- [ ] New queries are covered by integration tests.
- [ ] Client Components are only used where browser interactivity is required.
- [ ] `pnpm typecheck`, `pnpm lint`, `pnpm test`, and `pnpm build` pass.
- [ ] `.env.example` is updated for any new environment variables.
- [ ] No secrets, tokens, cookies, or private data are logged or committed.

## How Claude Should Work in This Repo

- Inspect existing patterns before creating new ones.
- Prefer the smallest change that satisfies the user request.
- Ask for clarification only when a product decision changes the implementation; otherwise choose the convention in this file.
- When adding a feature, include the route/page, service, query, validation schema, and tests in the same PR.
- When fixing a bug, add a regression test first or explain why the bug cannot be reproduced in a test.
- Keep explanations concise and mention the exact verification commands run.
