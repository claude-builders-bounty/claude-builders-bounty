# CLAUDE.md

This file is the operating manual for Claude Code in this repository. Treat it
as binding project context. If a request conflicts with this document, ask for
confirmation before changing the architecture.

## Project Shape

This is a production SaaS application built with:

| Layer | Choice | Reason |
| --- | --- | --- |
| Framework | Next.js 15 App Router | Server Components, layouts, route handlers, and Server Actions belong in one routing model. We do not mix in the legacy `pages/` router. |
| Runtime | Node.js 22 LTS | SQLite drivers and background jobs need the Node runtime. Edge runtime is opt-in only for routes that do not touch the database. |
| Language | TypeScript 5 strict mode | The app depends on inferred database and validation types. Loose TypeScript turns schema changes into runtime bugs. |
| Database | SQLite locally, Turso/libSQL in hosted environments | The schema stays SQLite-compatible while allowing a managed production database. Local development remains fast and offline. |
| ORM | Drizzle ORM | Drizzle keeps SQL visible, generates narrow TypeScript types, and avoids heavy runtime abstraction. |
| Validation | Zod | Every external input must be parsed before it reaches business logic. |
| Auth | Auth.js v5 with Drizzle adapter | Auth state is stored in the same database and works with App Router route handlers. |
| Styling | Tailwind CSS 4 plus CSS variables | Utility classes keep UI changes local. CSS variables make themes explicit and testable. |
| Tests | Vitest for units, Playwright for browser flows | Server logic should be fast to test; paid signup and account flows need real browser coverage. |

## Commands

Use these commands unless `package.json` defines stricter equivalents:

```bash
npm run dev          # start the Next.js dev server
npm run build        # production build; must pass before merging
npm run start        # run the production build locally
npm run lint         # ESLint and Next.js rules
npm run typecheck    # tsc --noEmit
npm run test         # Vitest unit/integration tests
npm run test:e2e     # Playwright end-to-end tests
npm run db:generate  # generate Drizzle migration files from schema changes
npm run db:migrate   # apply migrations to the configured database
npm run db:studio    # inspect local data during development
```

If a script is missing, add it to `package.json` rather than using one-off
commands in documentation. Reproducible commands are part of the product.

## Folder Structure

Use this structure for new work:

```text
.
├── app/
│   ├── (marketing)/
│   │   ├── page.tsx
│   │   └── pricing/page.tsx
│   ├── (app)/
│   │   ├── dashboard/page.tsx
│   │   ├── settings/page.tsx
│   │   └── layout.tsx
│   ├── api/
│   │   ├── auth/[...nextauth]/route.ts
│   │   └── webhooks/stripe/route.ts
│   ├── layout.tsx
│   ├── not-found.tsx
│   └── globals.css
├── components/
│   ├── ui/
│   └── layout/
├── features/
│   └── billing/
│       ├── actions.ts
│       ├── components/
│       ├── queries.ts
│       └── schemas.ts
├── lib/
│   ├── auth/
│   ├── db/
│   │   ├── client.ts
│   │   ├── schema.ts
│   │   └── migrations/
│   ├── env.ts
│   ├── errors.ts
│   └── utils.ts
├── tests/
│   ├── unit/
│   └── e2e/
├── drizzle.config.ts
├── middleware.ts
└── package.json
```

Rules:

- Keep `app/` for routes, layouts, loading states, and route handlers because
  App Router file names are public routing API.
- Keep reusable visual primitives in `components/ui` because they must not
  import database, auth, or feature code.
- Keep product behavior in `features/<domain>` because SaaS features evolve
  independently and need clear ownership.
- Keep database setup under `lib/db` because every query and migration should
  share one schema and one client.
- Keep cross-cutting helpers under `lib` only when they are domain-neutral.
  If a helper knows about billing, teams, projects, or users, it belongs in
  that feature.

## Naming Conventions

- Use kebab-case for folders and route segments: `billing-history`,
  `team-settings`. This matches URLs and avoids case-sensitive deployment bugs.
- Use PascalCase for React components: `PlanPicker.tsx`. Components are values,
  and values should be easy to distinguish from route files.
- Use camelCase for functions and variables: `createCheckoutSession`. This
  matches TypeScript and Drizzle conventions.
- Use `*.schema.ts` only for Zod schemas when colocated with a feature. Database
  schema stays in `lib/db/schema.ts` to keep migrations deterministic.
- Name Server Actions with verbs: `createTeam`, `updateSubscription`,
  `deleteInvite`. Action names should describe a mutation, not a UI event.
- Name query helpers as nouns or `get*` functions: `getCurrentTeam`,
  `listInvoices`. Query helpers should not mutate.

## Import Boundaries

Allowed dependencies flow downward:

```text
app -> features -> lib -> components/ui
```

Rules:

- `components/ui` must not import from `app`, `features`, `lib/db`, or `lib/auth`
  because UI primitives must stay reusable and easy to test.
- `features/<domain>/components` may import queries and actions from the same
  feature only. Cross-feature imports create hidden product coupling.
- `app` may compose multiple features because routes are the integration layer.
- `lib/db` must not import from `app` or `features` because schema and client
  code must be usable by migrations, tests, and scripts.
- Use the `@/` alias for app-local imports. Relative imports deeper than two
  levels hide architectural movement and should be cleaned up.

## Environment Variables

All environment variables are parsed once in `lib/env.ts`:

```ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  AUTH_URL: z.string().url().optional(),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_").optional(),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_").optional(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Never read `process.env` outside `lib/env.ts` because scattered reads bypass
  validation and make missing deployment secrets hard to diagnose.
- Do not expose server secrets through `NEXT_PUBLIC_*`. Public variables are
  bundled into client JavaScript.
- Add new variables to `.env.example` in the same change as the code that uses
  them. A feature that cannot be configured cannot be deployed.

## Database Rules

### Client

Create exactly one database client module:

```ts
// lib/db/client.ts
import { drizzle } from "drizzle-orm/libsql";
import { createClient } from "@libsql/client";
import { env } from "@/lib/env";
import * as schema from "./schema";

const client = createClient({ url: env.DATABASE_URL });

export const db = drizzle(client, { schema });
```

Rules:

- Import `db` from `@/lib/db/client`; do not instantiate database clients in
  route handlers, Server Actions, or tests. Multiple clients cause connection
  churn and inconsistent test setup.
- Use Drizzle query builders for normal queries. Use raw SQL only when Drizzle
  cannot express the operation, and keep that SQL in `features/*/queries.ts` or
  `lib/db`.
- Use transactions for multi-row writes because partial SaaS writes are support
  tickets waiting to happen.

### Schema

Prefer these defaults:

```ts
import { sql } from "drizzle-orm";
import { integer, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

export const users = sqliteTable(
  "users",
  {
    id: text("id").primaryKey(), // createId() at app level
    email: text("email").notNull(),
    name: text("name"),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .default(sql`(unixepoch())`),
    updatedAt: integer("updated_at", { mode: "timestamp" })
      .notNull()
      .default(sql`(unixepoch())`),
    deletedAt: integer("deleted_at", { mode: "timestamp" }),
  },
  (table) => ({
    emailIdx: uniqueIndex("users_email_idx").on(table.email),
  }),
);
```

Rules:

- Use text IDs generated by `@paralleldrive/cuid2`. They are URL-safe and avoid
  guessing volume from sequential integers.
- Use `created_at`, `updated_at`, and optional `deleted_at` on product tables
  because auditability and soft-delete recovery matter in SaaS.
- Store money in integer minor units plus currency, for example `amountCents`
  and `currency`. Floating point money corrupts invoices.
- Use explicit indexes for every lookup used in authentication, tenancy, and
  list pages. SQLite will not invent indexes for production traffic.
- Prefer keyset pagination over `OFFSET`. `OFFSET` gets slower as tables grow
  and creates duplicate/missing rows while data changes.

### Migrations

Rules:

- Generate migrations with `npm run db:generate`; do not hand-edit schema state
  files. Generated metadata keeps Drizzle aligned with the database.
- Migration files are append-only after review. Changing an existing migration
  breaks already-deployed databases.
- Name manual SQL migrations with a zero-padded prefix and action:
  `0007_add_team_members_role.sql`. The order should be obvious in file lists.
- Every schema PR must include the generated migration and a downgrade note in
  the PR body. SQLite migrations can be difficult to reverse, so reviewers need
  rollback context.
- Never run destructive migrations without a backfill or export plan. SaaS data
  belongs to customers.

## Data Access Patterns

Use one query module per feature:

```ts
// features/projects/queries.ts
import { and, eq, isNull } from "drizzle-orm";
import { db } from "@/lib/db/client";
import { projects, teamMembers } from "@/lib/db/schema";

export async function getProjectForUser(projectId: string, userId: string) {
  const rows = await db
    .select({ project: projects })
    .from(projects)
    .innerJoin(teamMembers, eq(teamMembers.teamId, projects.teamId))
    .where(
      and(
        eq(projects.id, projectId),
        eq(teamMembers.userId, userId),
        isNull(projects.deletedAt),
      ),
    )
    .limit(1);

  return rows[0]?.project ?? null;
}
```

Rules:

- Filter by membership in the database query, not after fetching. Returning a
  forbidden parent row and checking it later is a data leak pattern.
- Return `null` for not found and throw typed application errors for invalid
  state. Callers need to distinguish absence from a broken invariant.
- Do not return Drizzle internal row shapes from public APIs. Map database rows
  to feature-level DTOs at the boundary.

## Server Actions

Use Server Actions for authenticated UI mutations:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireUser } from "@/lib/auth/session";
import { createProject } from "./mutations";

const createProjectSchema = z.object({
  name: z.string().trim().min(2).max(80),
});

export async function createProjectAction(input: unknown) {
  const user = await requireUser();
  const parsed = createProjectSchema.safeParse(input);

  if (!parsed.success) {
    return { ok: false, error: parsed.error.flatten() } as const;
  }

  const project = await createProject({ ...parsed.data, ownerId: user.id });
  revalidatePath("/dashboard");

  return { ok: true, data: { projectId: project.id } } as const;
}
```

Rules:

- Parse `unknown`, not trusted typed objects. Browser inputs and hidden fields
  can be modified.
- Return serializable objects from actions. Class instances, Dates, and Errors
  make client handling fragile.
- Keep business writes in feature mutation helpers. Server Actions are the
  transport boundary, not the business layer.
- Call `revalidatePath` or `revalidateTag` after mutations that affect cached
  UI. Stale dashboards look like failed writes.

## Route Handlers

Use route handlers for webhooks, machine clients, and OAuth callbacks. Do not
create route handlers just to call them from your own React components; use
Server Actions or server queries instead.

Rules:

- Set `export const runtime = "nodejs"` on handlers that touch SQLite, Auth.js,
  Stripe, or crypto APIs. Edge runtime lacks the assumptions those libraries use.
- Verify webhook signatures before reading business fields. Unverified JSON is
  attacker-controlled JSON.
- Return typed JSON envelopes:

```ts
return Response.json({ ok: true, data });
return Response.json({ ok: false, error: { code: "INVALID_INPUT" } }, { status: 400 });
```

## Components

Rules:

- Server Components are the default. Add `"use client"` only when the component
  uses state, effects, browser APIs, or event handlers.
- Keep client components shallow. Fetch data in server parents and pass compact
  props down because client bundles should not include database or auth logic.
- Build forms with progressive enhancement: native `<form>` plus Server Action
  first, client-side interaction second.
- Put loading and error UI beside the route segment with `loading.tsx` and
  `error.tsx`. App Router already provides the state boundary.
- Components in `components/ui` accept data and callbacks; they do not know
  about teams, subscriptions, auth sessions, or database IDs unless those are
  generic props.

## Auth And Tenancy

Rules:

- Use `requireUser()` for authenticated server code. It should return the user
  or redirect/throw; callers should not repeat session parsing.
- Every team-scoped query must check membership in SQL. Middleware is not enough
  because users can hit Server Actions and route handlers directly.
- Keep role checks close to the mutation. UI hiding is convenience, not
  authorization.
- Use `middleware.ts` only for coarse route protection and redirects. Fine
  permissions belong in server code with database context.
- Never trust `teamId`, `userId`, or `role` from client input. Resolve identity
  from the session and membership tables.

## Billing

Rules:

- Stripe customer IDs and subscription IDs are unique indexed columns. Duplicate
  webhook delivery is normal and must be idempotent.
- Webhooks update billing state; UI actions create checkout or portal sessions.
  The browser should not decide subscription status.
- Store the last processed webhook event ID. This prevents double credits,
  double cancellations, and noisy support cases.
- Do not hard-code plan behavior in components. Keep plan limits in
  `features/billing/plans.ts` so pricing changes are reviewable.

## Error Handling

Use typed application errors:

```ts
export class AppError extends Error {
  constructor(
    public code: "NOT_FOUND" | "FORBIDDEN" | "INVALID_INPUT" | "CONFLICT",
    message: string,
  ) {
    super(message);
  }
}
```

Rules:

- Throw `AppError` for expected business failures and let route/action
  boundaries translate it into user-safe messages.
- Do not expose raw database or Stripe errors to users. They contain internal
  names and do not explain recovery steps.
- Log unexpected errors with request context, not secrets or full payloads.

## Testing

Rules:

- Unit-test pure helpers, Zod schemas, and plan-limit logic. These tests should
  not need Next.js or a browser.
- Integration-test database queries with a temporary SQLite database. Mocking
  Drizzle hides schema mistakes.
- E2E-test signup, login, project creation, billing checkout handoff, and team
  invite flows. These are the revenue and retention paths.
- Every bug fix gets a regression test unless the behavior is already covered.
  The test should fail before the fix.
- Do not snapshot full pages. Snapshots hide intent and create noisy reviews.

## Accessibility

Rules:

- Use semantic elements before ARIA. Native buttons and labels are more reliable
  than recreated controls.
- Every form input needs a visible label or an explicit accessible label.
- Icon-only buttons need `aria-label` because tooltips are not accessible names.
- Keep focus states visible. SaaS users work quickly and keyboard navigation is
  part of the product.

## Performance

Rules:

- Avoid `SELECT *` in list views. Fetch only the columns rendered by the page.
- Cache read-heavy public pages with `revalidate` or tags. Do not cache
  authenticated dashboards unless the invalidation path is explicit.
- Use `next/image` for remote marketing images and avatars. Layout shift makes
  the product feel broken.
- Keep client components behind route-level boundaries. A dashboard should not
  ship billing, admin, and onboarding JavaScript on every page.

## What We Do Not Do

| Avoid | Use instead | Reason |
| --- | --- | --- |
| `pages/` router | `app/` router only | Mixing routing systems creates duplicated data-fetching and auth paths. |
| Raw `process.env` reads | `env` from `lib/env.ts` | Runtime validation catches bad deployments before user traffic does. |
| Business logic in React components | Feature actions, queries, and mutations | Components should render state; server modules enforce product rules. |
| Client-side authorization | SQL membership filters plus server role checks | Hidden buttons do not stop forged requests. |
| Auto-increment public IDs | CUID2 text IDs | Sequential IDs leak volume and are easier to enumerate. |
| Float money values | Integer minor units plus currency | Floating point arithmetic breaks invoices and audits. |
| `OFFSET` pagination | Keyset pagination | Offset queries slow down and drift under concurrent writes. |
| Hard deletes for product data | Soft deletes with `deleted_at` | Customers expect recovery and audit trails. |
| Catch-all `any` types | Zod input types and Drizzle inferred rows | `any` removes the compiler from the highest-risk boundaries. |
| Route handlers for internal UI mutations | Server Actions | Internal HTTP calls add latency and duplicate validation. |
| Mocked database tests for queries | Temporary SQLite integration tests | Query bugs live in schema, joins, indexes, and migrations. |
| Silent webhook processing | Idempotent event table plus structured logs | Payment systems retry and fail asynchronously. |

## PR Completion Checklist

Before opening a PR:

- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm run test` passes, or the PR explains why tests are not applicable.
- `npm run build` passes for changes that touch routes, components, config, or
  database access.
- Database changes include generated migrations and rollback notes.
- New environment variables are added to `.env.example`.
- New user-facing flows include loading, empty, error, and unauthorized states.
- New protected behavior checks authorization on the server, not only in the UI.

## Claude Behavior Rules

- Prefer small, reviewable changes. SaaS apps fail from accidental coupling more
  often than from missing abstractions.
- Follow existing local patterns before introducing a new dependency or folder.
- When adding a dependency, explain why existing platform or project code is not
  enough.
- If a user asks for a shortcut that weakens auth, migrations, billing, or data
  safety, call out the risk before editing.
- Do not invent APIs. Check the installed package version and current local code
  before writing framework-specific calls.
