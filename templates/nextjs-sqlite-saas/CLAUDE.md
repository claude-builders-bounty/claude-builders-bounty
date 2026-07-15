# CLAUDE.md

This project is a production-oriented SaaS application built with Next.js 15 App Router, TypeScript, SQLite, and server-first React patterns. Treat this file as the operating manual for all code changes.

## Stack And Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode.
- SQLite as the application database, using either `better-sqlite3` for local embedded deployments or Turso/libSQL for hosted SQLite.
- Drizzle ORM is preferred for typed schema and migrations. If Prisma is already installed, follow the existing Prisma setup instead of introducing Drizzle.
- Tailwind CSS and shadcn/ui are preferred for UI when present.
- Authentication should use a proven provider such as Auth.js, Clerk, or Better Auth. Do not hand-roll sessions unless the project already does.

Reason: this stack is strongest when the server owns data access, the database schema is explicit, and UI stays close to the App Router route boundary.

## Expected Folder Structure

```text
app/
  (marketing)/
  (dashboard)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  dashboard/
db/
  schema.ts
  migrations/
  client.ts
lib/
  auth.ts
  env.ts
  permissions.ts
  validators.ts
server/
  actions/
  queries/
  services/
tests/
  unit/
  integration/
```

Use route groups to separate marketing, authenticated app surfaces, and admin surfaces. Put reusable UI in `components/`, database definitions in `db/`, server-only business logic in `server/`, and framework-neutral helpers in `lib/`.

Reason: App Router projects become hard to change when data access, UI components, and route handlers are mixed together.

## Naming Conventions

- Components use `PascalCase.tsx`.
- Hooks use `use-kebab-name.ts` only when they are client-side hooks.
- Server actions use verb-first names such as `createWorkspaceAction`.
- Query functions use noun-first names such as `workspaceBySlug`.
- Database tables use singular snake_case names, for example `user`, `workspace`, `subscription`.
- TypeScript types use explicit domain names such as `WorkspaceRole`, not vague names such as `Data` or `Item`.

Reason: predictable names let Claude Code find the right layer without asking clarifying questions.

## Development Commands

Use the package manager already present in the repository. If none exists, prefer `pnpm`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
```

If a script is missing, add it to `package.json` instead of documenting a command that cannot run.

Reason: every documented command should be executable by a new contributor and by automation.

## Environment Variables

All environment variables must be declared in `lib/env.ts` and validated at startup.

Required variables usually include:

```text
DATABASE_URL
AUTH_SECRET
NEXT_PUBLIC_APP_URL
```

Never read `process.env` directly inside components, server actions, or route handlers. Import validated config from `lib/env.ts`.

Reason: scattered environment reads make deployments fail late and unpredictably.

## SQLite And Migration Rules

- Every schema change must include a migration.
- Never edit an already-applied migration. Create a new migration instead.
- Prefer additive migrations: add nullable columns, backfill data, then enforce constraints in a later migration.
- Do not rely on SQLite foreign keys unless `PRAGMA foreign_keys = ON` is enabled in the database client.
- Use transactions for multi-step writes.
- Keep timestamps as ISO strings or integer milliseconds; do not mix formats within one table.
- Avoid long-running writes inside request handlers. Move them to background jobs or short transactional service functions.

Reason: SQLite is reliable when schema changes are deliberate and writes are short.

## Data Access Pattern

Use this flow for user-triggered writes:

```text
form/client component -> server action -> validator -> service -> db transaction
```

Use this flow for reads:

```text
route/server component -> server query -> db
```

Do not query the database directly from client components. Do not put business rules inside React components.

Reason: keeping reads and writes server-owned reduces hydration bugs and prevents accidental data leaks.

## Server Actions

Server actions must:

- Validate input with Zod, Valibot, or the existing project validator.
- Check authentication and authorization before writing.
- Return typed success/error objects rather than throwing for expected validation failures.
- Revalidate the smallest relevant path or tag.
- Keep side effects idempotent when possible.

Reason: server actions are API endpoints. Treat them with the same care.

## Route Handlers

Route handlers under `app/api` are for webhooks, third-party callbacks, public APIs, and non-form clients. Prefer server actions for first-party form submissions.

Route handlers must:

- Validate method, payload, and authentication.
- Return structured JSON errors.
- Avoid leaking stack traces or database details.
- Verify webhook signatures before parsing trusted actions.

Reason: route handlers are public attack surfaces.

## Component Patterns

- Default to Server Components.
- Add `"use client"` only for interactivity, browser APIs, local state, or effects.
- Keep client components small and pass serializable props from server parents.
- Put form state and optimistic UI in client components, but keep persistence in server actions.
- Prefer composition over prop-heavy mega-components.

Reason: App Router performance depends on minimizing client JavaScript.

## UI And Accessibility

- Forms must have labels, validation messages, and disabled/pending states.
- Buttons that perform writes must show pending state and prevent duplicate submissions.
- Tables and dashboards should be scannable before they are decorative.
- Do not introduce a new design system if shadcn/ui or another system already exists.
- Use semantic HTML before custom ARIA.

Reason: SaaS users repeat workflows; clarity beats ornament.

## Authentication And Authorization

- Authentication answers "who is this user?"
- Authorization answers "can this user do this action in this workspace?"
- Never check only authentication for workspace-scoped data.
- Put permission helpers in `lib/permissions.ts`.
- Include the current workspace/team/org ID in every scoped query.

Reason: multi-tenant SaaS bugs are usually authorization bugs, not login bugs.

## Error Handling

- Use expected error return values for validation, permission, and not-found states.
- Throw only for unexpected system failures.
- Log server errors with enough context to debug, but never log secrets or full tokens.
- Show user-facing errors that describe the next action, not internal implementation details.

Reason: clean error boundaries make production support possible.

## Testing Expectations

Add tests for:

- Permission checks.
- Server actions with validation and authorization branches.
- Database services that perform writes.
- Webhook signature verification.
- Any migration that backfills or transforms data.

Use integration tests for database behavior when possible. Mock external APIs at the service boundary.

Reason: most SaaS regressions happen in permissions, writes, and billing/webhook flows.

## Performance Rules

- Avoid `useEffect` data fetching for initial page data.
- Use server-side pagination for lists that can grow.
- Add database indexes for columns used in frequent filters, joins, or uniqueness checks.
- Avoid N+1 queries in dashboard pages.
- Cache read-heavy, user-independent data with Next.js cache APIs when appropriate.

Reason: SQLite can perform very well when query shape is intentional.

## Security Rules

- Validate all input at trust boundaries.
- Escape or sanitize user-generated rich text.
- Do not expose internal IDs if the existing app uses slugs or public IDs.
- Store secrets only in environment variables or the platform secret manager.
- Do not commit `.env` files or local SQLite databases.
- Rate-limit public mutation endpoints.

Reason: small SaaS apps still handle private customer data.

## What We Do Not Do

- Do not add global state management unless local state and server state are insufficient.
- Do not create client components for static or server-rendered content.
- Do not bypass migrations with manual database edits.
- Do not add a second ORM.
- Do not place business logic in `app/page.tsx`, route handlers, or UI components.
- Do not silently swallow errors from writes, webhooks, auth, or billing.
- Do not introduce background job infrastructure for work that can complete safely inside a short transaction.

Reason: every new moving part increases maintenance cost. Add infrastructure only when the current shape cannot meet the requirement.

## Before Opening A PR

Run:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
```

Include in the PR description:

- What changed.
- What data model or migration changed.
- How authorization was checked.
- Screenshots for user-facing UI.
- The exact commands run.

Reason: reviewers should be able to verify behavior without reconstructing your workflow.
