# Next.js 15 + SQLite SaaS Instructions

## Project Shape

This is a production-oriented SaaS application built with Next.js 15 App Router, TypeScript, server actions, SQLite, and either `better-sqlite3` for local/server deployments or Turso/libSQL when hosted at the edge.

Prefer boring server-rendered flows. Use client components only for stateful UI that cannot run on the server, because every client boundary increases bundle size, hydration work, and data-leak risk.

## Directory Conventions

- `app/` contains routes, layouts, route handlers, and server actions that are specific to those routes.
- `app/(marketing)/` contains public pages such as pricing, terms, and the landing page.
- `app/(app)/` contains authenticated product screens.
- `app/api/` contains webhook endpoints and integration callbacks only when a route handler is required.
- `components/` contains shared UI that is not tied to one route.
- `components/ui/` contains primitive design-system components.
- `features/<feature>/` contains feature-specific components, schemas, queries, and actions when a feature spans multiple routes.
- `lib/` contains shared server-safe utilities.
- `lib/db/` contains the SQLite connection, migrations, query helpers, and transaction helpers.
- `lib/auth/` contains session, user, and permission helpers.
- `migrations/` contains numbered SQL migration files.
- `tests/` contains integration tests and fixtures.

Keep route folders thin. Move reusable business logic into `features/` or `lib/` so route files stay easy to review and hard to accidentally couple.

## Naming Rules

- Use `PascalCase` for React components.
- Use `camelCase` for functions, variables, and object properties.
- Use `kebab-case` for route segments and file names that are not React components.
- Use `snake_case` for SQLite tables and columns.
- Use `userId`, `organizationId`, and similar names in TypeScript, but map them explicitly to `user_id`, `organization_id`, and similar database columns.
- Prefix server actions with the verb they perform, such as `createProjectAction` or `updateBillingEmailAction`.
- Name query helpers after the data they return, such as `getProjectById` or `listProjectsForUser`.

Use explicit names because Claude Code should be able to infer the owner, data shape, and side effects of a file before opening it.

## Dev Commands

Assume these commands exist. If the package manager differs, adapt only the command prefix.

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:migrate
npm run db:reset
npm run db:studio
```

Before opening a PR, run lint, typecheck, tests, and migrations against a temporary database.

## SQLite Rules

- Put all schema changes in `migrations/`.
- Use timestamped migration names: `YYYYMMDDHHMM_description.sql`.
- Never edit a migration that has already shipped. Add a new migration instead, because SQLite deployments may have already applied the old file.
- Every table must have a primary key.
- Prefer `TEXT` UUID or ULID ids for externally referenced records.
- Use `INTEGER` Unix timestamps or ISO `TEXT` timestamps consistently; do not mix both in the same table family.
- Add foreign keys for ownership and lifecycle relationships.
- Enable foreign keys on every connection with `PRAGMA foreign_keys = ON`.
- Wrap multi-step writes in a transaction.
- Keep raw SQL in query helpers, not inline inside components.
- Validate all user input before it reaches SQL.

SQLite is reliable when the write path is small, explicit, and transactional. Do not hide writes behind generic repository abstractions until repeated patterns prove the abstraction is worth it.

## Data Access Pattern

Use this shape for database files:

```ts
// lib/db/client.ts
export function getDb() {
  // Return a singleton connection for better-sqlite3 or a configured Turso client.
}
```

```ts
// features/projects/project-queries.ts
export async function getProjectById(projectId: string, userId: string) {
  // Fetch by id and ownership in the same query.
}
```

```ts
// features/projects/project-actions.ts
"use server";

export async function createProjectAction(formData: FormData) {
  // Parse input, authorize the user, write in a transaction, then revalidate/redirect.
}
```

Always check tenant ownership in the query, not only in the page. The database call is the last trustworthy boundary before data leaves the server.

## App Router Rules

- Fetch data in server components whenever possible.
- Keep `page.tsx` focused on composition and redirect/not-found decisions.
- Use route-level `loading.tsx` and `error.tsx` for user-facing async states.
- Use `generateMetadata` for public pages and shareable authenticated pages.
- Use `revalidatePath` or `revalidateTag` immediately after writes that affect rendered data.
- Use route handlers for webhooks, OAuth callbacks, file uploads, and third-party integrations.

Do not fetch internal API routes from server components. Call the underlying function directly so errors, types, and auth checks stay visible.

## Authentication And Authorization

- Treat authentication as identity only.
- Treat authorization as a separate check at the feature boundary.
- Every query for user-owned data must include `user_id` or `organization_id`.
- Every server action must obtain the current session server-side.
- Never trust hidden form fields for ownership, price, role, or plan state.
- Keep admin checks in named helpers such as `requireAdmin`.

This separation prevents a logged-in user from becoming accidentally authorized for records they do not own.

## Validation

- Use a schema library such as Zod for form input, webhook payloads, environment variables, and search params.
- Parse at the boundary.
- Return field-level errors for forms.
- Throw or return typed failures for internal service functions.
- Keep validation schemas near the feature that owns the data.

Do not let raw `FormData`, query strings, or webhook JSON flow through the application. Parse once, then pass typed values.

## UI Pattern

- Keep product screens dense, plain, and task-focused.
- Use server-rendered tables for list views before adding custom client-side grids.
- Use modals only for short, reversible actions.
- Use dedicated pages for multi-step workflows.
- Put destructive actions behind a confirmation state and a server-side permission check.

SaaS users scan, compare, and repeat actions. Favor predictable layout over decorative presentation.

## Payment And Billing

- Store billing provider ids in a dedicated billing table.
- Treat webhook events as the source of truth for paid state.
- Make webhook handlers idempotent by storing processed event ids.
- Do not update subscription state only from a client-side redirect.
- Keep price ids and product ids in environment variables or a typed config file.

Billing state affects access. It must be reconstructed from durable provider events, not from optimistic UI.

## Testing Expectations

- Unit test pure utilities and validation schemas.
- Integration test query helpers against a temporary SQLite database.
- Test migrations from an empty database.
- Test at least one complete server action per critical workflow.
- Add regression tests for every bug fix.

Prefer a few tests around real database behavior over many mocks that cannot catch SQL, migration, or transaction failures.

## Anti-Patterns To Avoid

- Do not put database queries in client components.
- Do not expose database ids for records before checking ownership.
- Do not create catch-all `lib/utils.ts` dumping grounds.
- Do not write new schema from server actions without a migration file.
- Do not mutate already-applied migrations.
- Do not use `any` to get around form, database, or webhook types.
- Do not store secrets in the repo, `.env.example`, screenshots, or logs.
- Do not add a new ORM or state library without a concrete local reason.
- Do not split a feature across many top-level folders unless the feature is actually shared.

Each anti-pattern makes Claude Code more likely to apply a broad, unsafe edit. Keep ownership and side effects obvious.

## PR Checklist

- [ ] Route files are thin and feature logic is in `features/` or `lib/`.
- [ ] Server actions validate input, authorize server-side, and revalidate affected routes.
- [ ] Database changes are represented by a new migration.
- [ ] Ownership checks are included in database queries.
- [ ] Lint, typecheck, tests, and migrations pass.
- [ ] No secrets, tokens, personal data, or generated local database files are committed.
