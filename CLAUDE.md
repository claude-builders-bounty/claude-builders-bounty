# CLAUDE.md — Next.js 15 + SQLite SaaS

This file gives Claude Code the project conventions for a production-minded SaaS built with **Next.js 15 App Router**, **TypeScript**, **SQLite** via `better-sqlite3` locally or **Turso/libSQL** in production, and server-first React.

## Stack & versions

- Next.js 15 with App Router in `app/`.
- TypeScript with `strict: true`.
- React Server Components by default; Client Components only for browser state/events.
- SQLite access through a small repository layer, not direct SQL scattered through routes.
- Auth/session code stays server-side.
- Validation uses Zod or equivalent schemas at all external boundaries.

Reason: this stack is fast and simple, but SQLite and App Router punish unclear boundaries. Keep DB writes, validation, and auth centralized.

## Dev commands

Use these commands unless the project README says otherwise:

```bash
npm run dev        # local development
npm run lint       # lint and framework checks
npm run typecheck  # TypeScript only, no emit
npm test           # unit/integration tests
npm run db:migrate # apply SQLite/Turso migrations
npm run db:studio  # optional DB explorer if configured
```

If a command is missing, add it to `package.json` instead of inventing one-off scripts.

## Folder structure

```text
app/
  (marketing)/          # public pages
  (app)/                # authenticated product routes
  api/                  # route handlers only when HTTP is required
components/
  ui/                   # small reusable primitives
  feature-name/         # feature-specific components
lib/
  auth/                 # session, permissions, current user helpers
  db/                   # connection, migrations, repositories
  env.ts                # typed environment validation
  validators/           # shared Zod schemas
features/
  billing/
  workspace/
  users/
migrations/             # ordered SQL migration files
tests/
  unit/
  integration/
```

Rules:

- Put route-specific UI in `app/` when it is not reused.
- Put reusable domain logic in `features/<name>/`.
- Put cross-cutting infrastructure in `lib/`.
- Do not create a generic `utils.ts` junk drawer; name modules by responsibility.

Reason: SaaS projects grow by feature. Feature folders reduce accidental coupling and make deletion/refactors safer.

## Naming conventions

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts` and only in Client Component paths.
- Server actions: `actions.ts` colocated with the route or feature.
- Repositories: `lib/db/<entity>.repo.ts`.
- Validation schemas: `<entity>.schema.ts`.
- Tests mirror the source name: `workspace.repo.test.ts`.

Reason: predictable filenames let Claude search and edit without asking where things belong.

## Server/client component rules

- Default to Server Components.
- Add `'use client'` only when a component needs browser APIs, local state, effects, or event handlers.
- Client Components receive serializable props only.
- Never import DB, secrets, filesystem, or server-only auth helpers into Client Components.
- Prefer server actions for form mutations when the result affects server data.

Reason: accidental client imports can leak secrets or bloat the bundle.

## Data access rules

All SQL goes through `lib/db` repositories:

```ts
// lib/db/workspace.repo.ts
export async function getWorkspaceBySlug(slug: string) {
  return db.prepare('select * from workspaces where slug = ?').get(slug);
}
```

Do:

- Use parameterized queries only.
- Keep transactions explicit for multi-step writes.
- Return typed domain objects, not raw driver-specific shapes.
- Validate inputs before repository calls.

Do not:

- Open new DB connections inside React components.
- Build SQL with string concatenation.
- Run migrations at request time.
- Mix auth decisions into SQL helpers unless the helper name says so.

Reason: SQLite is reliable when writes are deliberate. Hidden connections and ad hoc SQL cause locks, leaks, and security bugs.

## SQL / migration conventions

Migration files live in `migrations/` and use ordered names:

```text
0001_initial.sql
0002_add_workspaces.sql
0003_add_subscription_status.sql
```

Rules:

- Migrations are append-only after merge.
- Never edit a migration that may have run in another environment; create a new one.
- Every table has:
  - `id` primary key (`text` UUID/CUID or integer, choose once per project)
  - `created_at` ISO timestamp or integer epoch
  - `updated_at` where records are mutable
- Add indexes for foreign keys and common lookup columns.
- Use `not null` and sensible defaults aggressively.
- Include rollback notes in comments if destructive.

Reason: SQLite migrations are easy until environments diverge. Append-only history avoids drift.

## Route handlers and server actions

Use route handlers in `app/api/**/route.ts` for:

- Webhooks
- Third-party integrations
- Public API endpoints
- File downloads/uploads

Use server actions for:

- Product forms
- Authenticated mutations from App Router pages
- Simple create/update/delete flows

Every mutation must:

1. Authenticate the current user.
2. Authorize access to the target workspace/resource.
3. Validate input with a schema.
4. Perform DB writes in a transaction if more than one statement.
5. Return a typed success/error shape.

Reason: auth before validation can leak resource existence; validation before DB protects integrity.

## Auth and permissions

- Use `getCurrentUser()` / `requireUser()` helpers from `lib/auth`.
- Authorization must be checked close to the data operation.
- Workspace membership checks belong in `lib/auth/permissions.ts` or a feature-level service.
- Do not trust client-provided `userId`, `role`, or `workspaceId` without verifying membership server-side.

Reason: SaaS bugs usually happen at tenant boundaries, not login screens.

## Environment variables

All environment variables are declared and validated in `lib/env.ts`.

```ts
export const env = {
  DATABASE_URL: required('DATABASE_URL'),
  AUTH_SECRET: required('AUTH_SECRET'),
};
```

Rules:

- Never read `process.env` directly outside `lib/env.ts`.
- Prefix browser-exposed variables with `NEXT_PUBLIC_` only when truly public.
- Tests should provide explicit env defaults.

Reason: central validation fails fast and prevents accidental secret exposure.

## Component patterns

- Keep UI primitives small and dumb in `components/ui`.
- Keep data fetching in Server Components or feature services.
- Use forms that progressively enhance: HTML first, server action second.
- Prefer composition over global state.
- Add loading/error/empty states for every data-driven page.

Reason: server-first UI is simpler to test and ships less JavaScript.

## Testing expectations

Minimum coverage for new work:

- Repository tests for non-trivial SQL.
- Validation tests for public schemas.
- Server action or route handler tests for mutations.
- A smoke test for critical pages if the project has e2e tooling.

Use temporary SQLite databases in tests. Never point tests at production or shared dev DBs.

Reason: SQLite makes isolated integration tests cheap; use that advantage.

## Security checklist

Before finishing a task, verify:

- No secrets in Client Components or logs.
- All SQL uses parameters.
- Every mutation checks auth and tenant permissions.
- Webhook handlers verify signatures.
- Error messages do not leak whether private resources exist.
- File uploads, if any, validate type and size.

## What we don't do and why

- **No ORM by default** unless the project already has one. Reason: direct SQL is clearer for small SaaS apps and easier to optimize.
- **No global mutable singleton state** outside DB/client initialization. Reason: serverless and edge runtimes behave differently.
- **No client-side auth decisions.** Reason: UI hiding is not authorization.
- **No migration rewrites after merge.** Reason: deployed DBs cannot forget history.
- **No catch-all service files.** Reason: vague modules become impossible for Claude and humans to maintain.
- **No destructive SQL without backup/rollback notes.** Reason: SaaS data loss is unacceptable.

## Before opening a PR

Run:

```bash
npm run lint
npm run typecheck
npm test
```

Also include:

- Migration file names if DB schema changed.
- Screenshots or short notes for UI changes.
- Security notes for auth, permissions, webhooks, or billing changes.

If any command is unavailable, state that clearly in the PR and add the missing script when appropriate.
