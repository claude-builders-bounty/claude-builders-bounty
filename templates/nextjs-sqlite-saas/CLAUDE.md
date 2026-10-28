# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the operating contract for a greenfield SaaS product built with Next.js 15 App Router, React 19, TypeScript, and SQLite. Choose either Node-only `better-sqlite3` on one host with persistent local storage or remote Turso/libSQL; do not mix providers within an environment.

The goal is a small production system that is easy to reason about: server-first UI, explicit data access, boring migrations, predictable auth, and no hidden client-side business logic.

This file prescribes the target architecture; it does not establish what a fresh starter already contains. Before working, inspect the actual project tree, `package.json`, any existing lockfile, and configuration. Distinguish existing files, dependencies, and scripts from additions that still need implementation or installation. Copying this file does not configure SQLite, authentication, migrations, tests, or command scripts. Never describe a command as ready to run without checking its script and prerequisites, or claim a build or check passed without executing it.

- Report dependency declarations, resolved versions, installation, and successful execution as separate facts. `package.json` declares requirements; a lockfile records a resolution. Neither proves that packages are installed. A starter created with `--skip-install` has no installed dependencies until an installation is actually verified. When installation has not been checked, say so.
  Reason: a declared tool or package cannot establish that a development command is runnable.

- Before proposing implementation, summarize the observed starter separately from the target architecture, including existing scripts and missing setup. Carry forward the server-only identity boundary: unauthenticated requests are rejected, and protected operations remain unavailable until real authentication is integrated. A submitted user or owner id never establishes identity.
  Reason: an overview should preserve the constraints needed to start safely instead of implying that a fresh scaffold already implements them.

The runtime boundary applies from the start: use Node.js 22, and keep database access, trusted auth helpers, and secret environment values server-only. Native `better-sqlite3` cannot run in the browser or Edge Runtime; database-backed Route Handlers using it must export `runtime = "nodejs"`. Turso/libSQL credentials also stay on the server. Resolve identity through `requireCurrentUser()` and fail closed if real authentication is not configured; never invent a session or trust a submitted owner id.

## Stack And Versions

- Use Next.js 15 App Router with React 19 and TypeScript strict mode; pin `next` to an exact patched 15.x release, never below 15.5.28, and raise the pin when a newer security release is required.
  Reason: App Router gives server components, route handlers, metadata, layouts, and streaming in one model; strict TypeScript catches data-contract drift, while an unbounded `15` range can resolve to a release with known request-handling vulnerabilities.

- Use Node.js 22 as the baseline for projects created from this template; pin the same major in `package.json` `engines`, `.nvmrc`, CI, and deployment.
  Reason: a consistent runtime avoids dependency and native-module drift between development, automation, and production.

- In Next.js 15, await request APIs such as `params`, `searchParams`, `cookies()`, and `headers()`; keep the installed Next.js version and examples aligned.
  Reason: Next.js 15 made request-time APIs asynchronous, and relying on deprecated synchronous compatibility can break as the project upgrades.

- Choose exactly one SQLite provider per environment: `better-sqlite3` for a single Node.js host with persistent local storage, or a server-side Turso/libSQL client for a remote database.
  Reason: local-file and remote-database connection, durability, and deployment assumptions differ; mixing them makes migrations and failure behavior unpredictable.

- When choosing `better-sqlite3` in strict TypeScript, install `@types/better-sqlite3` as a devDependency; omit both local-driver packages on a Turso-only path.
  Reason: `better-sqlite3` does not bundle TypeScript declarations, so a direct import otherwise fails type-checking and the production build.

- Use Drizzle ORM for schema, migrations, and typed queries.
  Reason: Drizzle keeps SQL visible and migration files reviewable; avoid ORMs that hide query shape or create opaque runtime behavior.

- Use Server Actions for trusted writes and Route Handlers only for external integrations or public APIs.
  Reason: Server Actions keep form mutations close to the UI, while Route Handlers are better for webhooks, API clients, and machine-to-machine calls.

- Use Zod at every boundary: forms, search params, route handler bodies, webhook payloads, and environment variables.
  Reason: external input is not typed even when TypeScript compiles.

- Use one UI system, preferably shadcn/ui plus Tailwind CSS.
  Reason: one component vocabulary prevents inconsistent SaaS screens and reduces design drift.

- Use Vitest or Node's built-in `node:test` for pure units, Playwright for user flows, and targeted integration tests for database writes.
  Reason: most regressions in this stack happen at boundaries: forms, auth, database, and redirects.

## Project Structure

Use this structure unless the task explicitly requires a better local pattern:

App Router API files belong inside `app/`: for example, `app/api/webhooks/stripe/route.ts`. The `api/` directory shown below is nested under `app/`, never a repository-root `api/` directory.

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
    settings/
      page.tsx
  api/
    webhooks/
      stripe/
        route.ts
  layout.tsx
  globals.css
middleware.ts
components/
  ui/
  forms/
  layout/
db/
  client.ts
  schema.ts
  migrations/
features/
  auth/
    actions.ts
    queries.ts
    validators.ts
  billing/
    actions.ts
    queries.ts
    validators.ts
  projects/
    actions.ts
    queries.ts
    validators.ts
lib/
  env.ts
  auth.ts
  dates.ts
  ids.ts
  result.ts
tests/
  integration/
  e2e/
```

Rules:

- Keep route files thin. `page.tsx`, `layout.tsx`, and `route.ts` may orchestrate, but business rules live in `features/*`.
  Reason: thin routes make it possible to test product behavior without rendering the whole app.

- Put feature-specific reads in `features/<feature>/queries.ts` and writes in `features/<feature>/actions.ts`.
  Reason: separating reads and writes makes caching, authorization, and transaction boundaries easier to audit.

- Put reusable primitives in `lib/`, not product behavior.
  Reason: `lib/` should stay stable; product rules change with the feature.

- Keep `components/ui` generic and keep product-aware components under `features` or `components/forms`.
  Reason: generic UI should not import database, auth, billing, or feature-specific rules.

- Keep `middleware.ts` limited to request routing, auth redirects, and coarse guards.
  Reason: middleware runs before routes and should not contain product writes, database mutations, or billing logic.

## Naming Conventions

- Files use kebab-case except React components, which export PascalCase functions.
  Reason: kebab-case paths are URL-safe and readable across operating systems.

- Database tables use plural snake_case: `users`, `projects`, `billing_events`.
  Reason: snake_case matches SQL convention and avoids quoted identifiers.

- TypeScript variables use camelCase; database columns use snake_case and are mapped at the query edge if needed.
  Reason: each layer keeps its native convention without leaking into the other.

- Server Actions are named as commands: `createProject`, `archiveProject`, `updateBillingEmail`.
  Reason: command names make writes explicit in reviews.

- Read functions are named as queries: `getProjectById`, `listUserProjects`, `findActiveSubscription`.
  Reason: query names should reveal cardinality and filtering.

- Zod schemas end in `Schema`, inferred types end in `Input`.
  Reason: reviewers can see which type comes from untrusted input.

## Environment Rules

- All environment access goes through `lib/env.ts`.
  Reason: direct `process.env` reads scatter defaults and make deployments fragile.

- Validate env at startup with Zod and fail fast for missing production secrets.
  Reason: a broken deployment should fail before accepting traffic.

- Never default production secrets, webhook secrets, database URLs, or auth keys.
  Reason: silent defaults create real security incidents.

Example:

```ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

## Database And Migration Rules

- Schema changes require a migration file in `db/migrations/`.
  Reason: production data must move through reviewed, repeatable steps.

- Migrations are append-only after they have been merged.
  Reason: rewriting applied migrations breaks other developers and deployments.

- Use explicit `created_at` and `updated_at` columns on mutable business tables.
  Reason: SaaS support, billing, and audits need timelines.

- Use foreign keys and unique indexes for product invariants.
  Reason: application checks can race; database constraints cannot be skipped by another code path.

- Generate and review Drizzle migrations, then apply them once in the release/deployment step before deploying code that depends on them; do not migrate on every app boot or use schema push as the production migration plan.
  Reason: concurrent instances must not race to alter production schema, and reviewed migrations make deploys repeatable and recoverable.

- Use transactions for multi-table writes.
  Reason: partial writes create support tickets and inconsistent billing state.

- Do not use `db.run` or raw SQL inline in React components.
  Reason: database access belongs in query/action modules where auth and transactions can be enforced.

- For Turso/libSQL, design for network latency and avoid chatty query loops.
  Reason: remote SQLite stays more responsive when calls are batched and predictable.

### SQLite Runtime, Storage, And Concurrency

- `better-sqlite3` is a native Node.js driver: keep every import and query on the server, set database-backed Route Handlers to `runtime = "nodejs"`, and never use it in Edge Runtime or client code.
  Reason: native bindings cannot run in Edge or the browser, and bundling server dependencies into client code can expose internals or fail production builds.

- Store a file-backed database outside `public/` and source-controlled paths; ignore it in Git and use a persistent writable volume with tested backups and restores in production.
  Reason: ephemeral deployments can silently erase the system of record, while public or committed database files can disclose user data.

- Enable SQLite foreign-key enforcement on every connection; use WAL only on a supported local persistent filesystem, and configure a bounded busy timeout for short write contention.
  Reason: SQLite settings are connection-scoped, WAL is not a distributed-storage solution, and a bounded wait is safer than hanging requests.

- Design local SQLite writes around one writer at a time: keep transactions short, never hold one open across network calls, and do not scale file-backed writes across hosts or shared network volumes.
  Reason: SQLite serializes writes; extra app instances do not turn a local database file into a multi-writer database service.

- Before selecting `better-sqlite3`, verify the deployment supports its native module, Node.js runtime, persistent writable disk, backup/restore, and expected concurrency; otherwise choose a managed remote SQLite provider.
  Reason: a development database working locally does not prove the production platform can load its native binding or preserve its data.

- For Turso/libSQL, keep the client and credentials server-only, use the provider's remote connection and migration workflow, and do not apply local-file, WAL, or local-volume assumptions.
  Reason: remote SQLite has network, authentication, and replication semantics that differ from an on-disk database.

Migration example (assumes the `users` table was created by an earlier migration; in a new database, create the referenced identity table first and align its key with the configured auth provider):

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(owner_id, slug)
);
```

## Data Access Pattern

- Every query accepts the current actor or a verified account id when authorization matters.
  Reason: authorization must be part of the data access contract, not a caller memory test.

- Return plain objects from query modules.
  Reason: server components, actions, and tests should not depend on ORM-specific result wrappers.

- Use explicit column lists instead of `select *`.
  Reason: adding sensitive columns later should not leak into old API responses.

- Bind all user-controlled SQL values through Drizzle parameters; never interpolate input into SQL strings.
  Reason: parameter binding prevents injection while preserving correct query-plan behavior.

- Convert database `null` into product-level state intentionally.
  Reason: nullable data causes most SaaS edge-case bugs when it is passed through blindly.

## Auth And Authorization

- Authentication proves who the user is; authorization decides what they may do. Implement them as separate helpers.
  Reason: mixing them makes admin and account-boundary bugs easier to introduce.

- Resolve identity through one trusted server-only `requireCurrentUser()` boundary; if no auth provider is configured, fail closed and document the integration point instead of trusting submitted owner ids or inventing insecure auth.
  Reason: a greenfield scaffold must make authorization requirements explicit without pretending an unconfigured session is trustworthy.

- Every organization-scoped query checks membership in the same transaction or query path.
  Reason: dashboard data must not leak across accounts.

- Admin routes require both a valid session and an explicit role or permission check.
  Reason: "logged in" is not the same as "platform operator".

- Webhooks never trust client-submitted ids without verifying provider signatures.
  Reason: billing and provisioning flows are high-impact and easy to spoof.

- Prefer capability checks such as `canManageProject(user, project)` over scattered role comparisons.
  Reason: SaaS permissions become more complex as teams, billing, and invited users are added.

## Server And Client Component Rules

- Default to Server Components.
  Reason: server-first pages reduce JavaScript shipped to users and keep secrets off the client.

- Mark a component with `"use client"` only for local interactivity, browser APIs, controlled inputs, or client-side state.
  Reason: client components expand bundle size and cannot safely access server-only modules.

- Never import `db`, `env`, payment SDKs, or server auth helpers from a client component.
  Reason: these imports either fail at build time or risk exposing implementation details.

- Keep forms progressive: render server data first, submit through a Server Action, and show optimistic UI only after the server path exists.
  Reason: optimistic-only flows hide validation, authorization, and persistence bugs.

## Server Actions

- Server Actions validate input with Zod before touching the database.
  Reason: browser forms and malicious requests can submit anything.

- Server Actions return a typed result object for expected validation failures and throw only for unexpected system errors.
  Reason: predictable failures should produce user-facing messages, not error boundaries.

- Redirect only after the write succeeds.
  Reason: redirecting before commit creates confusing false-success states.

- Revalidate the smallest useful path or tag after writes.
  Reason: broad invalidation hides stale-data bugs and wastes server work.

Example:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireCurrentUser } from "@/lib/auth";
import { createProjectRecord } from "./queries";

const createProjectSchema = z.object({
  name: z.string().min(2).max(80),
});

export async function createProject(formData: FormData) {
  const input = createProjectSchema.safeParse({
    name: formData.get("name"),
  });

  if (!input.success) {
    return { ok: false as const, message: "Enter a project name." };
  }

  const actor = await requireCurrentUser();
  const project = await createProjectRecord({ ...input.data, ownerId: actor.id });
  revalidatePath("/dashboard");
  return { ok: true as const, projectId: project.id };
}
```

## Route Handlers And APIs

- Route Handlers are for webhooks, public API clients, file uploads, and integrations.
  Reason: normal app form writes are clearer as Server Actions.

- Validate method, auth, input, and response shape in every route.
  Reason: API consumers depend on stable contracts.

- Use idempotency keys for billing, provisioning, and webhook handlers.
  Reason: providers retry requests and users double-submit forms.

- Never return internal errors, stack traces, SQL text, or provider secrets.
  Reason: public APIs are a common information-disclosure surface.

## UI And Product Patterns

- Dashboards should show real next actions, not marketing copy.
  Reason: SaaS users return to operate the product, not to reread value propositions.

- Empty states include one primary action.
  Reason: empty SaaS screens are onboarding moments.

- Tables need loading, empty, error, and filtered states.
  Reason: operational tools are used repeatedly and must stay predictable.

- Use cards for repeated entities, dialogs, and framed tools; do not nest cards.
  Reason: nested cards make dashboards visually noisy and harder to scan.

- Keep text and controls compact in app screens.
  Reason: SaaS dashboards should optimize for scanning, comparison, and repeated actions.

## Error Handling

- Expected validation failures return typed results.
  Reason: users need actionable feedback without crashing the route.

- Unexpected failures are logged server-side with a request id.
  Reason: support needs traceability without exposing internals to the client.

- Add a route-level error boundary for app sections that call external providers.
  Reason: billing, email, and AI integrations fail independently from the core app.

## Testing Rules

- Add a test for every bug fix.
  Reason: the bug already proved the old behavior was possible.

- Test authorization boundaries with at least two users or organizations.
  Reason: single-user tests miss account leakage.

- Test database migrations on an empty database and on a seeded database when the migration touches existing data.
  Reason: migrations fail in production when they only work on clean schemas.

- For Server Actions, test invalid input, unauthorized access, and the successful write.
  Reason: those are the three production paths that matter.

- For Playwright flows, cover signup/login, main dashboard action, settings update, and billing handoff once those features exist.
  Reason: these flows determine whether the SaaS can onboard and retain users.

## Commands

Use the following as the target script configuration, not an inventory of a fresh starter. Inspect the actual `package.json` first, preserve suitable existing scripts, and add missing scripts only with their required packages and configuration. In particular, do not assume `check`, tests, or `db:*` scripts exist. The lint example uses the ESLint CLI for the starter's flat configuration.

For each recommended command, state whether its script already exists and whether its packages and configuration are available. For example, an existing `dev` script still needs installed dependencies; `start` also needs a successful production build. Proposed test and database commands need their runner, tests, provider, schema and configuration before use. In read-only work, report those prerequisites instead of installing packages or adding scripts.

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "eslint",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio",
    "check": "npm run typecheck && npm run lint && npm run test && npm run build"
  }
}
```

Rules:

- Once its scripts and dependencies are configured, run `npm run check` before opening a PR; otherwise report the missing setup and the existing checks actually run.
  Reason: type, lint, test, and build failures are cheaper locally than in review.

- Once Drizzle and its generation script are configured, run `npm run db:generate` after editing schema and commit the migration.
  Reason: schema and migrations must stay in sync.

- Do not add a new package manager unless the repo already uses it.
  Reason: mixed lockfiles create nondeterministic installs.

## Pull Request Rules

- PRs include summary, validation commands, migration notes, and screenshots for UI changes.
  Reason: reviewers need evidence, not intent.

- Keep PRs scoped to one product behavior or infrastructure change.
  Reason: small PRs are easier to merge and revert.

- Include rollback notes for migrations and billing changes.
  Reason: production SaaS work must be reversible or at least recoverable.

## What We Do Not Do

- Do not put business logic in React components.
  Reason: product rules need tests and should not depend on rendering.

- Do not use client-side checks as the only authorization layer.
  Reason: users can bypass the browser.

- Do not use `any` to silence type errors.
  Reason: `any` hides exactly the contract problems TypeScript is meant to catch.

- Do not create global mutable state for request-specific data.
  Reason: server runtimes can reuse modules across users.

- Do not expose database ids in logs when a public correlation id is enough.
  Reason: logs often reach third-party systems.

- Do not add background jobs without an idempotency strategy.
  Reason: retries and duplicate delivery are normal in production.

- Do not build custom auth, crypto, billing ledgers, or migration runners unless explicitly required.
  Reason: these domains are expensive to get right and have proven tools.

- Do not optimize for multi-region writes before there is real traffic pressure.
  Reason: SQLite is strongest when the write path stays simple.

- Do not create generic abstractions before two real features need them.
  Reason: premature abstraction slows MVP development and hides product intent.

## Agent Workflow

When changing this project:

1. Identify the user-facing behavior or production risk first.
2. Locate the route, feature module, schema, and tests that own it.
3. Make the smallest coherent change.
4. Add or update validation at the closest boundary.
5. Run the relevant configured test first, then `npm run check` when the change is broad and that script's prerequisites exist; report missing setup instead of claiming unavailable checks ran.
6. In the final response, report files changed, validation run, and any residual risk.

If requirements are ambiguous, choose the safer production behavior and document the assumption in the PR. Do not pause for clarification unless the wrong assumption could cause data loss, payment errors, or a security issue.

## Greenfield Claude Code Smoke Test

Run the reproducible acceptance procedure in `verification/claude-code-greenfield-smoke.md` in a disposable fresh project. The procedure is a manual Claude Code behavior test; the repository's automated contract check only verifies the template's contents and does not execute Claude Code.

The smoke-test prompt asks Claude Code, in read-only Plan mode, to plan a tenant-scoped project create/list flow using the documented conventions. It checks whether Claude Code inspects the fresh starter and avoids inventing package scripts, while making no code or database changes. It must not ask the user to choose stack, folder layout, migration, validation, or server/client patterns already specified here. If the starter has no configured identity provider, it must fail closed and report that integration point rather than inventing or bypassing authentication.

Expected behavior: Claude Code should inspect the starter and this file, explain safe assumptions, propose an append-only Drizzle migration, Zod validation, a server-first page, trusted authorization, focused tests, and commands that actually exist or should be added. It should not ask which stack, folder layout, migration, validation, or component patterns to use, and must not claim to have edited files or run checks. This is context-understanding evidence, not implementation or production validation.

Automated contract check: run `bash templates/nextjs-sqlite-saas/tests/validate-template-contract.sh` from the repository root. This copies the instructions into a temporary fixture and checks required guidance; it is not a substitute for the manual Claude Code acceptance test.
