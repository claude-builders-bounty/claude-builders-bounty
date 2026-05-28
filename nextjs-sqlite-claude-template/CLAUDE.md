# CLAUDE.md

This project is a production-minded SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and server-first React. Optimize for small, explicit modules and boring reliability. Prefer clarity over cleverness because this codebase should stay easy to debug under customer pressure.

## Stack & Versions

- Runtime: Node.js 20 LTS or newer.
- Framework: Next.js 15 with App Router only.
- Language: TypeScript in strict mode.
- UI: React Server Components by default, Client Components only for browser state, effects, or event handlers.
- Database: SQLite through `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted edge-ish SQLite.
- Styling: Tailwind CSS plus small local components. Do not add a second component framework without an explicit task.
- Validation: Zod at every boundary where untrusted input enters the app.
- Auth: a single server-side auth provider or a small custom session layer. Do not mix auth systems.

Reason: this stack is intentionally compact. Most product work should happen in server actions, route handlers, database queries, and typed UI components.

## Dev Commands

Use these commands unless the repository defines more specific package scripts:

```bash
npm run dev          # Start Next.js locally
npm run build        # Production build; must pass before PRs
npm run lint         # ESLint and Next.js lint rules
npm run typecheck    # tsc --noEmit
npm run test         # Unit/integration tests
npm run db:migrate   # Apply pending SQLite migrations
npm run db:studio    # Optional DB explorer if configured
```

When adding a new command, update `package.json` and this file in the same change. A command that only exists in memory is not part of the project.

## Folder Structure

```text
app/
  (auth)/                 # Login/signup/account routes
  (dashboard)/            # Authenticated product surface
  api/                    # Route handlers for webhooks or external callers
  layout.tsx
  page.tsx
components/
  ui/                     # Reusable primitives: Button, Input, Dialog
  forms/                  # Form components bound to schemas/actions
  layout/                 # Nav, sidebar, shell
db/
  migrations/             # Numbered SQL migrations, append-only
  schema.ts               # Typed table/query helpers if used
  client.ts               # SQLite/libSQL connection only
lib/
  actions/                # Server actions grouped by domain
  auth/                   # Session helpers and guards
  config/                 # Env parsing and feature flags
  services/               # Business logic, no React imports
  validators/             # Zod schemas
tests/
  unit/
  integration/
```

Keep domain code close to the layer that owns it. UI state belongs in components. Business rules belong in `lib/services`. SQL belongs in `db` or in narrowly scoped repository functions.

## Naming Conventions

- Files and folders use `kebab-case`: `billing-summary.tsx`, `create-project.ts`.
- React components use `PascalCase` exports: `BillingSummary`.
- Server actions use verb-first names: `createWorkspace`, `updatePlan`, `deleteInvite`.
- Zod schemas end in `Schema`: `createWorkspaceSchema`.
- Database IDs use explicit prefixes in code examples and tests: `user_`, `org_`, `sub_`.
- Boolean values start with `is`, `has`, `can`, or `should`.

Reason: predictable names reduce search time and make Claude's edits less likely to scatter duplicate concepts across the repo.

## SQL & Migration Rules

- Migrations are append-only. Never edit a migration that has been applied outside your local machine.
- Name migrations with a sortable prefix: `0001_create_users.sql`, `0002_add_workspaces.sql`.
- Every table gets `id TEXT PRIMARY KEY`, `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`, and `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP` unless there is a documented reason not to.
- Store money as integer minor units, never floating point.
- Use foreign keys and enable them when opening SQLite connections: `PRAGMA foreign_keys = ON`.
- Use transactions for multi-step writes. A partially created SaaS object is a bug.
- Add indexes in the same migration that introduces the query needing them.
- Prefer soft deletes for customer-owned entities: `deleted_at TEXT`. Hard delete only for ephemeral records or explicit privacy flows.
- For Turso/libSQL, avoid SQLite extensions that are not supported by hosted libSQL.

Reason: SQLite is robust when schema changes are disciplined. Most production incidents in small SaaS apps come from casual migrations and missing constraints.

## Database Access Pattern

Use one database client module. Do not instantiate SQLite connections throughout the codebase.

```ts
// db/client.ts
import Database from "better-sqlite3";

export const db = new Database(process.env.DATABASE_URL ?? "local.db");
db.pragma("foreign_keys = ON");
```

Create small repository functions for repeated queries:

```ts
export function getWorkspaceBySlug(slug: string) {
  return db.prepare("SELECT * FROM workspaces WHERE slug = ? AND deleted_at IS NULL").get(slug);
}
```

Reason: centralized DB access makes migrations, test setup, and Turso/better-sqlite3 swaps manageable.

## Server Actions & Route Handlers

- Use Server Actions for first-party form mutations from the app UI.
- Use Route Handlers for webhooks, public APIs, file callbacks, and third-party integrations.
- Validate all inputs with Zod before touching the database.
- Check authorization inside the action or handler, not only in the page.
- Return small typed result objects: `{ ok: true, data }` or `{ ok: false, error }`.
- Never leak raw database errors to the client.

Reason: colocating validation, authorization, and mutation logic prevents UI-only security.

## Component Patterns

- Default to Server Components.
- Add `"use client"` only when using browser APIs, local interactive state, effects, or event handlers.
- Keep Client Components as leaves. Pass serialized data down from Server Components.
- Forms should have a schema, a server action, pending state, and visible error state.
- Reusable primitives in `components/ui` should be style-light and behavior-stable.
- Product components may be domain-specific. Do not over-abstract a component used once.

Reason: App Router performs best when data loading and authorization stay server-side.

## Environment & Config

- Parse environment variables once in `lib/config/env.ts`.
- Fail fast for missing required production variables.
- Provide safe defaults only for local development.
- Never read `process.env` directly in random files.
- Do not expose secrets through `NEXT_PUBLIC_` unless the value is intentionally public.

Reason: centralized config makes deployment failures obvious and prevents secret leaks.

## Auth & Authorization

- Treat authentication as identity only. Authorization is checked per resource.
- Every workspace-scoped query must include the workspace/org ID.
- Never trust IDs from the client without verifying membership server-side.
- Keep session helpers in `lib/auth`.
- Use redirects for page-level auth failures and typed errors for action-level failures.

Reason: SaaS bugs usually come from cross-tenant access, not from missing login screens.

## Testing Expectations

- Add unit tests for pure services, validators, and permission helpers.
- Add integration tests for server actions that write to SQLite.
- Each migration should be exercised by at least one test database setup path.
- Include regression tests for bugs before changing the implementation.
- Do not mock the database for repository tests; use a temporary SQLite database.

Reason: SQLite is fast enough for real integration tests, and real SQL catches mistakes mocks hide.

## Error Handling

- User-facing errors should be clear and non-technical.
- Logs should include enough context to debug but never include secrets, tokens, or full payment payloads.
- Wrap third-party failures with product-specific messages.
- Prefer explicit error branches over broad `try/catch` blocks that swallow failures.

Reason: SaaS support quality depends on knowing what failed without exposing customer data.

## Patterns To Follow

- Parse env once, validate input once, authorize every mutation.
- Keep SQL explicit. Query builders are acceptable only if already present.
- Use transactions around billing, invitation, workspace creation, and onboarding flows.
- Keep pages thin: load data, check auth, render components.
- Keep services framework-agnostic: no React imports in `lib/services`.
- Include empty, loading, error, and success states for product UI.

## What We Do Not Do

- Do not add Prisma by default. This template intentionally uses direct SQLite/libSQL access to keep migrations transparent and deployment simple.
- Do not put business logic in React components. Components render; services decide.
- Do not create global client stores for server-owned data. Use server rendering and cache revalidation first.
- Do not use floating point for billing, credits, quotas, or balances.
- Do not edit old migrations after they are shared.
- Do not add `"use client"` at page or layout level unless the whole route truly needs browser-only behavior.
- Do not create generic `utils.ts` dumping grounds. Put helpers near their domain.
- Do not skip authorization because a route is hidden in the UI.

## Before Opening A PR

Run:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

Then verify:

- New database changes include a migration.
- New mutations validate input and check authorization.
- New UI has loading, empty, and error states where relevant.
- No secrets or personal data are present in code, logs, tests, or snapshots.

If a command cannot run in the current environment, state the exact reason in the PR notes and include the closest verification performed.

