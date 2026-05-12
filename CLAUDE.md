# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guide

This file is the operating manual for Claude Code in a production-oriented SaaS codebase using Next.js 15 App Router, React Server Components, TypeScript, SQLite, and either `better-sqlite3` for local/server deployments or Turso/libSQL for hosted SQLite.

The rules are intentionally opinionated. Follow them unless an existing project convention clearly contradicts them.

## Stack & Versions

Use this baseline for greenfield work:

- Next.js 15 with App Router under `app/`
- React 19 and React Server Components by default
- TypeScript with `strict: true`
- SQLite as the system of record
- `better-sqlite3` for single-node/serverful apps, or Turso/libSQL for edge/distributed SQLite
- Drizzle ORM for schema definitions, queries, and migrations
- Zod for runtime validation at all trust boundaries
- Server Actions for simple mutations; Route Handlers for webhooks, public APIs, and non-form clients
- Tailwind CSS plus small, accessible components
- Vitest for unit tests and Playwright for browser-level flows

Reason: this stack keeps the app deployable, inspectable, and cheap while avoiding unnecessary service sprawl.

## Project Structure

Use feature-oriented folders. Do not scatter one feature across many global directories unless the code is genuinely shared.

```txt
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
      loading.tsx
      error.tsx
  api/
    webhooks/
      stripe/route.ts
  layout.tsx
  globals.css
components/
  ui/
  forms/
features/
  billing/
    actions.ts
    queries.ts
    schema.ts
    components/
  auth/
    actions.ts
    queries.ts
    session.ts
  organizations/
    actions.ts
    queries.ts
    permissions.ts
lib/
  db/
    index.ts
    schema.ts
    migrations/
    migrate.ts
  env.ts
  auth.ts
  errors.ts
  ids.ts
  logger.ts
scripts/
  migrate.ts
  seed.ts
tests/
  unit/
  e2e/
```

Rules:

- Put route UI in `app/**/page.tsx`; keep business logic out of pages.
- Put feature-specific data access in `features/<feature>/queries.ts`.
- Put feature-specific mutations in `features/<feature>/actions.ts`.
- Put truly shared infrastructure in `lib/` only after two features need it.
- Keep `components/ui/` generic and dumb; feature components live inside `features/<feature>/components/`.

Reason: feature folders reduce cross-feature coupling and make it obvious where Claude should edit.

## Naming Conventions

- Files: `kebab-case.ts`, except React components may use `PascalCase.tsx` only when exported as a named component.
- Components: `PascalCase`.
- Server actions: verb-first names such as `createOrganization`, `updateSubscription`, `deleteInvite`.
- Query functions: read-first names such as `getOrganizationById`, `listUserInvoices`.
- Database tables: plural snake_case, e.g. `users`, `organizations`, `billing_events`.
- Database columns: snake_case, e.g. `created_at`, `stripe_customer_id`.
- TypeScript variables and object keys exposed to React: camelCase.

Reason: SQL stays idiomatic for SQLite, TypeScript stays idiomatic for app code, and the mapping boundary is explicit.

## Development Commands

Prefer these commands in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:seed": "tsx scripts/seed.ts",
    "check": "npm run typecheck && npm run lint && npm run test"
  }
}
```

Before opening a PR, run:

```bash
npm run check
npm run build
```

If a repository uses `pnpm`, `bun`, or `yarn`, keep the existing package manager. Do not introduce a second lockfile.

Reason: contributors need one reliable quality gate, not five undocumented commands.

## Environment Variables

All environment access must go through `lib/env.ts`.

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().optional(),
  STRIPE_WEBHOOK_SECRET: z.string().optional()
});

export const env = envSchema.parse(process.env);
```

Rules:

- Never read `process.env` directly outside `lib/env.ts`.
- Prefix browser-exposed variables with `NEXT_PUBLIC_` only when the value is safe for every user to see.
- Fail fast on missing required env vars during boot.
- Keep `.env.example` updated with every new variable.

Reason: typed, centralized env parsing prevents silent production misconfiguration.

## SQLite & Migration Conventions

Use migrations for every schema change. Never edit production data shape only in application code.

Rules:

- Define schema in `lib/db/schema.ts`.
- Generate SQL migrations into `lib/db/migrations/`.
- Every migration must be deterministic and safe to run once.
- Never rely on `drizzle-kit push` for production.
- Use transactions for multi-step data changes.
- Add indexes in the same PR as the query pattern that needs them.
- Use foreign keys and enable them for local SQLite connections.
- Store timestamps as integer Unix milliseconds or ISO text consistently across the whole app; do not mix formats.

Recommended SQLite pragmas for `better-sqlite3`:

```ts
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");
db.pragma("busy_timeout = 5000");
```

Reason: SQLite is reliable when schema changes are explicit, writes are short, and constraints are enforced.

## Database Access Patterns

Server-only data access belongs in query modules.

```ts
import "server-only";
import { db } from "@/lib/db";
import { organizations } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export async function getOrganizationById(id: string) {
  return db.query.organizations.findFirst({
    where: eq(organizations.id, id)
  });
}
```

Rules:

- Add `import "server-only";` to modules that touch secrets, sessions, or the database.
- Do not query the database from Client Components.
- Do not build SQL strings with user input. Use Drizzle query builders or parameterized SQL.
- Keep transactions small. Do not call slow network APIs inside a database transaction.
- Return plain objects, not ORM-specific objects that leak persistence details into UI components.

Reason: server-only boundaries protect secrets and keep React rendering predictable.

## Server Actions & Mutations

Use Server Actions for authenticated form mutations and small app-internal commands.

Action template:

```ts
"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";
import { requireUser } from "@/features/auth/session";

const inputSchema = z.object({
  name: z.string().min(1).max(80)
});

export async function createOrganization(input: unknown) {
  const user = await requireUser();
  const data = inputSchema.parse(input);

  // authorize before writing
  // write using a short transaction if needed

  revalidatePath("/dashboard");
  return { ok: true } as const;
}
```

Rules:

- Validate input with Zod inside the action.
- Authenticate and authorize before mutating data.
- Return small serializable results.
- Revalidate the narrowest path possible.
- Use Route Handlers instead of Server Actions for webhooks, third-party callbacks, and public APIs.

Reason: Server Actions are convenient, but validation and authorization still need to be explicit.

## Route Handlers & APIs

Use `app/api/**/route.ts` for HTTP APIs.

Rules:

- Validate params, query strings, headers, and JSON bodies.
- Return `Response.json(...)` with stable error shapes.
- Use idempotency keys for payment or email endpoints.
- Verify webhook signatures before parsing trusted business fields.
- Keep route handlers thin; call feature services for logic.

Reason: APIs become integration contracts and need stronger stability than internal function calls.

## Component Patterns

Default to Server Components.

Use Client Components only for:

- local interactive state
- browser-only APIs
- event handlers
- optimistic UI
- third-party widgets that require the DOM

Rules:

- Put `"use client"` at the smallest possible leaf component.
- Do not pass secrets, raw session objects, or database rows with private fields into Client Components.
- Prefer composition over global state.
- Use accessible HTML first; add custom ARIA only when native semantics are not enough.
- Put loading states in `loading.tsx` for route-level fetches and inline skeletons for component-level fetches.

Reason: smaller client islands reduce JavaScript, improve performance, and reduce accidental data exposure.

## Forms & Validation

Rules:

- Use the same Zod schema, or a deliberately derived schema, on both client and server when possible.
- Treat client validation as user experience only. Server validation is mandatory.
- Show field-level errors next to fields and form-level errors near submit buttons.
- Disable submit buttons only while submitting; do not trap users after an error.
- Preserve user input after validation failures.

Reason: forms are where most SaaS data quality bugs start.

## Authentication & Authorization

Rules:

- Authentication answers "who is this user?"; authorization answers "may this user do this?". Keep them separate.
- Put session helpers in `features/auth/session.ts` or `lib/auth.ts`.
- Put per-feature permission checks in `features/<feature>/permissions.ts`.
- Check authorization in every mutation and sensitive query.
- Never trust organization IDs, role names, or user IDs coming from the client.

Reason: most SaaS security bugs are authorization bugs, not login bugs.

## Caching & Revalidation

Rules:

- Be explicit about caching on any data that changes per user or per organization.
- Prefer uncached reads for private dashboard data unless there is a measured performance problem.
- Use `revalidatePath` or `revalidateTag` immediately after mutations.
- Do not cache permission-dependent data globally.

Reason: incorrect caching can leak tenant data or show stale billing/account state.

## Error Handling

Use typed application errors for expected failures.

```ts
export class AppError extends Error {
  constructor(
    public code: "UNAUTHORIZED" | "FORBIDDEN" | "NOT_FOUND" | "VALIDATION" | "CONFLICT",
    message: string
  ) {
    super(message);
  }
}
```

Rules:

- Expected user errors should become friendly messages.
- Unexpected errors should be logged with context and shown as generic messages.
- Do not leak stack traces, SQL, tokens, or provider responses to the browser.
- Include `error.tsx` for major route groups.

Reason: good errors help users without giving attackers implementation details.

## Testing Expectations

For every meaningful change, add or update tests near the behavior.

Minimum expectations:

- Unit-test pure functions, validators, permission checks, and query builders.
- Integration-test important database mutations against a temporary SQLite database.
- E2E-test signup, login, billing, onboarding, and primary dashboard flows.
- Regression-test every bug fix.

Use factories rather than shared global fixtures.

Reason: SQLite makes realistic integration tests cheap, so avoid over-mocking the core business behavior.

## Security Rules

Do not ship code that violates these rules:

- No secrets in Client Components.
- No raw SQL interpolation with user-controlled values.
- No mutation without server-side authorization.
- No webhook handler without signature verification.
- No user-uploaded file served without content type and size checks.
- No tenant-scoped query without tenant scoping in the `where` clause.
- No logging of passwords, tokens, cookies, payment payloads, or full session objects.

Reason: these are high-frequency SaaS failure modes.

## Performance Rules

- Avoid N+1 query patterns in dashboards and lists.
- Add indexes for foreign keys and high-cardinality filters.
- Use pagination for tables and activity feeds.
- Keep Server Components async work parallel when requests are independent.
- Keep Client Components small and avoid importing server-only utilities into them.
- Use `next/image` for local/static images and configured remote domains.

Reason: SaaS apps often feel slow because of avoidable data-loading patterns, not because SQLite is slow.

## What We Do Not Do

- We do not add Prisma by default. Drizzle plus SQLite keeps migrations transparent and runtime light.
- We do not add Redux by default. Most state is server state, URL state, or local component state.
- We do not put all business logic in `app/`. Routes should orchestrate, not own the domain.
- We do not use `any` to bypass unclear types. Model the type or narrow unknown input.
- We do not create generic utility folders until duplication proves they are needed.
- We do not introduce background job systems until a synchronous request is clearly insufficient.
- We do not optimize for edge runtime when using `better-sqlite3`; it requires a Node.js runtime.

Reason: each default avoids a common source of accidental complexity.

## PR Checklist for Claude Code

Before proposing or finalizing a change:

- [ ] Existing package manager and lockfile were respected.
- [ ] New environment variables were added to `.env.example` and `lib/env.ts`.
- [ ] Database changes include a migration.
- [ ] Mutations validate input and check authorization.
- [ ] Private data stays in Server Components or server-only modules.
- [ ] Tests were added or a clear reason was given.
- [ ] `npm run check` and `npm run build` pass, or failures are documented.
- [ ] The change is scoped to the requested feature or bug.

## How Claude Should Work in This Repo

1. Inspect existing conventions before editing.
2. Make the smallest complete change that satisfies the request.
3. Prefer boring, explicit code over clever abstractions.
4. Explain trade-offs when touching schema, auth, billing, or caching.
5. If requirements are ambiguous, choose the safest SaaS default and document the assumption.
6. Never silently weaken validation, authorization, or migration safety to make code pass.

Reason: production SaaS work rewards consistency, boring reliability, and clear boundaries.
