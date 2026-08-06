# Project instructions

This file is the operating contract for a greenfield SaaS application built with Next.js 15 App Router and SQLite. Follow it together with the user’s current request. When a request conflicts with this file, obey the user’s request and call out the trade-off in the change summary.

## Working method

### Before changing code

1. Read the target file and its nearest tests before editing it. This prevents local conventions from being replaced by a generic solution.
2. Trace the data path from route to UI to database before adding a new abstraction. This keeps validation, authorization, and persistence in the correct layer.
3. Search for existing helpers before creating a new one. Duplicate utilities drift and make behavior inconsistent.

### While changing code

- Keep changes narrow and reversible. Small diffs are easier to review and roll back.
- Prefer explicit types and named functions over clever inference. The codebase should be understandable to a new maintainer.
- Preserve existing behavior unless the request explicitly changes it. Compatibility is a feature.
- Add or update tests in the same change as the behavior. A feature without a regression test is unfinished.
- Never invent credentials, seed data that resembles real people, or external API responses. Fixtures must be clearly synthetic.

### After changing code

Run the smallest relevant checks first, then the full quality gate:

1. pnpm lint
2. pnpm typecheck
3. pnpm test
4. pnpm test:e2e when a route, form, auth flow, or database behavior changed
5. pnpm build

Do not report a task as complete if a required check was skipped. State the exact command and result.

## Stack and versions

- Node.js 20.18+; the repository’s .nvmrc is the source of truth.
- pnpm 9+; use pnpm consistently so lockfile behavior is reproducible.
- Next.js 15.x with the App Router; do not introduce the Pages Router.
- React 19.x and TypeScript 5.x with strict true.
- Tailwind CSS for styling and shadcn/ui-style primitives for reusable UI.
- Drizzle ORM for typed schema and queries.
- SQLite for local development and tests through better-sqlite3; use the same Drizzle schema with Turso/libSQL in deployed environments.
- Zod for parsing untrusted input at every boundary.
- Vitest for unit/integration tests and Playwright for browser tests.

Versions are intentionally major/minor scoped so security patches can be applied without rewriting the project instructions. When a dependency needs a breaking upgrade, update this section and the lockfile in the same change.

## Directory contract

src/
  app/
    (public)/                 Public pages and marketing routes
    (auth)/                   Authenticated route groups
    api/                      Thin HTTP adapters only
    layout.tsx                Root layout
    globals.css               Global styles and design tokens
  components/
    ui/                       Primitive, reusable UI components
    features/                 Feature-owned components
  lib/
    auth/                     Session and authorization boundary
    db/
      client.ts               Runtime-selected database client
      schema/                 One schema module per domain
      queries/                Named, server-only query functions
    env.ts                    Validated environment variables
    validation/               Shared Zod schemas
    http/                     Response and error helpers
  server/
    actions/                  Server Actions grouped by feature
    services/                 Use-case orchestration
drizzle/                      Generated SQL migrations; never hand-edit applied files
scripts/                      Deterministic local/CI scripts
tests/
  fixtures/                   Synthetic test data
  helpers/                    Test-only helpers
e2e/                          Playwright tests

Keep a feature’s UI, validation, service, query, and tests close enough to find together, but keep database primitives under src/lib/db. This separates product language from storage mechanics.

## Naming and module boundaries

- Use lower-case kebab-case for route folders and files, except Next.js special files such as page.tsx, layout.tsx, loading.tsx, error.tsx, and not-found.tsx.
- Use PascalCase for React components, camelCase for functions and variables, and useX for hooks.
- Use *.schema.ts for Zod schemas, *.queries.ts for database reads/writes, and *.test.ts for Vitest tests.
- Use snake_case for SQLite tables and columns; map them to camelCase in TypeScript.
- Name functions after business actions such as createInvoice and listProjectsForUser rather than transport details such as postData and runQuery.
- Keep one domain concept per module. Do not create catch-all utils.ts or helpers.ts files because they hide ownership and encourage circular dependencies.
- src/lib/db, src/server, and authentication modules are server-only. Add import server-only at the top of modules that must never enter a client bundle.
- Client components may receive serializable data and callbacks, but may not import database, filesystem, or secret-bearing modules.

## Development commands

The root package.json must expose these scripts:

pnpm dev             Start the Next.js development server
pnpm lint            Run ESLint
pnpm typecheck       Run tsc --noEmit
pnpm test            Run Vitest in CI mode
pnpm test:watch      Run Vitest interactively
pnpm test:e2e        Run Playwright
pnpm db:generate     Generate a new Drizzle migration from schema changes
pnpm db:migrate      Apply committed migrations to the configured database
pnpm db:seed         Load deterministic synthetic development data
pnpm db:check        Validate schema/migrations without changing production data
pnpm db:studio       Open Drizzle Studio for local inspection only
pnpm build           Create the production build
pnpm start           Start the production build

Run database commands with an explicit environment. A command must not silently point at a developer’s personal database because an accidental migration or seed is difficult to recover.

## Database rules

### Connection and environment

- src/lib/db/client.ts is the only module allowed to construct the Drizzle client.
- Local development uses DATABASE_URL=file:./data/dev.db with better-sqlite3.
- Turso uses TURSO_DATABASE_URL and TURSO_AUTH_TOKEN through the libSQL adapter.
- src/lib/env.ts validates environment variables at startup and never exports secrets to client code.
- Keep one process-local database client in development to avoid exhausting SQLite file handles during hot reload. Do not store request-specific state in that singleton.
- Enable foreign keys for every connection. SQLite does not enforce them by default on every connection.

### Schema and migrations

- Define tables and relations in src/lib/db/schema; the schema is the source of truth.
- Generate migrations with pnpm db:generate; commit the generated SQL and review it like application code.
- Apply migrations with pnpm db:migrate. Never use drizzle-kit push in CI or production because it bypasses a reviewable migration history.
- Never edit an already-applied migration. Add a new migration so rollback and audit history remain possible.
- Prefer additive migrations: add a nullable column, backfill it, then enforce NOT NULL in a later migration. SQLite table rebuilds can lock or rewrite data.
- Give every table a primary key, explicit foreign keys, created_at, and updated_at where the record is mutable.
- Store timestamps as UTC epoch milliseconds in SQLite and convert at the application boundary. Local-time strings sort incorrectly around daylight-saving changes.
- Add indexes for foreign keys and the exact filters and sorts used by real queries. Do not add speculative indexes because every index increases write cost.
- Use transactions for multi-row invariants, such as creating an order and its line items. A transaction must make the invariant true or leave no partial write.
- Use parameterized Drizzle expressions or bound parameters. Never concatenate user input into SQL.
- Select named columns rather than SELECT *. Stable response shapes prevent accidental data exposure when the schema grows.

### Query and service boundaries

- A query module owns persistence details and returns typed domain-shaped records.
- A service function owns a business use case and can call multiple query functions inside a transaction.
- A Server Action or route handler parses input, checks the session and authorization, calls a service, and maps the result to a response.
- Components never call the database directly. This makes authorization and transaction rules testable in one place.
- Do not issue one query per list row. Batch related reads or use a deliberate join to avoid N+1 behavior.
- Throw typed, user-safe domain errors from services. Do not leak SQL errors, stack traces, or internal IDs to clients.

## Next.js App Router rules

- Server Components are the default. Add use client only for state, event handlers, browser APIs, or a library that requires the browser; keeping interactive islands small reduces JavaScript sent to users.
- In Next.js 15, treat params, searchParams, cookies(), and headers() as asynchronous APIs and await them.
- Keep data fetching in Server Components or server services. Do not fetch the same server data again from a Client Component just to pass it through a second network hop.
- Use loading.tsx, error.tsx, and not-found.tsx at route boundaries where latency or failure is expected. A single root spinner hides which part failed.
- Make caching explicit. A request that contains user/session state must not be cached as public data.
- Revalidate after writes with the narrowest revalidatePath or tag invalidation that makes the changed view correct. Broad invalidation increases load and masks ownership.
- Use route handlers for public HTTP contracts, webhooks, and integrations. Use Server Actions for UI-triggered mutations that remain inside the application.
- Keep metadata and canonical URLs in the route that owns the page. Do not generate duplicate metadata in leaf components.

## Server Actions, forms, and validation

- Parse FormData, JSON bodies, query strings, and webhook payloads with Zod before using them.
- Validate again on the server even if the UI already validates. Client validation improves experience; it is not a security boundary.
- Authenticate before reading private data and authorize every object by ownership or explicit permission. Never rely on a hidden input containing a user ID.
- Return a small discriminated result for expected form errors, such as ok false with fieldErrors, and throw only for unexpected failures.
- Use idempotency keys for payment-like or retryable mutations. A browser retry must not create a second resource.
- Revalidate only after the transaction commits successfully.
- Escape or sanitize any user-controlled rich text at its rendering boundary. Do not use dangerouslySetInnerHTML for convenience.

## UI and accessibility

- Use semantic HTML before adding ARIA. A real button is preferable to a clickable div.
- Every form control needs a visible label or an equivalent accessible name, an error message, and a keyboard path.
- Keep loading, empty, error, and success states explicit. A blank table is ambiguous to users and hard to test.
- Keep feature-specific presentation in components/features; keep generic primitives in components/ui.
- Use design tokens and existing primitives before introducing new colors, spacing, or one-off CSS. Consistency is more valuable than local novelty.
- Do not put secrets, authorization decisions, or sensitive record fields into data attributes or client-readable props.

## Testing contract

- Unit-test pure parsing, authorization, business rules, and formatting.
- Integration-test services against a fresh temporary SQLite database with migrations applied. Never point tests at data/dev.db.
- Each test owns its data and can run in isolation. Use deterministic IDs and fixed UTC timestamps in fixtures.
- Test both success and failure paths: unauthenticated, unauthorized, invalid input, missing record, duplicate request, and transaction rollback.
- Playwright tests use a disposable database and a seeded synthetic account. Never use a personal account or production data.
- Mock third-party APIs at the boundary. Add a small contract test for the adapter when the provider’s schema matters.
- Accessibility checks belong in Playwright for important flows: keyboard navigation, labels, focus after errors, and meaningful status text.
- Do not weaken a test to make a bug pass. Fix the implementation or document the intentional behavior.

## Security and operations

- Keep all secrets in environment variables or the deployment secret store. Never commit .env, tokens, session cookies, or copied production payloads.
- Log event names, request IDs, and safe identifiers; never log passwords, auth tokens, full payment data, or raw personal records.
- Rate-limit public mutations and validate webhook signatures before parsing business content.
- Use secure, httpOnly, same-site cookies for sessions. Do not store session tokens in localStorage.
- Apply least privilege to database credentials and integration tokens.
- Prefer a safe failure: if authorization or signature verification cannot be completed, reject the request.
- Add an explicit timeout and bounded response size to every external request.

## What we do not do

- Do not add Pages Router files; the application has one routing model.
- Do not put use client on a layout or page to avoid designing a server/client boundary; that ships unnecessary JavaScript and can expose server assumptions.
- Do not call process.env throughout the codebase; use the validated environment module so missing configuration fails early.
- Do not change the schema without a migration; the production database cannot be reconstructed from TypeScript alone.
- Do not run destructive SQL, drizzle-kit push, or mass deletes in production without an explicit reviewed migration or operational runbook.
- Do not use any, ts-ignore, or broad type assertions to silence a failing check; make the boundary type-safe.
- Do not use SELECT *, unbounded list queries, or client-side filtering of private records.
- Do not use local timezone arithmetic for persisted timestamps.
- Do not add network-dependent tests to the default unit-test command.
- Do not add a dependency for a helper that fits in a small, tested local function.
- Do not include real secrets or personal information in examples, screenshots, fixtures, or commit messages.

## Definition of done

A change is ready only when:

1. The requested behavior is implemented at the correct boundary.
2. Input validation and authorization are present for every mutation or private read.
3. Database changes have a reviewed migration and a rollback or backfill story.
4. Loading, empty, error, and success states are handled where users can observe them.
5. Tests cover the happy path and the most important failure paths.
6. pnpm lint, pnpm typecheck, pnpm test, and pnpm build pass; run pnpm test:e2e when UI or integration behavior changed.
7. The final summary lists changed files, test commands, migration notes, and any follow-up risk.
