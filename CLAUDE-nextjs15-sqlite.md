# CLAUDE.md — Next.js 15 + SQLite SaaS

This file gives Claude Code project context for a production SaaS built with
Next.js 15 App Router, TypeScript, React Server Components, Server Actions, and
SQLite through Drizzle ORM plus either `better-sqlite3` locally or Turso/libSQL in
hosted environments.

## Stack and versions

- Next.js 15 with App Router only. Do not add Pages Router.
- React 19 and Server Components by default.
- TypeScript strict mode. No `any` unless the boundary is untyped and the value
  is immediately validated.
- SQLite as the source of truth.
- Drizzle ORM for schema, typed queries, and migrations.
- `better-sqlite3` for local/single-node deployments; Turso/libSQL when the app
  needs remote or edge-friendly SQLite.
- Zod for all external input validation.
- Tailwind CSS for styling and shadcn/ui-style colocated components.
- Vitest for unit tests and Playwright for critical auth/billing flows.

Reason: this stack keeps the app deployable as a small SaaS without introducing a
separate API server or heavyweight database until product-market fit demands it.

## Folder structure

Use this structure unless the existing repo already has a clear equivalent:

```text
app/
  (marketing)/          Public pages and landing pages
  (app)/                Authenticated product shell
  api/                  Route handlers only for webhooks or third-party callbacks
  actions/              Server Actions grouped by domain
components/
  ui/                   Primitive reusable UI
  domain/               Product-specific components
  forms/                Client components for validated forms
db/
  index.ts              DB client factory
  schema.ts             Drizzle table definitions
  migrations/           Generated SQL migrations
lib/
  auth.ts               Session/user helpers
  env.ts                Environment validation
  permissions.ts        Role/plan checks
  validators/           Zod schemas
server/
  services/             Domain service functions used by actions/routes
tests/
  unit/
  e2e/
```

Reason: routes stay thin, DB concerns stay explicit, and Claude can find the
right layer without inventing new architecture.

## Naming conventions

- Files and directories: kebab-case, e.g. `billing-page.tsx`.
- React components: PascalCase exports, e.g. `BillingPage`.
- Server Actions: verb-noun names ending with `Action`, e.g.
  `updateWorkspaceAction`.
- Service functions: verb-noun names without framework wording, e.g.
  `updateWorkspace`.
- Database tables: plural snake_case, e.g. `workspace_members`.
- Database columns: snake_case in SQLite, camelCase in TypeScript via Drizzle.
- Zod schemas: noun plus `Schema`, e.g. `workspaceUpdateSchema`.

Reason: names encode layer and intent, which reduces accidental client/server
boundary mistakes.

## Server/client boundaries

- Prefer Server Components. Add `"use client"` only for state, effects, browser
  APIs, or interactive form widgets.
- Never import `db`, `server/*`, secrets, or Node-only modules from a Client
  Component.
- Keep Client Components leaf-level. Pass serializable props from Server
  Components.
- Route Handlers are for webhooks, OAuth callbacks, file uploads, and public API
  surfaces. Internal UI mutations should use Server Actions.
- Server Actions must validate input, check auth/permission, call a service, and
  return a typed result. Do not put complex business logic directly inside the
  action.

Reason: most Next.js SaaS bugs come from leaking server-only code into the
client bundle or mixing UI and mutation logic.

## Database schema and migration rules

- `db/schema.ts` is the only place to define tables.
- Generate migrations with Drizzle tooling. Do not hand-edit generated migration
  files unless fixing a reviewed generation bug.
- Every schema change requires:
  1. updated Drizzle schema,
  2. generated migration,
  3. local migration test against a copy or disposable SQLite database,
  4. rollback notes in the PR if data is modified or removed.
- Never use destructive migrations casually. For renames, create new column,
  backfill, deploy, read from new column, then remove old column in a later PR.
- Avoid SQLite features unavailable in Turso/libSQL if the project targets Turso.
- Add indexes for foreign keys and query filters used on list pages.
- Use transactions for multi-table writes.
- Store money as integer minor units plus currency, not floating point.

Reason: SQLite is reliable for SaaS when migrations are boring, reversible, and
explicit about data movement.

## Query and service patterns

- Server Components may read through small query helpers in `server/services/*`.
- Mutations go through Server Actions or Route Handlers, then call service
  functions.
- Services receive a typed context object: `{ userId, workspaceId, role }` when
  authorization matters.
- Do not trust `workspaceId`, `userId`, `role`, or `priceId` from the client.
  Derive them from session, DB, or Stripe/webhook state.
- Return domain objects or typed DTOs, not raw request objects.
- Use cursor pagination for unbounded lists.

Reason: the service layer is the seam where auth, validation, and tests stay
framework-light.

## Validation and error handling

- Validate all form data, search params, route params, webhook payloads, and
  JSON request bodies with Zod or equivalent typed guards.
- Use `lib/env.ts` to validate environment variables at startup.
- Server Actions return `{ ok: true, data }` or `{ ok: false, error }` for
  expected failures.
- Throw only for unexpected invariant failures.
- Do not expose raw database, Stripe, OAuth, or stack errors to users.
- Log enough context to debug: action name, user id, workspace id, and safe error
  code. Never log secrets or full tokens.

Reason: predictable errors make Claude-generated UI easier to wire without
sprinkling try/catch everywhere.

## Auth, permissions, and tenancy

- All authenticated product pages must load the session on the server.
- Check workspace membership before every workspace-scoped read or write.
- Keep role and plan checks in `lib/permissions.ts`; do not duplicate permission
  logic in components.
- Use secure, httpOnly cookies for sessions.
- Never rely on hidden form fields for authorization.
- Treat billing plan state as cached display data unless confirmed by Stripe or
  the billing source of truth.

Reason: SaaS security bugs usually happen when one route trusts a client-provided
workspace or role value.

## Component patterns

- Server Component pages fetch data and pass plain props down.
- Client form components own local pending/error UI but call Server Actions for
  mutation.
- Keep UI primitives in `components/ui` free of product logic.
- Keep domain components in `components/domain` aware of product language but not
  database clients.
- Prefer composition over giant configurable components.
- Accessibility is required: labels, keyboard states, focus handling, and semantic
  HTML for forms/tables/navigation.

Reason: this keeps render paths simple and prevents generic UI from becoming a
hidden business-logic layer.

## Dev commands

Use the project's package manager. If none exists, prefer `pnpm`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

Before finishing a PR, run at minimum:

```bash
pnpm lint && pnpm typecheck && pnpm test
```

If database schema changed, also run:

```bash
pnpm db:generate && pnpm db:migrate
```

Reason: lint, types, tests, and migration execution catch the majority of
Claude-generated regressions before review.

## Patterns to follow

- Put `import "server-only"` at the top of server-only modules.
- Use `revalidatePath` or `revalidateTag` immediately after successful mutations
  that affect cached pages.
- Keep `loading.tsx`, `error.tsx`, and `not-found.tsx` close to the route segment
  they support.
- Use explicit selected columns in hot queries.
- Add tests for validators and permission helpers before large UI flows.
- Keep seed data realistic but tiny.
- For webhooks, verify signatures before parsing or mutating anything.

Reason: these patterns give Claude safe rails while preserving Next.js App Router
idioms.

## Anti-patterns to avoid

- Do not create a separate Express server for normal SaaS UI/API needs.
  Next.js Route Handlers are enough.
- Do not use Prisma unless the project already chose it. This template assumes
  Drizzle because migrations and SQLite/Turso control are more explicit.
- Do not put DB calls inside Client Components.
- Do not add global state libraries for server-owned data.
- Do not create one `utils.ts` dumping ground. Create domain-named modules.
- Do not use raw SQL string interpolation. Use Drizzle query builders or
  parameterized SQL.
- Do not run destructive migrations in production without a staged data plan.
- Do not treat Stripe checkout success redirects as proof of payment; use
  webhooks.

Reason: each anti-pattern adds avoidable operational or security risk for a small
SaaS team.

## PR checklist for Claude

When making changes, include this in the PR body:

- What changed and why
- Screenshots for UI changes
- Validation commands run
- Database migration notes, if any
- Auth/permission implications
- Rollback notes for risky changes

If you cannot run a command, say exactly why and what would need to run next.

## First response behavior for Claude Code

When Claude Code starts in this project:

1. Read this file, `package.json`, `db/schema.ts`, and route structure before
   editing.
2. Identify whether the task touches UI, server actions, DB schema, auth, billing,
   or webhooks.
3. Ask clarifying questions only if the task changes product behavior or payment
   logic. Otherwise inspect files and implement.
4. Prefer minimal, typed changes over broad refactors.
5. Validate with the smallest relevant command first, then the full PR checklist
   if changes are accepted.

Reason: Claude should spend tokens understanding the existing app, not inventing a
new SaaS architecture.
