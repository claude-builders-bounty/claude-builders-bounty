# CLAUDE.md

This file defines how Claude Code should work in this Next.js 15 App
Router SaaS project backed by SQLite. Treat it as project policy. Follow
these rules unless a more local `CLAUDE.md` overrides them.

## Stack And Versions

- Runtime: Node.js 22 LTS.
  Reason: Next.js 15, modern SQLite drivers, and current test tooling all
  work cleanly on this runtime without compatibility shims.
- Package manager: `pnpm`.
  Reason: one lockfile, fast installs, and strict dependency isolation make
  agent changes easier to review.
- Framework: Next.js 15 App Router with React Server Components by default.
  Reason: server-first data access keeps secrets and database handles out of
  client bundles.
- Language: TypeScript in `strict` mode.
  Reason: SaaS code changes often cross billing, auth, and data boundaries;
  type drift should fail before runtime.
- Database: SQLite through `better-sqlite3` for single-node/local deployments
  or Turso/libSQL for hosted edge-read deployments.
  Reason: both keep the data model simple while supporting an upgrade path.
- Styling: Tailwind CSS plus small local components.
  Reason: the product surface should stay consistent without adding a large
  design dependency before the business model is proven.
- Validation: Zod at every server boundary.
  Reason: form actions, route handlers, and webhooks receive untrusted input.
- Testing: Vitest for unit tests, Playwright for critical user flows.
  Reason: unit tests catch business logic regressions; browser tests protect
  signup, checkout, and account workflows.

## Dev Commands

Use these commands unless `package.json` says otherwise:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
```

If a command is missing, add the script before relying on it in docs or CI.
Do not invent commands in final answers.

## Folder Structure

Use this structure for greenfield work:

```text
app/
  (marketing)/
  (auth)/
  (app)/
  api/
components/
  ui/
  forms/
  layouts/
  domain/
db/
  migrations/
  schema.ts
  client.ts
features/
  billing/
  onboarding/
  workspaces/
  users/
lib/
  auth/
  config/
  email/
  errors/
  security/
  validation/
tests/
  unit/
  e2e/
```

Rules:

- Put route segments in `app/`; put reusable product logic in `features/`.
  Reason: App Router folders should describe URL and layout, not become the
  entire application architecture.
- Keep database access in `db/` or a feature repository module.
  Reason: direct SQL scattered through UI code makes migrations risky.
- Keep generic UI in `components/ui` and domain UI in `components/domain`.
  Reason: buttons and dialogs should be reusable; billing tables and workspace
  switchers should keep their business language.
- Keep secrets and environment parsing in `lib/config`.
  Reason: one startup failure is better than late partial failures.

## Naming Conventions

- Files that export React components use `PascalCase.tsx`.
  Reason: imports read like components and are easy to search.
- Feature helpers use `camelCase.ts`.
  Reason: helpers are values/functions, not components.
- Server actions end in `.action.ts`.
  Reason: call sites can distinguish server mutations from pure helpers.
- Database repository files end in `.repo.ts`.
  Reason: SQL ownership is visible during review.
- Zod schemas end in `.schema.ts`.
  Reason: validation code should be discoverable before editing forms or APIs.
- Tests mirror the file under test and end in `.test.ts` or `.spec.ts`.
  Reason: reviewers can infer coverage from filenames.

## SQL And Migration Rules

- Every schema change requires a migration file in `db/migrations`.
  Reason: SQLite is file-backed; untracked schema drift is hard to diagnose.
- Migration filenames use `YYYYMMDDHHMM_description.sql`.
  Reason: lexicographic order should match execution order.
- Prefer additive migrations: add nullable columns, backfill, then make stricter
  constraints in a later migration.
  Reason: SaaS apps need deploys that can roll forward safely.
- Always enable foreign keys when opening a SQLite connection.
  Reason: SQLite does not enforce them unless asked.
- Use transactions for multi-table writes.
  Reason: account, subscription, and workspace updates must not partially save.
- Do not store booleans as strings.
  Reason: SQLite accepts anything; the app must still have a stable contract.
- Store timestamps as ISO-8601 UTC text unless the project already uses integer
  epoch milliseconds.
  Reason: text timestamps are readable in support and migration debugging.
- Never build SQL by string interpolation.
  Reason: prepared statements are simple and remove injection risk.

Example database client boundary:

```ts
// db/client.ts
import Database from "better-sqlite3";

export function openDatabase(path = process.env.DATABASE_URL ?? "data/app.db") {
  const db = new Database(path);
  db.pragma("foreign_keys = ON");
  db.pragma("journal_mode = WAL");
  return db;
}
```

## Component Patterns

- Default to Server Components.
  Reason: they reduce client JavaScript and keep data fetching close to the
  route.
- Add `"use client"` only for state, effects, browser APIs, or event handlers.
  Reason: client components are a cost, not the default.
- Keep form state at the smallest useful boundary.
  Reason: broad client state makes server revalidation harder.
- Use typed props with domain names, not generic bags.
  Reason: `workspaceId` and `planId` are safer than `id` and `data`.
- Put loading, empty, and error states beside the component that owns the data.
  Reason: SaaS users repeat workflows; missing states become support issues.
- Keep cards compact and information-dense in application views.
  Reason: dashboards are work surfaces, not landing pages.

## Server Actions And Route Handlers

- Validate all input with Zod before authorization or database writes.
  Reason: malformed data should fail before it touches business logic.
- Check authorization in the same module that performs the mutation.
  Reason: callers are easy to bypass; mutations must protect themselves.
- Return typed result objects instead of throwing for expected validation errors.
  Reason: forms need predictable error rendering.
- Throw only for unexpected system failures.
  Reason: logs should separate user mistakes from broken infrastructure.
- Revalidate exact paths or tags after writes.
  Reason: broad revalidation hides stale data bugs and wastes work.

Example action shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; fieldErrors?: Record<string, string>; message: string };
```

## Authentication And Authorization

- Model permissions around workspace membership, not only user identity.
  Reason: most SaaS bugs happen after users join multiple teams.
- Keep auth session helpers in `lib/auth`.
  Reason: routes, actions, and background jobs need one source of truth.
- Never trust client-provided role, plan, or workspace data.
  Reason: those fields are authorization facts and must come from the database.
- Add tests for owner/admin/member boundaries when changing permissions.
  Reason: role regressions are high-impact and hard to see visually.

## Billing Rules

- Treat billing provider events as the source of truth for subscription state.
  Reason: UI redirects and client callbacks are not reliable payment evidence.
- Store provider IDs separately from internal IDs.
  Reason: internal records should survive provider migrations.
- Make webhook handlers idempotent.
  Reason: payment providers retry events.
- Do not grant paid access until the verified webhook or trusted server fetch
  confirms payment.
  Reason: checkout success pages can be spoofed or abandoned.

## Error Handling And Logging

- Use typed application errors for expected failures.
  Reason: users need clear messages, operators need clean logs.
- Log server errors with request, user, and workspace context when available.
  Reason: production incidents need correlation.
- Do not log secrets, tokens, cookies, payment payloads, or full request bodies.
  Reason: logs are widely copied during debugging.

## Testing Strategy

- Unit test pure domain logic, validation schemas, permission checks, and SQL
  mapping functions.
  Reason: these change often and are cheap to verify.
- Integration test repository methods against a temporary SQLite database.
  Reason: SQL that type-checks can still be wrong.
- Browser test only the money paths:
  signup, login, workspace creation, checkout, invite, cancellation, and the
  main paid workflow.
  Reason: broad E2E suites become slow and ignored.
- Every bug fix should include a regression test unless the test would be more
  brittle than the bug.
  Reason: bounties and support issues should not repeat.

## Patterns To Follow

- Read existing files before editing.
  Reason: consistency matters more than a preferred style from another project.
- Make small commits with focused intent.
  Reason: SaaS changes often need quick rollback or review.
- Keep shared abstractions boring.
  Reason: the project earns money from product behavior, not clever plumbing.
- Use feature flags for risky paid-plan or onboarding changes.
  Reason: partial rollouts reduce support blast radius.
- Prefer explicit data loading over hidden global state.
  Reason: App Router caching rules are easier to reason about when data sources
  are visible.

## Anti-Patterns To Avoid

- Do not put business logic directly in React components.
  Reason: it becomes untestable and duplicated across routes.
- Do not introduce a second ORM or query layer.
  Reason: SQLite migrations and transactions need one owner.
- Do not use `any` to pass CI.
  Reason: it hides the exact contracts TypeScript is meant to protect.
- Do not add background queues before the product needs them.
  Reason: a cron job or webhook is easier to operate for early SaaS workloads.
- Do not create generic `utils.ts` dumping grounds.
  Reason: generic files hide ownership and grow without review pressure.
- Do not call payment, email, or analytics services from Client Components.
  Reason: secrets and trusted events belong on the server.
- Do not change environment variable names without a migration note.
  Reason: deploys fail silently when dashboards still hold old names.

## Environment Variables

Use a typed config module and fail fast at startup:

```text
DATABASE_URL=
AUTH_SECRET=
NEXT_PUBLIC_APP_URL=
BILLING_WEBHOOK_SECRET=
EMAIL_FROM=
```

Rules:

- `NEXT_PUBLIC_*` variables are public.
  Reason: Next.js exposes them to the browser.
- Server-only secrets stay unprefixed.
  Reason: accidental public exposure is a security incident.
- Document every variable in `.env.example`.
  Reason: setup should not depend on chat history or tribal knowledge.

## Pull Request Checklist

Before opening a PR:

- Run `pnpm lint`.
- Run `pnpm typecheck`.
- Run `pnpm test`.
- Run `pnpm test:e2e` when auth, billing, onboarding, or the main paid workflow
  changed.
- Run `pnpm db:migrate` against a disposable local database when migrations
  changed.
- Update `.env.example` when config changes.
- Add or update screenshots for visible UI changes.
- Mention any command that could not be run and why.

## How Claude Should Work Here

- Start by identifying the route, feature, and database tables involved.
- State assumptions only when they affect implementation.
- Prefer editing existing modules over creating parallel systems.
- Keep final answers short: changed files, verification, and remaining risk.
- If a task touches legal, payment, personal data, or account permissions, pause
  before taking irreversible external action.
