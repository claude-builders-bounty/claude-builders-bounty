# CLAUDE.md - Next.js 15 App Router + SQLite SaaS

## Stack & Versions

- Next.js 15 with App Router only. Use `app/` routes, layouts, route handlers, and server actions.
- React Server Components are the default. Add `"use client"` only for browser-only state, effects, event handlers, or DOM APIs.
- TypeScript is strict. Prefer explicit domain types over broad `any` and avoid weakening compiler checks to make a change pass.
- SQLite is the source of truth through `better-sqlite3` for local/server deployments or Turso/libSQL for hosted SQLite. Keep the SQL shape portable between both.
- Styling can use Tailwind or CSS modules, but UI primitives must stay framework-light unless the project already has a component library.

Reason: this stack is strongest when server-rendered data access, simple SQL, and small deployable units stay close together.

## Folder Structure

```text
app/
  (marketing)/
  (app)/
  api/
  layout.tsx
components/
  ui/
  forms/
db/
  client.ts
  migrations/
  queries/
lib/
  auth/
  billing/
  validation/
server/
  actions/
  services/
tests/
```

- Put route-specific UI inside the route folder when it is not reused elsewhere.
- Put shared presentational components in `components/`.
- Put database connection setup in `db/client.ts`; do not open SQLite connections from components.
- Put raw SQL in `db/queries/` or narrowly scoped service modules, not inline across route files.
- Put mutations in server actions or route handlers; keep read-only page loading in server components.

Reason: clear boundaries let Claude Code edit a page, a service, or a query without guessing where business rules live.

## Naming Conventions

- Route folders use kebab-case: `app/(app)/team-settings/page.tsx`.
- React components use PascalCase: `TeamSettingsForm.tsx`.
- Server actions use verb-first names: `createWorkspace`, `updateSubscription`, `deleteInvite`.
- SQL migration files use sortable timestamps: `202605161200_create_workspaces.sql`.
- Database tables use plural snake_case: `workspaces`, `workspace_members`, `billing_events`.
- TypeScript domain types use singular PascalCase: `Workspace`, `WorkspaceMember`.

Reason: names should show whether a file is UI, database, or business logic before it is opened.

## SQL & Migration Conventions

- Every schema change gets a migration file in `db/migrations/`.
- Migrations must be append-only after merge. Create a new migration instead of editing an applied one.
- Prefer explicit constraints: `not null`, `unique`, `check`, and foreign keys with intentional `on delete` behavior.
- Store timestamps as ISO 8601 text unless the project already standardizes on integer epoch time.
- Use transactions for multi-step writes.
- Keep migration SQL compatible with SQLite. Do not use PostgreSQL-only syntax.
- Add indexes for common lookup paths such as `user_id`, `workspace_id`, `email`, and external provider IDs.

Reason: SQLite stays reliable when schema evolution is boring, explicit, and reversible by review.

## Data Access Patterns

- Validate all external input with a schema before it reaches a query.
- Use parameterized statements only. Never build SQL by concatenating user input.
- Return plain objects from query functions. Do not leak database driver rows across the app.
- Keep query functions small and named by intent, for example `getWorkspaceBySlug` or `listInvoicesForWorkspace`.
- Handle empty states explicitly. A missing row is not an exception unless the caller requires it.

Reason: server components make data access easy, so the project needs conventions that prevent easy mistakes.

## Component Patterns

- Server components fetch data and compose layout.
- Client components own interactions only: form state, optimistic UI, menus, modals, drag/drop, or browser APIs.
- Forms should call server actions through a small wrapper that validates input and returns typed field errors.
- Keep loading and error UI colocated with the route using `loading.tsx` and `error.tsx` where useful.
- Prefer accessible HTML first. Add custom widgets only when native controls cannot represent the workflow.

Reason: minimizing client components keeps SaaS pages fast and reduces hydration bugs.

## Dev Commands

Use these defaults unless the project package manager says otherwise:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
```

Database commands should be explicit in `package.json`, for example:

```bash
npm run db:migrate
npm run db:seed
npm run db:reset
```

Reason: Claude Code should run the narrowest verification command that proves the changed area works.

## Patterns To Follow

- Add a migration, query function, server action, and UI change as separate reviewable steps.
- Keep auth and billing checks in server-side code paths.
- Prefer small route handlers over catch-all API files.
- Use environment variables through one typed config module.
- Include the exact command run for verification in the final response or PR body.

Reason: SaaS bugs usually come from cross-boundary assumptions, not from a single isolated line.

## Anti-Patterns To Avoid

- Do not put secrets in `NEXT_PUBLIC_*`; those are browser-visible.
- Do not call SQLite directly from client components.
- Do not introduce a second ORM or query builder unless the project already uses it.
- Do not edit old migrations that may already be applied.
- Do not make every component a client component.
- Do not silently swallow database errors; convert them to user-safe messages at the boundary.
- Do not create broad shared helpers before there are at least two real call sites.

Reason: these shortcuts make the first change faster and every later SaaS change riskier.

## Claude Code Operating Rules

- Before editing, inspect the route, service, query, and migration patterns already present.
- Keep changes scoped to the requested feature or bug.
- If a change touches data shape, update migration, query types, validation, and UI states together.
- If tests are missing, add the smallest useful test around the changed behavior.
- If a requirement is ambiguous, make the safest server-side assumption and state it in the final response.

Reason: this file is meant to make Claude Code decisive without making it reckless.
