# CLAUDE.md

This file gives Claude Code the project rules for a Next.js 15 SaaS application backed by SQLite. Follow these instructions before changing code, database schema, tests, or project conventions.

## Project Profile

- Framework: Next.js 15 with the App Router.
- Language: TypeScript.
- Runtime: Prefer server components and server actions for data mutations.
- Database: SQLite for local-first persistence, small deployments, previews, and tests.
- Product shape: Multi-tenant SaaS with authenticated users, organizations, billing-ready domain models, auditability, and predictable migrations.

## Core Commands

Use the package manager already present in the repository. Do not introduce a second lockfile.

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
```

If the project uses `pnpm` or `yarn`, translate commands without changing behavior:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Before opening a PR, run the smallest relevant validation first, then the full validation set when the change touches shared code, schema, authentication, billing, or routing.

## Repository Structure

Prefer this structure unless the repository already has a strong convention:

```text
app/
  (marketing)/
  (auth)/
  dashboard/
  api/
components/
  ui/
  forms/
  layout/
db/
  migrations/
  schema.ts
  client.ts
  queries/
lib/
  auth/
  billing/
  config/
  errors/
  validation/
server/
  actions/
  services/
  jobs/
tests/
  unit/
  integration/
  e2e/
```

Keep route handlers thin. Put business rules in `server/services`, database access in `db/queries`, and reusable validation in `lib/validation`.

## Next.js Rules

- Use server components by default.
- Add `"use client"` only when a component needs browser state, effects, event handlers, or browser-only APIs.
- Do not fetch sensitive data from client components.
- Use route handlers for webhooks, third-party callbacks, and public API endpoints.
- Use server actions for authenticated form submissions and simple mutations.
- Keep metadata, redirects, and access checks close to the route segment they protect.
- Use `revalidatePath`, `revalidateTag`, or cache tags intentionally after mutations.
- Do not rely on client-side authorization checks for protected data.

## TypeScript Rules

- Prefer explicit domain types at module boundaries.
- Avoid `any`. Use `unknown` and narrow it.
- Keep DTOs separate from database rows when API shape differs from storage shape.
- Use discriminated unions for state machines, billing states, job states, and onboarding flows.
- Export types from the module that owns the behavior.
- Avoid global type augmentation unless it is required by a library.

## SQLite Rules

- Use SQLite as a real relational database, not as a JSON dump.
- Enable foreign keys for every connection.
- Keep migrations append-only after they are merged.
- Never edit a migration that may already have run in another environment. Add a new migration instead.
- Prefer explicit indexes for tenant ID, foreign keys, unique constraints, and common dashboard filters.
- Store timestamps as ISO text or integer epoch consistently across the project.
- Keep writes short and transactional.
- Use `BEGIN IMMEDIATE` or the ORM equivalent when a mutation must be serialized.
- Do not perform long network calls inside a database transaction.
- Avoid N+1 query patterns in dashboard routes and list endpoints.

Recommended table conventions:

```text
id              text primary key
organization_id text not null
created_at      text not null
updated_at      text not null
deleted_at      text null
```

Use soft deletes only when the product needs recovery, audit trails, or billing history. Otherwise prefer hard deletes with foreign-key cascades.

## Multi-Tenancy Rules

- Every tenant-owned table must include `organization_id` unless there is a documented reason.
- Every query for tenant-owned data must filter by `organization_id`.
- Never trust organization IDs from client input without checking membership on the server.
- Centralize membership and role checks in `lib/auth` or `server/services`.
- Prefer scoped query helpers such as `getProjectForOrg(orgId, projectId)` over unscoped helpers such as `getProject(projectId)`.

## Authentication And Authorization

- Authentication answers who the user is.
- Authorization answers what the user can do.
- Check both on the server before reading or mutating protected data.
- Use role names that match product behavior, for example `owner`, `admin`, `member`, and `viewer`.
- Do not scatter role string comparisons across routes. Use helper functions such as `canManageBilling(member)` or `canInviteMembers(member)`.
- Treat webhooks as unauthenticated until their signature is verified.

## Billing Rules

- Keep billing provider IDs in dedicated columns.
- Do not derive entitlement only from client state.
- Store the last known subscription status and update it from verified webhooks.
- Make billing state changes idempotent.
- Log enough metadata to reconcile webhook delivery failures.
- Do not delete historical billing records when an account is canceled.

## Server Actions

Use this shape for mutations:

```ts
export async function updateProjectAction(input: unknown) {
  const user = await requireUser()
  const data = updateProjectSchema.parse(input)
  const membership = await requireOrgMembership(user.id, data.organizationId)

  assertCanUpdateProject(membership)

  return updateProject({
    organizationId: data.organizationId,
    projectId: data.projectId,
    name: data.name,
  })
}
```

Rules:

- Validate `unknown` input before use.
- Re-check ownership and permissions on the server.
- Return structured success and error states for forms.
- Keep side effects explicit.
- Revalidate affected routes after successful writes.

## API Route Handlers

Use route handlers for:

- Webhooks.
- Public API endpoints.
- OAuth callbacks.
- File upload callbacks.
- Integrations that need raw request access.

Rules:

- Validate method, headers, body, and authentication.
- Return typed JSON responses.
- Keep handler code small.
- Move reusable logic into services.
- Do not expose stack traces or internal error messages.

## Validation

- Use a schema validator at all external boundaries.
- Validate form input, query params, route params, webhook payloads, and environment variables.
- Keep validation schemas near the feature that owns them unless they are shared across features.
- Use server-side validation even when client-side validation exists.

## Environment Variables

- Read environment variables through a central config module.
- Validate required variables at startup or first use.
- Do not access `process.env` throughout the codebase.
- Do not commit secrets.
- Keep `.env.example` updated when adding a variable.

Example:

```ts
export const config = {
  databaseUrl: requiredEnv("DATABASE_URL"),
  appUrl: requiredEnv("NEXT_PUBLIC_APP_URL"),
}
```

Only expose variables with `NEXT_PUBLIC_` when they are safe to send to the browser.

## Error Handling

- Use typed application errors for expected failures.
- Log unexpected failures on the server.
- Show user-safe messages in the UI.
- Avoid throwing raw database or provider errors into client responses.
- Include enough context in logs to debug tenant, user, and request scope without logging secrets.

## Testing Rules

Prioritize tests in this order:

1. Validation and permission helpers.
2. Database query helpers.
3. Server actions and route handlers.
4. Critical UI states.
5. End-to-end happy paths for signup, onboarding, billing, and core product workflows.

For SQLite tests:

- Use an isolated temporary database per test file or test worker.
- Run migrations before integration tests.
- Seed only the data needed by the test.
- Clean up databases after tests.
- Test tenant isolation explicitly.

## UI Rules

- Keep forms accessible and keyboard usable.
- Show loading, empty, error, and success states.
- Use server-rendered data for initial dashboard views when possible.
- Use optimistic UI only when rollback behavior is clear.
- Avoid placing authorization logic only in UI components.
- Keep reusable UI primitives separate from product-specific components.

## Naming Conventions

- Database tables: plural snake_case, for example `organizations`, `project_members`.
- TypeScript files: kebab-case or existing repo convention.
- React components: PascalCase.
- Server actions: verb-first names ending in `Action`.
- Query helpers: verb-first names such as `getProjectForOrg`, `listInvoicesForOrg`.
- Migrations: ordered prefix plus short description, for example `0004_add_project_members.sql`.

## Common Patterns

Tenant-scoped query:

```ts
export async function getProjectForOrg(organizationId: string, projectId: string) {
  return db.query.projects.findFirst({
    where: and(
      eq(projects.id, projectId),
      eq(projects.organizationId, organizationId)
    ),
  })
}
```

Idempotent webhook handling:

```ts
export async function handleBillingEvent(event: BillingEvent) {
  const existing = await findWebhookEvent(event.id)
  if (existing) return

  await transaction(async (tx) => {
    await recordWebhookEvent(tx, event)
    await applyBillingEvent(tx, event)
  })
}
```

## Anti-Patterns

- Adding `"use client"` to a whole page because one child component needs interactivity.
- Reading tenant-owned records without filtering by `organization_id`.
- Updating historical migrations.
- Storing secrets in client-visible environment variables.
- Performing provider API calls inside database transactions.
- Swallowing errors with empty `catch` blocks.
- Returning raw database rows from public APIs when they include internal columns.
- Adding a new ORM, auth provider, state library, or UI framework without a clear project-level reason.

## Pull Request Checklist

Before submitting:

- Run linting and type checks.
- Run affected tests.
- Add or update migrations when schema changes.
- Update `.env.example` for new configuration.
- Update docs for new commands, setup steps, or feature behavior.
- Confirm tenant isolation and authorization for protected changes.
- Keep the PR focused on one issue.

## When Unsure

- Prefer a small, reversible change.
- Follow existing repository conventions.
- Ask for clarification before changing schema, auth, billing, or public API behavior.
- Document assumptions in the PR description.
