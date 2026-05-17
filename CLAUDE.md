# CLAUDE.md

This file gives Claude Code the project rules for a production SaaS built with
Next.js 15 App Router, TypeScript, SQLite, and server-first React patterns.

## Stack And Versions

- Runtime: Node.js 22 LTS or newer. Use one runtime across local development,
  CI, and production so native SQLite bindings behave consistently.
- Framework: Next.js 15 with the App Router in `app/`.
- Language: TypeScript in strict mode. Do not add new JavaScript source files.
- UI: React 19, Server Components by default, Client Components only when
  browser state, effects, refs, or event handlers are required.
- Database: SQLite through either `better-sqlite3` for a single-node app or
  Turso/libSQL for hosted SQLite. Keep the data-access contract the same when
  switching between them.
- Styling: Tailwind CSS plus small, typed component wrappers. Do not introduce a
  second styling system unless the project already has one.
- Validation: Zod at every external boundary, including route handlers, server
  actions, webhooks, and environment variables.
- Authentication: Auth.js, Clerk, or a project-approved provider. Never roll
  password storage, sessions, or OAuth flows by hand.
- Testing: Vitest for unit tests, Playwright for critical flows, and a migration
  smoke test for schema changes.

## Development Commands

Use the package manager already present in the lockfile. If this is a new
project, prefer `pnpm`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
pnpm build
```

When adding scripts, keep names boring and predictable:

- `dev`: start the local Next.js server.
- `build`: create a production build.
- `start`: run the production build.
- `lint`: run ESLint.
- `typecheck`: run `tsc --noEmit`.
- `test`: run unit and integration tests that do not need a browser.
- `test:e2e`: run Playwright.
- `db:generate`: generate migration files if the migration tool supports it.
- `db:migrate`: apply pending migrations.
- `db:rollback`: rollback only when the tool has a safe, reviewed rollback path.
- `db:studio`: open the database browser.

Do not mark a task complete until `pnpm lint`, `pnpm typecheck`, and the most
focused relevant tests pass.

## Project Structure

Use `app/` for routing and composition only. Keep business logic in `features/`
or `lib/` so it is testable without rendering a route.

```text
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
      stripe/
        route.ts
  layout.tsx
  globals.css
components/
  ui/
  layout/
features/
  billing/
    actions.ts
    components/
    data.ts
    schemas.ts
    service.ts
    tests/
  projects/
    actions.ts
    components/
    data.ts
    schemas.ts
    service.ts
    tests/
lib/
  auth/
  db/
    client.ts
    migrations/
    schema.ts
    seed.ts
  env.ts
  errors.ts
  ids.ts
  permissions.ts
  result.ts
tests/
  e2e/
public/
```

Folder rules:

- Route groups such as `(marketing)` and `(app)` separate layouts without
  changing URLs.
- Each feature owns its server actions, data access, schemas, service logic,
  feature-specific components, and tests.
- Shared UI primitives live in `components/ui`. Domain components stay inside
  their feature unless two or more features genuinely need them.
- `lib/` is for cross-cutting infrastructure only: database, auth, env parsing,
  permissions, ids, logging, and typed error helpers.
- Do not put reusable service code under `app/`. Route files should be thin.

## Naming Conventions

- Files and folders use kebab-case: `billing-portal-button.tsx`.
- React components use PascalCase exports: `BillingPortalButton`.
- Hooks start with `use` and live in Client Component files only when they depend
  on browser APIs.
- Server actions end with `Action`: `createProjectAction`.
- Data-access functions describe the query: `getProjectById`,
  `listProjectsForUser`, `insertProject`.
- Zod schemas end with `Schema`: `createProjectInputSchema`.
- Types are nouns: `Project`, `ProjectSummary`, `BillingPlan`.
- Environment variables are uppercase and validated in `lib/env.ts`.
- Database columns use snake_case. TypeScript objects use camelCase. Convert at
  the data boundary, not throughout the UI.

## App Router Rules

- `page.tsx`, `layout.tsx`, `loading.tsx`, and `error.tsx` are composition
  files. They fetch data, compose components, and delegate behavior.
- Server Components are the default. Add `"use client"` only at the smallest
  leaf that needs interactivity.
- Do not import server-only modules into Client Components. This includes
  database clients, filesystem access, secrets, and admin SDKs.
- Prefer direct server-side function calls from Server Components over calling
  your own route handlers with `fetch`.
- Use route handlers for third-party webhooks, public HTTP APIs, file uploads,
  callbacks, and endpoints consumed outside the React tree.
- Keep dynamic route params typed and validated before use.
- Add `loading.tsx` for slow routes and `error.tsx` for recoverable route-level
  failures.
- Use `notFound()` for missing resources and typed authorization errors for
  forbidden resources.

## Data Fetching And Mutations

- Read data in Server Components or server-only data functions.
- Mutate data through server actions for app UI forms and route handlers for
  external clients or webhooks.
- Validate every mutation input with Zod before touching the database.
- Check authorization in the same server-side function that performs the read or
  write. UI checks are for user experience, not security.
- Return typed domain results from services. Do not leak raw SQLite driver errors
  into components.
- Revalidate paths or tags immediately after successful mutations that affect
  rendered data.
- Prefer small, explicit queries over generic repository methods that hide SQL.
- Avoid hidden writes in read functions. A function named `get...` must not
  mutate state.

## SQLite Rules

SQLite is reliable for SaaS when the access pattern is explicit and migrations
are disciplined.

- Use WAL mode for local single-node SQLite when supported.
- Enable foreign keys on every connection.
- Keep transactions short. Do not perform network calls inside a transaction.
- Add indexes for foreign keys and common filters before shipping the query.
- Store money in integer minor units such as cents.
- Store timestamps as ISO strings or integer epoch milliseconds. Pick one per
  project and document it in `lib/db/schema.ts`.
- Use text ids generated by the application, such as `user_...` or `proj_...`,
  when records cross system boundaries.
- Do not use SQLite as a background job queue once jobs need concurrency,
  retries, or delayed scheduling. Use a real queue for that.

Connection pattern:

- `lib/db/client.ts` owns driver initialization.
- Server code imports query functions, not the raw driver, unless it is inside
  `lib/db`.
- Tests use isolated temporary databases and run migrations before assertions.
- Production code must not call seed helpers.

## Migration Conventions

Schema changes are append-only and reviewable.

- Every schema change gets a migration file committed with the code that uses it.
- Migration filenames start with an ordered timestamp:
  `202605171030_add_projects_table.sql`.
- A migration must be deterministic. Do not depend on local paths, current time,
  or external network calls.
- Prefer expand-and-contract changes for production data:
  1. Add nullable column or new table.
  2. Backfill data with an idempotent script.
  3. Deploy code that reads both old and new shapes.
  4. Enforce `NOT NULL` or remove old columns in a later migration.
- Never edit a migration that has already been applied outside local development.
  Add a new migration instead.
- Include rollback notes in the PR when rollback is not automatic.
- For destructive migrations, require a backup plan and a count query showing the
  affected rows.

Migration review checklist:

- Does it run on a fresh database?
- Does it run on a database with existing data?
- Are foreign keys and indexes present?
- Are default values intentional?
- Is the application code compatible during a rolling deploy?

## Environment Variables

All environment access goes through `lib/env.ts`.

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Client-exposed variables must start with `NEXT_PUBLIC_`.
- Secrets must never be read in Client Components.
- Tests should set explicit environment variables instead of depending on a
  developer machine.
- Do not add fallback secrets in code. Fail fast during startup.

## Component Patterns

- Keep pages server-rendered and pass only serializable props to Client
  Components.
- Move interactivity into small client leaves such as menus, dialogs, forms,
  comboboxes, and optimistic buttons.
- Use composition over configuration objects for UI. A clear component tree is
  easier for Claude Code and humans to change safely.
- Keep form components close to their feature. Shared form primitives can live in
  `components/ui`.
- Accessibility is part of done: labels, keyboard navigation, focus states, and
  useful error messages.
- Use `Suspense` around slow, independent sections rather than blocking the
  whole route.
- Prefer server-rendered empty, loading, and error states over client-only
  spinners.

Client Component rules:

- The first line must be `"use client"`.
- Do not import database, auth admin, filesystem, or server-only modules.
- Receive minimal props. Do not pass entire database rows when only a label and
  id are needed.
- Keep browser state local unless multiple routes need it.

## Server Actions

Server actions are for app-owned mutations triggered by the UI.

```ts
"use server";

import { revalidatePath } from "next/cache";
import { createProjectInputSchema } from "./schemas";
import { createProject } from "./service";

export async function createProjectAction(input: unknown) {
  const parsed = createProjectInputSchema.safeParse(input);

  if (!parsed.success) {
    return { ok: false, error: "Invalid project details" };
  }

  const project = await createProject(parsed.data);
  revalidatePath("/dashboard/projects");

  return { ok: true, projectId: project.id };
}
```

Rules:

- Validate `unknown` input.
- Authenticate and authorize on the server.
- Return small typed results. Do not return raw errors or stack traces.
- Revalidate affected routes after successful writes.
- Keep side effects explicit and test service logic separately from the action.

## Route Handlers

Route handlers are public HTTP boundaries.

- Use them for webhooks, OAuth callbacks, public APIs, file upload signatures,
  and integrations.
- Validate method, headers, params, query, and body.
- Verify webhook signatures before parsing or trusting payloads.
- Return `Response.json()` with stable status codes.
- Do not expose internal exception messages.
- Keep route handlers thin: validate, authorize, call a service, return a
  response.

## Authentication And Authorization

- Authentication identifies the user. Authorization decides what the user can do.
  Keep both checks server-side.
- Centralize session lookup in `lib/auth`.
- Centralize permission checks in `lib/permissions.ts`.
- Every query for user-owned data must scope by the authenticated user or
  organization.
- Do not trust ids from forms or URLs without checking ownership.
- Admin-only operations require an explicit role check in the server function,
  even if the UI hides the button.

## Error Handling

- Use typed domain errors for expected failures: validation, unauthorized,
  forbidden, not found, conflict, and rate limited.
- Let unexpected errors surface to route-level error boundaries after logging.
- User-facing messages should be useful but not leak implementation details.
- Include enough context in logs to debug, but never log secrets, tokens, full
  payment data, or private user content.
- Do not swallow errors with empty `catch` blocks.

## Testing Rules

- Test service functions with isolated SQLite databases.
- Test server actions at the input/output boundary with mocked auth only when
  unavoidable.
- Test route handlers with real `Request` objects.
- Add Playwright coverage for signup, login, billing, and the primary paid user
  workflow.
- Every migration must be exercised against a fresh test database.
- Regression tests are required for bug fixes.

Test naming:

```text
features/projects/tests/create-project.test.ts
features/billing/tests/stripe-webhook.test.ts
tests/e2e/project-lifecycle.spec.ts
```

## Security Rules

- Treat all form data, route params, query params, headers, cookies, and webhook
  bodies as untrusted.
- Validate input with Zod and authorize with server-side checks.
- Keep secrets on the server. Never put secrets in `NEXT_PUBLIC_` variables.
- Use parameterized queries or the query builder provided by the chosen SQLite
  library. Never concatenate user input into SQL.
- Add rate limiting to public mutation endpoints.
- Verify CSRF posture for cookie-authenticated mutations.
- Sanitize user-provided HTML or avoid rendering it as HTML.
- Use secure cookie settings in production.

## Performance Rules

- Start with Server Components and streamed route sections.
- Avoid client-side data waterfalls.
- Keep Client Components small to reduce JavaScript shipped to the browser.
- Add database indexes before adding caching.
- Cache only when invalidation is clear.
- Do not cache user-specific data in a way that can cross accounts.
- Prefer pagination over loading unbounded lists.
- Avoid N+1 queries in dashboards and list pages.

## Pull Request Checklist

Before opening a PR:

- `pnpm lint` passes.
- `pnpm typecheck` passes.
- Relevant unit or integration tests pass.
- `pnpm build` passes for routing, server action, or config changes.
- Database migrations run on a fresh database.
- New environment variables are documented and validated in `lib/env.ts`.
- User-facing changes include loading, empty, and error states.
- Security-sensitive changes include authorization tests.

PR description must include:

- What changed.
- Why this approach was chosen.
- How it was tested.
- Migration notes, if any.
- Screenshots or recordings for UI changes.

## What We Do Not Do

- Do not use the Pages Router. This project is App Router first so routing,
  layouts, and Server Components share one mental model.
- Do not put business logic in `page.tsx` or `route.ts`. Thin routes make the
  code easier to test and safer for Claude Code to modify.
- Do not make broad abstractions before two features need the same shape.
  Premature abstractions hide product rules.
- Do not add a global state manager for server data. Use server rendering,
  actions, cache revalidation, and small client state.
- Do not call internal route handlers from Server Components. Direct function
  calls keep types, errors, and auth easier to reason about.
- Do not create new database connections throughout the app. Centralized
  connection management prevents native binding and file-lock surprises.
- Do not edit applied migrations. Production databases need an auditable history.
- Do not ship generic CRUD without ownership checks. SaaS data is almost always
  tenant-scoped.
- Do not return raw driver errors to users. They leak details and create brittle
  UI behavior.
- Do not introduce heavy dependencies for one component. Prefer small local code
  unless the dependency is already part of the stack.

## Claude Code Operating Rules

- Read existing files before editing and follow the local pattern when it exists.
- Keep changes scoped to the requested behavior.
- Prefer deleting unnecessary code over adding compatibility layers.
- When uncertain about product behavior, make the smallest reversible change and
  leave a clear note in the PR.
- Do not change formatting across unrelated files.
- Do not add comments that restate obvious code. Add comments only to explain
  business rules, security decisions, or non-obvious tradeoffs.
- If a command fails, fix the underlying issue or report the exact blocker.
- Never mark work complete without saying which checks ran.
