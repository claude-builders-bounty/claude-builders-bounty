# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the root `CLAUDE.md` for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite through either `better-sqlite3` for local-first deployments or Turso/libSQL for hosted edge-friendly deployments.

## Stack & Versions

- Next.js 15 App Router with TypeScript strict mode. Reason: App Router keeps routing, data loading, and mutations colocated while strict types catch schema and form drift early.
- React 19 Server Components by default, Client Components only for browser state. Reason: most SaaS screens are data views and forms, so server rendering reduces bundle size and avoids duplicated fetching.
- SQLite as the source of truth, using `better-sqlite3` in Node runtimes or `@libsql/client` for Turso. Reason: both support SQL-first development and small operational overhead.
- Zod for boundary validation. Reason: request bodies, search params, env vars, and webhook payloads must be checked at runtime even when TypeScript compiles.
- Vitest for unit tests and Playwright for critical flows. Reason: fast unit coverage catches domain rules, while one or two browser flows protect auth, billing, and onboarding.

## Folder Structure

```text
app/
  (marketing)/
  (auth)/
  (dashboard)/
    layout.tsx
    page.tsx
    settings/
      page.tsx
      actions.ts
  api/
    webhooks/
      stripe/route.ts
components/
  ui/
  forms/
db/
  client.ts
  migrations/
    0001_initial.sql
  schema.ts
lib/
  auth/
  env.ts
  ids.ts
  permissions.ts
server/
  organizations/
    queries.ts
    mutations.ts
    validators.ts
tests/
  unit/
  e2e/
```

- Put route files under `app/` and business logic under `server/<domain>/`. Reason: route handlers should stay thin and domain code must be testable without rendering a page.
- Keep reusable visual primitives in `components/ui/` and product-specific forms in `components/forms/`. Reason: UI primitives should not import database or auth code.
- Keep `db/client.ts`, `db/schema.ts`, and SQL migrations in `db/`. Reason: database ownership is visible and migrations stay reviewable.
- Group authenticated product routes under `app/(dashboard)/`. Reason: layouts, auth guards, and navigation stay consistent across the SaaS surface.

## Naming Conventions

- Use kebab-case for route segments and file-system URLs, such as `team-members/page.tsx`. Reason: URLs are user-visible and should be stable and readable.
- Use PascalCase for React components and camelCase for functions, variables, and server actions. Reason: this matches TypeScript and React conventions.
- Name server actions with verb-first names such as `updateOrganizationName` or `inviteTeamMember`. Reason: action names should describe the mutation being authorized.
- Name SQL migrations as `NNNN_short_description.sql`. Reason: lexical order must match execution order in every environment.
- Use domain IDs with explicit prefixes, such as `org_`, `usr_`, and `inv_`. Reason: prefixed IDs make logs, support tickets, and foreign-key mistakes easier to diagnose.

## Dev Commands

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run test:e2e
npm run db:migrate
npm run db:studio
```

- Prefer `npm run typecheck` before opening a PR. Reason: Next.js build can hide unrelated work behind bundling noise, while typecheck points directly at contract drift.
- Run `npm run db:migrate` after pulling migrations. Reason: local schema must match the code before debugging application behavior.
- Add missing scripts to `package.json` instead of running one-off commands. Reason: Claude and humans need the same reproducible command surface.

## SQL / Migration Conventions

- Migrations are forward-only SQL files in `db/migrations/`. Reason: production rollback is handled by restoring data and shipping a corrective migration, not by guessing how to reverse data loss.
- Every migration must be safe to run exactly once and wrapped in a transaction when SQLite supports the statements. Reason: half-applied schema changes create hard-to-debug local and deployed states.
- Never change an already-merged migration. Reason: deployed databases have already executed it, so edits create environment drift.
- Use `created_at`, `updated_at`, and soft-delete columns for customer-owned records. Reason: auditability and recovery matter more than saving a few bytes.
- Enforce important invariants with SQL constraints, not only application checks. Reason: imports, scripts, and future routes can bypass a single form validator.
- For destructive changes, add the new column/table first, backfill, switch reads and writes, then remove old data in a later migration. Reason: multi-step changes reduce deploy risk.
- Keep SQL readable and explicit. Reason: SQLite is the source of truth and reviewers must be able to understand indexes, joins, and constraints without generated noise.

## Component Patterns

- Default to Server Components for pages and data-heavy sections. Reason: server components can read from the database directly and keep secrets out of the client bundle.
- Use Client Components only for interactivity such as menus, optimistic form state, charts, and drag/drop. Reason: client code has higher bundle and hydration cost.
- Put server actions next to the route that owns the form in `actions.ts`. Reason: locality keeps validation, authorization, and cache invalidation easy to review.
- Validate form input with Zod before calling mutations. Reason: HTML constraints and TypeScript do not protect server boundaries.
- Return typed action results instead of throwing for expected validation errors. Reason: forms need stable field-level feedback.
- Use `revalidatePath` or `revalidateTag` immediately after successful mutations. Reason: App Router caches can otherwise show stale SaaS data.
- Keep loading, empty, and error states in the route segment. Reason: SaaS users need predictable recovery paths for every operational screen.

## Server & Data Patterns

- Put all database reads in `server/<domain>/queries.ts` and writes in `server/<domain>/mutations.ts`. Reason: separating reads from writes makes authorization and tests simpler.
- Check authorization inside every mutation and sensitive query. Reason: route-level guards are useful but not sufficient when code is reused.
- Read environment variables only through `lib/env.ts`. Reason: a single parser gives clear startup failures and prevents optional secret drift.
- Use parameterized SQL for all user input. Reason: string-built SQL turns form fields and search params into injection risk.
- Prefer small transaction-scoped mutations. Reason: SaaS writes often touch memberships, audit logs, and billing state together.
- Add an audit log row for organization, billing, membership, and permission changes. Reason: operators need to answer who changed what and when.

## Testing Rules

- Unit test domain validators, permission checks, and SQL row mapping. Reason: these fail more often than static page rendering.
- Add at least one Playwright flow for sign-in, organization creation, and the primary paid workflow. Reason: these flows carry the highest business risk.
- For every migration, test a database created from an empty state and a database upgraded from the previous migration. Reason: both new installs and existing customers must work.
- Mock external services at the boundary. Reason: tests should verify webhook and email handling without depending on Stripe, Resend, or Slack availability.

## What We Do Not Do

- Do not put database calls in Client Components. Reason: secrets and database clients must never enter the browser bundle.
- Do not hide mutations inside generic utility functions. Reason: authorization, validation, and cache invalidation must be visible at the call site.
- Do not use an ORM unless the project owner explicitly chooses one. Reason: this template is SQL-first so migrations and constraints stay transparent.
- Do not build a global service locator. Reason: simple imports are easier for Claude and maintainers to trace.
- Do not add API routes for forms that can use server actions. Reason: server actions reduce duplicated validation and keep form behavior colocated.
- Do not skip empty states. Reason: new SaaS accounts start empty and blank screens look broken.
- Do not add decorative dashboard UI that hides core tables, forms, and status. Reason: SaaS users need dense, scannable operational screens.

## PR Checklist

- The change has a clear route, domain module, or migration owner.
- New server input is validated with Zod.
- New database access uses parameterized SQL.
- Mutations check authorization and revalidate affected routes.
- Migrations are new files and were not edited after merge.
- Tests cover the domain rule or user flow most likely to break.
