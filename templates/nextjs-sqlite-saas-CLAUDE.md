# CLAUDE.md - Next.js 15 + SQLite SaaS Template

Use this file as the project memory for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for local-first/server deployments or Turso/libSQL for hosted edge-friendly SQLite.

## Stack & Versions

- Next.js 15 with App Router, React Server Components, Server Actions where they simplify form mutations, and Route Handlers for API-style endpoints.
- TypeScript in strict mode. Types should describe domain intent, not hide uncertainty behind `any`.
- SQLite as the source of truth. Use `better-sqlite3` for single-region Node runtimes and Turso/libSQL when hosted replication is required.
- SQL migrations are plain, reviewable files in `db/migrations`. Avoid magical runtime schema sync.
- Styling may use Tailwind plus small local components. Do not introduce a design system package until repeated UI patterns justify it.

Reason: this stack is small enough for fast iteration but still production-capable when schema changes, auth, and server boundaries are treated carefully.

## Folder Structure

```text
src/
  app/
    (marketing)/          public pages
    (app)/                authenticated product pages
    api/                  route handlers for webhooks and integration endpoints
  components/
    ui/                   primitive reusable UI
    feature-name/         feature-specific client components
  db/
    client.ts             SQLite/libSQL client factory
    migrations/           numbered SQL migrations
    queries/              typed query modules grouped by domain
  lib/
    auth.ts               auth/session helpers
    env.ts                environment validation
    result.ts             shared Result/error helpers
  server/
    actions/              server actions that mutate data
    services/             orchestration that crosses domains
  tests/
    unit/
    integration/
```

Reason: App Router files are routing surface area, not a dumping ground. Query code belongs near the database layer, feature UI belongs near the feature, and cross-domain orchestration belongs in `server/services`.

## Naming Conventions

- Components use `PascalCase.tsx`; hooks use `useThing.ts`; server actions use `thing.actions.ts`.
- Database tables use snake_case plural names: `users`, `subscriptions`, `invoice_items`.
- TypeScript domain types use singular PascalCase: `User`, `Subscription`, `InvoiceItem`.
- SQL migration files use `YYYYMMDDHHMM_description.sql`, for example `202605131700_create_subscriptions.sql`.
- Route segments should describe user-facing concepts, not implementation details.

Reason: consistent names make it easy for Claude Code to find the right layer without asking where things live.

## SQL & Migration Rules

- Every schema change requires a migration file. Do not edit old migrations after they are merged.
- Migrations must be deterministic and safe to run exactly once.
- Prefer explicit columns over JSON blobs for data that is filtered, joined, or reported.
- Always include `created_at` and `updated_at` for user-owned core records.
- Use foreign keys and indexes intentionally.
- Use transactions for multi-step writes.
- Never build SQL with string concatenation. Use prepared statements or the query API.
- Keep deletes conservative. Prefer soft delete for user-visible business records and hard delete for ephemeral tokens/logs.

Reason: SQLite is reliable when writes are explicit, migrations are boring, and query paths are designed instead of guessed.

## Data Access Patterns

- Query modules expose small functions such as `getUserById`, `listInvoicesForUser`, and `createCheckoutSessionRecord`.
- Query functions receive a database client or transaction object. Do not import a mutable global transaction.
- Service functions combine query modules and external APIs.
- UI components never import `db/client.ts`.
- Route Handlers and Server Actions validate input before calling services.

Reason: this keeps server-only code out of client bundles and makes tests possible without mocking the whole app.

## Component Patterns

- Server Components are the default for pages that fetch data.
- Client Components are for interactivity: forms, menus, optimistic state, charts, and browser APIs.
- Keep Client Components small and pass them serializable props from Server Components.
- Forms should have loading, success, validation error, and unexpected error states.
- Use semantic HTML before custom abstractions.
- Shared UI primitives should be boring: button, input, dialog, dropdown, table, toast.

Reason: App Router performs best when the server/client boundary is intentional and UI states are visible instead of implicit.

## Server Actions & Route Handlers

- Use Server Actions for first-party form mutations where progressive enhancement is useful.
- Use Route Handlers for webhooks, third-party integrations, file uploads, and public API endpoints.
- Validate all input with a schema or explicit parser at the boundary.
- Return typed results rather than throwing for expected validation errors.
- Revalidate only the paths/tags that changed.

Reason: predictable mutation boundaries reduce accidental cache bugs and make failures easier to show in the UI.

## Auth & Authorization

- Authentication answers "who is this user"; authorization answers "can this user touch this record." Check both.
- Every query that reads user-owned data must include `user_id` or an equivalent ownership condition.
- Do not trust IDs from client components without re-checking ownership on the server.
- Session helpers should return a typed current user object or redirect/throw in one place.

Reason: most SaaS data leaks come from missing ownership checks, not broken login forms.

## Environment Variables

- Define all required env vars in `src/lib/env.ts`.
- Fail fast on server startup if required values are missing.
- Only expose variables with `NEXT_PUBLIC_` when they are safe for the browser.
- Do not read `process.env` throughout the app; import from the env module.

Reason: scattered env reads create runtime-only failures and make deployments harder to reason about.

## Testing Expectations

- Unit test pure helpers and query builders.
- Integration test critical flows against a temporary SQLite database.
- Add regression tests for every bug fix.
- Do not snapshot large HTML trees unless structure is the behavior under test.
- Tests should create their own data and clean up after themselves.

Reason: SQLite makes integration tests cheap, so use them for auth, ownership, and migration-sensitive flows.

## Dev Commands

Use these names unless the project has already standardized differently:

```bash
npm run dev          # start local Next.js
npm run lint         # eslint
npm run typecheck    # tsc --noEmit
npm run test         # unit and integration tests
npm run db:migrate   # apply migrations
npm run db:reset     # reset local database
```

Reason: common command names let Claude Code run verification without asking which script matters.

## Patterns To Follow

- Add the database migration first, then query functions, then service logic, then UI.
- Keep feature work vertical but narrow: schema, server, UI, tests, docs in one focused change.
- Prefer explicit empty states over blank panels.
- Keep money, dates, and time zones formatted through shared helpers.
- Use optimistic UI only when rollback behavior is clear.
- Log operational errors on the server, but show safe messages to users.

Reason: these patterns keep each change reviewable and reduce product surprises.

## Anti-Patterns To Avoid

- Do not put database calls in Client Components. It breaks the server boundary.
- Do not create catch-all utility files like `helpers.ts` for unrelated logic.
- Do not use `any` to silence schema mismatches. Fix the type or parser.
- Do not mutate SQLite schema at app startup. Migrations should be explicit.
- Do not add global state for data that should come from the URL or server.
- Do not swallow errors in Server Actions. Return a typed error result.
- Do not add a queue, Redis, or background worker until a real async workload exists.

Reason: these shortcuts feel fast for the first week and expensive for every week after.

## How Claude Code Should Work In This Repo

- Read the nearest route, query module, and migration before editing.
- Preserve existing naming and folder patterns.
- For schema changes, create a migration and update tests in the same change.
- For UI work, check mobile and empty/error states.
- Before finishing, run lint, typecheck, tests, and any focused migration checks that apply.
- If a requirement is ambiguous, choose the smallest production-ready implementation and mention the assumption in the final response.

Reason: the goal is steady product progress, not clever rewrites.
