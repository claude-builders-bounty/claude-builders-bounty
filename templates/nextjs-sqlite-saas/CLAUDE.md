# CLAUDE.md - Next.js 15 + SQLite SaaS

This file is the operating guide for a greenfield SaaS built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite through `better-sqlite3` for local/single-node deployments or Turso/libSQL when the app needs hosted replication.

## Stack And Versions

- Next.js 15 App Router with TypeScript strict mode. Reason: App Router keeps server data access close to routes and avoids legacy Pages Router split-brain.
- React Server Components by default; Client Components only for browser state, effects, event handlers, and third-party browser widgets. Reason: the default path should ship less JavaScript.
- SQLite schema managed through SQL migrations in `db/migrations`. Reason: SQLite is the source of truth; generated ORM drift is harder to audit in small SaaS projects.
- `better-sqlite3` for embedded deployments or Turso/libSQL for managed edge-friendly SQLite. Reason: choose one database driver per app and keep the SQL dialect portable.
- Zod for all external input validation. Reason: route handlers, server actions, webhooks, and forms need one shared validation language.
- Vitest for unit tests and Playwright for critical auth/billing flows. Reason: cheap business-rule tests plus a small number of real browser checks catch most regressions.

## Folder Structure

```text
app/
  (marketing)/             public pages, pricing, blog
  (app)/dashboard/         authenticated product surface
  api/                     route handlers for webhooks and external APIs
components/
  ui/                      generic primitives with no product knowledge
  forms/                   form components paired with server actions
  product/                 domain-specific reusable UI
db/
  migrations/              ordered SQL migrations, never edited after merge
  schema.sql               latest full schema snapshot
  seed.ts                  deterministic local seed data
lib/
  auth/                    session, current user, authorization helpers
  db/                      connection, query helpers, transactions
  env.ts                   typed environment validation
  validators/              Zod schemas shared by UI and server
server/
  actions/                 server actions grouped by domain
  services/                business use cases, no React imports
  repositories/            SQL access only, no HTTP or UI knowledge
tests/
  unit/                    pure services and validators
  e2e/                     Playwright flows for signup, login, billing
```

Reason: feature code flows from UI to server action to service to repository. SQL stays behind repositories, while business rules stay out of React components.

## Naming Conventions

- Route segments use kebab-case: `app/(app)/billing-history/page.tsx`. Reason: URLs are public API.
- Components use PascalCase files: `SubscriptionStatus.tsx`. Reason: component names match imports and React DevTools.
- Server actions end with `.action.ts`: `server/actions/update-plan.action.ts`. Reason: mutations are easy to search and review.
- Services end with `.service.ts`; repositories end with `.repository.ts`. Reason: business logic and SQL access are intentionally separate.
- Zod schemas end with `.schema.ts` and export both `Input` and `Output` types when transforms exist. Reason: transformed data should not be confused with raw user input.

## Dev Commands

```bash
pnpm dev                  # local Next.js server
pnpm lint                 # eslint and TypeScript lint rules
pnpm typecheck            # tsc --noEmit
pnpm test                 # Vitest unit tests
pnpm test:e2e             # Playwright critical paths
pnpm db:migrate           # apply pending SQL migrations
pnpm db:reset             # recreate local SQLite DB and seed data
```

Reason: every routine command is scriptable and CI-friendly. Do not invent ad hoc one-off database or build commands.

## SQL And Migration Rules

- Every schema change gets a new migration named `YYYYMMDDHHMM_description.sql`. Reason: chronological names make production order unambiguous.
- Never edit a merged migration. Add a follow-up migration instead. Reason: deployed databases cannot replay your local rewrite.
- Wrap multi-step migrations in a transaction when SQLite supports the statements. Reason: partially-applied schema changes are harder to recover than failed migrations.
- Keep foreign keys enabled with `PRAGMA foreign_keys = ON` on every connection. Reason: SQLite does not save you unless you ask it to.
- Use integer primary keys for internal IDs and stable public IDs such as `cuid2` or UUID text for URLs. Reason: public IDs should not leak row counts.
- Store money as integer minor units plus a currency code. Reason: decimal floating point corrupts billing math.
- Use soft deletes only when the product needs recovery or audit. Reason: soft deletes complicate unique constraints and queries.
- Add indexes in the same migration as the query pattern they support. Reason: indexes are product behavior, not cleanup.

## Data Access Pattern

Repositories own SQL:

```ts
export function findWorkspaceBySlug(slug: string) {
  return db.prepare("select * from workspaces where slug = ?").get(slug);
}
```

Services own decisions:

```ts
export async function renameWorkspace(userId: string, workspaceId: string, name: string) {
  await requireWorkspaceRole(userId, workspaceId, "admin");
  return workspaceRepository.updateName(workspaceId, name);
}
```

Reason: SQL helpers should not know who is allowed to do something, and services should not hand-build SQL strings.

## Route Handlers And Server Actions

- Use server actions for first-party form mutations inside the app. Reason: they keep validation, mutation, and revalidation close to the UI.
- Use route handlers for webhooks, third-party callbacks, file downloads, and public APIs. Reason: those need explicit HTTP semantics.
- Validate every action and route handler input with Zod before touching services. Reason: TypeScript does not validate runtime input.
- Return typed result objects from actions: `{ ok: true, data }` or `{ ok: false, fieldErrors, formError }`. Reason: UI error handling stays predictable.
- Call `revalidatePath` or `revalidateTag` only after successful mutation. Reason: failed writes should not invalidate stable cache entries.

## Component Patterns

- Default to Server Components for pages, layouts, and read-only product views. Reason: data fetching belongs on the server unless the user is actively editing.
- Put `"use client"` at leaf components, not page roots. Reason: one interactive control should not force an entire dashboard into the client bundle.
- Keep forms split into `Form.tsx`, `*.schema.ts`, and `*.action.ts`. Reason: validation, UI, and mutation evolve at different speeds.
- UI primitives in `components/ui` cannot import from `server`, `db`, or product services. Reason: primitives must stay reusable and safe for client usage.
- Domain components in `components/product` can compose primitives but should not query the database. Reason: data access belongs in routes/pages/actions.

## Auth And Authorization

- `currentUser()` may identify the session; it must not imply permission. Reason: authentication and authorization are different checks.
- Every workspace-scoped mutation calls an authorization helper in the service layer. Reason: route-level checks are easy to bypass when code is reused.
- Store webhook secrets and OAuth credentials in validated environment variables only. Reason: missing secrets should fail at boot, not mid-request.
- Do not expose raw database IDs to clients when the route can use public IDs. Reason: predictable IDs make scraping and authorization bugs worse.

## Environment Variables

Define `lib/env.ts` with one Zod object for all required variables:

```ts
const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  AUTH_SECRET: z.string().min(32),
});
```

Reason: deployments should fail fast when configuration is missing or malformed.

## Error Handling

- Use expected domain errors for user-fixable states, such as duplicate slug or missing permission. Reason: these become form errors, not 500s.
- Log unexpected errors once at the boundary. Reason: repeated logging in repositories, services, and routes creates noise without context.
- Never return raw SQL errors to the browser. Reason: database messages can leak schema and implementation details.

## Testing Rules

- Unit test validators, services, and repository edge cases with temporary SQLite databases. Reason: SQLite behavior matters and mocks miss constraints.
- E2E test signup, login, workspace creation, and billing portal access. Reason: these flows cross auth, database, and UI boundaries.
- Add a regression test for every production bug before fixing it. Reason: the bug already proved the old test suite was too weak.
- Do not snapshot entire pages. Reason: snapshots create noise and rarely prove product behavior.

## Anti-Patterns

- Do not put database queries in Client Components. Reason: secrets and server-only drivers must never reach the browser.
- Do not use raw `process.env` across the app. Reason: scattered configuration hides missing variables until runtime.
- Do not create generic `utils.ts` dumping grounds. Reason: vague modules become unowned dependency magnets.
- Do not mutate data in GET route handlers. Reason: crawlers and prefetching can trigger GET requests.
- Do not build SQL with string interpolation. Reason: parameterized statements prevent injection and keep query plans stable.
- Do not add Prisma, Drizzle, or another ORM after choosing raw SQLite migrations unless the team explicitly migrates the whole data layer. Reason: two schema sources create drift.
- Do not store Stripe or provider payloads without verifying signatures. Reason: unsigned webhooks are attacker-controlled input.
- Do not make every component configurable with large prop bags. Reason: product components should encode product decisions.

## Greenfield Smoke Test

After creating a fresh project, paste this file as `CLAUDE.md` and ask Claude Code:

```text
Create a workspace settings page that lets an admin rename a workspace.
```

Expected behavior: Claude should create or reference a Zod schema, a server action, a service authorization check, a repository update query, and a Server Component page with a small Client Component form. It should not ask which router, database style, migration approach, or validation library to use.
