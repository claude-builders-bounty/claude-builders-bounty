# Next.js 15 + SQLite SaaS Project Guide

Use this file as the default Claude Code context for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, SQLite, Drizzle ORM, and Tailwind CSS. The goal is a small, production-shaped codebase that can move to Turso/libSQL later without changing application boundaries.

## Stack And Versions

- Runtime: Node.js 22 LTS.
- Framework: Next.js 15 with the App Router, React Server Components by default, Server Actions for mutations, and Route Handlers only for external HTTP integrations.
- Language: TypeScript with `strict: true`.
- Database: SQLite in local development, Turso/libSQL-compatible schema choices in production.
- ORM: Drizzle ORM with checked-in SQL migrations.
- Auth: Better Auth or Auth.js, isolated behind `src/auth`.
- Styling: Tailwind CSS plus a small local component layer in `src/components/ui`.
- Validation: Zod at all request, action, and form boundaries.
- Tests: Vitest for domain and data-access tests, Playwright for the highest-value user flows.

Prefer boring, explicit dependencies. Do not add state managers, server frameworks, UI kits, queues, or RPC layers until a real feature needs them.

## Dev Commands

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

If a command is missing, add it to `package.json` before using it in documentation or scripts. Keep commands deterministic and runnable on a fresh clone.

## Folder Structure

```text
src/
  app/
    (marketing)/
    (app)/
    api/
  auth/
  components/
    ui/
    feature/
  db/
    client.ts
    schema.ts
    migrations/
  features/
    billing/
    organizations/
    projects/
  lib/
  server/
  tests/
```

Use route groups to separate public marketing pages from authenticated app pages. Keep feature code in `src/features/<feature>` and expose small server-facing functions from each feature instead of importing across deep paths.

The `src/app` tree should coordinate routing, layouts, loading states, and metadata. Business rules belong in `src/features` or `src/server`, not inside page components.

## Naming Conventions

- Files and folders use kebab-case: `invite-member-form.tsx`.
- React components use PascalCase exports: `InviteMemberForm`.
- Server Actions end with `.action.ts`.
- Database query modules end with `.queries.ts`.
- Validation schemas end with `.schema.ts`.
- Tests live next to the unit under test as `*.test.ts`, except Playwright specs in `src/tests/e2e`.
- Environment variables use descriptive uppercase names and are parsed once in `src/lib/env.ts`.

Names should describe business meaning, not implementation details. Prefer `organizationMemberships` over `userOrgJoinRows`.

## Server And Client Component Rules

Start with Server Components. Add `"use client"` only when the component needs browser state, effects, refs, event handlers, or client-only APIs.

Data fetching belongs in Server Components or server-only query functions. Client Components receive already-shaped props and call Server Actions for mutations. Never pass raw database rows into broad UI trees when a smaller view model will do.

Use Suspense around slow panels, not around entire pages. Keep loading states stable in size so navigation does not jump.

## Data Access Rules

All database access goes through `src/db/client.ts` and feature-level query modules. Pages, components, and Server Actions do not construct SQL directly.

Use transactions for multi-step writes:

```ts
await db.transaction(async (tx) => {
  await createOrganization(tx, input)
  await createAuditEvent(tx, event)
})
```

Return typed domain results from query modules. Avoid leaking ORM internals outside the feature boundary.

## SQL And Migration Conventions

Migrations are append-only after they have been shared. Do not edit an applied migration; create a new migration that moves the schema forward.

Every table must include:

- `id` as a stable text primary key.
- `createdAt` and `updatedAt` timestamps.
- Foreign keys where SQLite can enforce them.
- Indexes for every user-facing lookup and foreign-key traversal.

Use integer cents for money, ISO currency codes for currency, and text timestamps or integer epoch milliseconds consistently across the schema. Do not store floats for financial amounts.

SQLite-specific constraints matter. Enable foreign keys in the database client. Avoid migrations that require long exclusive locks when a simple additive migration will work.

## Server Actions

Server Actions are the write boundary for form submissions and app mutations. Each action must:

- Validate input with Zod.
- Check authentication and authorization before writing.
- Call feature services or query modules rather than inline database logic.
- Return a typed success/error object suitable for the form.
- Revalidate the smallest useful path or tag.

Do not trust hidden form fields for ownership, pricing, role, or billing state. Read sensitive state from the database.

## Auth And Authorization

Authentication answers "who is this?" Authorization answers "can they do this here?" Keep both checks visible near the mutation or read.

Use membership and role checks at feature boundaries. Never rely only on route protection middleware for data access. Middleware can redirect unauthenticated users, but server-side queries must still enforce tenant scoping.

Every multi-tenant query must include the organization or workspace scope. If a query cannot explain its tenant boundary, it is not ready.

## Component Patterns

Build small, composable feature components. A page should read like a product flow:

```tsx
export default async function ProjectsPage() {
  const projects = await listProjectsForCurrentUser()

  return (
    <PageShell>
      <ProjectToolbar />
      <ProjectTable projects={projects} />
    </PageShell>
  )
}
```

Use local UI primitives for buttons, inputs, dialogs, tables, and menus. Keep styling close to the component unless repeated behavior justifies a shared abstraction.

Forms should have clear pending, success, empty, validation-error, and unexpected-error states. Use accessible labels and keyboard-friendly controls.

## Error Handling

Expected errors return typed results. Unexpected errors are logged server-side and shown to users as short, non-technical messages.

Do not swallow errors in background work or Server Actions. If the user cannot recover, log enough context to debug without storing secrets.

## Testing Expectations

Write tests around business rules, authorization checks, migration-sensitive query behavior, and expensive regressions. Avoid snapshot tests for broad UI trees.

For each new feature, include at least:

- One unit test for the core rule.
- One data-access test if SQL changed.
- One Playwright path if the feature changes onboarding, billing, auth, or checkout.

Tests should use disposable SQLite databases. Do not point tests at development or production databases.

## What We Do Not Do

- Do not put business logic in React components. It makes authorization and testing weaker.
- Do not use raw SQL from pages or Client Components. It breaks the data boundary.
- Do not edit old migrations after they are shared. It breaks existing environments.
- Do not add global state for server data. Server Components and focused Client Components cover most needs.
- Do not create generic abstractions before the third real use. Premature layers hide product behavior.
- Do not store secrets, tokens, or provider responses in logs.
- Do not use `any` to quiet TypeScript. Fix the type at the boundary.
- Do not skip tenant filters, even in admin screens.

## Before Opening A PR

Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, and any relevant Playwright spec. Include migration notes, environment variable changes, and screenshots for UI changes in the PR body.

If a task changes schema, auth, billing, or tenant boundaries, describe the rollback plan. If no rollback is possible, say so clearly.
