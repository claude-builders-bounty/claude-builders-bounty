# CLAUDE.md - Next.js 15 App Router + SQLite SaaS

Use this file as the project memory for a greenfield SaaS built with Next.js 15 App Router, React 19, TypeScript, Tailwind CSS, and SQLite through either `better-sqlite3` for single-node deployments or Turso/libSQL for hosted edge-adjacent deployments.

## Stack And Versions

- Use Next.js 15 App Router, React 19, TypeScript `strict: true`, and Server Components by default. Reason: App Router keeps data fetching close to routes, and strict TypeScript catches schema drift before runtime.
- Use SQLite as the transactional source of truth. Reason: SaaS MVPs benefit from one simple relational database before adding distributed systems.
- Use `better-sqlite3` only in Node.js runtime routes, server actions, scripts, and background jobs. Reason: it is synchronous and native; it must not be imported by Client Components or Edge runtime code.
- Use Turso/libSQL when the app must run near users or deploy without local disk. Reason: the HTTP client is portable while keeping SQLite semantics.
- Use Zod for runtime validation at every external boundary. Reason: TypeScript cannot validate form posts, webhooks, query params, or JSON payloads at runtime.
- Use Playwright for critical flows and Vitest for pure functions. Reason: SaaS regressions usually happen in auth, billing, forms, and DB writes.

## Dev Commands

- `pnpm dev`: run the Next.js dev server.
- `pnpm build`: compile production code and catch route/runtime mistakes.
- `pnpm lint`: run ESLint and formatting checks.
- `pnpm test`: run unit tests.
- `pnpm test:e2e`: run Playwright flows.
- `pnpm db:migrate`: apply pending migrations.
- `pnpm db:studio`: inspect local development data.
- `pnpm db:seed`: seed deterministic local demo data.

If a command is missing, add the script to `package.json` instead of inventing a one-off command. Reason: repeatable commands are part of the developer interface.

## Folder Structure

```text
app/
  (auth)/
  (dashboard)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  domain/
db/
  client.ts
  schema.ts
  migrations/
  queries/
lib/
  auth/
  billing/
  env.ts
  validation/
server/
  actions/
  jobs/
tests/
  unit/
  e2e/
```

- Keep route-specific UI inside `app/` route segments. Reason: local route ownership makes App Router behavior obvious.
- Keep reusable visual primitives in `components/ui/`. Reason: UI primitives should not import business logic.
- Keep business components in `components/domain/`. Reason: domain components can encode product language without polluting primitives.
- Keep all database access under `db/` or `server/`. Reason: this prevents accidental DB imports from Client Components.
- Keep environment parsing in `lib/env.ts`. Reason: central validation gives one failure point for missing secrets.

## Naming Conventions

- Components use `PascalCase.tsx`. Reason: file names match React component names.
- Server actions use `verbNounAction`, such as `createWorkspaceAction`. Reason: actions are imperative mutations and should read that way.
- Query helpers use `get/list/find/count` prefixes. Reason: reads and writes stay visually distinct.
- Mutation helpers use `create/update/delete/archive/restore` prefixes. Reason: destructive code should be obvious in review.
- Database tables use `snake_case` plural nouns. Reason: SQL stays readable and independent from TypeScript naming.
- TypeScript types use `PascalCase`; Zod schemas use the same name plus `Schema`. Reason: `CreateUserInput` and `CreateUserInputSchema` stay paired.

## SQL And Migration Rules

- Every schema change must be represented by a committed migration file. Reason: production deploys need reproducible state changes.
- Never edit a migration after it has been merged. Reason: existing environments may already have applied it.
- Use timestamped migration names like `202606160930_add_workspace_members.sql`. Reason: chronological order is reviewable and conflict-resistant.
- Wrap destructive migrations in explicit comments and a reversible plan. Reason: SQLite migrations often need table rebuilds, and data loss must be intentional.
- Prefer additive migrations: add nullable columns, backfill, then enforce constraints in a later migration. Reason: this reduces downtime and rollback risk.
- Enable foreign keys on every connection with `PRAGMA foreign_keys = ON`. Reason: SQLite does not protect relational integrity unless this is enabled.
- Use transactions for multi-step writes. Reason: SaaS data often spans users, workspaces, roles, and audit rows.
- Store times as ISO-8601 UTC text unless a library requires integer epochs. Reason: text timestamps are readable and sort correctly when normalized.
- Do not build SQL with string concatenation. Reason: parameterized statements are the baseline defense against injection.
- Put read queries in `db/queries/` and writes in server actions or server-only services. Reason: review can quickly separate data reads from mutations.

## Server And Client Boundaries

- Default to Server Components. Reason: less JavaScript ships to the browser and data fetching is simpler.
- Add `"use client"` only for interactive state, browser APIs, or client-only libraries. Reason: accidental Client Components expand bundle size and can leak server-only imports.
- Never import `db/client.ts`, secrets, or filesystem APIs into a Client Component. Reason: it breaks builds or leaks implementation details.
- Mark server-only modules with `import "server-only"`. Reason: Next.js can catch boundary mistakes early.
- Use Server Actions for trusted form mutations and Route Handlers for public APIs/webhooks. Reason: each has a different security and calling model.

## Component Patterns

- Build forms with a shared validation schema used by both the client form and server action. Reason: users get fast feedback while the server remains authoritative.
- Keep loading, empty, and error states next to the route that owns them. Reason: App Router has first-class `loading.tsx` and `error.tsx` conventions.
- Keep UI primitives unopinionated and accessible. Reason: buttons, dialogs, inputs, and menus are reused across product areas.
- Prefer composition over boolean prop explosions. Reason: large prop matrices make product UI hard to reason about.
- Use optimistic UI only when the rollback path is clear. Reason: SaaS data edits must not lie about persisted state.

## Auth, Tenancy, And Authorization

- Treat `user_id` and `workspace_id` as separate concepts. Reason: a user may belong to many workspaces.
- Check authorization in the same server function that performs the data access. Reason: route-level checks are easy to bypass during refactors.
- Include `workspace_id` in tenant-scoped tables. Reason: queries need a reliable tenant boundary.
- Add audit rows for billing, role, and destructive data changes. Reason: SaaS support depends on knowing who changed what and when.

## Patterns To Follow

- Validate inputs with Zod before touching the database. Reason: invalid writes should fail before opening a transaction.
- Return typed result objects from server actions: `{ ok: true, data }` or `{ ok: false, error }`. Reason: callers can handle failures without parsing thrown errors.
- Keep secrets in environment variables validated by `lib/env.ts`. Reason: deploy failures should happen at boot, not mid-request.
- Add tests for every migration that changes constraints or data shape. Reason: SQLite errors often appear only with real inserts.
- Use feature flags for risky product changes. Reason: small SaaS teams need rollback without redeploying.

## What We Do Not Do

- Do not add Prisma by default. Reason: for SQLite-first SaaS, raw SQL or a small query builder keeps migrations explicit and avoids ORM lock-in.
- Do not put database calls in React Client Components. Reason: client bundles cannot safely access server resources.
- Do not use Edge runtime with `better-sqlite3`. Reason: native SQLite drivers require Node.js.
- Do not create generic `utils.ts` dumping grounds. Reason: vague files become unreviewable and hide ownership.
- Do not silently swallow server action errors. Reason: failures need telemetry and user-visible recovery.
- Do not add global state for server data. Reason: App Router, caching, and server data ownership should stay predictable.
- Do not ship unscoped admin routes. Reason: SaaS admin actions are high-risk and require explicit authorization.

## Default Task Behavior For Claude

- Before editing, inspect the route, server action, query, schema, and tests that own the behavior. Reason: App Router behavior is split across files.
- For DB changes, update schema, migration, seed data if needed, and tests in the same change. Reason: partial DB edits are expensive to debug.
- For UI changes, preserve accessibility semantics and keyboard behavior. Reason: SaaS workflows are repeated often and must be reliable.
- For auth or billing changes, state the threat model and failure mode in the PR summary. Reason: reviewers need to focus on risk, not only code style.
- If requirements are ambiguous, choose the smallest reversible change and document assumptions. Reason: SaaS product direction changes quickly.
