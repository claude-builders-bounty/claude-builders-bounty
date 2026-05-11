# CLAUDE.md

Guidance for Claude Code when working on this Next.js 15 App Router + SQLite SaaS project.

## Stack And Versions

- Next.js 15 with the App Router.
- React Server Components by default.
- TypeScript in strict mode.
- SQLite through `better-sqlite3` for local/self-hosted apps or Turso/libSQL for hosted edge-friendly deployments.
- Tailwind CSS for styling.
- Zod for request, form, and environment validation.
- Vitest for unit tests and Playwright for browser-level workflows.

Reason: this stack keeps the app deployable as a small SaaS without introducing a separate API server, ORM layer, or distributed database before the product needs it.

## Dev Commands

Use these commands unless the local `package.json` says otherwise:

```bash
npm run dev        # start local Next.js dev server
npm run lint       # lint and static checks
npm run typecheck  # TypeScript validation
npm run test       # unit tests
npm run db:migrate # apply pending SQLite migrations
npm run db:studio  # optional DB browser, if configured
```

If a command is missing, add it to `package.json` instead of inventing one-off shell commands in documentation.

## Project Structure

```text
app/
  (marketing)/              # public pages: landing, pricing, docs
  (app)/                    # authenticated product area
  api/                      # route handlers only for webhooks or third-party callbacks
  actions/                  # server actions grouped by domain
components/
  ui/                       # reusable primitives: Button, Input, Dialog
  forms/                    # form components with validation wiring
  domain/                   # feature-specific UI
db/
  client.ts                 # SQLite connection factory
  schema.sql                # current schema snapshot
  migrations/               # ordered SQL migration files
lib/
  auth/                     # session, current-user, permissions
  config/                   # environment parsing
  validation/               # shared Zod schemas
  services/                 # server-only domain operations
tests/
  unit/
  e2e/
```

Reason: App Router code can blur UI, data access, and side effects. This layout keeps database writes in predictable places and keeps route handlers from becoming a second application.

## Naming Conventions

- Components use `PascalCase.tsx`.
- Server actions use `verbNounAction`, for example `createWorkspaceAction`.
- Service functions use plain verbs, for example `createWorkspace`.
- Database migrations use `YYYYMMDDHHMM_description.sql`.
- Tables use plural snake_case: `users`, `workspaces`, `workspace_members`.
- Columns use snake_case: `created_at`, `owner_id`, `billing_status`.
- TypeScript types use app language, not database language: `WorkspaceMember`, not `workspace_members`.

Reason: database names should be stable and SQL-friendly, while TypeScript names should stay readable in application code.

## Database Rules

- Every schema change must be a new SQL file in `db/migrations/`.
- Never edit an already-applied migration.
- Keep `db/schema.sql` updated after adding a migration.
- Wrap multi-step writes in a transaction.
- Add indexes in the same migration as the query pattern that needs them.
- Store timestamps as ISO 8601 text or integer epoch milliseconds; choose one in the first migration and stay consistent.
- Use foreign keys and enable `PRAGMA foreign_keys = ON` when opening a SQLite connection.
- Prefer explicit column lists over `SELECT *`.

Reason: SQLite is simple and reliable when migrations are append-only and query patterns are intentional.

## Data Access Pattern

Use this flow:

1. UI calls a server action or server component.
2. Server action validates input with Zod.
3. Server action calls a service function.
4. Service function performs database reads/writes.
5. UI receives a typed result or redirects.

Do not query SQLite directly from React components unless the component is a server component whose only job is to render read-only data.

Reason: validation, permissions, and transactions need one obvious home.

## Server Actions

- Put actions in `app/actions/<domain>.ts` or beside a tightly scoped route segment.
- Start action files with `"use server"`.
- Validate all external input with Zod.
- Check authorization inside the action or service, never only in the UI.
- Return serializable objects. Do not return database handles, class instances, or raw errors.
- Use `revalidatePath` or `revalidateTag` after writes that affect cached UI.

Reason: server actions are part of the public mutation surface of the app.

## Route Handlers

Use `app/api/**/route.ts` only for:

- Webhooks
- OAuth callbacks
- Third-party integrations
- Public machine-readable endpoints

Do not create internal REST endpoints just so client components can mutate app state. Use server actions for first-party UI mutations.

Reason: internal APIs add auth, validation, and cache behavior duplication.

## Component Patterns

- Prefer server components for data fetching and static layout.
- Use client components only for interactivity: forms, menus, dialogs, optimistic UI, charts, and browser APIs.
- Keep client components small and pass them already-shaped data.
- Put shared primitives in `components/ui`.
- Put business-specific components in `components/domain/<feature>`.
- Keep forms accessible: labels, errors, pending state, and disabled submit state.

Reason: small client islands preserve App Router performance and make database-backed pages easier to reason about.

## Auth And Permissions

- Centralize `getCurrentUser()` and `requireUser()` in `lib/auth`.
- Never trust `user_id` from form data or search params.
- Derive tenant/workspace access from the session and membership tables.
- Check permissions in services before writes.
- For multi-tenant data, every query must scope by `workspace_id` or another tenant boundary.

Reason: SaaS bugs are often authorization bugs disguised as ordinary query bugs.

## Environment Variables

- Define environment schema in `lib/config/env.ts`.
- Validate env vars at startup with Zod.
- Prefix browser-exposed variables with `NEXT_PUBLIC_`.
- Never read `process.env` throughout the app; import the parsed config.

Reason: scattered environment access makes deployment failures late and confusing.

## Error Handling

- Show safe user-facing messages.
- Log detailed server errors on the server only.
- Do not expose SQL errors, stack traces, tokens, paths, or internal IDs in UI responses.
- Use typed result objects for expected failures: validation, not found, unauthorized, conflict.
- Throw only for unexpected failures.

Reason: expected failures are product states, not crashes.

## Testing Rules

- Add unit tests for services that contain permissions, billing, or non-trivial SQL.
- Add one Playwright test for each critical user workflow.
- Migration tests should apply migrations to an empty temporary SQLite database.
- Test both allowed and denied permission paths.

Reason: SaaS regressions usually appear in permissions, payments, and migrations before they appear in isolated components.

## What We Do Not Do

- Do not add Prisma by default. Reason: raw SQL migrations are simpler for SQLite and avoid an unnecessary abstraction until schema complexity justifies it.
- Do not put secrets in `.env.example`. Reason: examples should show names and safe placeholders only.
- Do not use API routes for first-party form submissions. Reason: server actions are the App Router-native mutation path.
- Do not create client components for pages that only read data. Reason: it moves data fetching to the browser and creates avoidable loading states.
- Do not edit old migrations. Reason: deployed databases cannot replay changed history safely.
- Do not make every component generic. Reason: SaaS UI evolves faster when feature components are allowed to express the domain.
- Do not skip authorization checks because a route is hidden in the UI. Reason: hidden links are not security boundaries.

## Before Making A Change

1. Identify whether the change touches UI, data, permissions, or migrations.
2. Read the nearest route segment, service, and migration before editing.
3. Prefer the smallest change that preserves the structure above.
4. Run typecheck and the narrowest relevant tests.
5. Update migrations, schema snapshot, and tests together when the database changes.

## When Unsure

Choose boring, explicit code over clever abstraction. This project optimizes for a small team shipping a maintainable SaaS, not for framework experimentation.
