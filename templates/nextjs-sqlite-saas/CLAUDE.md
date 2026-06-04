# CLAUDE.md - Next.js 15 + SQLite SaaS

This project is a production-oriented SaaS app built with Next.js 15 App Router, TypeScript, and SQLite through either `better-sqlite3` for single-node deployments or Turso/libSQL for hosted edge-friendly deployments.

## Stack & Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript strict mode. Do not introduce `any` unless a third-party boundary is impossible to type cleanly.
- SQLite as the source of truth. Use `better-sqlite3` for local/server deployments and Turso/libSQL only behind the same repository interface.
- Server Actions are allowed for narrow mutations. Route Handlers are preferred for webhook, API, and third-party callback surfaces.
- Styling should use the app's existing design system first. If none exists, use small, composable components and avoid landing-page decoration inside product surfaces.

Reason: this stack is fast when the server/client boundary is kept simple, but it becomes fragile if database calls leak into client components or migrations are treated casually.

## Folder Structure

Use this structure for new code:

```text
app/
  (auth)/
  (dashboard)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  dashboard/
db/
  client.ts
  migrations/
  repositories/
  schema.ts
lib/
  auth/
  billing/
  env.ts
  validators/
server/
  actions/
  services/
tests/
  unit/
  integration/
```

Rules:

- `app/` owns routes, layouts, loading states, and route-level data composition.
- `components/ui/` contains generic presentational primitives only. It must not import from `db/` or `server/`.
- `db/client.ts` creates the SQLite/libSQL connection and nothing else.
- `db/repositories/` contains persistence functions. Repositories return typed records and do not know about React.
- `server/services/` contains business workflows that may call repositories, billing, email, or auth helpers.
- `server/actions/` wraps service calls for forms and server actions.

Reason: clear ownership keeps RSC rendering predictable and prevents the common SaaS failure mode where UI components become hidden database clients.

## Naming Conventions

- Files and folders use kebab-case: `create-organization.ts`, `billing-status-card.tsx`.
- React components use PascalCase exports: `BillingStatusCard`.
- Server actions are named as verbs: `createWorkspaceAction`, `inviteMemberAction`.
- Repository functions are explicit about persistence: `insertWorkspace`, `findUserByEmail`, `listInvoicesForAccount`.
- Boolean columns and variables start with `is`, `has`, or `can`.

Reason: these names make call sites readable and let Claude Code infer intent without asking whether a function mutates state.

## SQL & Migration Conventions

- Every schema change must be a new migration file in `db/migrations/`.
- Migration filenames use ordered timestamps: `202606050900_create_workspaces.sql`.
- Migrations must be forward-only. Do not edit an already-applied migration.
- Prefer explicit constraints: `not null`, `unique`, `check`, and foreign keys with clear delete behavior.
- Store timestamps as ISO 8601 text unless the existing project already uses integer epochs.
- Use transactions for multi-statement writes.
- Never build SQL by string-concatenating user input. Use prepared statements or libSQL parameter binding.

Example:

```sql
create table workspaces (
  id text primary key,
  name text not null,
  slug text not null unique,
  owner_user_id text not null references users(id) on delete cascade,
  created_at text not null
);
```

Reason: SQLite is reliable when constraints are in the database, not only in TypeScript validators.

## Data Access Pattern

Use repositories for raw persistence:

```ts
// db/repositories/workspaces.ts
export function findWorkspaceBySlug(slug: string): Workspace | null {
  return db.prepare("select * from workspaces where slug = ?").get(slug) as Workspace | undefined ?? null;
}
```

Use services for decisions:

```ts
// server/services/workspaces.ts
export async function createWorkspace(input: CreateWorkspaceInput, actor: User) {
  assertCanCreateWorkspace(actor);
  const parsed = createWorkspaceSchema.parse(input);
  return insertWorkspace({ ...parsed, ownerUserId: actor.id });
}
```

Reason: repositories make the database testable; services keep business rules out of route files.

## Component Patterns

- Default to Server Components for pages and data-heavy views.
- Add `"use client"` only for components that need browser state, effects, event handlers, or client-side libraries.
- Keep client components small and pass serializable props from server parents.
- Forms should use server actions for simple mutations and Route Handlers for API-like behavior.
- Use `loading.tsx`, `error.tsx`, and empty states for dashboard routes.

Reason: the App Router performs best when data fetching stays server-side and client islands are intentionally small.

## Dev Commands

Use these commands unless the package manager differs:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
```

If a command is missing, add the smallest useful script to `package.json` rather than documenting a command that does not exist.

Reason: repeatable commands are part of the product's operating surface, not optional polish.

## Validation & Environment

- Put environment parsing in `lib/env.ts`.
- Fail fast at startup for missing required secrets.
- Use Zod or the existing validation library for all form and webhook inputs.
- Redact secrets in logs. Never print API keys, database URLs, session secrets, OAuth tokens, or webhook signing secrets.

Reason: SaaS bugs often come from invalid runtime configuration that fails late under customer traffic.

## Testing Rules

- Repository tests cover SQL constraints and query behavior.
- Service tests cover authorization and business rules.
- Route Handler tests cover webhooks and public API contracts.
- Component tests are useful for complex client interactions, not for static markup snapshots.

Reason: test the boundary where regressions are expensive, not every line.

## What We Do Not Do

- Do not query SQLite from Client Components. It leaks server-only concerns into browser bundles.
- Do not hide writes inside React render paths. Mutations belong in actions, route handlers, or services.
- Do not edit old migrations after they have shipped. Add a new migration.
- Do not use `any` to silence schema drift. Fix the type or add a narrow adapter.
- Do not add a second ORM/query style without removing the first one. Mixed data layers create inconsistent transaction behavior.
- Do not create decorative marketing layouts for dashboard/product workflows. SaaS users need dense, scannable, repeatable interfaces.
- Do not store money as floating-point numbers. Use integer cents or provider-native atomic amounts.

Reason: each prohibition prevents a failure mode that is common in small SaaS codebases and expensive to unwind later.

## Before Opening A PR

- Run lint, typecheck, tests, and migrations against a fresh local SQLite database.
- Include the exact commands and results in the PR body.
- Mention any skipped checks with the reason.
- If the change touches auth, billing, database migrations, or webhooks, describe the rollback plan.

Reason: reviewers need operational confidence, not just a diff.
