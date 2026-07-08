# CLAUDE.md - Next.js 15 App Router + SQLite/Turso SaaS

This file is the operating manual for Claude Code in this repository. Treat these rules as project defaults unless an existing file proves otherwise. When a rule conflicts with current code, preserve working behavior and explain the conflict in your final response.

## 1. Stack & versions

### Required stack

- **Runtime:** Node.js 22 LTS.
- **Package manager:** `pnpm` only.
- **Framework:** Next.js 15 with the App Router in `src/app`.
- **Language:** TypeScript in `strict` mode.
- **UI:** React 19 Server Components by default, Tailwind CSS, shadcn/ui-style primitives in `src/components/ui`.
- **Database:** SQLite schema managed by Drizzle ORM.
  - Local development/test: `better-sqlite3` against `./data/dev.db` and `./data/test.db`.
  - Preview/production: Turso/libSQL via `@libsql/client`.
- **Validation:** Zod at all trust boundaries: forms, route handlers, server actions, webhooks, and environment variables.
- **Auth and billing:** Keep auth, billing, and email providers behind adapters in `src/lib`; never call provider SDKs directly from UI components.

### Rules with rationale

- **Use Server Components unless interactivity requires a Client Component.** Reason: this keeps secrets and database access on the server, reduces shipped JavaScript, and matches App Router performance defaults.
- **Use Server Actions for first-party mutations and Route Handlers for external callers/webhooks.** Reason: actions give typed form/mutation flows inside the app; route handlers provide stable HTTP contracts for integrations.
- **Use Drizzle-generated schema and migrations, not ad hoc SQL scattered through the app.** Reason: SQLite is permissive; one migration source prevents drift between local better-sqlite3 and Turso.
- **Use `pnpm` commands in docs, scripts, and examples.** Reason: one lockfile and one package manager prevents duplicate dependency trees and CI mismatches.

## 2. Commands Claude should know

Run these from the repository root.

```bash
pnpm install          # install dependencies from pnpm-lock.yaml
pnpm dev              # start Next.js locally
pnpm build            # production build; must pass before PRs
pnpm start            # run the built app
pnpm lint             # eslint/next lint rules
pnpm typecheck        # tsc --noEmit
pnpm test             # unit/integration tests
pnpm test:e2e         # Playwright e2e tests when present
pnpm db:generate      # generate Drizzle migration files from schema changes
pnpm db:migrate       # apply migrations to the configured SQLite/libSQL database
pnpm db:studio        # inspect local database with Drizzle Studio
pnpm db:seed          # seed local development data only
```

If a script is missing, add it to `package.json` instead of inventing one-off commands in documentation. Reason: repeatable scripts are easier for humans, CI, and Claude Code to run consistently.

## 3. Environment variables

- Keep `.env.example` complete and safe; never commit `.env`, `.env.local`, database files, or Turso tokens.
- Validate env vars in `src/env.ts` with Zod and import from there only.
- Use these conventional names unless existing code differs:

```bash
DATABASE_URL="file:./data/dev.db"       # local SQLite
TURSO_DATABASE_URL="libsql://..."       # preview/production
TURSO_AUTH_TOKEN="..."                  # preview/production
NEXT_PUBLIC_APP_URL="http://localhost:3000"
AUTH_SECRET="change-me"
```

Reason: central env validation fails fast during boot/build and prevents undefined values from becoming production bugs.

## 4. Folder structure

Use this shape for greenfield work and move new files toward it.

```text
src/
  app/
    (marketing)/
      page.tsx
      pricing/page.tsx
    (auth)/
      sign-in/page.tsx
      sign-up/page.tsx
    (app)/
      dashboard/page.tsx
      settings/page.tsx
    api/
      webhooks/route.ts
    layout.tsx
    globals.css
  components/
    ui/                 # reusable low-level primitives only
    layout/             # nav, shell, footer, sidebar
    forms/              # reusable form components
  db/
    client.ts           # database client factory
    schema.ts           # Drizzle table definitions
    queries/            # read/query helpers grouped by domain
    mutations/          # write helpers grouped by domain
    migrations/         # generated SQL migrations committed to git
    seed.ts
  features/
    accounts/
      actions.ts        # server actions for this feature
      components/
      validators.ts
      permissions.ts
    billing/
    onboarding/
  lib/
    auth.ts
    billing.ts
    email.ts
    dates.ts
    utils.ts
  env.ts
  middleware.ts

tests/
  unit/
  integration/
  e2e/

data/
  .gitkeep             # local db files are ignored
```

### Folder rules with rationale

- **Route files stay thin.** Pages/layouts should compose components and call feature/query functions; they should not contain long business workflows. Reason: thin routes are easier to cache, test, and refactor.
- **Put domain behavior in `src/features/<domain>`.** Reason: SaaS domains such as accounts, billing, and onboarding change independently; feature folders reduce cross-domain coupling.
- **Put generic primitives in `src/components/ui`, never domain-specific UI.** Reason: `ui` should be safe to reuse anywhere; domain assumptions belong in feature components.
- **Keep database access in `src/db/**` or server-only feature actions.** Reason: this prevents accidental client imports and makes transaction boundaries visible.
- **Use route groups `(marketing)`, `(auth)`, and `(app)` for layouts, not URL semantics.** Reason: route groups let us share shells without changing public paths.

## 5. Naming conventions

- Files and folders: `kebab-case` except Next.js required files (`page.tsx`, `layout.tsx`, `route.ts`, `loading.tsx`, `error.tsx`).
- React components: `PascalCase` exports from `kebab-case.tsx` files.
- Server actions: verb-first names such as `createWorkspaceAction`, `updateSubscriptionAction`.
- Query helpers: `getWorkspaceBySlug`, `listInvoicesForAccount`.
- Mutation helpers: `createWorkspace`, `archiveProject`, `upsertCustomerMapping`.
- Database tables: plural `snake_case` names (`users`, `workspaces`, `workspace_members`).
- Database columns: `snake_case`; TypeScript properties may use Drizzle's mapped camelCase when configured.
- Booleans: prefix with `is_`, `has_`, or `can_` in SQL and `is`, `has`, or `can` in TypeScript.
- Timestamps: `created_at`, `updated_at`, `deleted_at`; store ISO strings or integer epoch consistently per existing schema.

Reason: predictable names let Claude Code find related files quickly and reduce accidental duplicate abstractions.

## 6. SQL, schema, and migration conventions

### Schema rules

- Define tables in `src/db/schema.ts` or split by domain and re-export from `schema.ts` once the file grows.
- Every business table must include `id`, `created_at`, and `updated_at` unless it is a pure join table.
- Use text UUID/ULID primary keys for SaaS entities. Do not expose auto-increment integer IDs in URLs.
- Add foreign keys for ownership and membership relationships and enable `PRAGMA foreign_keys = ON` for local SQLite connections.
- Use unique indexes for natural uniqueness: email, workspace slug, provider customer ID, idempotency key.
- Model soft deletes with `deleted_at` only when restore/audit is required; otherwise hard delete inside a transaction.

### Migration rules

- Generate migrations with `pnpm db:generate`; review the SQL before committing.
- Commit every migration file in `src/db/migrations` with the code that depends on it.
- Never edit a migration that has been merged. Create a new migration instead.
- Never use destructive production migrations without an expand-migrate-contract plan:
  1. Add nullable/new column or table.
  2. Backfill data safely.
  3. Deploy code that reads/writes both old and new shape if needed.
  4. Remove old column/table in a later PR after verification.
- Wrap multi-step writes in transactions.
- Make webhook writes idempotent with a unique event/idempotency key table.
- For Turso/libSQL, assume network latency and avoid N+1 query loops in request paths.

### SQLite-specific guidance

- Prefer `TEXT` for IDs, emails, slugs, enum-like values, and ISO timestamps.
- Prefer `INTEGER` for booleans (`0`/`1`), counts, cents, and epoch times.
- Store money as integer minor units (`amount_cents`) plus `currency`; never use floating point.
- Be explicit with `NOT NULL` and defaults. SQLite's permissiveness is not a substitute for constraints.
- Use transactions for create-account/create-workspace flows so partial SaaS setup cannot leak.

Reason: SQLite is excellent for a small SaaS when constraints and migrations are disciplined; these rules keep local, preview, and production databases compatible.

## 7. Data access patterns

Use server-only modules for database access.

```ts
// src/db/queries/workspaces.ts
import "server-only";
import { db } from "@/db/client";
import { workspaces } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function getWorkspaceBySlug(slug: string) {
  return db.query.workspaces.findFirst({
    where: eq(workspaces.slug, slug),
  });
}
```

Rules:

- Return plain objects from query/mutation helpers; do not return React components or `Response` objects from `src/db`.
- Authorize before reading sensitive tenant data. Check workspace membership in the same server action/query path.
- Use `cache()` only for per-request memoization of safe reads. Do not cache user-specific data globally.
- Invalidate paths/tags after mutations using `revalidatePath` or `revalidateTag` in the action layer.

Reason: separating data access, authorization, and UI keeps tenant boundaries auditable.

## 8. Component patterns

### Server Components

- Default to async Server Components for pages that fetch data.
- Fetch data close to the route that needs it, then pass serializable props to child components.
- Use `notFound()` for missing public resources and explicit redirects for auth flows.

### Client Components

Add `"use client"` only for components that need state, effects, browser APIs, or event handlers.

- Keep Client Components small and leaf-level.
- Pass data into Client Components as serializable props.
- Do not import `src/db`, `fs`, provider SDKs, or server-only utilities from Client Components.

### Forms and mutations

- Validate form inputs with Zod on the server even if client-side validation exists.
- Use `useActionState`/server actions for first-party forms.
- Return typed action state: `{ ok: boolean; message?: string; fieldErrors?: Record<string, string[]> }`.
- Use optimistic UI only after the server action is idempotent or safely retryable.

Reason: Server Components protect secrets by default, while small Client Components preserve interactivity without turning the whole app into a client bundle.

## 9. API routes, webhooks, and integrations

- Put external HTTP contracts in `src/app/api/**/route.ts`.
- Verify webhook signatures before parsing or trusting payloads.
- Store raw webhook event IDs in a table with a unique index before applying side effects.
- Return stable JSON errors from APIs: `{ "error": { "code": "...", "message": "..." } }`.
- Never leak stack traces, SQL, tokens, or provider payload secrets in API responses.

Reason: third-party systems retry and attackers call public routes; stable idempotent handlers prevent duplicate billing/auth side effects.

## 10. Security and tenant isolation

- All dashboard reads and writes must be scoped by the current user and workspace/account ID.
- Never trust `workspaceId`, `userId`, role, price, or plan values from the client without server-side verification.
- Use `middleware.ts` only for coarse redirects/session checks; do fine-grained authorization in server functions.
- Treat slugs as public identifiers and IDs as internal identifiers; do not assume either proves access.
- Keep secrets server-only and import provider clients only from server modules.

Reason: most SaaS incidents are authorization bugs, not missing UI checks.

## 11. Testing expectations

- Add unit tests for pure utilities and validators.
- Add integration tests for database queries/mutations using `DATABASE_URL=file:./data/test.db` or an in-memory SQLite database when compatible.
- Add e2e tests for critical SaaS paths: sign up, create workspace, invite member, billing checkout/portal stubs.
- Before marking work complete, run:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

If a command cannot run because dependencies or scripts are missing, state exactly why and what was checked instead. Reason: clear validation prevents false confidence.

## 12. What we do not do, and why

- **Do not add Pages Router files (`pages/**`).** Reason: this project standardizes on App Router layouts, Server Components, and route handlers.
- **Do not put database calls in Client Components.** Reason: it leaks server concerns and can expose credentials or bundle server-only code.
- **Do not create generic catch-all abstractions before two real use cases exist.** Reason: premature abstractions slow small SaaS iteration.
- **Do not bypass migrations with manual production SQL.** Reason: schema drift breaks local reproduction and future deploys.
- **Do not use floating-point numbers for money.** Reason: rounding errors become billing defects.
- **Do not silently swallow errors.** Reason: SaaS support needs actionable logs and users need clear recovery messages.
- **Do not log secrets, auth tokens, cookies, raw webhook signatures, or full payment payloads.** Reason: logs are long-lived and widely accessible.
- **Do not introduce a second ORM/query builder.** Reason: mixed data layers make migrations, transactions, and typing unreliable.
- **Do not make everything a Client Component to fix one hydration issue.** Reason: it hides the real boundary problem and increases JavaScript shipped to users.
- **Do not add dependencies for trivial utilities.** Reason: smaller dependency graphs reduce security, maintenance, and cold-start risk.

## 13. PR checklist for Claude Code

Before opening or updating a PR:

- [ ] The change follows the folder structure or explains why existing structure differs.
- [ ] New env vars are added to `.env.example` and `src/env.ts`.
- [ ] Schema changes include generated migrations.
- [ ] Mutations validate input and authorize server-side.
- [ ] Client Components are justified by interactivity needs.
- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build` pass or failures are documented.
- [ ] The PR summary links the related issue and lists validation performed.

Reason: this checklist mirrors the failure modes most likely to hurt a Next.js + SQLite SaaS in production.

## 14. When uncertain

Make the smallest safe change that preserves the stack above. Prefer explicit code over clever abstractions, ask for clarification only when a decision changes product behavior or data safety, and document assumptions in the final response.
