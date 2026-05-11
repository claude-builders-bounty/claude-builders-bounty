# CLAUDE.md

## Stack And Versions

This project is a greenfield SaaS application built with:

- Next.js 15 App Router
- React Server Components by default
- TypeScript in strict mode
- SQLite through `better-sqlite3` for local-first apps or Turso/libSQL for hosted SQLite
- Drizzle ORM for schema definitions, typed queries, and migrations
- Server Actions for small trusted mutations
- Route Handlers for public APIs, webhooks, and third-party integrations
- Tailwind CSS plus a small component layer for UI
- Vitest for unit tests and Playwright for browser-level flows

Reason: this stack keeps the runtime simple, makes local development match production closely, and avoids introducing a separate API service before the product needs it.

## Dev Commands

Use these commands unless the project package manager says otherwise:

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

If a command is missing, add it to `package.json` before relying on it. Do not invent one-off scripts in answers when a reusable script belongs in the project.

## Folder Structure

Use this structure for new code:

```text
app/
  (marketing)/
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
  schema.ts
  migrations/
features/
  billing/
  auth/
  accounts/
  projects/
lib/
  env.ts
  auth.ts
  dates.ts
  result.ts
server/
  actions/
  queries/
  services/
tests/
  unit/
  e2e/
```

Rules:

- Put route-owned UI inside `app/` only when it is not reused elsewhere.
- Put reusable presentational components in `components/`.
- Put product behavior in `features/<domain>/` so code is grouped by business concept, not by framework primitive.
- Put database schema, migrations, and the database client in `db/`.
- Put server-only mutation and query helpers in `server/`.
- Keep `lib/` small. It is for shared primitives, not product domains.

Reason: domain folders make SaaS features easier to delete, test, and move than a large `utils/` or `services/` folder.

## Naming Conventions

- Components: `PascalCase.tsx`
- Hooks: `useThing.ts`
- Server Actions: `verbNounAction`, for example `createProjectAction`
- Server queries: `getThing`, `listThings`, `findThingById`
- Database tables: plural snake case, for example `team_members`
- Database columns: snake case in SQL, camel case in TypeScript only when mapped by the ORM
- Route segments: lowercase kebab case
- Test files: `*.test.ts` for unit tests, `*.spec.ts` for browser tests

Reason: the codebase should make it obvious whether a function reads, writes, renders, or adapts data.

## Data And SQLite Rules

Use SQLite as the source of truth. Do not create in-memory side stores for data that must survive a request.

Schema rules:

- Define every table in `db/schema.ts`.
- Generate migrations from schema changes. Do not hand-edit generated migrations unless the generator cannot express the needed operation.
- Every table needs an `id`, `created_at`, and `updated_at` unless it is a pure join table.
- Use foreign keys for ownership and lifecycle constraints.
- Add indexes for every foreign key and every high-cardinality lookup used in route loaders or dashboard tables.
- Store timestamps as ISO strings or integer milliseconds consistently across the whole app. Do not mix both in new tables.

Migration rules:

- Never change a migration that may have run outside your machine. Add a new migration instead.
- For destructive changes, use a two-step migration: add the new shape, backfill/copy data, then remove the old shape in a later migration.
- Include rollback notes in the PR when a migration drops, renames, or rewrites data.
- Keep seed data separate from migrations.

Reason: SQLite is reliable, but SaaS data survives because migrations are boring, auditable, and reversible.

## Query And Mutation Patterns

Reads:

- Use server components for page-level data loading.
- Put reusable reads in `server/queries/`.
- Return plain objects from query helpers, not ORM internals.
- Validate user authorization inside query helpers when the data is user- or team-scoped.

Writes:

- Use Server Actions for form-backed mutations from trusted app screens.
- Use Route Handlers for webhooks, external integrations, and public API calls.
- Validate all inputs with a schema before touching the database.
- Revalidate or redirect at the mutation boundary, not inside low-level services.

Reason: reads and writes have different caching, validation, and security needs. Keeping them separate prevents accidental data leaks.

## Auth And Authorization

- Authentication answers "who is this?" Authorization answers "can they access this resource?" Implement both.
- Never trust a `userId`, `teamId`, or role from the client.
- Every team-scoped query must include the authenticated user's membership constraint.
- Prefer capability checks like `canManageBilling(user, team)` over scattering role string comparisons.
- Route Handlers must return `401` for unauthenticated requests and `403` for authenticated users without permission.

Reason: most SaaS bugs are not login bugs; they are cross-tenant access bugs.

## Component Patterns

- Default to React Server Components.
- Add `"use client"` only for state, effects, browser APIs, or event handlers.
- Keep client components shallow and pass them serialized data from server components.
- Forms should use native form semantics first, then progressively enhance with client behavior when needed.
- UI components should accept data and callbacks. They should not import database clients, auth helpers, or server services.
- Prefer composition over boolean prop matrices. If a component needs many mode flags, split it.

Reason: Server Components reduce client bundle size and make data access explicit.

## API And Webhook Patterns

- Put public endpoints under `app/api`.
- Parse and validate request bodies at the edge of the handler.
- Keep provider-specific webhook verification in `features/<provider>/`.
- Return typed JSON envelopes: `{ "data": ... }` for success and `{ "error": { "code": "...", "message": "..." } }` for failures.
- Log enough context to debug, but never log secrets, tokens, raw payment details, or full request bodies from third parties.

Reason: APIs are contracts. Small predictable response shapes make integrations and tests simpler.

## Environment Variables

- Define environment parsing in `lib/env.ts`.
- Fail fast on missing required variables during server startup or command execution.
- Keep client-exposed variables prefixed with `NEXT_PUBLIC_`.
- Never read `process.env` directly inside feature code. Import the parsed env object.
- Do not add fallback secrets or fake production defaults.

Reason: scattered environment reads cause runtime-only failures and accidental secret exposure.

## Error Handling

- Use expected errors for validation and permission failures.
- Throw only for programmer errors or infrastructure failures.
- Show user-safe messages in UI. Keep technical details in server logs.
- Do not swallow errors in Server Actions. Return a typed result the form can render.
- Add an error boundary for dashboard areas that can fail independently.

Reason: SaaS users need clear recovery paths, while engineers need logs with enough detail to fix the real issue.

## Testing Rules

- Unit test pure domain logic, validation, formatting, and permission helpers.
- Add integration tests for database queries that encode tenant isolation or billing state.
- Add Playwright tests for signup, login, critical dashboard flows, and billing gates.
- For migrations, test the behavior after migration, not the generated SQL text.
- Do not mock the database for code whose purpose is to query the database.

Reason: tests should protect business behavior, not implementation trivia.

## Pull Request Checklist

Before opening a PR:

- `pnpm lint` passes
- `pnpm typecheck` passes
- `pnpm test` passes
- New migrations are committed when schema changes
- User- or team-scoped data access includes authorization checks
- New environment variables are documented
- UI changes handle loading, empty, error, and narrow viewport states
- No secrets, tokens, or generated local database files are committed

## What We Do Not Do

- Do not add a separate backend service for ordinary SaaS CRUD. Next.js Route Handlers and Server Actions are enough until scale proves otherwise.
- Do not put business logic directly in components. Components render; services decide.
- Do not create generic `utils.ts` dumping grounds. Name helpers by domain or primitive.
- Do not use `any` to bypass schema or API uncertainty. Model the uncertainty with validation.
- Do not hard-delete customer data without an explicit product requirement and audit trail.
- Do not introduce global client state for data already owned by the server. Use server reads and targeted client state.
- Do not skip migrations because SQLite is "just a file." Production data still needs history.
- Do not copy external API payloads through the app unvalidated.

Reason: these shortcuts make early demos faster and production maintenance slower.

## How To Work In This Repo

When changing code:

1. Identify the domain folder first.
2. Read the related schema, queries, actions, and tests before editing.
3. Make the smallest change that preserves the established boundaries.
4. Add or update tests at the level where the behavior can fail.
5. Run the relevant checks and report exact commands and results.

When requirements are ambiguous, choose the simpler server-owned design and state the assumption in the PR. Do not block on clarification for details that are reversible.
