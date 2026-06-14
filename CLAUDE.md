# CLAUDE.md

Project guidance for a greenfield SaaS app using Next.js 15 App Router, React Server Components, TypeScript, SQLite, and either `better-sqlite3` for embedded/local deployments or Turso/libSQL for hosted SQLite.

## Stack And Versions

- Next.js 15 with the App Router under `app/`.
- React 19 and Server Components by default.
- TypeScript with `strict` enabled.
- SQLite as the primary database.
- Drizzle ORM is the default data layer because it keeps migrations explicit, works well with SQLite/libSQL, and avoids a separate schema runtime.
- Use `better-sqlite3` only in the Node.js runtime for embedded or local development. It is a native addon and is not compatible with the Edge runtime.
- Use Turso/libSQL, or another shared database, for hosted multi-instance or serverless deployments. Do not use `file:` SQLite URLs when instances have separate filesystems or concurrent locking/consistency requirements.
- Server Actions are allowed for simple mutations, but route handlers are preferred for public API boundaries and webhook-style integrations.
- Tailwind CSS plus small local UI primitives are preferred over a large component framework until product workflows prove repeated patterns.

Reason: this stack keeps a SaaS codebase deployable on common platforms while preserving SQLite's operational simplicity. The main risk is accidental client/server boundary confusion, so the conventions below are strict about where data access, mutations, and UI state live.

## Folder Structure

Use this structure unless the project already has a stronger convention:

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
  api/
    health/route.ts
components/
  ui/
  forms/
  layout/
db/
  client.ts
  schema.ts
  migrations/
features/
  billing/
  organizations/
  projects/
  users/
lib/
  auth.ts
  env.ts
  result.ts
tests/
  unit/
  integration/
```

- `app/` owns routing, layouts, loading states, metadata, and route handlers.
- `components/ui/` contains generic primitives such as Button, Input, Dialog, and Table.
- `components/forms/` contains form shells that can be reused across routes.
- `features/<name>/` contains domain-specific actions, queries, validators, and components.
- `db/` is the only folder that may define tables, migration helpers, or database clients.
- `lib/env.ts` validates environment variables once at process startup.

Reason: App Router projects become hard to maintain when route folders absorb every helper. Feature folders keep business logic close together while `app/` stays focused on routing.

## Naming Conventions

- Files that export React components use `PascalCase.tsx`.
- Route files use Next.js names exactly: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, and `route.ts`.
- Server-only modules end with `.server.ts` when they might be imported near client code.
- Client components start with `"use client"` and should have names ending in `Client` only when a server wrapper also exists.
- Database query functions are verbs plus domain nouns, for example `getUserById`, `listProjectsForUser`, and `createSubscription`.
- Mutations return typed result objects instead of throwing for expected validation errors.

Reason: naming should make execution context obvious before opening the file. Most Next.js production bugs in this stack come from importing server-only code into client bundles or hiding expected validation failures behind exceptions.

## Server And Client Boundaries

- Use Server Components by default.
- Add `"use client"` only for browser state, event handlers, refs, media APIs, or third-party client widgets.
- Never import `db/`, `fs`, `crypto` secrets, or environment variables into a Client Component.
- Pass plain serializable data from Server Components into Client Components.
- Keep Client Components leaf-level when possible.

Reason: Server Components reduce bundle size and simplify data loading, but the boundary must stay explicit for SQLite clients and secrets to remain server-only.

## SQL And Migration Conventions

- Every schema change requires a checked-in migration under `db/migrations/`.
- Migrations must be append-only once merged. Create a new migration instead of editing a historical migration.
- Use `created_at` and `updated_at` on user-owned business tables.
- Use text UUIDs or cuid-style IDs for externally visible records.
- Use integer timestamps only when a library requires them; otherwise use ISO-compatible datetime columns.
- Add indexes in the same migration as the query pattern that needs them.
- Prefer foreign keys with explicit `on delete` behavior. Use cascading deletes only when child records have no audit value.
- Keep raw SQL in migration files or clearly named query helpers. Do not embed ad hoc SQL strings inside React components.
- Describe rollback and data backfill behavior in the PR for every migration, even when the migration tool only runs forward.

Reason: SQLite makes local iteration easy, but production safety depends on migrations being reviewable and deterministic. Indexes and foreign-key behavior should be discussed with the schema change that introduces the access pattern.

## Database Access

- Create one database client in `db/client.ts`.
- Import the database client only from server-only files, route handlers, or Server Actions.
- Keep table definitions in `db/schema.ts`.
- Keep read queries and write mutations near the feature they serve unless they are shared across several features.
- Wrap multi-step writes in transactions.
- Do not run database writes during render. Use Server Actions, route handlers, or explicit service functions.
- Scope every tenant-owned query by `organization_id`; never rely on a client-provided record ID alone.

Reason: SQLite performs well when access is predictable. Centralized client creation prevents duplicate connections and makes Turso/local switching boring.

## Auth, Tenancy, And Caching

- Perform authentication and authorization in the server function that reads or mutates data.
- Treat `organization_id` as part of every tenant-owned lookup, update, and delete.
- Keep role checks in one server-only policy module instead of scattering role strings across components.
- Include actor, organization, target record, and action in audit logs for billing and administrative mutations.
- Use `revalidatePath`, `revalidateTag`, or an explicit no-store boundary after mutations; do not let authenticated dashboards inherit accidental public caching.

Reason: hiding controls in the browser is not authorization, and stale cross-tenant data is both a correctness and security failure.

## Environment Variables

Define and validate environment variables in `lib/env.ts`.

Expected baseline:

```text
DATABASE_URL=file:./data/local.db
NEXT_PUBLIC_APP_URL=http://localhost:3000
AUTH_SECRET=<generated-secret>
```

- Prefix only browser-safe values with `NEXT_PUBLIC_`.
- Fail fast when required server variables are missing.
- Keep example values in `.env.example`.
- Treat `file:` database URLs as local/development-only and keep the target path gitignored.
- For hosted Turso/libSQL deployments, prefer a shared URL such as `DATABASE_URL=libsql://<database>.turso.io` plus the auth token environment variable required by the selected client.

Reason: leaking secrets through `NEXT_PUBLIC_` is easy in Next.js. A typed env module creates one place to review runtime requirements.

## Component Patterns

- Server Components fetch data and choose layout.
- Client Components handle local interaction only.
- Forms use a shared validation schema for both client hints and server validation.
- UI primitives accept `className` and forward relevant HTML attributes.
- Use composition over boolean prop explosions. Prefer `<Card><CardHeader /></Card>` to `Card` props for every layout variant.
- Keep loading and empty states close to the route segment that owns the data.

Reason: SaaS screens accumulate edge states quickly. Composition keeps UI extensible without turning primitives into product-specific components.

## Mutations And Validation

- Validate all user input on the server.
- Use a schema library such as Zod for request and form payloads.
- Return field-level errors for forms.
- Revalidate affected paths or tags after successful mutations.
- Treat authz checks as part of the mutation, not a caller responsibility.

Reason: client validation is a usability feature, not a security boundary. Server validation and authorization must travel with the mutation.

## Dev Commands

Use these commands unless the project defines equivalents:

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

If scripts do not exist yet, add them before relying on them in docs or CI.

Reason: agents should not invent commands during implementation. Stable scripts make CI, local development, and automation use the same entry points.

## Testing Rules

- Unit test pure functions, validators, and query builders.
- Integration test route handlers and Server Actions with a temporary SQLite database.
- Add regression tests for every bug fix.
- Avoid snapshot tests for full pages unless the UI is intentionally static.
- Test authorization failures as carefully as successful paths.

Reason: SQLite makes integration tests cheap. SaaS defects often hide in validation, authorization, and migration behavior rather than isolated components.

## Patterns To Follow

- Prefer explicit server-only query functions over calling the database inline from route components.
- Keep route handlers thin: parse input, call a feature function, return a typed response.
- Use `notFound()` for missing route resources and structured errors for API failures.
- Keep product copy close to the screen unless it is reused across multiple flows.
- Make empty states actionable.

Reason: these patterns keep the codebase understandable for both humans and coding agents. Thin boundaries make changes easier to review.

## Anti-Patterns To Avoid

- Do not put database calls in Client Components.
- Do not use API routes from Server Components when a server-side function call would work.
- Do not create a global `types.ts` dumping ground. Place types with the feature that owns them.
- Do not edit old migrations after merge.
- Do not use `any` to silence data-shape uncertainty. Validate and narrow instead.
- Do not introduce background jobs, queues, or external services for simple synchronous SaaS flows.
- Do not add a component library before the first repeated UI pattern exists.

Reason: each anti-pattern adds hidden coupling or operational weight. The default should remain small, typed, and server-first.

## Before Opening A PR

Run:

```bash
pnpm lint
pnpm typecheck
pnpm test
```

Then check:

- New environment variables are documented in `.env.example`.
- New database behavior includes a migration.
- Server/client boundaries are explicit.
- Expected validation and authorization failures are covered.
- Tenant-owned queries prove cross-organization access is rejected.
- Migration PRs explain rollback, backfill, and deployment ordering.
- The PR description explains the user-facing behavior, not only the files changed.
