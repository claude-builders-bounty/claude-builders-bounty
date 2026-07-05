# CLAUDE.md - Next.js 15 + SQLite SaaS

This project is a production-minded SaaS app built with Next.js 15 App Router,
TypeScript, SQLite, and server-first React. Follow these rules unless a human
explicitly changes the architecture.

## Claude Operating Mode

- Start every task by identifying which boundary is touched: route, server
  action, query, migration, component, or test; reason: most SaaS bugs come from
  mixing data, permission, and UI concerns.
- Prefer small, reviewable changes with a matching test; reason: SaaS behavior
  often affects billing, access, or customer data.
- Before editing, inspect the nearest existing pattern and follow it unless it
  conflicts with this file; reason: consistency is more valuable than a clever
  one-off.
- When requirements are ambiguous, choose the server-side, least-privilege
  option and state the assumption; reason: auth and billing mistakes are costly.

## Stack And Versions

- Use Next.js 15 with the App Router in `app/`; reason: routing, data loading,
  metadata, and server actions should live in the same convention-driven tree.
- Use TypeScript in strict mode; reason: SaaS billing, auth, and data workflows
  need compile-time checks before users touch them.
- Use SQLite through `better-sqlite3` for local/single-node deployments or Turso
  for hosted/libSQL deployments; reason: both keep the SQL model explicit and
  avoid a heavy ORM for a small SaaS.
- Use Drizzle only when the project already wants typed schema helpers; reason:
  raw SQL plus tiny typed helpers is often enough, but Drizzle is a good fit
  when migrations and generated types are already part of the workflow.
- Use React Server Components by default; reason: secrets, database access, and
  authorization checks belong on the server.
- Use Tailwind plus shadcn/ui, CSS modules, or the existing design system, but
  keep business state out of CSS; reason: UI styling should not hide data or
  permission logic.

## Default Implementation Choices

Use this table when starting a greenfield app. If the existing project already
made a different choice, follow the project and document the mismatch in the PR.

| Boundary | Default | Reason |
| --- | --- | --- |
| Runtime | Node.js 22 LTS | Native SQLite drivers and auth libraries are most predictable on the Node runtime. |
| Package manager | Keep the detected lockfile; otherwise use `npm` | Mixing package managers causes noisy diffs and broken installs. |
| Database | `better-sqlite3` locally, Turso/libSQL for hosted deployments | Local development stays fast while production has a managed SQLite option. |
| ORM/query layer | Drizzle for schema and typed queries; raw SQL only for targeted migrations | Typed schema helps Claude preserve table names, relation shape, and parameterized queries. |
| Auth | Auth.js/NextAuth v5 with server-side session helpers | It works with App Router and keeps session checks close to server actions. |
| Validation | Zod at every server boundary | User input, webhook payloads, and env vars must fail before mutation. |
| Payments | Stripe Checkout plus signed webhooks | SaaS money paths need provider-side pricing and idempotent event handling. |
| Tests | Vitest for units/integration, Playwright for critical flows | This covers validators, DB-backed actions, and browser-level paid workflows. |

Reason: Claude should not pause a greenfield task to ask which ordinary SaaS
defaults to use. It should make these choices, then adapt only when the project
already contains a stronger local convention.

## Project Structure

```text
app/
  (marketing)/              Public pages and pricing copy.
  (app)/                    Authenticated product surface.
  api/                      Route handlers for webhooks and external clients.
  actions/                  Server actions grouped by domain.
components/
  ui/                       Reusable presentational primitives.
  forms/                    Client form shells only when interactivity is needed.
  tables/                   Dense SaaS data views.
db/
  client.ts                 Database connection factory.
  schema.sql                Canonical schema for fresh installs.
  migrations/               Numbered forward-only SQL migrations.
  queries/                  Typed query helpers by aggregate/root concept.
lib/
  auth.ts                   Session and user lookup helpers.
  env.ts                    Runtime env validation.
  permissions.ts            Role and ownership checks.
  validators/               Zod schemas shared by forms and actions.
  billing.ts                Provider event and entitlement helpers.
tests/
  unit/                     Pure functions and validators.
  integration/              DB-backed actions and route handlers.
  e2e/                      Critical user paths.
```

Reason: folders follow runtime boundaries. Server-only code stays in `db/` and
`lib/`; UI composition stays in `app/` and `components/`; domain mutations live
in `app/actions/` where App Router expects them.

## Dev Commands

- `npm run dev`: start the app locally.
- `npm run lint`: run ESLint and framework lint checks.
- `npm run typecheck`: run `tsc --noEmit`.
- `npm run test`: run unit and integration tests.
- `npm run test:e2e`: run browser tests for signup, login, billing, and the main
  paid workflow.
- `npm run db:migrate`: apply pending SQL migrations.
- `npm run db:reset`: rebuild the local SQLite database from schema plus
  migrations.
- If the project uses `pnpm` or `bun`, keep the same script names; reason:
  Claude should not guess package-manager-specific command names inside tasks.

Reason: every PR should prove type safety, lint cleanliness, and database
compatibility without relying on a deployed environment.

## CI And Release Gates

Every pull request should pass the same gates locally and in CI:

```bash
npm run lint
npm run typecheck
npm run test
npm run db:migrate -- --dry-run
npm run build
```

If the project does not support a dry-run migration command, run migrations
against a temporary SQLite database in CI instead.

Required CI jobs:

- `lint-and-types`: run lint plus `tsc --noEmit`; reason: App Router errors
  often surface as type or import-boundary failures before runtime.
- `unit-and-integration`: run Vitest with a temporary SQLite database; reason:
  server actions and query helpers need database-backed regression coverage.
- `migration-check`: apply all migrations to an empty database and to the last
  committed schema snapshot when available; reason: SaaS deploys cannot rely on
  manual database repair.
- `build`: run the production Next.js build; reason: server/client boundary and
  route handler mistakes often fail only during build.
- `e2e-critical-path`: run Playwright for signup, login, primary paid workflow,
  and billing cancellation when those features exist; reason: money and access
  flows deserve browser-level proof.

Do not merge a schema, auth, billing, or permission change without a matching CI
gate. If the test would be too expensive, document the skipped risk in the PR.

## Environment Rules

- Read environment variables only from `lib/env.ts`; reason: validation,
  defaults, and error messages should be centralized.
- Never read `process.env` in client components; reason: client bundles must not
  leak secrets.
- Required variables should fail fast during server startup or first server
  action call; reason: misconfigured billing/auth should not fail halfway through
  a user flow.
- Keep `.env.example` current whenever env requirements change; reason: new
  deployments should be reproducible.

Example environment contract:

```ts
// lib/env.ts
import { z } from "zod";

const serverEnvSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  AUTH_URL: z.string().url().optional(),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_").optional(),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_").optional(),
  TURSO_AUTH_TOKEN: z.string().optional(),
});

export const env = serverEnvSchema.parse(process.env);
```

```dotenv
# .env.example
DATABASE_URL=file:./data/dev.sqlite
AUTH_SECRET=replace-with-32-plus-random-characters
AUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
TURSO_AUTH_TOKEN=
```

Reason: env validation belongs in one server-only module. Claude must update
this contract before adding a feature that reads a new secret or deployment
variable.

## SQLite And Migration Rules

- Write migrations as numbered SQL files, for example
  `db/migrations/0007_add_team_members.sql`; reason: review order and production
  rollout order must be obvious.
- Migrations are forward-only. Do not edit a migration after it has shipped;
  reason: deployed databases may already have applied it.
- Every table must include a stable text primary key or integer primary key,
  `created_at`, and `updated_at` where updates are possible; reason: SaaS audit
  and support workflows depend on timestamps.
- Prefer non-sequential text IDs such as cuid2 or UUIDv7 for tenant-visible
  records; reason: public URLs, invoices, invites, and support links should not
  leak customer counts or make enumeration easy.
- Choose one timestamp encoding per project, preferably ISO text for
  human-readable audit rows or integer milliseconds for high-volume sortable
  rows, and do not mix encodings in the same database; reason: SQLite will not
  protect the team from inconsistent date comparisons.
- Use `deleted_at` soft deletes for user-facing or billing-adjacent records;
  reason: support, audit, and recovery workflows often need the original row.
- Use foreign keys and enable `PRAGMA foreign_keys = ON` when opening SQLite
  connections; reason: relational integrity should not depend on application
  discipline.
- Wrap multi-row writes in transactions; reason: plan changes, invites, and
  billing updates must not partially commit.
- Prefer explicit SQL query helpers over string-building in actions; reason:
  mutations are easier to review and test when SQL lives near the domain.
- Add an integration test for every migration that changes constraints or data
  shape; reason: SQLite accepts many shapes that only fail at runtime.

Example migration shape:

```sql
-- db/migrations/0007_add_team_members.sql
CREATE TABLE team_members (
  id TEXT PRIMARY KEY,
  team_id TEXT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TEXT,
  UNIQUE(team_id, user_id)
);

CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_active_team_id
  ON team_members(team_id)
  WHERE deleted_at IS NULL;
```

Reason: migrations should show constraints, ownership relationships, and query
indexes in the same review.

## Database Client Contracts

Use one database client module and import it from server-only code. Do not open
SQLite connections inside request handlers or client components.

Local `better-sqlite3` shape:

```ts
// db/client.ts
import "server-only";

import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { env } from "@/lib/env";
import * as schema from "./schema";

const sqlite = new Database(env.DATABASE_URL.replace(/^file:/, ""));
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("foreign_keys = ON");

export const db = drizzle(sqlite, { schema });
```

Hosted Turso/libSQL shape:

```ts
// db/client.ts
import "server-only";

import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import { env } from "@/lib/env";
import * as schema from "./schema";

const client = createClient({
  url: env.DATABASE_URL,
  authToken: env.TURSO_AUTH_TOKEN,
});

export const db = drizzle(client, { schema });
```

Rules:

- Use one of these shapes, not both in the same runtime path; reason: accidental
  dual clients create inconsistent connection behavior.
- Keep `db/schema.ts` or `db/schema.sql` as the canonical source of tables;
  reason: migrations and query helpers need one truth source.
- Put seed scripts in `scripts/seed.ts` and make them idempotent; reason: Claude
  should be able to reset a demo database without creating duplicate tenants.
- Never run `db:push` against production; reason: production schema changes need
  reviewed migrations.

## Naming Conventions

- Route segments use kebab-case, for example `app/(app)/team-settings/page.tsx`;
  reason: URLs should be readable and stable.
- Server actions use verb-first names, for example `createTeamAction` or
  `updateBillingEmailAction`; reason: mutation intent should be obvious.
- Query helpers use noun-first names, for example `teamById` or
  `activeSubscriptionForTeam`; reason: read paths should describe the returned
  data.
- Zod schemas end with `Schema`, for example `createInviteSchema`; reason:
  validators should be easy to find and reuse.
- Test files mirror the unit under test, for example
  `tests/integration/actions/create-team.test.ts`; reason: failed tests should
  point to the owning code quickly.

## Data Access Patterns

- Server components may call read-only query helpers directly.
- Server actions and route handlers are the only places that may perform writes.
- Every write path must call `requireUser()` or a more specific permission helper
  before touching the database.
- Validate untrusted input with Zod before constructing SQL parameters.
- Return small DTOs from query helpers instead of raw database rows; reason: UI
  components should not learn storage details.

Example server action pattern:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { createInviteSchema } from "@/lib/validators/invites";
import { requireTeamRole } from "@/lib/permissions";
import { createInvite } from "@/db/queries/invites";

export async function createInviteAction(input: unknown) {
  const user = await requireTeamRole("admin");
  const data = createInviteSchema.parse(input);

  await createInvite({
    teamId: user.teamId,
    email: data.email,
    role: data.role,
    invitedByUserId: user.id,
  });

  revalidatePath("/team-settings/members");
  return { ok: true };
}
```

Reason: validation, authorization, mutation, and revalidation should be visible
in one reviewable flow.

## App Router Patterns

- Use `page.tsx` for route composition and load data there or in colocated
  server helpers.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` for real route states, not
  ad hoc spinners embedded deep in business components.
- Use server actions for form submissions that mutate first-party data.
- Use route handlers for webhooks, third-party callbacks, public APIs, and
  streaming responses.
- Revalidate by path or tag after writes; reason: users should see the result of
  their action without a manual refresh.

## Component Patterns

- Components are server components unless they need browser state, effects, or
  event handlers.
- Client components receive serializable props only; reason: they cross the
  server/client boundary.
- Put form interactivity in a small client shell and keep validation/business
  logic in shared schemas and server actions.
- UI primitives in `components/ui/` must not import app-specific queries or
  actions; reason: reusable components should remain portable.
- Empty, loading, error, and permission-denied states are part of the component
  contract; reason: SaaS users spend real time in edge states.

## Auth, Tenancy, And Permissions

- All tenant-scoped queries must include `team_id` or the relevant ownership key.
- Do not trust IDs from forms or URLs until ownership is checked server-side.
- Keep role checks in `lib/permissions.ts`; reason: scattered role logic becomes
  inconsistent.
- For admin routes, check both authentication and role before loading privileged
  data.
- For webhooks, verify signatures before parsing business payloads.
- Prefer database-enforced uniqueness for memberships, slugs, billing customers,
  and provider event IDs; reason: concurrency should not create duplicate tenant
  state.

## Billing And Entitlements

- Treat billing provider events as eventually consistent.
- Store provider event IDs and ignore duplicates.
- Separate plan state from usage counters; reason: plan changes and metered
  usage have different lifecycles.
- Check entitlements in the server action or route handler that performs the
  paid action, not only in the UI.
- Keep provider IDs out of client components unless they are explicitly public;
  reason: billing identifiers are support data, not UI state.

## Deployment Notes

- Vercel is fine for Turso/libSQL deployments; reason: remote SQLite access works
  well with serverless request lifecycles.
- For `better-sqlite3`, prefer a single Node server or container with persistent
  disk; reason: local SQLite files do not belong in stateless serverless
  instances.
- Run migrations as a release step before serving new code; reason: request
  handlers should not race to change schema.
- Add a health check that verifies app boot, env validation, and database
  connectivity; reason: uptime checks should catch broken deploy configuration.

## Testing Expectations

- Unit test pure validators, formatting, and permission helpers.
- Integration test server actions with a temporary SQLite database.
- Test migrations against an empty database and at least one previous schema
  when practical.
- E2E test the money path: signup, create team, use the primary feature, change
  plan, and cancel.
- Add regression tests for every fixed bug before changing implementation.
- For greenfield work, ask Claude to propose the first migration and one server
  action before writing code; reason: this proves the project context is loaded
  and the architecture is understood.

## Anti-Patterns

- Do not put database calls in client components; reason: it leaks boundaries and
  cannot safely protect secrets.
- Do not bypass migrations with `CREATE TABLE IF NOT EXISTS` inside request
  handlers; reason: request traffic should not mutate schema.
- Do not add a generic repository layer unless it removes real duplication;
  reason: SQL is clearer than a thin abstraction that hides important joins.
- Do not use `any` to silence domain or billing types; reason: unclear money and
  permission types become production bugs.
- Do not trust optimistic UI as authorization; reason: users can call server
  actions directly.
- Do not add dependencies for one-line helpers; reason: SaaS apps already carry
  enough supply-chain surface.
- Do not accept a webhook without idempotency storage; reason: payment providers
  retry and can deliver events out of order.
- Do not hide permission failures as empty states; reason: support and audit
  workflows need clear access-denied behavior.

## Greenfield Smoke Prompt

After copying this file into a new project, run this prompt in Claude Code:

```text
Read CLAUDE.md and propose the first database migration, App Router structure,
and server-action pattern for a tiny B2B todo SaaS. Do not write files yet.
```

Expected behavior:

- Claude chooses Next.js 15 App Router, TypeScript, and SQLite without asking
  for stack clarification.
- Claude proposes tenant-scoped tables such as teams, users, memberships, and
  todos.
- Claude keeps reads in server components or query helpers.
- Claude keeps writes in server actions with Zod validation and permission
  checks.
- Claude names at least one migration and test path.

## PR Checklist

- The change keeps server-only logic out of client bundles.
- SQL changes include a migration and a test.
- New env vars are documented in `.env.example`.
- Mutations validate input and check permissions server-side.
- Lint, typecheck, tests, and relevant E2E flows pass.
- The main user-facing states are covered: loading, empty, error, success, and
  permission denied.
