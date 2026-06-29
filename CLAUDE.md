# CLAUDE.md

Guidance for Claude Code when working in a greenfield SaaS project built with Next.js 15 App Router and SQLite.

## Stack & Versions

- Use Next.js 15 with the App Router, React 19, TypeScript in strict mode, and Node.js 20 LTS or newer.
  Reason: these versions match the current stable App Router model and avoid mixing legacy Pages Router assumptions into new work.
- Use SQLite as the application database in development and small production deployments.
  Reason: the product should be easy to clone, test, migrate, and reason about without a required external service.
- Prefer `better-sqlite3` for local or single-node deployments, and Turso/libSQL when the app needs managed hosting, read replicas, or edge-friendly access.
  Reason: both keep the SQLite mental model while serving different deployment shapes.
- Use Server Components by default. Add Client Components only for browser-only state, effects, forms that need instant client feedback, or interactive widgets.
  Reason: less shipped JavaScript keeps the app faster and reduces hydration bugs.

## Dev Commands

Use these commands unless this repository defines stricter equivalents in `package.json`.

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:seed
npm run build
```

If a command is missing, add it before relying on a custom workflow. Do not invent one-off scripts hidden outside `package.json`.

## Project Structure

Use this structure for new features:

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  layout/
features/
  billing/
  dashboard/
  settings/
lib/
  auth/
  db/
  env.ts
  result.ts
server/
  actions/
  queries/
  services/
db/
  migrations/
  schema.sql
  seed.ts
tests/
  unit/
  integration/
```

Rules:

- Keep route files thin. `page.tsx`, `layout.tsx`, and `route.ts` compose behavior; they do not hold business logic.
  Reason: routes change frequently, while business rules should be testable without rendering a page.
- Put feature-specific behavior in `features/<feature-name>` when it belongs to one product area.
  Reason: billing code should not be scattered through generic folders.
- Put shared server-only database code in `lib/db` and query orchestration in `server/queries` or `server/services`.
  Reason: it prevents accidental imports of database clients into Client Components.
- Put reusable visual primitives in `components/ui` and product-specific components next to their feature.
  Reason: the UI layer stays consistent without turning every feature into a global abstraction.

## Naming Conventions

- Files and folders use kebab-case: `create-invoice-form.tsx`, `user-menu.tsx`, `billing-settings`.
  Reason: kebab-case is readable in URLs, imports, and file explorers.
- React components use PascalCase exports: `CreateInvoiceForm`.
  Reason: JSX distinguishes components from native elements.
- Server actions use verb-first names: `createWorkspace`, `updateSubscription`, `deleteInvite`.
  Reason: mutation names should read like commands.
- Query functions use noun-focused names: `getWorkspaceBySlug`, `listInvoicesForAccount`.
  Reason: reads should describe the data they return.
- Database tables use plural snake_case: `users`, `workspaces`, `workspace_members`.
  Reason: SQL stays conventional and easy to inspect.
- IDs use the table name as a prefix when exposed outside the database, such as `user_`, `workspace_`, and `invoice_`.
  Reason: prefixed IDs make logs, support tickets, and webhook payloads easier to debug.

## SQLite & Migration Conventions

- Treat migrations as append-only history. Never edit a migration after it has been merged.
  Reason: deployed SQLite databases cannot safely replay rewritten history.
- Use timestamped migration names: `202606281030_create_workspaces.sql`.
  Reason: ordering remains obvious without depending on filesystem quirks.
- Every migration must be idempotent where SQLite allows it, using `IF NOT EXISTS` for tables and indexes.
  Reason: local resets and partial deploy retries should not destroy developer flow.
- Enable foreign keys for every connection with `PRAGMA foreign_keys = ON`.
  Reason: SQLite does not enforce them unless explicitly enabled.
- Use explicit transactions for multi-statement writes.
  Reason: partial writes create subtle SaaS account and billing bugs.
- Store timestamps as ISO-8601 UTC text unless a library in the repo already standardizes another format.
  Reason: ISO text is human-readable and sorts correctly.
- Use integer cents for money, not floats.
  Reason: subscription and invoice math must be exact.
- Add indexes with the query in mind. Each index needs a reason tied to a read path.
  Reason: unnecessary indexes slow writes and make migrations harder to audit.
- Prefer soft deletion only when the product needs restore, audit, or compliance behavior. Otherwise delete directly inside a transaction.
  Reason: default soft delete adds filters to every query and causes data leaks when forgotten.

## Data Access Patterns

- Create one database entry point in `lib/db/client.ts`.
  Reason: connection pragmas, tracing, and test overrides belong in one place.
- Keep raw SQL in named functions, not inline inside React components or route handlers.
  Reason: SQL should be searchable, testable, and reviewed as data access code.
- Validate all external input with a schema before it reaches SQL.
  Reason: TypeScript types disappear at runtime.
- Return typed domain objects from queries instead of leaking driver rows through the app.
  Reason: UI code should not know database column naming details.
- Use prepared statements for all dynamic values.
  Reason: string-built SQL is not acceptable in product code.

## App Router Patterns

- Fetch data in Server Components for page-level reads.
  Reason: the server can access SQLite directly and avoid client waterfalls.
- Use Server Actions for form mutations that belong to the app shell.
  Reason: they keep validation, authorization, writes, and cache invalidation together.
- Use `route.ts` handlers for webhooks, public APIs, file uploads, and integrations.
  Reason: those flows need explicit HTTP semantics and status codes.
- Call `revalidatePath` or `revalidateTag` immediately after successful mutations.
  Reason: users should see the new database state after a write.
- Keep `loading.tsx`, `error.tsx`, and `not-found.tsx` close to the route segment they affect.
  Reason: each product area deserves targeted empty and failure states.

## Component Patterns

- Start with Server Components. Add `'use client'` at the smallest possible boundary.
  Reason: one client directive pulls the whole imported subtree into the browser bundle.
- Use controlled inputs only when the UI needs live validation or computed state.
  Reason: plain HTML forms with Server Actions are simpler and more resilient.
- Keep design primitives small: `Button`, `Input`, `Select`, `Dialog`, `DropdownMenu`, `Table`.
  Reason: primitives should compose product workflows, not encode product decisions.
- Put feature forms in `components/forms` only when multiple features reuse them. Otherwise keep them under the feature folder.
  Reason: premature shared forms become hard to change.
- Always render pending, success, empty, and error states for data-mutating UI.
  Reason: SaaS users repeat workflows and need clear feedback.
- Use accessible labels and semantic elements before adding ARIA.
  Reason: native HTML is more reliable than decorative accessibility patches.

## Authentication & Authorization

- Authenticate at the boundary, authorize near the data.
  Reason: route protection is not enough; every query or mutation must enforce tenant access.
- Every workspace-scoped query must include `workspace_id` or a verified membership join.
  Reason: cross-tenant leaks are the highest-risk SaaS bug.
- Do not trust client-provided role, plan, price, or ownership fields.
  Reason: those values must come from the database or the payment provider.

## Environment Variables

- Read environment variables through `lib/env.ts` only.
  Reason: central parsing fails fast and documents required configuration.
- Separate public and server variables. Public variables must use `NEXT_PUBLIC_` and contain no secrets.
  Reason: public variables are bundled into browser code.
- Tests should override environment through the test runner setup, not by mutating random modules.
  Reason: deterministic tests need one configuration path.

## Testing Expectations

- Unit test pure formatting, validation, and authorization helpers.
  Reason: these rules break quietly and are cheap to test.
- Integration test database queries and migrations against a temporary SQLite database.
  Reason: mocks do not catch SQL syntax, constraints, or transaction bugs.
- Test Server Actions through their exported functions when possible.
  Reason: form behavior should be validated without a full browser for every case.
- Add at least one build-time check before opening a PR: lint, typecheck, tests, and build.
  Reason: App Router mistakes often surface only during production compilation.

## What We Do Not Do

- Do not add a Pages Router directory.
  Reason: mixed routers create duplicate conventions and confusing data-fetching rules.
- Do not call SQLite from Client Components.
  Reason: database access belongs on the server.
- Do not create generic `utils.ts` dumping grounds.
  Reason: helpers need ownership and a domain name.
- Do not hide important business behavior inside middleware.
  Reason: middleware is hard to test and should stay focused on routing/session concerns.
- Do not add an ORM unless the repository already uses one or the schema complexity justifies it.
  Reason: SQLite plus typed query functions is often clearer for a small SaaS product.
- Do not store secrets, tokens, or webhook payload samples in the repo.
  Reason: local convenience is not worth credential leakage.
- Do not introduce background jobs without a durable queue or explicit retry strategy.
  Reason: SaaS workflows such as billing, email, and provisioning need observable failure handling.

## PR Checklist For Claude Code

Before proposing changes, confirm:

- The code follows the App Router and Server Component defaults above.
- Database changes include an append-only migration and a rollback/reset story for local development.
- Workspace or tenant access is enforced at the query or mutation layer.
- New UI has loading, empty, and error states where relevant.
- `npm run lint`, `npm run typecheck`, tests, and `npm run build` have been run or the reason they could not run is stated.
