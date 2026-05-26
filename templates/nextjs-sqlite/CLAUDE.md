# CLAUDE.md: Next.js 15 + SQLite SaaS

Use this file as the operating contract for a greenfield SaaS project built with Next.js 15 App Router, TypeScript, SQLite, and server-first React.

## Stack And Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode. Do not introduce `any` unless it is isolated at an integration boundary and explained.
- SQLite through `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted edge-compatible deployments.
- Zod for request, form, and environment validation.
- Drizzle or hand-written SQL migrations. Pick one and keep it consistent.
- Tailwind CSS is acceptable for styling, but component behavior must not depend on utility-class string tricks.

Reason: this stack is small, fast, debuggable, and easy to deploy without turning a young SaaS into a distributed systems project.

## Folder Structure

Use this structure unless there is a strong reason not to:

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  domain/
db/
  client.ts
  schema.ts
  migrations/
  queries/
lib/
  auth/
  billing/
  env.ts
  errors.ts
  rate-limit.ts
  result.ts
server/
  actions/
  jobs/
  services/
tests/
  unit/
  integration/
```

Rules:

- `app/` owns routes, layouts, loading states, and server actions that are directly coupled to UI.
- `components/ui/` contains reusable primitives only. No product-specific data fetching here.
- `components/domain/` contains product-specific UI that receives already-loaded data.
- `db/queries/` contains database access functions. Route handlers and components must not inline SQL.
- `server/services/` contains business workflows that can be tested without rendering React.

Reason: clear boundaries keep Claude Code from scattering SQL, auth, and side effects through UI files.

## Naming Conventions

- React components: `PascalCase.tsx`.
- Server actions: `action-name.action.ts`.
- Database queries: `entity-queries.ts`.
- Zod schemas: `entity-schema.ts`.
- Tests mirror the file or workflow under test.
- Database tables use `snake_case`; TypeScript objects use `camelCase`.

Reason: names should reveal runtime behavior and ownership before a file is opened.

## SQL And Migration Conventions

- Every schema change gets a migration. Never edit an applied migration.
- Migrations must be forward-only. Add a separate rollback note when the change is risky.
- Use explicit column lists in `INSERT` statements.
- Do not use `SELECT *` outside one-off debug scripts.
- Wrap multi-step writes in transactions.
- Add indexes for foreign keys and high-cardinality lookup columns used in production queries.
- Store money as integer minor units plus currency code.
- Store timestamps as ISO strings or integer milliseconds consistently; do not mix formats.
- Enable foreign keys for local SQLite connections:

```ts
db.pragma("foreign_keys = ON");
```

Reason: SQLite is reliable when constraints, transactions, and migrations are treated seriously.

## Data Access Pattern

Use query functions that return typed domain data:

```ts
export function getWorkspaceBySlug(slug: string): Workspace | null {
  return db.prepare(
    `select id, name, slug, created_at from workspaces where slug = ?`,
  ).get(slug) as Workspace | null;
}
```

Do not return raw database rows across the whole app. Convert at the query boundary.

Reason: the database can stay simple while the rest of the app gets stable types.

## Server Actions

Server actions must:

1. Validate input with Zod.
2. Check authentication and authorization.
3. Call a service or query function.
4. Return a small typed result object.
5. Revalidate only the paths or tags that changed.

Do not put business rules directly into form components.

Reason: server actions are entry points, not a replacement for an application layer.

## Component Patterns

- Prefer Server Components for data loading.
- Use Client Components only for interactivity, browser APIs, optimistic UI, or local state.
- Pass data into Client Components as serializable props.
- Keep forms small. Move parsing and mutation logic to server actions.
- Avoid nested cards and decorative layout wrappers in product screens.

Reason: Server Components keep SaaS pages fast and reduce client-side state bugs.

## Auth And Authorization

- Authentication answers "who is this user?"
- Authorization answers "can this user access this workspace/resource?"
- Every query or service that reads workspace-owned data must receive `workspaceId` or a verified membership object.
- Never trust route params for ownership.
- Keep session lookup in `lib/auth/` and permission checks in small reusable functions.

Reason: most SaaS security bugs are tenant-boundary mistakes, not cryptography mistakes.

## Environment Variables

Create `lib/env.ts` and validate all required variables once at process startup:

```ts
import { z } from "zod";

const Env = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().optional(),
});

export const env = Env.parse(process.env);
```

Do not read `process.env` throughout the app.

Reason: missing config should fail early and loudly.

## Billing Rules

- Billing webhooks must be idempotent.
- Store external provider IDs separately from internal IDs.
- Never grant paid access from the client after checkout success alone. Wait for a verified webhook or server-side provider check.
- Log billing state changes without logging full payment details.

Reason: checkout redirects are not proof of payment.

## Error Handling

- Use expected result objects for validation and business errors.
- Throw only for unexpected failures.
- Do not expose raw database, auth, or billing errors to users.
- Include enough server-side context to debug without storing secrets.

Reason: product flows need useful user feedback while logs stay safe.

## Dev Commands

Use commands like these and keep them current in `package.json`:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
```

Before a PR is ready, run lint, typecheck, tests, and migrations against a disposable local database.

Reason: a SaaS project should prove that UI, types, and schema changes still agree.

## Testing Priorities

1. Unit test services and query mapping.
2. Integration test server actions with a temporary SQLite database.
3. Test auth and tenant boundaries before polishing UI.
4. Snapshot only stable generated output, not entire pages.

Reason: tests should protect revenue and data boundaries first.

## What We Do Not Do

- Do not add a job queue until a recurring task actually needs retries or scheduling.
- Do not add Postgres only because the project may grow someday.
- Do not call third-party APIs directly from React components.
- Do not store secrets, API keys, or tokens in SQLite.
- Do not use global mutable singletons for per-user state.
- Do not add generic abstractions before there are two real call sites.
- Do not build an admin panel before the underlying service functions are tested.

Reason: early SaaS projects die from accidental complexity as often as from missing features.

## Claude Code Behavior

When working in this project:

- Read `db/schema.ts`, `lib/env.ts`, and the relevant route before editing.
- Preserve the folder boundaries in this file.
- Ask before changing the database provider, auth provider, or billing provider.
- Prefer small PRs with a migration, tests, and a short verification note.
- If a request touches money, auth, or tenant data, identify the risk before editing.

Reason: Claude Code should act like a careful senior engineer in a revenue-bearing SaaS app.
