# CLAUDE.md

Use this file as the standing context for a production Next.js 15 SaaS app that stores application data in SQLite during local development and Turso/libSQL in hosted environments.

## Stack And Versions

- Runtime: Node.js 22 LTS. Reason: it is the current stable baseline for Next.js 15 and avoids edge-only surprises.
- Framework: Next.js 15 App Router with React Server Components by default. Reason: data loading should happen close to the route that renders it.
- Language: TypeScript with `strict: true`. Reason: SaaS code carries billing, auth, and tenant boundaries, so implicit `any` is a bug source.
- Database: SQLite locally, Turso/libSQL remotely through `@libsql/client`. Use `better-sqlite3` only for scripts and one-process local tooling. Reason: the app should run the same SQL in local and hosted environments.
- Styling: Tailwind CSS with small reusable components. Reason: it keeps product UI consistent without inventing a design system too early.
- Validation: Zod at all input boundaries. Reason: `FormData`, URL params, webhook payloads, and AI-generated edits are not trusted types.
- Tests: Vitest for unit tests and Playwright for browser flows that cross auth, billing, or persistence. Reason: database-heavy apps need cheap logic tests and a few real workflow tests.

## Dev Commands

Prefer these commands unless the repository defines different scripts in `package.json`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:studio
```

If a command is missing, add the script instead of silently using another package manager. Reason: one command surface keeps local, CI, and Claude Code runs reproducible.

## Project Structure

```text
src/
  app/
    (marketing)/
    (app)/
      dashboard/
      settings/
    api/
      webhooks/
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    schema.ts
    migrations/
  features/
    accounts/
    billing/
    projects/
  lib/
    auth.ts
    env.ts
    errors.ts
    ids.ts
  server/
    actions/
    queries/
  tests/
```

- Route files under `src/app` only orchestrate rendering, redirects, and metadata. Reason: route files become unreadable when they also hold business rules.
- Feature modules own product behavior under `src/features/<feature>`. Reason: accounts, billing, and projects change at different speeds.
- Database reads live in `src/server/queries`; mutations live in server actions or route handlers. Reason: separating reads from writes makes caching and authorization review easier.
- Shared presentational components go in `src/components`; feature-specific components stay inside the feature folder. Reason: not every card or table deserves to become global API surface.
- Environment parsing belongs in `src/lib/env.ts` and exports typed values. Reason: scattered `process.env` reads hide deploy-time failures.

## Naming Conventions

- Use kebab-case for route segments and file names that are not React components: `billing-plans`, `account-menu.tsx`.
- Use PascalCase for React components and types exported from component files: `AccountMenu`, `BillingPlan`.
- Use camelCase for functions, variables, database columns in TypeScript, and Zod schemas: `createProject`, `projectId`.
- Use snake_case for SQL table and column names: `project_members`, `created_at`. Reason: SQL stays readable in migrations and database tools.
- Name server actions with verbs: `createProjectAction`, `updateBillingEmailAction`. Reason: mutations should announce their side effects.
- Name query functions by returned data, not transport: `getProjectForDashboard`, not `fetchProject`. Reason: server-side SQLite queries are not browser fetches.

## Database Rules

- Every schema change must be represented by a numbered SQL migration in `src/db/migrations`. Do not use `db push` as the only record. Reason: Turso and production SQLite need a replayable history.
- Migrations are append-only after merge. If a mistake ships, create a new migration. Reason: rewriting applied SQLite migrations causes drift that is hard to detect.
- Use explicit primary keys, usually text ids generated in application code. Reason: stable ids travel cleanly through URLs, logs, webhooks, and test fixtures.
- Store timestamps as ISO-8601 UTC text named `created_at` and `updated_at`. Reason: SQLite has flexible typing, so consistency must be a project rule.
- Add indexes in the same migration that introduces a new tenant, lookup, or foreign-key access pattern. Reason: SQLite can look fast locally and still degrade under real tenant data.
- Every multi-tenant table includes `account_id` or an equivalent owner key. Reason: authorization should be expressible in every query.
- Never build SQL by string concatenation. Use placeholders from `@libsql/client` or `better-sqlite3`. Reason: user input reaches filters, search, webhooks, and admin tools.
- Wrap related writes in transactions. Reason: SaaS mutations often touch audit rows, membership rows, usage rows, and the primary entity together.

## Data Access Pattern

```ts
// src/server/queries/projects.ts
export async function getProjectForDashboard(projectId: string, accountId: string) {
  return db.execute({
    sql: `
      select id, name, created_at
      from projects
      where id = ? and account_id = ?
      limit 1
    `,
    args: [projectId, accountId],
  });
}
```

- Always include the tenant or owner condition in the query, not only in the caller. Reason: a reused helper should not accidentally become an authorization bypass.
- Return plain data objects from query modules. Reason: React Server Components serialize data; custom classes and driver result objects leak implementation details.
- Keep caching opt-in. Reason: account, billing, and project state can become stale in ways users notice immediately.

## Component Patterns

- Default to Server Components for pages and data display. Add `"use client"` only for state, browser APIs, focus management, or event handlers. Reason: most SaaS screens are read-heavy.
- Keep forms as small Client Components that receive typed defaults and call server actions. Reason: validation stays server-owned while the browser handles interaction.
- Use semantic HTML before custom widgets. Reason: keyboard behavior and accessibility should not be rebuilt for basic controls.
- Put loading states beside the route segment that suspends. Reason: App Router loading UI is easiest to reason about when scoped to the data boundary.
- Use optimistic UI only for reversible, low-risk changes. Reason: billing, permissions, and destructive actions must show confirmed state.

## Server Actions And APIs

- Parse every server action input with Zod before using it. Reason: `FormData` values are strings or files, not trusted domain types.
- Check authorization inside the action or route handler, even if the UI already hides the button. Reason: hidden buttons are not security.
- Return typed result objects such as `{ ok: true }` or `{ ok: false, fieldErrors }`. Reason: predictable action results make forms simple and testable.
- Use route handlers for webhooks and third-party callbacks. Reason: these flows need raw headers, signature checks, and clear HTTP status codes.
- Log webhook ids and external event ids. Reason: providers retry, and idempotency is the difference between one invoice and two.

## Error Handling

- Throw typed application errors from server modules and translate them at the route or action boundary. Reason: low-level code should not decide UI copy.
- Never expose raw database, provider, or stack errors to users. Reason: errors often contain table names, secrets, or implementation details.
- Include enough context in server logs to debug without logging tokens, cookies, passwords, private keys, or full webhook payloads. Reason: logs are production data.

## Testing Expectations

- Add unit tests for schema helpers, id generation, validation, and authorization predicates.
- Add integration tests for important SQLite queries using a temporary database.
- Add Playwright tests for signup, login, create project, invite member, billing settings, and destructive confirmation flows when those features exist.
- Every migration should be exercised against an empty database in CI. Reason: a SaaS app that cannot migrate cannot deploy.

## What We Do Not Do

- Do not put business logic directly in React components. Reason: it becomes impossible to test without rendering UI.
- Do not use global mutable singletons for per-request user, account, or transaction state. Reason: concurrent requests can leak context.
- Do not make client components fetch privileged data from ad hoc API routes. Reason: it duplicates authorization and caching rules.
- Do not skip foreign keys because SQLite is "small". Reason: SaaS data is relational even when the database is lightweight.
- Do not add an ORM unless the project already uses one. Reason: handwritten SQL is clearer for a focused SQLite app and keeps migrations explicit.
- Do not create generic `utils.ts` dumping grounds. Reason: unclear ownership makes future edits slower and riskier.
- Do not introduce background jobs without an idempotency key and retry plan. Reason: billing, email, and webhook work fails in real deployments.

## Claude Code Working Rules

- Before editing, inspect `package.json`, existing migrations, and the nearest feature folder. Follow the local pattern if it is already coherent.
- Make the smallest change that fully solves the requested behavior. Reason: SaaS apps have many cross-cutting surfaces.
- When changing persistence, update schema, migration, query code, validation, and tests in the same change.
- When adding UI, handle empty, loading, error, and permission-denied states.
- When a requirement is ambiguous, choose the safer production behavior: validate more, reveal less, and require explicit confirmation for destructive work.
