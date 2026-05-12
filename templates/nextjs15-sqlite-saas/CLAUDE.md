# CLAUDE.md - Next.js 15 SQLite SaaS

This file is the operating contract for a greenfield SaaS app built with
Next.js 15 App Router, TypeScript, SQLite, Drizzle ORM, Better Auth, Tailwind,
and shadcn/ui. Follow these rules unless a human explicitly changes the stack.

## Stack And Versions

Use these choices without asking for alternatives:

| Layer | Decision | Reason |
| --- | --- | --- |
| Framework | Next.js 15 App Router | Reason: App Router keeps data loading, layouts, route handlers, metadata, and Server Components in one routing model. |
| React mode | Server Components by default | Reason: most SaaS pages render account data and tables without client-side state. |
| Runtime | Node.js for all database routes | Reason: `better-sqlite3` and most SQLite drivers are not Edge-compatible. |
| Language | TypeScript with `strict: true` | Reason: SaaS billing, auth, and tenant data need type failures before runtime. |
| Package manager | `pnpm` | Reason: deterministic installs and fast workspaces are better for CI and templates. |
| Database | SQLite locally, Turso/libSQL in hosted environments | Reason: SQLite keeps setup simple while Turso provides a production path without changing the SQL model. |
| ORM | Drizzle ORM and Drizzle Kit | Reason: Drizzle keeps schema, SQL shape, and migrations visible instead of hiding them behind generated clients. |
| Auth | Better Auth with Drizzle adapter | Reason: it fits App Router route handlers and avoids custom auth tables early in the project. |
| Validation | Zod at every external boundary | Reason: route handlers, forms, webhooks, and env vars all receive untrusted data. |
| Styling | Tailwind plus shadcn/ui | Reason: this gives a consistent component base without inventing a design system first. |
| Unit tests | Vitest | Reason: it is fast for TypeScript server utilities, actions, and data modules. |
| E2E tests | Playwright | Reason: authentication, onboarding, and billing flows need browser-level confidence. |

## Dev Commands

Assume these scripts exist in `package.json`; add them if they are missing:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "check": "pnpm lint && pnpm typecheck && pnpm test",
    "test": "vitest run",
    "test:watch": "vitest",
    "e2e": "playwright test",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio",
    "db:seed": "tsx db/seed.ts"
  }
}
```

Reason: Claude Code should run the narrowest useful command first, then
`pnpm check` before proposing a PR.

## Folder Structure

Create this structure first and keep new code inside it:

```text
app/
  (marketing)/
    page.tsx
  (auth)/
    sign-in/page.tsx
    sign-up/page.tsx
  (app)/
    dashboard/page.tsx
    settings/page.tsx
  api/
    auth/[...all]/route.ts
    webhooks/stripe/route.ts
components/
  ui/
  forms/
  data-display/
db/
  client.ts
  schema/
    auth.ts
    billing.ts
    orgs.ts
  migrations/
  queries/
    members.ts
    orgs.ts
  seed.ts
lib/
  auth.ts
  env.ts
  errors.ts
  ids.ts
  money.ts
server/
  actions/
  services/
tests/
  factories/
  unit/
  e2e/
```

Rules:

- Route groups must separate public marketing, auth screens, and logged-in app
  screens. Reason: layout, metadata, and authorization concerns should not leak
  between user journeys.
- `db/schema/*` owns table definitions only. Reason: migrations and query code
  should review schema separately from business logic.
- `db/queries/*` owns SQL reads and writes. Reason: pages and actions should not
  scatter query details across the app.
- `server/actions/*` owns form mutations. Reason: mutation boundaries need
  validation, authorization, revalidation, and typed return values in one place.
- `server/services/*` owns workflows that call multiple query modules. Reason:
  cross-table business rules should not live in React components.
- `lib/env.ts` is the only file allowed to read `process.env` directly. Reason:
  missing secrets should fail during boot, not during a customer request.
- `components/ui/*` contains generated shadcn primitives only. Reason: local app
  components should not be overwritten when shadcn components are updated.

## Naming Conventions

| Thing | Convention | Reason |
| --- | --- | --- |
| Route folders | kebab-case | Reason: URLs stay stable and readable. |
| React components | PascalCase file and export names | Reason: component imports remain obvious in mixed server/client files. |
| Utility modules | kebab-case or short domain nouns | Reason: modules like `money.ts` and `ids.ts` stay easy to scan. |
| Server actions | `verbNounAction` | Reason: forms can import mutations without ambiguous names. |
| Query functions | `getNoun`, `listNouns`, `insertNoun`, `updateNoun`, `deleteNoun` | Reason: reads and writes are clear at call sites. |
| Database tables | snake_case plural nouns | Reason: SQL stays idiomatic and migrations remain readable. |
| Database columns | snake_case | Reason: SQL queries should not mix JavaScript casing with database casing. |
| IDs | `text` ULID strings | Reason: IDs can be generated before insert and do not reveal row counts. |
| Money | integer cents | Reason: floating point math creates billing errors. |
| Timestamps | integer milliseconds named `created_at`, `updated_at`, `deleted_at` | Reason: SQLite stores integers reliably and JavaScript can compare them directly. |

## Database And Migration Rules

Use Drizzle schema as the source of truth.

- Every table has `id text primary key`, `created_at integer not null`, and
  `updated_at integer not null`. Reason: all SaaS records need stable identity
  and audit timing.
- Tenant-owned tables include `org_id text not null` and an index on `org_id`.
  Reason: every query must constrain tenant data by organization.
- Use soft delete with `deleted_at integer` for customer-owned business records.
  Reason: accidental deletion and billing disputes require recovery context.
- Use hard delete only for ephemeral tokens, invites, and sessions. Reason:
  these records have limited security lifetimes and do not carry business value.
- Add foreign keys in schema and enable SQLite foreign keys in the client.
  Reason: tests should catch orphaned rows before production data does.
- Add indexes with the query in mind, not as decoration. Reason: SQLite performs
  well when high-cardinality filters are indexed intentionally.
- Migrations are append-only after merge. Reason: teammates and production
  environments may already have run old migration files.
- Never edit an applied migration. Reason: changing historical migrations causes
  local, CI, and production databases to diverge.
- Put data backfills in explicit migration scripts or one-shot jobs. Reason:
  schema changes and data changes need independent review.
- Wrap multi-table writes in transactions. Reason: billing, membership, and
  invitation flows must not partially commit.
- Use prepared statements or Drizzle query builders for user input. Reason:
  string-concatenated SQL invites injection bugs.

Example schema pattern:

```ts
import { index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";
import { createId } from "@/lib/ids";

export const orgs = sqliteTable("orgs", {
  id: text("id").primaryKey().$defaultFn(createId),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp_ms" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp_ms" }).notNull(),
});

export const members = sqliteTable(
  "members",
  {
    id: text("id").primaryKey().$defaultFn(createId),
    orgId: text("org_id").notNull().references(() => orgs.id),
    userId: text("user_id").notNull(),
    role: text("role", { enum: ["owner", "admin", "member"] }).notNull(),
    createdAt: integer("created_at", { mode: "timestamp_ms" }).notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" }).notNull(),
  },
  (table) => ({
    orgUserIdx: index("members_org_user_idx").on(table.orgId, table.userId),
  }),
);
```

## Data Access Pattern

Do not query the database from React components. Use `db/queries/*`.

```ts
// db/queries/members.ts
import { and, eq } from "drizzle-orm";
import { db } from "@/db/client";
import { members } from "@/db/schema/orgs";

export async function listMembers(orgId: string) {
  return db.query.members.findMany({
    where: and(eq(members.orgId, orgId)),
    orderBy: (member, { asc }) => [asc(member.createdAt)],
  });
}
```

Reason: centralized query modules make tenant filters, indexes, tests, and
authorization reviews possible.

## Server Component Rules

- Pages and layouts are Server Components unless they need browser state,
  effects, or event handlers. Reason: server rendering removes unnecessary
  JavaScript from dashboard pages.
- Fetch data in the closest route segment that owns the data. Reason: layouts
  should not over-fetch for pages that do not use the data.
- Call `requireUser()` or `requireOrg()` before loading protected data. Reason:
  redirecting before data access reduces accidental leakage.
- Pass plain serializable props into Client Components. Reason: React cannot
  safely serialize database clients, dates with methods, or class instances.
- Do not place secrets or privileged objects in props. Reason: Client Component
  props are visible in the browser payload.

## Client Component Rules

Add `"use client"` only to files that need it.

- Use Client Components for interactive widgets, menus, dialogs, optimistic UI,
  and local form state. Reason: these features require browser APIs.
- Keep Client Components as leaves under Server Components. Reason: fewer client
  boundaries reduce bundle size and hydration work.
- Do not fetch initial page data in `useEffect`. Reason: App Router can fetch on
  the server and stream the result faster with better SEO.
- Prefer Server Actions for first-party mutations. Reason: forms can share
  validation, auth, revalidation, and error handling.

## Server Actions Pattern

Every Server Action follows this shape:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireOrg } from "@/lib/auth";
import { createInvite } from "@/server/services/invites";

const inviteInput = z.object({
  email: z.string().email(),
  role: z.enum(["admin", "member"]),
});

export async function inviteMemberAction(input: unknown) {
  const org = await requireOrg();
  const parsed = inviteInput.safeParse(input);

  if (!parsed.success) {
    return { ok: false, fieldErrors: parsed.error.flatten().fieldErrors };
  }

  await createInvite({ orgId: org.id, ...parsed.data });
  revalidatePath("/dashboard/members");
  return { ok: true };
}
```

Rules:

- Accept `unknown` or `FormData`, never trusted typed objects. Reason: callers
  can bypass TypeScript at runtime.
- Validate with Zod inside the action. Reason: Server Actions are public network
  boundaries.
- Derive `userId` and `orgId` on the server. Reason: tenant identity from a form
  field can be forged.
- Return typed success or field errors. Reason: forms need predictable rendering
  without parsing thrown exceptions.
- Revalidate the affected route after writes. Reason: cached Server Components
  must not show stale SaaS state.

## Auth And Authorization

- Use Better Auth route handlers under `app/api/auth/[...all]/route.ts`. Reason:
  auth stays inside the App Router and uses the same deployment target.
- Keep auth helpers in `lib/auth.ts`: `getSession()`, `requireUser()`,
  `requireOrg()`, and `requireRole()`. Reason: call sites should state the
  access level they require.
- Authorization happens in server actions, route handlers, and service functions.
  Reason: UI checks are helpful but not security boundaries.
- Membership roles are `owner`, `admin`, and `member`. Reason: three roles cover
  SaaS administration without over-designing permissions.
- A user can see only rows for organizations where they are an active member.
  Reason: multi-tenant data isolation is the core security rule.
- Invites expire and are single-use. Reason: stale invites become account takeover
  paths.

## API Routes And Webhooks

- Use route handlers for third-party webhooks and public API endpoints only.
  Reason: first-party form mutations should be Server Actions.
- Set `export const runtime = "nodejs"` for handlers that touch SQLite. Reason:
  database drivers need Node APIs.
- Verify webhook signatures before parsing business fields. Reason: untrusted
  requests can spoof billing and account state.
- Store external event IDs in an idempotency table. Reason: providers retry
  webhooks and duplicate processing creates billing bugs.
- Return typed JSON through a small helper in `lib/http.ts`. Reason: status codes
  and error shapes should be consistent.

## Environment Variables

`lib/env.ts` validates and exports all environment variables:

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().optional(),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Do not read `process.env` outside `lib/env.ts`. Reason: missing variables
  should fail once and loudly.
- Keep public env vars prefixed with `NEXT_PUBLIC_`. Reason: unprefixed secrets
  must not reach the browser bundle.
- Do not commit real `.env` values. Reason: secrets belong in deployment
  configuration, not git history.

## Error Handling And Logging

- Throw typed domain errors from services, not strings. Reason: routes and forms
  need stable error handling.
- Show generic messages for auth, billing, and account lookup failures. Reason:
  detailed messages can leak whether an account or resource exists.
- Log request IDs, user IDs, org IDs, and external event IDs when available.
  Reason: SaaS support needs correlation without exposing sensitive payloads.
- Never log access tokens, cookies, webhook secrets, or full payment payloads.
  Reason: logs are copied into external systems and retained longer than code.

## Testing Strategy

- Unit test query modules and services with an isolated SQLite database. Reason:
  mocking SQL hides migration and constraint failures.
- Test Server Actions by calling them with invalid input, unauthorized users, and
  valid input. Reason: actions combine validation, auth, writes, and cache
  revalidation.
- Add Playwright tests for sign-up, sign-in, onboarding, invite acceptance, and
  billing settings. Reason: these flows are where SaaS users lose access or
  money.
- Use factories in `tests/factories/*`. Reason: tests should create valid rows
  without repeating schema details.
- CI must run `pnpm check`, `pnpm build`, and `pnpm e2e` for user-facing changes.
  Reason: type correctness alone does not prove App Router pages render.

## Feature Workflow

When asked to add a feature:

1. Identify the route group and URL.
2. Add or update Drizzle schema.
3. Generate a migration with `pnpm db:generate`.
4. Add query functions in `db/queries/*`.
5. Add service logic in `server/services/*` when more than one table is touched.
6. Add Server Actions for mutations.
7. Render the page as a Server Component and isolate interactive leaves.
8. Add tests for schema constraints, query filters, action validation, and the
   main browser path.
9. Run the narrowest relevant test, then `pnpm check`.

Reason: this sequence keeps data model, authorization, UI, and validation aligned
instead of letting the UI shape the database by accident.

## Common Task Prompts

Use these prompts as the expected interpretation of future work:

- "Add team invitations" means add `invites` schema, migration, queries, service,
  action, dashboard page, email stub, and tests. Reason: an invite feature crosses
  auth, tenant membership, and expiration rules.
- "Add billing settings" means add customer/subscription tables, Stripe webhook
  idempotency, server-only Stripe client, settings page, and Playwright coverage.
  Reason: billing cannot be only a UI integration.
- "Add audit log" means add append-only `audit_events`, service helpers, and
  query filters by `org_id`. Reason: audit trails are security records, not
  mutable activity feeds.
- "Add public API key support" means hash keys at rest, show the token once,
  scope by organization, and audit every use. Reason: API keys are credentials.

## What We Do Not Do

| Anti-pattern | Replacement | Reason |
| --- | --- | --- |
| Ask which stack to use | Use the stack in this file | Reason: greenfield speed comes from fixed decisions. |
| Fetch initial page data in `useEffect` | Fetch in Server Components | Reason: users should not wait for client waterfalls. |
| Read `process.env` throughout the app | Import from `lib/env.ts` | Reason: env validation must be centralized. |
| Put SQL in pages or components | Put queries in `db/queries/*` | Reason: tenant filters must be reviewable. |
| Trust `orgId` from client input | Derive it with `requireOrg()` | Reason: client-provided tenant IDs can be forged. |
| Use floats for money | Store integer cents | Reason: floating point rounding breaks billing. |
| Edit applied migrations | Add a new migration | Reason: historical migrations may already be deployed. |
| Add broad global state | Use server state and local component state first | Reason: SaaS dashboards usually need fresh server data. |
| Use `any` for external payloads | Parse `unknown` with Zod | Reason: external inputs are not TypeScript values. |
| Mock the database in service tests | Use isolated SQLite | Reason: constraints and SQL behavior are part of the product. |
| Expose database errors to users | Map to safe domain errors | Reason: raw errors leak schema and account details. |
| Add Client Components by default | Keep client code as leaf widgets | Reason: bundle size grows with every client boundary. |
| Skip webhook idempotency | Store processed event IDs | Reason: payment providers retry events. |
| Commit sample secrets | Document names, not values | Reason: templates should never leak credentials. |

## Review Checklist

Before finishing a change, confirm:

- The affected route is in the correct route group. Reason: auth and layout
  behavior follows route groups.
- Every protected query filters by `org_id`. Reason: tenant isolation is the
  highest-risk SaaS invariant.
- New database changes include a migration. Reason: schema-only edits do not
  change deployed databases.
- Every mutation validates input and checks authorization. Reason: Server Actions
  and route handlers are public network boundaries.
- New UI is a Server Component unless browser interactivity is required. Reason:
  server-first keeps the app fast and simple.
- Tests cover invalid input and unauthorized access. Reason: happy paths miss the
  security failures that matter most.
- `pnpm check` passes. Reason: lint, type, and unit tests are the minimum merge
  gate.
