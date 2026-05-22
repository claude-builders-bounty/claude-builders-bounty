# CLAUDE.md

This project is a greenfield SaaS app built with Next.js 15 App Router, TypeScript, React Server Components, Tailwind CSS, Zod, and SQLite through `better-sqlite3` for local/single-node deploys or Turso/libSQL for hosted edge-adjacent deploys.

## Stack & Versions

- Use Next.js 15 App Router with TypeScript strict mode because route handlers, server actions, and server components need compile-time contracts before data reaches SQLite.
- Use React Server Components by default because most SaaS screens read account data and should not ship client JavaScript until interaction is required.
- Use SQLite with `better-sqlite3` for synchronous server-only access in Node runtime; use Turso/libSQL only behind the same repository interface so deploy targets do not leak into features.
- Use Zod at every external boundary because route params, form data, webhooks, and environment variables are untrusted input.
- Use Tailwind plus small colocated components because this template optimizes for SaaS CRUD speed, not a large design-system package.

## Folder Structure

```text
src/
  app/
    (marketing)/page.tsx
    (app)/dashboard/page.tsx
    (app)/settings/page.tsx
    api/
      webhooks/stripe/route.ts
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    migrations/
    schema.sql
    repositories/
      accounts.ts
      users.ts
      subscriptions.ts
  features/
    billing/
    onboarding/
    teams/
  lib/
    auth.ts
    env.ts
    ids.ts
    result.ts
  server/
    actions/
    queries/
  tests/
    unit/
    integration/
```

Keep route files thin. Put business rules in `features/*`, database access in `db/repositories/*`, and reusable server-only helpers in `server/*` or `lib/*`. This keeps App Router file conventions from becoming the domain model.

## Naming Conventions

- Use `PascalCase` for React components, `camelCase` for functions, `SCREAMING_SNAKE_CASE` for environment variable constants, and `snake_case` for SQLite table and column names.
- Name server actions as verb phrases such as `createTeamAction` because they mutate state and need to stand out from queries.
- Name read functions as nouns with `get` or `list`, such as `getCurrentUser` and `listInvoicesForAccount`, because server components should read like data requirements.
- Name migration files `YYYYMMDDHHMM_description.sql` because SQLite migrations need deterministic order without relying on filesystem creation time.
- Name repository files after aggregates, not tables, because one user-facing operation may touch multiple tables in a transaction.

## Dev Commands

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:studio
```

Do not add a command unless it is used in CI or by a documented local workflow. Extra scripts become stale faster than code.

## SQL & Migration Conventions

- Every schema change must be a checked-in SQL migration under `src/db/migrations`; never mutate `schema.sql` without a migration because deployed SQLite files need a replayable history.
- Each migration must be forward-only and idempotent where SQLite allows it, using `IF NOT EXISTS` for tables and indexes because local preview databases are frequently recreated.
- Use explicit foreign keys, `not null`, and `check` constraints because SQLite will otherwise accept invalid SaaS state that TypeScript cannot see.
- Prefer integer timestamps in milliseconds named `created_at`, `updated_at`, and `deleted_at` because they sort naturally and avoid timezone parsing in SQL.
- Wrap multi-row writes in transactions in repository functions because partial account setup or billing updates are worse than a rejected request.
- Never build SQL with string concatenation. Use bound parameters because SaaS inputs are attacker-controlled by default.

## Database Access Rules

- Only files under `src/db/repositories/*` may import the database client. This keeps queries auditable and avoids accidental client bundle imports.
- Repository functions return plain objects, not `Response`, JSX, or framework types, because data access should be testable without Next.js.
- Server actions call repositories and then `revalidatePath` or `redirect`; repositories never call App Router APIs because persistence should not know about rendering.
- Use soft deletes for user-owned SaaS records unless legal or billing rules require hard deletion, because audit trails matter for support.
- Add indexes in the same migration as the query pattern that needs them because SQLite performance cliffs are easy to miss in small local datasets.

## Component Patterns

- Make pages and layouts server components unless they need browser state, event handlers, or effects. This keeps auth and database reads on the server.
- Put interactive islands behind a small `"use client"` component and pass serialized props only. Do not pass database rows with extra fields into client components.
- Keep form components dumb: collect input, show validation, and call one server action. Business logic belongs in the action or feature service.
- Prefer composition over global providers. Add a provider only when several distant client islands need the same live browser state.
- Use loading and error boundaries per route group because SaaS dashboards should degrade one panel at a time, not blank the whole app.

## Server Actions & Route Handlers

- Validate `FormData` with Zod at the start of each server action because form values are strings and missing keys are common.
- Check authentication and account membership before every mutation because layouts are not an authorization boundary.
- Return typed result objects for recoverable validation errors; throw only for unexpected failures. This lets forms render useful feedback.
- Use route handlers for webhooks and external API surfaces. Use server actions for first-party UI mutations.
- Pin webhook route handlers to the Node runtime when they need raw body verification or `better-sqlite3`, because edge runtime cannot run native SQLite bindings.

## Auth & Authorization

- Store users, accounts, memberships, and roles as separate tables because SaaS authorization usually becomes team-based even when v1 starts single-user.
- Authorize by account membership in repository queries, not only in UI checks, because hidden buttons do not protect direct requests.
- Use a small role set: `owner`, `admin`, `member`, `billing`. Add permissions only when a feature proves roles are too coarse.
- Write tests for cross-account access denial because this is the most expensive SaaS bug class.

## Environment & Config

- Define environment variables in `src/lib/env.ts` with Zod and export a typed `env` object. Read `process.env` nowhere else.
- Required variables: `DATABASE_URL`, `AUTH_SECRET`, `APP_URL`.
- Optional variables must have explicit defaults in `env.ts`; do not scatter `??` fallbacks through features.
- Never log secrets or database URLs. Redact values in diagnostics because local logs often get pasted into support tickets.

## Testing Rules

- Unit-test pure feature functions and validation schemas.
- Integration-test repositories against a temporary SQLite database created from migrations because mocked SQL hides migration drift.
- Add at least one authorization failure test for each feature that reads or mutates account-owned data.
- Do not snapshot whole pages. Assert user-visible text and state transitions because App Router markup changes often.
- Tests may seed the database directly through repositories, not by clicking through onboarding, because setup noise should not obscure the behavior under test.

## Patterns To Follow

- Start features with a repository contract, a Zod input schema, and one server action. This gives Claude Code a narrow path from UI to persistence.
- Keep all dates in UTC and format at the edge of the UI because SaaS users and servers rarely share a timezone.
- Use `Result<T, E>` style return objects for expected failures because server actions need typed messages that components can display.
- Keep billing and auth adapters behind feature modules because vendors change more often than account concepts.
- Document every migration with a short SQL comment explaining the user-facing reason for the change.

## What We Do Not Do

- Do not put database calls in client components because it either fails at build time or leaks server-only concepts into browser code.
- Do not create generic `utils.ts` dumping grounds. Name modules by purpose so future Claude sessions can find the right boundary.
- Do not use Prisma in this template. The project standard is direct SQLite SQL so migrations, indexes, and constraints stay visible.
- Do not use `any` to move faster because SaaS data bugs become billing, auth, or support bugs; unknown values must be parsed.
- Do not create API routes for internal form submissions when a server action is enough. Extra HTTP layers add validation and auth duplication.
- Do not hide destructive operations behind reusable helpers without explicit names such as `deleteAccountPermanently`; dangerous calls should be searchable.
- Do not make every component configurable because SaaS UI benefits from consistent defaults more than abstract components.

## Claude Code Operating Rules

- Before editing, identify whether the change touches UI, persistence, auth, billing, or migrations; say which boundary is affected.
- If a request changes stored data shape, create or update a migration in the same change.
- If a request adds a mutation, include validation, authorization, repository write, and at least one failure test.
- If a request adds a dashboard view, keep data loading in the server component and interactivity in small client children.
- If requirements are ambiguous, choose the smallest SaaS-safe path: typed input, explicit auth, transaction for multi-row writes, and no client-side secrets.
