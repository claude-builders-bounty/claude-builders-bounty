# CLAUDE.md - Next.js 15 + SQLite SaaS

This project is a production-oriented SaaS application built with Next.js 15 App Router, React Server Components, TypeScript, and SQLite through either `better-sqlite3` for local/single-node deployments or Turso/libSQL for managed edge-friendly SQLite.

Use this file as the operating contract for Claude Code. Prefer small, typed, server-first changes. If a request conflicts with this file, call out the conflict before editing.

## Stack And Versions

| Rule | Reason |
| --- | --- |
| Use Next.js 15 App Router in `app/`; do not add a Pages Router `pages/` tree. | Mixing routers creates two routing mental models and weakens caching, metadata, and layout conventions. |
| Use TypeScript in strict mode for application code, database adapters, server actions, and tests. | SQLite has loose runtime types, so TypeScript must catch shape mistakes before data reaches storage. |
| Use React Server Components by default; add `"use client"` only for browser APIs, local component state, or event handlers. | Server-first rendering keeps database access off the client bundle and reduces hydration work. |
| Use `better-sqlite3` for local file databases and Turso/libSQL only behind the same repository interface. | One repository interface lets deployment switch providers without rewriting product code. |
| Use Zod or an equivalent schema validator at all form, route-handler, and webhook boundaries. | User input and third-party payloads must be validated before becoming SQL parameters. |
| Use `pnpm` as the package manager unless the project already has a lockfile for another manager. | One package manager avoids lockfile drift and inconsistent dependency resolution. |

## Dev Commands

Run these from the repository root.

| Command | Purpose |
| --- | --- |
| `pnpm install` | Install dependencies from the lockfile. |
| `pnpm dev` | Start the Next.js development server. |
| `pnpm lint` | Run ESLint and framework lint checks. |
| `pnpm typecheck` | Run `tsc --noEmit`; this must pass before PR handoff. |
| `pnpm test` | Run unit and integration tests. |
| `pnpm db:migrate` | Apply pending SQLite migrations. |
| `pnpm db:studio` | Open the configured database browser when available. |
| `pnpm build` | Verify production compile, route types, and server/client boundaries. |

If a command is missing, add it to `package.json` before relying on it in documentation or CI.

## Folder Structure

Use this structure for new greenfield work.

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  layouts/
lib/
  auth/
  billing/
  config/
  dates/
server/
  actions/
  services/
  repositories/
  db/
    client.ts
    schema.ts
    migrations/
    migrate.ts
tests/
  unit/
  integration/
  fixtures/
```

| Rule | Reason |
| --- | --- |
| Keep route files in `app/` thin: load data, call one service, render one view. | Route files become untestable when they own business rules and SQL details. |
| Put reusable visual components in `components/`; put product workflows in route-local folders when they are not reused. | Shared folders should contain stable primitives, not one-off feature fragments. |
| Put server-only business logic in `server/services/`. | Services are testable without rendering React and prevent mutations from leaking into components. |
| Put all SQL access in `server/repositories/` or `server/db/`; never run SQL directly from a component. | Centralized SQL is easier to migrate, audit, and protect with transactions. |
| Put environment parsing in `lib/config/` and export typed config objects. | Reading `process.env` throughout the app makes runtime behavior hard to validate. |
| Put integration fixtures in `tests/fixtures/`, not beside production migrations. | Test data must not look like deployable schema changes. |

## Naming Conventions

| Rule | Reason |
| --- | --- |
| Route segments use `kebab-case`; React components use `PascalCase`; functions and variables use `camelCase`. | Each name shape signals what kind of file or symbol Claude is editing. |
| SQLite tables and columns use `snake_case`; TypeScript objects use `camelCase`. | SQL stays idiomatic while UI and service code stay idiomatic. Map at repository boundaries. |
| Table names are plural nouns: `users`, `organizations`, `invoices`. | Plural table names read naturally in queries and avoid collisions with reserved terms. |
| Join tables use both table names: `organization_members`, `user_roles`. | The relationship is visible without opening schema docs. |
| Server actions end with `Action`, repository functions start with a verb, and services expose product language. | Names should reveal whether code mutates input, persists data, or expresses a business operation. |

## Database Rules

| Rule | Reason |
| --- | --- |
| Always enable SQLite foreign keys on connection startup with `PRAGMA foreign_keys = ON`. | SQLite can otherwise accept invalid references silently. |
| Use prepared statements or query-builder parameters for every dynamic value. | String-built SQL is a security bug even in small internal tools. |
| Wrap multi-write product operations in transactions. | SaaS workflows such as signup, billing, and invitations must be all-or-nothing. |
| Store timestamps as ISO 8601 UTC text unless a library already standardizes another format. | Text timestamps are readable, sortable, and portable across local SQLite and Turso. |
| Prefer explicit constraints: `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys. | The database should reject invalid state even if a server action has a bug. |
| Keep database rows boring: no nested JSON unless the field is truly schemaless product metadata. | JSON blobs make filtering, migrations, and analytics harder. |
| Do not import database clients into client components. | The database must never become reachable from browser bundles. |

### Repository Pattern

Use repositories for persistence and services for product rules.

```ts
// server/repositories/organizationRepository.ts
export async function findOrganizationBySlug(slug: string) {
  return db
    .prepare("select id, name, slug from organizations where slug = ?")
    .get(slug);
}

// server/services/createOrganization.ts
export async function createOrganization(input: CreateOrganizationInput) {
  const parsed = createOrganizationSchema.parse(input);
  return organizationRepository.create(parsed);
}
```

| Rule | Reason |
| --- | --- |
| Repositories return typed records or `null`; they do not call `redirect`, `notFound`, or `revalidatePath`. | Persistence code should not know about Next.js response behavior. |
| Services decide authorization, transactions, and cache invalidation. | Product rules belong in one layer that can be tested directly. |
| Route handlers and server actions call services, not repositories directly, unless the operation is read-only and trivial. | This keeps future authorization and audit logging from being scattered. |

## Migration Conventions

| Rule | Reason |
| --- | --- |
| Every schema change is a numbered SQL file in `server/db/migrations/`, for example `0007_add_organization_members.sql`. | Ordered files make deployment history obvious and reviewable. |
| Never edit a migration after it has been merged. Add a new migration instead. | Rewriting history breaks existing databases and teammate environments. |
| Use a `schema_migrations` table to record applied migration filenames. | The app can safely know what has already run. |
| Migrations must be backward-compatible unless the PR includes a clear deploy plan. | Production SaaS data often outlives one release and may be served by old code briefly. |
| Destructive changes require a two-step migration: add new shape, backfill, then remove old shape later. | This gives rollback room and protects customer data. |
| Do not run migrations automatically during request handling. | A web request should not unexpectedly block on schema changes or partially migrate production. |
| Include a rollback note in the PR when a migration touches billing, auth, or tenant membership. | These tables are business-critical and need explicit recovery thinking. |

Example migration:

```sql
-- server/db/migrations/0003_add_organization_members.sql
create table organization_members (
  id text primary key,
  organization_id text not null references organizations(id) on delete cascade,
  user_id text not null references users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'member')),
  created_at text not null,
  unique (organization_id, user_id)
);
```

## Component Patterns

| Rule | Reason |
| --- | --- |
| Fetch data in server components or services; pass plain serializable props to client components. | Client components should handle interaction, not persistence. |
| Use server actions for first-party form mutations and route handlers for webhooks or third-party callbacks. | This separates browser-driven writes from external HTTP integrations. |
| Keep form validation schemas near the action or service that consumes them. | The validation contract should move with the mutation logic. |
| Prefer composition over prop explosion. | SaaS screens change often; composed sections are easier to rearrange. |
| Use accessible HTML first, then style it. | SaaS UI must remain usable with keyboard navigation and assistive technology. |
| Do not hide loading, empty, or error states inside generic wrappers. | Product states need copy, analytics, and recovery actions. |

Server action pattern:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { createOrganization } from "@/server/services/createOrganization";

export async function createOrganizationAction(formData: FormData) {
  await createOrganization({
    name: String(formData.get("name") ?? ""),
    slug: String(formData.get("slug") ?? ""),
  });

  revalidatePath("/app/organizations");
}
```

## Auth, Tenancy, And Billing

| Rule | Reason |
| --- | --- |
| Every protected service accepts an explicit actor context: `actorUserId`, `organizationId`, and role when needed. | Hidden global session reads make authorization hard to test. |
| Check tenant membership before reading or mutating tenant-owned rows. | SaaS bugs often become data leaks across organizations. |
| Treat billing webhooks as idempotent and store provider event IDs. | Payment providers retry; duplicate events must not duplicate state. |
| Keep authorization checks in services, not only middleware. | Middleware protects routes, but services protect data paths and future callers. |

## Error Handling And Logging

| Rule | Reason |
| --- | --- |
| Return user-safe messages from actions; log internal error details on the server. | Users need recovery steps, not stack traces. |
| Include operation names and stable IDs in logs, never raw secrets or full payment payloads. | Logs must help debugging without becoming a liability. |
| Use typed result objects for expected validation failures. | Expected failures should not look like system crashes. |

## Testing Rules

| Rule | Reason |
| --- | --- |
| Unit test services and repositories with a temporary SQLite database. | The most important behavior is business rules plus persistence. |
| Integration test server actions and route handlers around real input shapes. | Boundaries are where validation and auth bugs appear. |
| Use deterministic fixtures and reset the database between tests. | Tests should not depend on order or leftover rows. |
| Test at least one migration path whenever schema changes. | Passing code against a fresh schema does not prove existing deployments can upgrade. |
| Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build` before handoff. | These catch different classes of errors: style, types, behavior, and framework integration. |

## What We Do Not Do

| Anti-pattern | Why |
| --- | --- |
| Do not add an ORM just to avoid writing SQL. | SQLite is transparent and fast when SQL is explicit; unnecessary ORM layers hide query behavior. |
| Do not build SQL strings with template interpolation. | It creates injection risk and breaks query planning. |
| Do not put secrets in `NEXT_PUBLIC_*` variables. | `NEXT_PUBLIC_*` is exposed to the browser bundle. |
| Do not use client components for pages that only read data. | It increases JavaScript shipped to the user and weakens server caching. |
| Do not create generic `utils.ts` dumping grounds. | Mixed utilities become invisible coupling. Use domain folders. |
| Do not mutate cookies, sessions, or billing state from random helpers. | These side effects must stay in auditable services or route handlers. |
| Do not skip migrations for "small" schema changes. | Small direct edits are how local and production databases drift. |
| Do not silently catch database errors and return empty arrays. | Empty data can hide outages and cause destructive follow-up actions. |

## Claude Code Working Agreement

Before editing:

1. Identify whether the task touches UI, service logic, auth, billing, database schema, or migrations.
2. If it touches database schema, create or update a numbered migration and describe upgrade risk.
3. If it touches tenant data, state where authorization is enforced.
4. If it adds a client component, explain why server components are not enough.

When editing:

1. Keep changes small and route work through services and repositories.
2. Add or update tests at the layer where the risk lives.
3. Preserve existing public behavior unless the request explicitly changes it.
4. Do not introduce new dependencies unless the value exceeds the maintenance cost.

Before handoff:

1. Run the relevant commands from the Dev Commands section.
2. Summarize changed files by product concern, not by file list.
3. Call out migrations, env vars, or deployment steps explicitly.
