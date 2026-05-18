# CLAUDE.md - Next.js 15 + SQLite SaaS

## Stack And Versions

This project is a production SaaS app built with:

- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode.
- SQLite for local and single-region deployments, using `better-sqlite3`.
- Turso/libSQL only when the app must run on edge or multi-region infrastructure.
- Drizzle ORM for typed queries and migrations.
- Zod for validating all external input before it reaches business logic.
- Server Actions for small form mutations and route handlers for API/webhook boundaries.

Reason: this stack keeps the data model explicit, avoids unnecessary services, and lets Claude make changes without inventing infrastructure the project does not need.

## Dev Commands

Use these commands unless the repository defines a more specific script:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

Before opening a PR, run:

```bash
pnpm lint && pnpm typecheck && pnpm test
```

If a change edits schema or queries, also run:

```bash
pnpm db:generate && pnpm db:migrate
```

Reason: UI-only changes should stay fast, while data changes must prove the schema and generated migration still match.

## Folder Structure

Use this structure for greenfield work:

```text
src/
  app/
    (marketing)/
    (app)/
      dashboard/
      settings/
    api/
      webhooks/
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    schema.ts
    migrations/
    queries/
  features/
    billing/
    organizations/
    projects/
    users/
  lib/
    auth.ts
    env.ts
    errors.ts
    validation.ts
  server/
    actions/
    services/
  tests/
```

Rules:

- Put route files only in `src/app`; do not hide reusable logic inside route folders.
- Put domain behavior in `src/features/<domain>` or `src/server/services`.
- Put reusable SQL access in `src/db/queries`; keep raw SQL close to the data model.
- Put shared presentational components in `src/components/ui`.
- Put feature-specific components inside their feature folder when they are not reused.

Reason: routes stay thin, database code is discoverable, and feature changes do not spread across unrelated folders.

## Naming Conventions

- Components use `PascalCase`: `ProjectSwitcher.tsx`.
- Hooks use camelCase with a `use` prefix: `useProjectMembers.ts`.
- Server actions use verb-first names: `createProjectAction`, `inviteMemberAction`.
- Query helpers describe the record and access pattern: `getProjectBySlug`, `listProjectsForUser`.
- Database tables use plural snake_case: `users`, `organizations`, `project_members`.
- Column names use snake_case and include units when relevant: `created_at`, `quota_bytes`.
- IDs use text UUIDs unless the schema has a strong reason for integer IDs.

Reason: consistent names let Claude infer ownership and avoid creating duplicate helpers.

## SQL And Migration Conventions

Schema changes must follow these rules:

- Never edit an applied migration. Create a new migration instead.
- Every migration must be reversible in practice, even if the tool stores only forward SQL.
- Add nullable columns first, backfill them, then enforce `NOT NULL` in a later migration.
- Add indexes for every foreign key and every frequent lookup path.
- Use foreign keys with explicit `ON DELETE` behavior.
- Store money as integer minor units, never floating point.
- Store timestamps as ISO strings or Unix milliseconds consistently across the whole schema.
- Keep application-level authorization outside SQL, but enforce integrity constraints in SQL.

Preferred Drizzle layout:

```text
src/db/schema.ts
src/db/client.ts
src/db/queries/projects.ts
src/db/queries/users.ts
src/db/migrations/
```

For SQLite:

- Enable WAL mode for server deployments that write locally.
- Keep transactions short.
- Wrap multi-step writes in a transaction.
- Avoid long-running reports on the request path.

For Turso:

- Treat network latency as real. Batch related reads where possible.
- Do not rely on process-local write ordering.
- Keep migrations compatible with libSQL.

Reason: SQLite is reliable when writes are explicit, migrations are additive, and request handlers do not hold locks longer than necessary.

## Server Patterns

Server Components should fetch data directly through query helpers:

```tsx
export default async function Page() {
  const projects = await listProjectsForCurrentUser();
  return <ProjectList projects={projects} />;
}
```

Server Actions should:

- Validate input with Zod.
- Check authentication and authorization inside the action.
- Call a service function for business behavior.
- Return typed success or field errors.
- Revalidate only the paths or tags affected by the mutation.

Route handlers should be used for:

- Webhooks.
- External API clients.
- File uploads.
- Health checks.
- Integrations that need custom status codes or headers.

Reason: App Router works best when reads are simple Server Components and mutations have one clear server boundary.

## Component Patterns

Default to Server Components. Add `"use client"` only when the component needs:

- Local interactive state.
- Browser APIs.
- Event handlers.
- Client-only libraries.

Client components must receive serializable props. They should not import database clients, server actions through indirect barrels, or environment secrets.

Forms should use:

- Native HTML form semantics.
- Server Actions for first-party app mutations.
- Pending and error states.
- Accessible labels and validation messages.

Reason: keeping most components server-side reduces bundle size and prevents accidental secret or database access in the browser.

## Auth And Authorization

Every data access path must answer:

- Who is the current user?
- Which organization or tenant is active?
- What role or permission is required?
- What happens when access is denied?

Do not rely on hidden form fields for authorization. Treat IDs from the client as untrusted lookup hints.

Use service-level guards:

```ts
await requireOrganizationRole(userId, organizationId, "admin");
```

Reason: SaaS bugs usually come from cross-tenant access, not from missing UI checks.

## Environment Variables

Define environment parsing in `src/lib/env.ts` and validate on startup. Do not read `process.env` throughout the app.

Use separate variables for local SQLite and Turso:

```text
DATABASE_URL=file:./local.db
TURSO_DATABASE_URL=
TURSO_AUTH_TOKEN=
```

Secrets must never be prefixed with `NEXT_PUBLIC_`. Public variables need a comment explaining why they are safe for the browser.

Reason: one env module prevents production-only crashes and accidental secret exposure.

## Testing Rules

Write tests at the lowest useful level:

- Query tests for data filtering, tenancy, and migration-sensitive behavior.
- Service tests for permissions and business rules.
- Component tests only for user-visible branching.
- End-to-end tests for signup, billing, onboarding, and core paid workflows.

Use a temporary SQLite database per test file or test worker. Tests must not share a developer's local database.

Reason: SaaS regressions often happen in permissions and persistence; tests should cover those directly.

## Error Handling

- Throw typed domain errors from services.
- Convert domain errors to user-facing messages at the route/action boundary.
- Log unexpected errors with request context, but never log secrets, tokens, session cookies, or full payment payloads.
- Return generic messages for auth failures.

Reason: useful logs and safe user messages require different levels of detail.

## What We Do Not Do

- Do not add a global state library unless a real cross-page client state problem exists. Server state belongs on the server.
- Do not create API routes for data that a Server Component can read directly.
- Do not put business logic in React components.
- Do not use floating point for money, credits, usage, or quotas.
- Do not use string-built SQL. Use Drizzle query APIs or parameterized SQL.
- Do not edit old migrations after they are merged.
- Do not add background job infrastructure for work that can be handled by a short transaction or scheduled script.
- Do not add edge runtime by default. SQLite file access and many Node libraries need the Node runtime.
- Do not expose admin actions through UI-only checks. Enforce permissions on the server.

Reason: each avoided pattern prevents a common SaaS failure mode: bundle bloat, duplicated APIs, data corruption, migration drift, or cross-tenant access.

## PR Checklist For Claude

Before submitting a change:

- Confirm the change fits the folder ownership above.
- Run lint, typecheck, and tests.
- Include a migration for schema changes.
- Add or update tests for authorization, validation, and persistence changes.
- Check that no secret is imported into a client component.
- Keep the PR focused on one feature or fix.

If requirements are ambiguous, make the smallest production-safe assumption and state it in the PR description.
