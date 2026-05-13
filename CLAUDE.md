# CLAUDE.md

This file is the operating manual for Claude Code in a production-minded
Next.js 15 App Router SaaS application backed by SQLite. Treat it as a contract:
follow these rules unless the user explicitly asks for a different architecture.

## Stack And Versions

- Framework: Next.js 15 with App Router, React Server Components by default, and
  Server Actions only for small trusted mutations.
- Language: TypeScript in strict mode. Do not introduce `any` unless the value is
  from an untyped boundary and is immediately narrowed.
- Database: SQLite through a typed query layer. Prefer Drizzle ORM with either
  `better-sqlite3` for local/serverful deployments or `@libsql/client` for Turso.
- Styling: Tailwind CSS plus small local components. Keep component APIs boring
  and explicit so SaaS screens remain easy to scan and maintain.
- Auth: use a server-side session helper behind `src/server/auth.ts`. Do not read
  raw cookies in page components.
- Payments/email/storage: isolate providers behind server modules. Product code
  should depend on `src/server/billing`, `src/server/email`, and
  `src/server/storage`, not vendor SDKs directly.

Why: a small SaaS stays reliable when framework, database, and external service
boundaries are explicit. Most bugs in this stack come from mixing browser code,
server-only code, and database effects in the same file.

## Useful Commands

- `pnpm dev`: run the app locally.
- `pnpm lint`: run ESLint and framework checks.
- `pnpm typecheck`: run `tsc --noEmit`.
- `pnpm test`: run unit and integration tests.
- `pnpm db:generate`: generate a migration after schema changes.
- `pnpm db:migrate`: apply migrations locally or in CI.
- `pnpm db:studio`: inspect local development data.

If a command is missing, add the script instead of inventing a one-off command in
the answer. Repeatable project commands are part of the product.

## Folder Structure

Use this layout for new code:

```text
src/
  app/
    (app)/                 # authenticated product screens
    (marketing)/           # public pages, pricing, docs
    api/                   # route handlers for webhooks and public API only
  components/
    ui/                    # primitive reusable UI
    forms/                 # form components with no business effects
    data-display/          # tables, empty states, charts, lists
  features/
    organizations/
      components/
      queries.ts
      actions.ts
      validators.ts
      permissions.ts
    billing/
    projects/
  server/
    auth.ts
    db/
      index.ts
      schema.ts
      migrations/
    billing/
    email/
    logger.ts
  lib/
    dates.ts
    env.ts
    errors.ts
    ids.ts
  tests/
```

Rules:

- Put route segments in `src/app`, not business logic. Pages compose feature
  modules and server queries.
- Put domain behavior in `src/features/<domain>`. Each feature owns its queries,
  actions, validation, permissions, and local components.
- Put cross-cutting infrastructure in `src/server` or `src/lib`.
- Never import from `src/app` into `src/features`, `src/server`, or `src/lib`.

Why: App Router files change shape with routing requirements. Domain modules
should survive URL and layout changes without being rewritten.

## Server And Client Boundaries

- Components are Server Components unless they need browser state, effects,
  browser APIs, or event handlers.
- A file with `"use client"` may import only UI helpers, types, and safe client
  utilities. It must not import database clients, secrets, auth internals, or
  server modules.
- Use Server Components for initial data loading. Use client components for local
  interaction after data is loaded.
- Keep Server Actions small: validate input, check permissions, call one domain
  service, revalidate or redirect, and return a typed result.
- Use route handlers for webhooks, third-party callbacks, file uploads, and
  public API endpoints. Do not route normal form submissions through `/api`.

Why: Next.js can blur server and browser code. Explicit boundaries prevent secret
leaks, oversized bundles, and hydration bugs.

## Naming Conventions

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts`.
- Server queries: `getThing`, `listThings`, `countThings`.
- Mutations/actions: `createThing`, `updateThing`, `deleteThing`, `archiveThing`.
- Validators: `thingInputSchema`, `createThingSchema`.
- Permissions: `canReadThing`, `canUpdateThing`.
- Database tables: singular snake case, for example `organization`, `project`,
  `subscription`.
- Database columns: snake case in SQL, camelCase in TypeScript when the ORM
  supports mapping.

Why: predictable names let Claude find the right layer quickly and avoid
duplicating code under near-miss names.

## Environment Variables

- Define all environment variables in `src/lib/env.ts`.
- Validate env at process start with Zod or an equivalent schema.
- Split public variables from server-only variables. Only variables prefixed with
  `NEXT_PUBLIC_` may reach the browser.
- Do not read `process.env` outside `src/lib/env.ts`.

Why: scattered env reads create late runtime failures and make preview
deployments fragile.

## SQLite And Migration Conventions

- The schema source of truth lives in `src/server/db/schema.ts`.
- Migrations are append-only. Never edit a migration that has been merged.
- Generate migrations with `pnpm db:generate`; apply them with `pnpm db:migrate`.
- Every table has:
  - `id` as a stable text primary key unless there is a strong reason to use an
    integer rowid.
  - `created_at` and `updated_at`.
  - foreign keys with explicit `on delete` behavior.
- Store money in integer minor units plus currency, never floating point.
- Store timestamps as ISO strings or integer milliseconds consistently across
  the whole app. Prefer UTC.
- Add indexes for every foreign key and every high-cardinality filter used in a
  list page.
- Use transactions for multi-row writes and for any mutation that must remain
  consistent with an audit log, subscription state, or usage counter.
- Do not use SQLite triggers unless a plain transaction cannot express the rule.
- Do not rely on SQLite accepting loose types. Validate at the application
  boundary and keep schema constraints strict.

Why: SQLite is excellent for SaaS when writes are deliberate and migrations are
boring. Most SQLite production incidents come from missing indexes, edited
migrations, and multi-step writes without transactions.

## Query And Mutation Patterns

Server query example:

```ts
export async function getProjectForUser(projectId: string, userId: string) {
  const session = await requireSession();
  assertSameUser(session.user.id, userId);

  return db.query.project.findFirst({
    where: and(eq(project.id, projectId), eq(project.ownerId, userId)),
  });
}
```

Server action shape:

```ts
export async function updateProjectAction(input: unknown) {
  const session = await requireSession();
  const parsed = updateProjectSchema.parse(input);

  await assertCanUpdateProject(session.user.id, parsed.projectId);

  return db.transaction(async (tx) => {
    const updated = await updateProject(tx, parsed);
    await writeAuditEvent(tx, {
      actorId: session.user.id,
      action: "project.updated",
      subjectId: updated.id,
    });
    return { ok: true, project: updated };
  });
}
```

Rules:

- Parse `unknown` input at the edge. Do not pass unvalidated request data deeper
  into feature code.
- Check permissions in the same server-side call path as the database write.
- Return typed success or failure objects from actions that are used by client
  forms.
- Throw typed server errors for unexpected conditions and log them once at the
  boundary.

Why: colocating validation, authorization, and the write keeps SaaS mutations
auditable and easier to review.

## Component Patterns

- Keep page components thin: load data, choose layout, and pass typed props.
- Prefer small presentational components over generic configurable panels.
- Forms use `react-hook-form` plus a schema resolver when client interactivity is
  needed. Simple forms can post to a Server Action directly.
- Tables expose empty, loading, and error states. A SaaS list without an empty
  state is unfinished.
- Buttons that mutate data must show pending state and prevent duplicate submits.
- Destructive actions require a confirmation UI and should call an action named
  for the domain operation, such as `archiveProjectAction`.
- Do not fetch data from client components on initial page load unless the data is
  truly browser-specific.

Why: SaaS users repeat workflows. Stable states, predictable forms, and server
loaded data make the interface feel fast and trustworthy.

## API And Webhook Rules

- Webhook routes live under `src/app/api/<provider>/webhook/route.ts`.
- Always verify webhook signatures before parsing business fields.
- Store provider event IDs and make webhook handlers idempotent.
- Return 2xx only after the event has been durably recorded or safely ignored.
- Keep provider-specific payload shapes inside the provider module.

Why: payment and email providers retry aggressively. Idempotency prevents duplicate
invoices, duplicate emails, and inconsistent subscription state.

## Testing Expectations

- Add unit tests for validators, permissions, and pure domain functions.
- Add integration tests for database queries and mutations that touch more than
  one table.
- Add at least one route/action test for each high-risk workflow: signup,
  checkout, webhook processing, inviting a user, changing roles, and deleting or
  archiving data.
- Tests may use an in-memory SQLite database only if it matches production
  pragmas and migration behavior. Otherwise use a temporary file database.
- Do not mock the database for query builder tests. Mock external providers at
  the provider boundary.

Why: the database is part of the product contract. Mocking it hides the exact
class of bugs SQLite projects most often ship.

## Logging And Errors

- Use `src/server/logger.ts` for server logs.
- Log each unexpected error once with request ID, user ID when available, and
  relevant domain IDs.
- Never log secrets, raw cookies, access tokens, payment method details, or full
  webhook payloads.
- User-facing errors should be specific enough to recover from, but not reveal
  whether another account or private resource exists.

Why: useful logs shorten incident response, but SaaS logs easily become a privacy
liability if they capture provider payloads or authentication data.

## Security And Multi-Tenancy

- Every query for tenant-owned data must include organization or owner scope.
- Do not trust IDs from the client. Re-check ownership on the server.
- Keep role checks in `permissions.ts` for each feature.
- Use secure, httpOnly cookies for sessions.
- Rate-limit public auth, invite, password reset, and webhook endpoints.
- Use CSRF-safe patterns for cookie-authenticated mutations.
- Do not render untrusted HTML. If unavoidable, sanitize it server-side.

Why: SaaS security failures are often simple tenant isolation mistakes. Make the
scope explicit in every query and every mutation.

## Performance Rules

- Prefer one explicit server query over many small queries in a component tree.
- Watch for N+1 queries in dashboards, tables, and activity feeds.
- Paginate list pages from the first implementation.
- Add database indexes in the same change that adds a new filtered list or
  lookup path.
- Use `revalidatePath` or `revalidateTag` narrowly after mutations.

Why: SQLite performs very well when access patterns are intentional. It degrades
when list pages grow without indexes or pagination.

## What We Do Not Do

- Do not put database queries in client components. It leaks architecture and can
  leak secrets.
- Do not edit merged migrations. Create a new migration that moves the schema
  forward.
- Do not introduce a global state library for server data. Use Server Components,
  actions, and cache invalidation first.
- Do not create catch-all utility files such as `helpers.ts` or `utils.ts`. Name
  modules by domain or responsibility.
- Do not add an API route just because a form needs to mutate data. Use a Server
  Action unless the endpoint is public or provider-facing.
- Do not store JSON blobs for core relational data. Use tables and relations so
  permissions, indexes, and migrations remain clear.
- Do not swallow errors with `console.error` and a generic fallback. Return a
  typed result or throw a typed server error.

Why: these shortcuts feel fast at the start and become expensive when the product
adds teams, billing, audits, support workflows, and data exports.

## Claude Workflow For This Project

1. Inspect existing files before editing. Match the local patterns unless they
   conflict with this guide.
2. Identify the server/client boundary for the change.
3. Update schema and migrations together when data shape changes.
4. Add or update tests at the lowest layer that proves the behavior.
5. Run `pnpm lint`, `pnpm typecheck`, and relevant tests before finalizing.
6. Summarize changed files, commands run, and any verification gaps.

When uncertain, choose the smallest change that preserves tenant isolation,
typed data flow, and migration safety.
