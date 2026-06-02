# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the operating contract for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and server-first React.

## Stack And Versions

- Next.js 15 with the App Router in `src/app`.
  Reason: route handlers, server components, metadata, and layouts stay colocated without the legacy Pages Router split.
- React 19 and TypeScript in strict mode.
  Reason: strict types catch data boundary mistakes before SQLite rows reach UI code.
- SQLite through `better-sqlite3` for local-first apps or Turso/libSQL when remote replication is required.
  Reason: both keep the SQL model explicit while avoiding a premature ORM abstraction.
- Zod for input validation at every external boundary.
  Reason: TypeScript cannot validate form posts, route params, webhook payloads, or JSON bodies at runtime.
- `pnpm` for package management.
  Reason: deterministic installs and fast workspace support matter once the SaaS grows into packages.

## Dev Commands

Run these commands from the project root:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
```

If a command is missing, add it to `package.json` before using a substitute.
Reason: Claude should improve the project contract instead of inventing one-off local commands.

`pnpm db:migrate` must run a checked-in migration runner, preferably `tsx scripts/migrate.ts`.
The runner reads `src/db/migrations/*.sql` in filename order, creates a `_migrations` ledger table, applies each new file inside a transaction, and records `filename`, `checksum`, and `applied_at`. If an already-applied filename has a different checksum, fail instead of rewriting history.
Reason: every contributor and deploy target must apply the same schema sequence with the same safety guarantees.

## Folder Structure

Prefer this shape:

```text
src/
  app/
    (marketing)/
    (dashboard)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
  db/
    client.ts
    migrations/
    schema.ts
    queries/
  features/
    billing/
    auth/
    organizations/
    projects/
  lib/
    auth.ts
    env.ts
    result.ts
  server/
    actions/
    services/
  tests/
```

Rules:

- Put route-specific UI inside the route folder.
  Reason: local route ownership makes App Router layouts and loading states easier to reason about.
- Put reusable visual primitives in `src/components/ui`.
  Reason: shared UI should not import business logic or database code.
- Put product capabilities in `src/features/<feature>`.
  Reason: SaaS complexity grows by domain area, not by file type.
- Put direct SQL access in `src/db/queries`.
  Reason: database reads and writes need one obvious audit location.
- Put orchestration in `src/server/services`.
  Reason: services can coordinate auth, validation, billing, and database calls without leaking that work into components.

## Naming Conventions

- Use kebab-case for route folders and filenames that map to URLs.
  Reason: URL naming stays readable and stable.
- Use PascalCase for React components.
  Reason: it matches React conventions and makes component imports obvious.
- Use camelCase for functions, variables, and Zod schemas.
  Reason: it keeps TypeScript code consistent and searchable.
- Name server actions as verbs, such as `createProjectAction`.
  Reason: actions mutate state and should read like commands.
- Name query helpers by result intent, such as `getProjectById` or `listProjectsForOrg`.
  Reason: callers should know cardinality and filtering without opening the SQL.

## Environment Rules

- Define all environment variables in `src/lib/env.ts`.
  Reason: a single validated env module prevents scattered `process.env` reads.
- Fail fast when required env vars are missing.
  Reason: broken deploys should fail at boot, not after a customer clicks checkout.
- Never read secrets in client components.
  Reason: `NEXT_PUBLIC_` is the only safe client exposure path.

Example:

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  STRIPE_WEBHOOK_SECRET: z.string().min(1).optional(),
});

export const env = envSchema.parse(process.env);
```

## Deployment Rules

- Use `better-sqlite3` only on the Node.js runtime with a persistent filesystem.
  Reason: native bindings cannot run on Edge, and ephemeral/serverless disks are unsafe for production persistence.
- For Vercel Edge, serverless-only, or managed multi-region deploys, use Turso/libSQL or another hosted SQLite-compatible service.
  Reason: the database has to survive cold starts, redeploys, and horizontal scaling.
- Mark route handlers that touch local SQLite as Node runtime only.
  Reason: runtime intent should be explicit at the file boundary.

```ts
export const runtime = "nodejs";
```

## SQL And Migration Conventions

- Keep migrations in `src/db/migrations` with monotonic names like `0001_create_users.sql`.
  Reason: ordering must be deterministic in local, CI, and production.
- Never edit an applied migration.
  Reason: SQLite has no central migration server; changing history breaks collaborators and deployed databases.
- Add a new migration for every schema change.
  Reason: forward-only history is easier to review and recover.
- Wrap multi-step writes in transactions.
  Reason: SaaS state changes often touch account, audit, and billing rows together.
- Enable foreign keys on every connection with `PRAGMA foreign_keys = ON`.
  Reason: SQLite supports constraints only when explicitly enabled per connection.
- Use `created_at`, `updated_at`, and stable text primary keys for product tables.
  Reason: timestamps support audit/debugging and text IDs avoid leaking row counts.
- Prefer explicit SQL over a heavy ORM.
  Reason: the app is small enough that readable SQL beats generated abstractions.

Query pattern:

```ts
export function getProjectById(projectId: string) {
  return db
    .prepare(
      `select id, organization_id, name, created_at
       from projects
       where id = ?`
    )
    .get(projectId);
}
```

## Server And Data Flow

- Default to server components.
  Reason: database reads and auth checks belong on the server where secrets stay private.
- Use client components only for browser state, event handlers, focus management, charts, and optimistic UI.
  Reason: client bundles should stay small and intentional.
- Validate every server action input with Zod before touching the database.
  Reason: forms are untrusted input even when rendered by this app.
- Re-check authorization inside every server action and route handler.
  Reason: hidden buttons are not access control.
- Return typed result objects from mutations.
  Reason: UI can handle success and failure without parsing thrown strings.

Result pattern:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };
```

## Component Patterns

- Keep page components thin: load data, check access, pass props.
  Reason: pages should describe composition, not contain business rules.
- Keep forms in `src/components/forms` or the owning feature folder.
  Reason: form behavior usually belongs to a domain workflow.
- Use accessible labels, button text, and error messages.
  Reason: SaaS users repeat workflows; clarity reduces support load.
- Use loading, empty, and error states for every data-heavy view.
  Reason: dashboards fail badly when only the happy path is designed.
- Do not fetch from internal API routes inside server components.
  Reason: call the service or query directly to avoid unnecessary HTTP hops.

## Auth And Tenancy

- Model organizations before teams become urgent.
  Reason: most SaaS apps eventually need shared ownership and billing.
- Store membership role in a join table.
  Reason: user roles differ per organization.
- Scope every project, invoice, and setting row by `organization_id`.
  Reason: tenant isolation should be visible in every query.
- Add authorization helpers such as `requireOrgMember(userId, organizationId)`.
  Reason: duplicated role checks drift over time.

## Testing Rules

- Test pure utilities with unit tests.
  Reason: they are cheap and stable.
- Test database queries against a temporary SQLite database.
  Reason: mocks miss SQL syntax, constraints, and transaction behavior.
- Test server actions through their exported functions.
  Reason: actions are the mutation boundary that customers actually hit.
- Add at least one regression test for each bug fix.
  Reason: the app should remember production incidents.

## What We Do Not Do

- Do not introduce a full ORM unless the project already chose one.
  Reason: schema drift and hidden queries are worse than explicit SQL at this size.
- Do not put business logic in React components.
  Reason: UI should render product state, not decide product rules.
- Do not create API routes for server-only workflows.
  Reason: internal HTTP adds latency and another auth surface.
- Do not use `any` to silence TypeScript.
  Reason: it hides the exact uncertainty Claude should resolve.
- Do not edit old migrations.
  Reason: migration history is a contract with every existing database.
- Do not store billing or auth secrets in `.env.local` examples.
  Reason: examples get copied into public repos.

## Change Checklist

Before finishing a task:

1. Run `pnpm lint`.
2. Run `pnpm typecheck`.
3. Run focused tests for changed services, queries, or actions.
4. Confirm every new mutation validates input and checks authorization.
5. Confirm every schema change has a new migration.

If a check cannot run, explain why and name the next command the maintainer should run.
