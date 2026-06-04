# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the project instruction source for a greenfield SaaS built with Next.js 15 App Router, TypeScript, Tailwind, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack And Versions

- Next.js 15 App Router with React Server Components by default because server-first rendering keeps data access close to routes and avoids unnecessary client bundles.
- TypeScript in strict mode because SaaS code tends to accumulate edge cases around billing, permissions, and multi-tenant data.
- SQLite for local development and early production. Use `better-sqlite3` for single-node deployments and Turso/libSQL when remote replicas or managed hosting are required.
- Tailwind CSS for styling because component-level utility classes keep small SaaS screens fast to iterate without creating a premature design system.
- Server Actions for mutations that are owned by the app. Use Route Handlers only for webhooks, public APIs, uploads, and integrations that need HTTP semantics.

## Folder Structure

Use this structure unless the user explicitly asks for another layout:

```text
app/
  (marketing)/
  (auth)/
  dashboard/
  api/
components/
  ui/
  forms/
  layouts/
db/
  client.ts
  migrations/
  schema.sql
features/
  billing/
  organizations/
  projects/
  users/
lib/
  auth.ts
  env.ts
  errors.ts
  permissions.ts
  validation.ts
tests/
```

Reasons:
- `app/` owns routing and page composition only.
- `features/` owns domain behavior so billing, organizations, and projects do not leak logic into pages.
- `db/` owns schema, migrations, and the SQLite client.
- `components/ui/` holds generic primitives only. Product-specific components live beside their feature.

## Naming Conventions

- Files and folders use kebab-case: `project-list.tsx`, `create-project-form.tsx`.
- React components use PascalCase exports: `ProjectList`.
- Server actions end with `Action`: `createProjectAction`.
- Database helpers start with a verb: `getProjectById`, `listUserProjects`, `insertAuditEvent`.
- Boolean fields use `is`, `has`, or `can`: `isActive`, `hasPaidPlan`, `canInviteMembers`.
- Table names are plural snake_case: `users`, `organizations`, `project_members`.

## Dev Commands

Prefer these commands and keep package scripts aligned with them:

```bash
npm install
npm run dev
npm run typecheck
npm run lint
npm run test
npm run db:migrate
npm run db:studio
```

If a command is missing, add it before using a one-off command. Repeatable workflows belong in `package.json`.

## Environment Rules

- Read environment variables only from `lib/env.ts`.
- Validate required variables at startup.
- Never read `process.env` inside components, Server Actions, or database modules.
- Use explicit names: `DATABASE_URL`, `AUTH_SECRET`, `APP_URL`, `STRIPE_WEBHOOK_SECRET`.

Reason: central validation makes failed deploys obvious and prevents hidden runtime differences between local and production.

## SQL And Migration Conventions

- Every schema change gets a migration file in `db/migrations/` named `YYYYMMDDHHMM_description.sql`.
- Never edit an applied migration. Add a new migration instead.
- Keep `db/schema.sql` as the current full schema for fresh installs.
- Use explicit foreign keys and indexes. If a query filters by `organization_id`, add an index for it.
- Store timestamps as ISO 8601 text unless the project already uses Unix milliseconds.
- Use `deleted_at` for soft deletes only when restore or audit is required. Otherwise prefer hard deletes with audit events.
- Wrap multi-step writes in a transaction.

Default SaaS tables:

```sql
users(id, email, name, created_at, updated_at)
organizations(id, name, slug, created_at, updated_at)
organization_members(id, organization_id, user_id, role, created_at)
projects(id, organization_id, name, status, created_at, updated_at)
audit_events(id, organization_id, actor_user_id, action, metadata_json, created_at)
```

## Data Access Patterns

- Server Components may call read-only database helpers directly.
- Client Components never import from `db/`.
- Server Actions perform validation, permission checks, mutation, and redirect/cache invalidation in that order.
- Route Handlers validate input at the boundary and return typed JSON envelopes.
- Return plain objects from `db/` helpers. Do not return raw driver-specific rows if the shape is unclear.

Preferred mutation flow:

```text
parse input -> get session -> check permission -> transaction -> revalidatePath -> redirect or return result
```

## Component Patterns

- Use Server Components by default.
- Add `"use client"` only for local state, browser APIs, or event handlers.
- Keep forms split into a Server Component wrapper and a focused Client Component when interactivity is needed.
- Use accessible labels for every input.
- Use `disabled` and pending states on submit buttons.
- Keep loading and empty states near the data they describe.

Reason: this keeps the default path fast, accessible, and easy to reason about.

## Auth And Permissions

- Treat authentication and authorization as separate checks.
- Every organization-scoped query must include `organization_id`.
- Never trust IDs from the client without checking membership.
- Use role strings only from a central union type: `owner`, `admin`, `member`, `viewer`.
- Put permission logic in `lib/permissions.ts`, not inside UI components.

## Error Handling

- Throw typed domain errors for expected failures: validation, not found, forbidden, conflict.
- Log unexpected errors on the server only.
- Show user-safe messages in UI. Do not expose SQL errors, stack traces, or webhook secrets.
- Route Handlers should return `{ "status": "error", "error": { "code": "...", "message": "..." } }`.

## Testing Rules

- Test database helpers with a temporary SQLite database.
- Test permission functions with table-driven cases.
- Test Server Actions around validation, permission failure, and successful mutation.
- Do not snapshot whole pages. Assert visible user outcomes and important branching behavior.

## Anti-Patterns To Avoid

- Do not put business logic in `page.tsx`; pages compose features.
- Do not create a generic repository layer unless two real data stores exist.
- Do not run migrations from request handlers.
- Do not import `better-sqlite3` or Turso clients into Client Components.
- Do not add global state for server data; use server rendering and cache invalidation.
- Do not build a large component library before there are repeated components.
- Do not store money as floating point values. Use integer cents and currency codes.

## Pull Request Expectations

- Keep changes scoped to one feature or bug.
- Include migration files and schema updates in the same PR.
- Mention any new environment variables.
- Include manual test notes for auth, permission, and database paths touched.
- Prefer small, reviewable PRs over broad rewrites.

## Claude Code Behavior

When working in this project:

- Inspect existing scripts before inventing commands.
- Prefer the patterns in this file over generic Next.js advice.
- Ask a clarifying question only when the data model, payment provider, or auth provider is genuinely ambiguous.
- If a requested change touches data ownership, include the organization-scoped permission check.
- If a requested change touches SQLite schema, include a migration and update `db/schema.sql`.
