# CLAUDE.md

This file gives Claude Code project-specific rules for a production-minded SaaS app built with Next.js 15 App Router, TypeScript, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack And Versions

- Use Next.js 15 with the App Router in `app/`.
- Use TypeScript in strict mode. Avoid `any`; prefer explicit domain types at boundaries.
- Use SQLite as the source of truth. Use `better-sqlite3` for local/serverful deployments or Turso/libSQL when the app needs hosted SQLite.
- Use Server Components by default. Add `"use client"` only for browser state, effects, event handlers, or client-only libraries.
- Use Server Actions or route handlers for mutations. Do not mutate data directly from Client Components.
- Keep styling local to the existing project convention: Tailwind/shadcn if already installed, CSS modules or plain CSS otherwise.

## Folder Structure

Use this layout unless the repository already has a stronger convention:

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  layout/
db/
  client.ts
  migrations/
  queries/
  schema.sql
lib/
  auth/
  env.ts
  validation/
server/
  actions/
  services/
tests/
```

- `app/` owns routing, layouts, metadata, loading states, and error boundaries.
- `components/ui/` contains small reusable primitives. Feature-specific components stay near the route or feature that uses them.
- `db/` owns SQLite connection setup, migrations, schema, and low-level query helpers.
- `server/actions/` contains Server Actions that validate input, call services, and revalidate paths.
- `server/services/` contains business rules. Keep SQL out of React components.
- `lib/env.ts` is the only place that reads `process.env` directly.
- `tests/` mirrors the behavior under test; do not build a parallel architecture only for tests.

## Dev Commands

Prefer these scripts in `package.json`:

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:studio
```

If the project uses npm, yarn, or bun, keep the same command names where possible.

## Naming Conventions

- Route folders use lowercase kebab-case: `app/(app)/billing/settings`.
- React components use PascalCase filenames: `BillingTable.tsx`.
- Server-only modules use clear names: `db/client.ts`, `server/services/billing.ts`.
- Server Actions use verb phrases: `createWorkspace`, `updateSubscription`, `deleteInvite`.
- SQLite tables use snake_case plural names: `users`, `workspaces`, `workspace_members`.
- Columns use snake_case. TypeScript fields exposed to UI may use camelCase, but conversion must happen at the query boundary.

## Database Rules

- Treat migrations as append-only history. Never edit a migration that has been committed unless the repo is still pre-release and the PR says so.
- Every schema change gets a migration and, when useful, a small data backfill or rollback note.
- Prefer explicit SQL over hidden ORM magic for core SaaS data paths.
- Use transactions for multi-step writes.
- Keep `created_at` and `updated_at` as ISO strings or integer milliseconds consistently across the whole project.
- Add indexes for foreign keys and common lookup paths.
- Use `ON DELETE` behavior intentionally. Do not rely on accidental orphan cleanup.

Example query shape:

```ts
export function getWorkspaceBySlug(slug: string): Workspace | null {
  return db
    .prepare("select id, name, slug, created_at from workspaces where slug = ?")
    .get(slug) as Workspace | null;
}
```

## Migration Workflow

1. Update `db/schema.sql` if the project keeps a canonical schema snapshot.
2. Add a timestamped migration under `db/migrations/`.
3. Run the migration locally against a disposable database.
4. Add or update tests for the behavior that depends on the schema.
5. Document manual production steps in the PR body if the migration is not fully automatic.

## Component Patterns

- Keep Server Components responsible for data loading and composition.
- Keep Client Components small and interaction-focused.
- Pass plain serializable props from Server Components to Client Components.
- Use forms with Server Actions for simple mutations before adding client-side mutation libraries.
- Prefer accessible HTML first: labels, buttons, fieldsets, semantic headings, and useful empty states.
- Keep route-level loading and error states in `loading.tsx` and `error.tsx`.

## Auth And Tenancy

- Always scope reads and writes by the current user and workspace.
- Never trust workspace IDs, role names, or prices from the client.
- Centralize authorization checks in server helpers such as `requireUser`, `requireWorkspaceRole`, and `canManageBilling`.
- For multi-tenant tables, include `workspace_id` unless the table is intentionally global.

## Validation And Errors

- Validate all external input with a shared schema library such as Zod.
- Return field-level errors for forms and typed error objects for Server Actions.
- Do not leak raw SQL errors, stack traces, secrets, or provider responses to the client.
- Log enough server context to debug, but never log tokens, password reset links, Stripe secrets, or session cookies.

## Caching And Revalidation

- Assume user-specific SaaS data is dynamic unless explicitly proven cacheable.
- Use `revalidatePath` or `revalidateTag` after mutations.
- Do not cache authorization-dependent data globally.
- Keep marketing pages static where possible.

## Testing Expectations

- Run `pnpm typecheck` and `pnpm lint` before every PR.
- Add unit tests for pure business rules and query helpers.
- Add integration tests for migrations and critical Server Actions.
- Use a temporary SQLite database for tests. Tests must not read or write the developer's real local database.

## What We Do Not Do

- Do not put SQL queries in Client Components. The client is not a data-access layer.
- Do not add an ORM just to avoid writing three SQL statements. SQLite is simple enough to keep explicit.
- Do not create broad abstractions before the second real use case.
- Do not use `useEffect` for initial data loading that can happen in a Server Component.
- Do not silently swallow failed writes. Mutations must return a useful error or throw to an error boundary.
- Do not store money as floating-point numbers. Use integer cents or provider-native amount types.
- Do not mix app setup, business logic, and React rendering in the same file.

## PR Checklist

- The change follows the existing folder structure and naming convention.
- Database changes include migrations and tests or a clear reason tests are not needed.
- Server Actions validate input and enforce authorization server-side.
- Client Components are only used where interactivity requires them.
- `pnpm lint`, `pnpm typecheck`, and relevant tests pass.
