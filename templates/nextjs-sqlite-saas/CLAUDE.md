# CLAUDE.md - Next.js 15 + SQLite SaaS

This file is the project operating manual for Claude Code. Treat every rule as intentional: if a task conflicts with this document, ask for confirmation before changing architecture.

## Stack And Versions

- Use Next.js 15 App Router with React 19 and TypeScript strict mode. Reason: App Router server components, server actions, route handlers, and metadata APIs are the default production path for new SaaS apps.
- Use SQLite for the primary relational database. Reason: SQLite keeps local development, preview deployments, and small SaaS workloads simple before a managed database is justified.
- Use `better-sqlite3` for single-node/serverful deployments and Turso/libSQL for distributed or serverless deployments. Reason: `better-sqlite3` is fast and simple locally, while Turso avoids filesystem constraints on serverless platforms.
- Use Drizzle ORM with SQL migrations. Reason: it keeps schema changes explicit, reviewable, and close to SQLite instead of hiding database behavior behind heavy abstractions.
- Use Zod at all input boundaries. Reason: TypeScript validates code at build time, but route handlers, server actions, forms, and webhooks receive runtime data.
- Use Tailwind CSS for styling and keep reusable primitives in `components/ui`. Reason: SaaS UI needs speed and consistency more than bespoke CSS for every screen.
- Use Vitest for unit tests and Playwright only for critical flows. Reason: most SaaS behavior is domain logic plus forms; full browser tests should cover revenue or auth paths, not every component.

## Dev Commands

Prefer these scripts in `package.json`:

```bash
pnpm dev
pnpm build
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

Rules:

- Use `pnpm` as the package manager. Reason: one lockfile and fast installs make Claude's generated commands predictable.
- Run `pnpm typecheck` before claiming TypeScript work is done. Reason: Next.js route types and server action signatures often fail outside the editor.
- Run `pnpm lint` before formatting-related changes are considered complete. Reason: lint catches accessibility, hook, import, and server/client boundary mistakes.
- Run `pnpm build` before submission when touching routes, metadata, config, or server-only modules. Reason: App Router can pass dev mode while failing production compilation.
- Do not invent scripts. Reason: if a command is missing, add it to `package.json` or state that verification is manual.

## Folder Structure

Use this structure for a greenfield SaaS:

```text
.
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (marketing)/
│   │   ├── page.tsx
│   │   └── pricing/page.tsx
│   ├── (product)/
│   │   ├── dashboard/page.tsx
│   │   └── settings/page.tsx
│   ├── api/
│   │   └── webhooks/
│   │       └── stripe/route.ts
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/
│   └── features/
├── db/
│   ├── index.ts
│   ├── schema.ts
│   ├── migrations/
│   └── seed.ts
├── lib/
│   ├── auth/
│   ├── billing/
│   ├── env.ts
│   ├── errors.ts
│   └── validators/
├── server/
│   ├── actions/
│   └── queries/
├── tests/
│   ├── unit/
│   └── e2e/
└── types/
```

Rules:

- Keep route groups named by product purpose: `(marketing)`, `(auth)`, `(product)`, `(admin)`. Reason: URL structure stays clean while layout ownership remains obvious.
- Put database schema, connection code, migrations, and seed data under `db/`. Reason: database state must be easy to audit without searching the app tree.
- Put server actions in `server/actions` unless they are tiny and used by exactly one route segment. Reason: shared mutations need reviewable authorization, validation, and cache invalidation.
- Put read-only database access in `server/queries`. Reason: separating reads from writes makes caching and authorization easier to reason about.
- Put reusable visual primitives in `components/ui` and business-specific components in `components/features`. Reason: UI primitives should not import product data or server modules.
- Put runtime configuration in `lib/env.ts`. Reason: environment validation should fail at startup, not halfway through a payment or auth flow.

## Naming Conventions

- Use kebab-case for route folders and filenames that map to URLs. Reason: URLs should stay lowercase and copy-safe.
- Use PascalCase for React component names. Reason: it matches JSX conventions and makes component imports visually distinct from utilities.
- Use camelCase for functions, variables, server actions, and Zod schemas. Reason: generated code remains idiomatic TypeScript.
- Prefix server actions with an imperative verb, for example `createCheckoutSession`, `updateProfile`, `deleteWorkspace`. Reason: actions mutate state and their names should reveal side effects.
- Name database tables as plural snake_case, for example `users`, `workspaces`, `subscriptions`. Reason: SQL queries remain readable and consistent with migration files.
- Name migration files as `0001_create_users.sql`, `0002_add_workspace_members.sql`. Reason: ordered numeric prefixes make migration history deterministic.
- Name tests after behavior, not implementation, for example `creates-workspace.test.ts`. Reason: tests should survive internal refactors.

## SQLite And Migration Rules

- Never change production schema with ad-hoc SQL in application code. Reason: untracked schema drift breaks previews, rollbacks, and local reproduction.
- Every schema change needs a migration file and an update to `db/schema.ts`. Reason: Drizzle types and the real database must evolve together.
- Use forward-only migrations. Reason: SQLite rollback semantics are limited; recovery should be handled by backups and explicit follow-up migrations.
- Prefer additive migrations: add columns nullable or with safe defaults, backfill, then tighten constraints later. Reason: SQLite table rewrites and locks are risky during live traffic.
- Enable foreign keys for every connection with `PRAGMA foreign_keys = ON`. Reason: SQLite does not reliably protect relations unless this is enabled.
- Use transactions for multi-table writes. Reason: SaaS workflows like signup, workspace creation, billing updates, and invitations must be all-or-nothing.
- Store timestamps as ISO strings or integer milliseconds consistently across all tables. Reason: mixed timestamp formats create sorting and timezone bugs.
- Use `text` IDs with generated UUIDs or cuid-style IDs for public entities. Reason: integer IDs leak growth and are easier to enumerate.
- Keep raw SQL in migrations and performance-critical queries only. Reason: raw SQL is useful, but scattered SQL bypasses schema types and validation.

Example schema pattern:

```ts
// db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp_ms" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp_ms" }).notNull(),
});
```

## Data Access Patterns

- Validate input before calling the database. Reason: database constraints protect integrity, but user-facing errors should be explicit and safe.
- Keep authorization checks next to data access. Reason: separating them makes it easy for generated code to reuse a query without permission checks.
- Return plain objects from queries. Reason: React Server Components serialize data across boundaries; class instances and database handles do not belong in props.
- Use narrow select lists for dashboards and lists. Reason: SaaS tables grow quickly and accidental `select *` leaks private fields.
- Centralize pagination. Reason: every list eventually needs limits, cursors, and deterministic ordering.

## Server Components, Client Components, And Actions

- Default to Server Components. Reason: they reduce client JavaScript and allow direct server-side data loading.
- Add `"use client"` only for interactivity, browser APIs, or hooks. Reason: one unnecessary client boundary can pull server-safe code into the browser bundle.
- Do not import `db`, `fs`, secrets, or server actions into client components. Reason: client bundles must never contain server-only modules or credentials.
- Use Server Actions for form mutations inside the app. Reason: they keep validation, authorization, database writes, and cache invalidation in one server-side path.
- Use Route Handlers for webhooks, public API endpoints, and third-party callbacks. Reason: those flows are HTTP integrations, not UI form submissions.
- Revalidate or redirect after mutations. Reason: stale dashboards after writes create support issues and duplicate submissions.

Server action pattern:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireUser } from "@/lib/auth/session";
import { createWorkspace } from "@/server/queries/workspaces";

const inputSchema = z.object({
  name: z.string().trim().min(2).max(80),
});

export async function createWorkspaceAction(input: unknown) {
  const user = await requireUser();
  const data = inputSchema.parse(input);
  await createWorkspace({ ownerId: user.id, name: data.name });
  revalidatePath("/dashboard");
}
```

## Component Patterns

- Keep pages thin: load data, compose feature components, set metadata. Reason: pages become hard to test when they contain business logic.
- Keep forms as client components that call server actions. Reason: forms need local pending/error state, but mutations belong on the server.
- Pass only serializable props from server to client components. Reason: React cannot safely serialize functions, database rows with methods, or secret-bearing objects.
- Build shared UI as small primitives. Reason: SaaS screens change often; composable primitives survive product pivots.
- Co-locate feature-specific components under `components/features/<feature>`. Reason: ownership is clearer than a giant flat components directory.
- Use accessible labels and semantic elements before custom ARIA. Reason: generated UI should be usable and testable without fragile accessibility patches.

## Auth, Billing, And Security

- Protect product routes at the layout level when possible. Reason: route-level protection prevents accidentally exposing nested pages.
- Never trust user IDs from client input. Reason: the current session is the source of identity.
- Verify webhook signatures before parsing business payloads. Reason: billing and auth webhooks are externally reachable mutation endpoints.
- Store secrets only in environment variables validated by `lib/env.ts`. Reason: missing or malformed secrets should fail fast.
- Never log tokens, session cookies, full payment payloads, or password reset links. Reason: logs are copied into observability tools and support tickets.
- Use rate limiting on auth, invitation, and billing endpoints. Reason: these endpoints are cheap to abuse and expensive to recover from.

## Environment Variables

Use a typed env module:

```ts
// lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Only expose variables with `NEXT_PUBLIC_` when the browser truly needs them. Reason: every public variable is visible to users.
- Keep `.env.example` current. Reason: Claude and new developers need one source of truth for setup.
- Do not provide fake production secrets in examples. Reason: placeholder values are copied into real deployments.

## Error Handling

- Convert expected failures into typed results or user-safe messages. Reason: validation errors, duplicate records, and missing permissions are normal SaaS events.
- Let unexpected failures throw after adding context on the server. Reason: hiding unknown errors makes debugging production incidents slower.
- Do not expose raw database or provider errors to users. Reason: those messages can leak schema, credentials, or provider internals.
- Add `not-found.tsx` and `error.tsx` where product areas need custom recovery. Reason: App Router gives route-scoped error boundaries; use them.

## Testing Rules

- Unit test pure domain logic, validators, and permission helpers. Reason: these are cheap tests that prevent high-impact regressions.
- Integration test server actions that perform important writes. Reason: validation, authorization, database writes, and cache invalidation must work together.
- E2E test signup/login, checkout, and the core paid workflow. Reason: these paths affect revenue and user access.
- Use a temporary SQLite database for tests. Reason: tests must not depend on local developer state.
- Do not mock the database for migration or query behavior. Reason: SQLite-specific constraints and transactions are part of the product behavior.

## Patterns To Follow

- "Validate, authorize, mutate, revalidate" for every write. Reason: this order prevents invalid or unauthorized state changes and avoids stale UI.
- "Server by default, client by exception" for React components. Reason: smaller client bundles and fewer secret-boundary mistakes.
- "One migration per logical schema change." Reason: review and rollback planning are easier when migrations are focused.
- "Feature folders for product behavior, UI folders for primitives." Reason: product code and design-system code change at different speeds.
- "Explicit dependencies in examples." Reason: Claude should not infer whether the app uses Drizzle, Prisma, Auth.js, or custom sessions.

## Anti-Patterns To Avoid

- Do not use Prisma by default for this template. Reason: the issue targets SQLite with `better-sqlite3` or Turso; Drizzle keeps SQL behavior explicit and lightweight.
- Do not put business logic in React client components. Reason: client code is user-controlled and harder to protect.
- Do not create generic `utils.ts` dumping grounds. Reason: unclear ownership makes generated changes risky.
- Do not mix Pages Router and App Router. Reason: Next.js 15 greenfield projects should not carry legacy routing complexity.
- Do not run migrations from request handlers. Reason: schema changes must be deliberate deployment steps, not runtime side effects.
- Do not use global mutable singletons except for the database connection in development. Reason: hot reload needs a stable connection, but hidden state causes test pollution.
- Do not swallow errors with `catch { return null; }`. Reason: missing data, failed auth, and provider outages need different handling.
- Do not accept unchecked `FormData` directly in writes. Reason: form fields are untyped strings and can be missing, duplicated, or malicious.
- Do not add dependencies for one-line helpers. Reason: SaaS projects live long enough for dependency churn to become maintenance cost.
- Do not optimize with caching until correctness and authorization are clear. Reason: cached private data is one of the easiest SaaS bugs to ship.

## Common Task Instructions For Claude

When adding a page:

1. Put the route under the correct route group.
2. Load data in the server page or a `server/queries` function.
3. Keep interactive pieces in focused client components.
4. Add metadata if the page is public.
5. Run typecheck and lint.

When adding a mutation:

1. Create or update a Zod schema.
2. Add authorization based on the current session.
3. Write through a server action or route handler.
4. Use a transaction for multiple database writes.
5. Revalidate affected paths or redirect.
6. Add a unit or integration test for the rule being changed.

When changing the database:

1. Update `db/schema.ts`.
2. Generate or write a numbered SQL migration.
3. Review the SQL manually.
4. Run migrations against a local copy.
5. Update seed data and tests if required.

## Completion Checklist

Before marking a task complete:

- `pnpm typecheck` passes, or the reason it cannot run is documented.
- `pnpm lint` passes, or the reason it cannot run is documented.
- `pnpm test` passes for touched logic, or the manual verification path is documented.
- Database migrations are included for schema changes.
- New environment variables are added to `.env.example`.
- Server/client boundaries have been checked for secret leaks.
- The final answer names the files changed and the verification performed.
