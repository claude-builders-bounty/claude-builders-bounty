# CLAUDE.md

This file defines the production rules for a greenfield SaaS built with Next.js 15 App Router, React 19, TypeScript 5.x, SQLite, and Drizzle ORM.

These instructions are intentionally opinionated. Follow them unless the user explicitly changes the technical direction.

## Stack And Versions

- Runtime: Node.js 22 LTS.
- Package manager: pnpm 10.x.
- Framework: Next.js 15.3.x using the App Router only.
- UI runtime: React 19.1.x and React DOM 19.1.x.
- Language: TypeScript 5.8.x with `strict: true`.
- Database: SQLite 3.x.
- Local SQLite driver: `better-sqlite3` 11.x.
- Hosted SQLite option: Turso using `@libsql/client` 0.15.x.
- ORM and migrations: Drizzle ORM 0.43.x and drizzle-kit 0.31.x.
- Validation: Zod 3.24.x.
- Forms: React Hook Form 7.x with Zod resolvers when client-side forms are needed.
- Styling: Tailwind CSS 4.x plus CSS Modules only when local scoping is clearer.
- Testing: Vitest 3.x, React Testing Library 16.x, Playwright 1.52.x.
- Formatting and linting: ESLint 9.x, `eslint-config-next`, Prettier 3.x.
- Auth: Keep auth behind a small application-owned interface.
- Email: Keep email behind a small provider interface.
- Payments: Keep billing behind a small provider interface.

Reason: fixed versions make generated code reproducible and stop the project from drifting across incompatible major versions.

## Core Principles

- Server-first is the default.
- Client components are the exception.
- SQLite is treated as a real production database, not a toy.
- Schema changes are explicit migrations.
- Domain code does not import UI code.
- UI code does not contain database queries.
- Route handlers validate every external input.
- Server actions validate every external input.
- Every rule in this file exists to reduce production ambiguity.

Reason: SaaS projects fail from unclear boundaries before they fail from missing abstractions.

## Project Structure

Use this folder structure for a greenfield app:

```txt
.
├── app/
│   ├── (marketing)/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── (auth)/
│   │   ├── sign-in/
│   │   │   └── page.tsx
│   │   ├── sign-up/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (app)/
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── settings/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── api/
│   │   ├── health/
│   │   │   └── route.ts
│   │   └── webhooks/
│   │       └── stripe/
│   │           └── route.ts
│   ├── globals.css
│   ├── layout.tsx
│   ├── error.tsx
│   ├── not-found.tsx
│   └── loading.tsx
├── components/
│   ├── ui/
│   ├── forms/
│   ├── layout/
│   └── domain/
├── db/
│   ├── index.ts
│   ├── schema.ts
│   ├── migrations/
│   └── seed.ts
├── drizzle.config.ts
├── lib/
│   ├── env.ts
│   ├── errors.ts
│   ├── ids.ts
│   ├── logger.ts
│   ├── time.ts
│   └── validation.ts
├── server/
│   ├── actions/
│   ├── auth/
│   ├── billing/
│   ├── email/
│   ├── repositories/
│   └── services/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── public/
├── scripts/
├── next.config.ts
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

Reason: this layout separates routing, UI, database, server use cases, and test concerns without inventing framework abstractions.

## App Router Conventions

- Use `app/` exclusively.
- Use route groups like `(marketing)`, `(auth)`, and `(app)` to organize layouts without changing URLs.
- Place URL-owning components in `page.tsx`.
- Place shared route chrome in `layout.tsx`.
- Place route-specific loading states in `loading.tsx`.
- Place route-specific error boundaries in `error.tsx`.
- Place 404 behavior in `not-found.tsx`.
- Use `route.ts` only for HTTP endpoints consumed by external systems or non-React clients.
- Keep metadata close to the route using `metadata` or `generateMetadata`.
- Do not create barrel exports inside `app/`.

Reason: App Router conventions are strongest when routing files remain obvious and locally inspectable.

## Naming Conventions

- Use kebab-case for folders and route segments.
- Use PascalCase for React components.
- Use camelCase for functions, variables, and object properties.
- Use UPPER_SNAKE_CASE for process environment variables.
- Use snake_case for database table names and column names.
- Use plural names for database tables, such as `users`, `organizations`, and `subscriptions`.
- Use singular names for TypeScript domain types, such as `User`, `Organization`, and `Subscription`.
- Name server actions with an action verb, such as `createOrganizationAction`.
- Name repository functions by operation and entity, such as `getUserById` or `insertOrganization`.
- Name migrations with a timestamp prefix and short intent, such as `20260511120000_create_users.sql`.
- Name tests after behavior, such as `create-organization.test.ts`.

Reason: consistent names make it clear whether a symbol is a route, component, use case, table, or test.

## TypeScript Rules

- Keep `strict: true`.
- Keep `noUncheckedIndexedAccess: true`.
- Keep `exactOptionalPropertyTypes: true`.
- Do not use `any`.
- Use `unknown` for untrusted values.
- Narrow unknown values with Zod or explicit type guards.
- Use `satisfies` for config objects.
- Prefer discriminated unions for multi-state domain results.
- Export types only when another module needs them.
- Keep shared type definitions near their owning module.
- Avoid global ambient types unless integrating a third-party package.

Reason: strict TypeScript catches SaaS data bugs before they become customer data bugs.

## Environment Variables

- Define all environment variables in `lib/env.ts`.
- Validate environment variables with Zod at process startup.
- Expose browser-safe variables only when prefixed with `NEXT_PUBLIC_`.
- Never read `process.env` directly outside `lib/env.ts`.
- Keep secrets out of client components.
- Keep `.env.example` current with all required keys.

Reason: environment validation turns deployment mistakes into immediate startup failures.

Example:

```ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
});

export const env = envSchema.parse(process.env);
```

## Database Driver Rules

- Use `better-sqlite3` for local development, tests, and single-node deployments.
- Use Turso through `@libsql/client` when the app needs hosted SQLite, read replicas, or edge-adjacent access.
- Hide the selected driver behind `db/index.ts`.
- Do not import `better-sqlite3` or `@libsql/client` outside the database module.
- Keep the app runtime on Node.js when using `better-sqlite3`.
- Do not deploy `better-sqlite3` routes to the Edge runtime.
- Use Turso for Edge-compatible database access.

Reason: SQLite driver differences should not leak through application code.

## Drizzle Schema Conventions

- Keep all table definitions in `db/schema.ts` until the file becomes difficult to navigate.
- Split schema by domain only after there are clear independent domains.
- Export table objects and inferred row types from schema modules.
- Use `sqliteTable` for every table.
- Define primary keys explicitly.
- Use text IDs for public identifiers.
- Use integer timestamps only when there is a clear reason.
- Prefer ISO 8601 text timestamps for app-created timestamps.
- Use `created_at` and `updated_at` on mutable business tables.
- Use `deleted_at` only for entities that need soft delete.
- Use `notNull()` unless null has a specific domain meaning.
- Use check constraints for small finite database-level invariants.
- Use foreign keys for ownership and relational integrity.
- Use cascading deletes only when child records have no independent business value.

Reason: the database is the final consistency boundary, so schema intent must be visible in code.

## SQL And Migration Conventions

- All schema changes go through Drizzle migrations.
- Do not use `db push` against production.
- Do not hand-edit applied migration files.
- Do not reorder migration files.
- Do not squash migrations after they have been shared.
- Generate migrations with drizzle-kit.
- Review generated SQL before committing.
- Keep migrations small and focused.
- Use one logical schema change per migration.
- Include explicit indexes in migrations for every frequent lookup.
- Include explicit unique constraints for every uniqueness rule.
- Include foreign key indexes when queries filter or join on the foreign key.
- Do not create indexes speculatively.
- Add a comment in the PR when a migration is expected to be slow.
- Use expand-and-contract migrations for destructive changes.
- Backfill data before adding a non-null constraint to existing data.
- Never drop a column in the same deploy that stops writing it.
- Never rename a table or column in production without a compatibility plan.

Reason: migrations are deployment artifacts, and production deploys need reversible thinking even when SQLite cannot reverse every operation automatically.

Migration naming:

```txt
YYYYMMDDHHMMSS_short_imperative_description.sql
20260511120000_create_users.sql
20260511121500_add_organizations_slug_index.sql
20260511123000_add_subscription_status.sql
```

Reason: timestamped names preserve order across branches and make intent readable during incident review.

## Index Rules

- Index every foreign key used in joins.
- Index every column used for tenant scoping, such as `organization_id`.
- Index every column used for auth lookup, such as `email` or `provider_account_id`.
- Use composite indexes for common multi-column filters.
- Put the highest-cardinality equality column first in composite indexes.
- Add unique indexes for slugs, external IDs, and idempotency keys.
- Avoid indexing low-cardinality status columns alone.
- Avoid redundant prefix indexes when a composite index already serves the query.
- Confirm query shape before adding an index.

Reason: indexes are part of the application contract and should match real query paths.

## Tenant And SaaS Data Rules

- Every tenant-owned table includes `organization_id`.
- Every tenant-owned query filters by `organization_id`.
- Never trust a client-provided organization ID without checking membership.
- Keep user membership in a join table, such as `organization_members`.
- Use role names that map to permissions.
- Do not hard-code authorization checks directly in UI components.
- Put authorization checks in server services or policies.
- Return 404 for inaccessible tenant resources unless the user should know the resource exists.

Reason: tenant isolation is a data access rule, not a UI affordance.

## Component Patterns

- Server components are the default.
- Client components must begin with `"use client"`.
- Client components are used for browser state, event handlers, effects, focus management, and interactive widgets.
- Server components fetch data directly through server services.
- Server components do not pass raw database rows to deeply nested UI.
- Normalize data into view models at the route or service boundary.
- Keep page components thin.
- Extract repeated UI into `components/`.
- Extract route-specific components beside the route only when they are not reused elsewhere.
- Keep design-system primitives in `components/ui/`.
- Keep domain components in `components/domain/`.
- Keep form components in `components/forms/`.

Reason: server-first components reduce JavaScript shipped to the browser and make data ownership clear.

## Data Fetching Patterns

- Fetch data in server components when rendering page content.
- Use server actions for mutations triggered by forms.
- Use route handlers for webhooks, health checks, and external API clients.
- Use repositories for direct database access.
- Use services for business workflows.
- Do not fetch from internal API routes inside server components.
- Do not duplicate authorization checks between the route and repository.
- Keep authorization in services or policy helpers.
- Return typed results from services.
- Use `cache`, `revalidatePath`, and `revalidateTag` deliberately.
- Default to dynamic rendering for authenticated SaaS pages.
- Use static rendering for marketing pages when content allows it.

Reason: server components can call server code directly, so internal HTTP calls add latency and failure modes without value.

## Server Actions

- Place server actions in `server/actions/`.
- Add `"use server"` at the top of action modules.
- Validate `FormData` with Zod before calling services.
- Check authentication inside the action or service.
- Return a typed action state for forms.
- Do not throw validation errors for expected user mistakes.
- Throw only unexpected infrastructure or programmer errors.
- Revalidate affected paths after successful mutations.
- Redirect after successful create flows when appropriate.

Reason: server actions sit on a trust boundary and must treat form input as untrusted.

## Route Handlers

- Place route handlers only where HTTP is the product boundary.
- Validate request method and content type.
- Validate request body with Zod.
- Verify webhook signatures before parsing trusted fields.
- Use idempotency keys for webhook event processing.
- Return JSON with stable error shapes.
- Do not leak stack traces or database errors to callers.
- Log unexpected errors with correlation context.

Reason: route handlers are public interfaces and need stricter input and error discipline than internal functions.

## Error Handling Patterns

- Use expected result types for domain failures.
- Use exceptions for unexpected failures.
- Define shared app errors in `lib/errors.ts`.
- Include stable error codes for errors shown in UI.
- Do not expose raw exception messages to users.
- Log the original error on the server.
- Show user-safe messages in the client.
- Use `notFound()` for missing route resources.
- Use `redirect()` for successful navigation changes.
- Use `error.tsx` for route-level unexpected rendering failures.
- Use `global-error.tsx` only for root-level failures.

Reason: expected errors are product states, while unexpected errors are operational events.

Example result type:

```ts
type Result<T> =
  | { ok: true; value: T }
  | { ok: false; code: "forbidden" | "not_found" | "invalid_input"; message: string };
```

## Forms And Validation

- Use native HTML forms where possible.
- Use React Hook Form only when client-side form state improves the experience.
- Use the same Zod schema for client-side hints and server-side enforcement when practical.
- Treat client-side validation as convenience only.
- Parse numbers, booleans, and dates explicitly.
- Return field-level errors for correctable input.
- Preserve user input after validation failure.
- Disable submit buttons while pending.
- Make destructive actions confirm intent.

Reason: forms are high-volume interaction points, and validation must work without trusting the browser.

## Styling Rules

- Use Tailwind CSS 4.x for layout, spacing, typography, and state styles.
- Use CSS Modules for complex component-local styling when Tailwind becomes unreadable.
- Do not use runtime CSS-in-JS.
- Keep global CSS limited to tokens, base styles, and third-party resets.
- Prefer semantic HTML before ARIA.
- Use accessible focus states.
- Use responsive layouts that work at 320px width.
- Do not use arbitrary values when a design token works.
- Do not create one-off color palettes in feature code.

Reason: Tailwind and CSS Modules keep styling static, inspectable, and compatible with server rendering.

## State Management

- Use URL search params for shareable filters and pagination.
- Use server state from server components where possible.
- Use local React state for local UI state.
- Use `useReducer` for complex local interactions.
- Do not add a global state library by default.
- Do not mirror server data into client state unless the UI edits a draft.
- Keep optimistic updates small and reversible.

Reason: most SaaS state is either server-owned or URL-owned, so global client state usually adds stale data risk.

## Authentication And Authorization

- Keep auth provider details inside `server/auth/`.
- Expose functions like `getCurrentUser`, `requireUser`, and `requireOrganizationRole`.
- Do not call provider SDKs directly from page components.
- Store external provider IDs separately from internal user IDs.
- Normalize email addresses before uniqueness checks.
- Require authorization in every service that reads tenant-owned data.
- Do not rely on middleware as the only authorization layer.
- Use middleware only for coarse routing protection.

Reason: auth changes over time, but the application should keep stable authorization semantics.

## Logging And Observability

- Create a small logger in `lib/logger.ts`.
- Log structured objects, not interpolated strings.
- Include request IDs when available.
- Include user ID and organization ID only when safe and useful.
- Never log secrets, tokens, passwords, or full payment details.
- Log webhook event IDs.
- Log migration and seed script failures.
- Keep client logging minimal.

Reason: structured logs make incidents diagnosable without exposing customer data.

## Security Rules

- Validate all external input.
- Escape or sanitize user-generated HTML.
- Prefer plain text rendering for user content.
- Use CSRF-safe mutation patterns.
- Use secure, httpOnly cookies for session tokens.
- Set appropriate security headers in `next.config.ts` or middleware.
- Rate limit auth, invite, and billing-sensitive endpoints.
- Store secrets only in environment variables or a secret manager.
- Do not commit `.env` files.
- Do not expose internal IDs when public IDs are available.

Reason: SaaS applications hold customer data and billing state, so security controls must be default behavior.

## Dev Commands

Use these package scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio",
    "db:seed": "tsx db/seed.ts",
    "check": "pnpm typecheck && pnpm lint && pnpm test && pnpm build"
  }
}
```

Reason: predictable command names let humans and agents verify changes the same way in every environment.

## Development Workflow

- Start with `pnpm install`.
- Run `pnpm dev` for local development.
- Run `pnpm db:generate` after changing `db/schema.ts`.
- Run `pnpm db:migrate` before testing code that depends on schema changes.
- Run `pnpm db:seed` only against development or test databases.
- Run `pnpm check` before opening a pull request.
- Keep commits small enough that schema, service, and UI changes are reviewable.

Reason: tight feedback loops prevent schema drift and catch integration failures before deployment.

## Testing Conventions

- Use Vitest for unit and integration tests.
- Use Playwright for browser-level flows.
- Put unit tests in `tests/unit/`.
- Put database-backed tests in `tests/integration/`.
- Put end-to-end tests in `tests/e2e/`.
- Test services more than components.
- Test repositories against a real SQLite database.
- Use temporary SQLite databases for integration tests.
- Reset database state between tests.
- Do not share mutable fixtures across tests.
- Test authorization failures.
- Test validation failures.
- Test the happy path.
- Test migration assumptions when a migration has data movement.
- Keep snapshot tests rare and targeted.

Reason: services and database behavior carry the most business risk in a SaaS app.

## Unit Test Rules

- Unit test pure functions and service branches.
- Mock provider interfaces, not internal implementation details.
- Avoid mocking Drizzle query builders in unit tests.
- Use integration tests for real SQL behavior.
- Keep test names behavior-focused.

Reason: unit tests should describe decisions, while integration tests should prove persistence behavior.

## Integration Test Rules

- Use a real SQLite database.
- Run migrations before the test suite.
- Seed only the data needed by the test.
- Use factory helpers for repeated records.
- Assert database side effects directly for mutations.
- Use transactions for isolation only when the driver and test runner make that reliable.

Reason: SQLite behavior, constraints, indexes, and transactions cannot be proven with mocks.

## End-To-End Test Rules

- Cover sign-up, sign-in, tenant creation, core CRUD, and billing-critical flows.
- Keep E2E tests focused on user-visible behavior.
- Do not test every validation branch through Playwright.
- Use stable selectors such as accessible roles and labels.
- Avoid arbitrary sleeps.
- Use network and UI assertions that reflect actual readiness.

Reason: E2E tests are expensive, so they should protect the highest-value workflows.

## Patterns To Follow

- Keep pages thin and delegate business logic to services.
- Keep database access inside repositories.
- Keep provider SDKs behind interfaces.
- Validate at boundaries.
- Authorize before reading tenant data.
- Use database constraints for invariants.
- Use transactions for multi-write workflows.
- Prefer composition over configuration-heavy abstractions.
- Prefer explicit imports over barrel exports for server code.
- Keep generated code out of hand-written modules.
- Make loading, empty, error, and success states explicit.
- Keep UI copy direct and action-oriented.

Reason: explicit boundaries make production behavior easier to debug and safer to change.

## Anti-Patterns To Avoid

- Do not use Prisma.
- Do not use the Pages Router.
- Do not use runtime CSS-in-JS.
- Do not put database queries in client components.
- Do not call internal API routes from server components.
- Do not create generic `utils.ts` dumping grounds.
- Do not use `any`.
- Do not swallow errors silently.
- Do not catch errors only to rethrow the same error.
- Do not store money as floating point values.
- Do not store local times without a timezone strategy.
- Do not put secrets in `NEXT_PUBLIC_` variables.
- Do not use middleware as the only authorization layer.
- Do not add Redis, queues, or external caches before there is a measured need.
- Do not add a global state manager by default.
- Do not add GraphQL by default.
- Do not expose sequential database IDs in public URLs.

Reason: each avoided pattern either increases operational surface area, weakens type safety, or fights the chosen stack.

## What We Do Not Do And Why

- No Prisma because Drizzle maps more directly to SQL, keeps migrations transparent, and fits SQLite-first development better.
- No Pages Router because Next.js 15 App Router is the current routing model and supports server components natively.
- No CSS-in-JS because runtime style generation adds client cost and complicates server rendering.
- No default GraphQL layer because App Router, server actions, and typed services are enough for a greenfield SaaS.
- No default tRPC because server components can call server code directly and route handlers cover external HTTP APIs.
- No default global state library because URL state, server state, and local React state cover most SaaS needs.
- No edge runtime with `better-sqlite3` because native SQLite bindings require the Node.js runtime.
- No unreviewed generated migrations because database changes are production changes.
- No direct provider SDK calls in UI because providers change and UI should depend on application capabilities.
- No speculative abstraction because abstractions are easier to add than remove.

Reason: production readiness comes from reducing unnecessary moving parts.

## Money And Billing Rules

- Store money in integer minor units, such as cents.
- Store currency as a three-letter ISO code.
- Store external payment provider IDs with unique constraints.
- Store webhook event IDs for idempotency.
- Process billing webhooks inside transactions where possible.
- Never trust client-submitted prices.
- Read product and price IDs from server configuration or the payment provider.

Reason: billing bugs are costly and must be protected by database constraints and idempotent processing.

## Time And Date Rules

- Store timestamps in UTC.
- Prefer ISO 8601 strings for application timestamps.
- Convert to user-local time only at the display edge.
- Do not store ambiguous local dates for events that need exact ordering.
- Use helper functions from `lib/time.ts`.
- Do not call `new Date()` throughout business logic when testability matters.

Reason: consistent time handling prevents subtle reporting, billing, and audit bugs.

## ID Rules

- Use internal primary keys for relations.
- Use public opaque IDs for URLs and external references.
- Generate public IDs in `lib/ids.ts`.
- Do not expose autoincrement IDs in public routes.
- Add unique constraints to public IDs.
- Keep external provider IDs in separate columns.

Reason: public opaque IDs reduce enumeration risk and decouple URLs from storage details.

## Repository Rules

- Repositories contain SQL and Drizzle queries.
- Repositories do not contain React code.
- Repositories do not decide authorization policy.
- Repositories may accept scoped identifiers, such as `organizationId`.
- Repositories return database-shaped data or small persistence DTOs.
- Repositories should be boring and explicit.

Reason: repositories are persistence adapters, not the place for product workflows.

## Service Rules

- Services contain business workflows.
- Services call repositories.
- Services perform authorization checks.
- Services manage transactions for multi-step writes.
- Services return typed results.
- Services do not import React.
- Services do not know about form libraries.
- Services may call provider interfaces.

Reason: services are the stable core that can be reused by pages, actions, jobs, and route handlers.

## Transaction Rules

- Use transactions for multi-write workflows.
- Use transactions when writing parent and child records together.
- Use transactions for idempotent webhook processing.
- Keep transactions short.
- Do not perform slow network calls inside a database transaction.
- If a workflow needs a network call and a database write, design an explicit pending state.

Reason: transactions protect consistency, but long transactions create lock contention in SQLite.

## Seed Rules

- Keep seeds deterministic.
- Make seed scripts safe to rerun in development.
- Do not seed production through `db:seed`.
- Include a demo organization, demo user, and representative domain records.
- Use obvious test data that cannot be mistaken for real customers.
- Hash passwords if local password auth exists.

Reason: deterministic seeds make local debugging and automated tests repeatable.

## Accessibility Rules

- Use semantic elements before ARIA.
- Every form input has a label.
- Every icon-only button has an accessible name.
- Dialogs trap focus and restore focus.
- Menus support keyboard navigation.
- Color is not the only state indicator.
- Text contrast must meet WCAG AA.
- Loading states must not permanently hide content from assistive technology.

Reason: accessibility is part of production quality and is cheaper when built into primitives.

## Performance Rules

- Keep client components small.
- Avoid sending large objects to client components.
- Paginate unbounded lists.
- Add database indexes for common filters before launch.
- Use `next/image` for local and remote images.
- Use dynamic imports for heavy client-only widgets.
- Measure before adding caching infrastructure.
- Prefer query improvements before application-level caching.

Reason: most performance wins in this stack come from less client JavaScript and better SQL access paths.

## Review Checklist

- Does every new route follow App Router conventions?
- Does every mutation validate input on the server?
- Does every tenant query enforce organization scope?
- Does every schema change include a migration?
- Does every new lookup have the right index or a reason not to?
- Does every service return safe errors?
- Does every client component justify its client-side boundary?
- Does every external provider call sit behind an interface?
- Do tests cover success, validation failure, and authorization failure where relevant?
- Does `pnpm check` pass?

Reason: a checklist catches cross-cutting production risks that are easy to miss in feature-focused review.

## Default Implementation Order

- Define schema and migration.
- Add repository functions.
- Add service workflow and authorization.
- Add server action or route handler.
- Add server component page.
- Add client component only if interaction requires it.
- Add tests around the service and database behavior.
- Run migrations and checks.

Reason: building from persistence to workflow to UI keeps dependencies pointed in the right direction.

## Final Rule

When a request conflicts with this file, ask whether the user wants to override the project standard. If the request is clearly intentional, follow the user and keep the change locally consistent.

Reason: project rules should guide work, not block explicit product decisions.
