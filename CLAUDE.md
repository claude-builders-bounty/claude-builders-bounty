# CLAUDE.md — Next.js 15 + SQLite SaaS

These are project rules, not suggestions. Follow them unless the user explicitly asks for a trade-off. If a request conflicts with security, data integrity, or an existing convention, explain the conflict before changing code.

## 1. Stack and defaults

- **Next.js 15 App Router**, **React 19**, **TypeScript** in strict mode, and **Node.js 20.9+**.
- Use the App Router under `src/app/`. Use **npm** and commit `package-lock.json`; do not switch package managers without being asked.
- Use **Tailwind CSS** for styling and **shadcn/ui** for accessible primitives when a component is needed. Do not add a UI library for one small component.
- Use **Zod** to validate form input, route parameters, environment variables, and data crossing a trust boundary.
- Use **Vitest** for unit/integration tests and **Playwright** for critical browser flows when browser testing is configured.
- Default database for a persistent Node.js deployment: **SQLite via `better-sqlite3`**.
- For serverless or horizontally scaled deployments, use **Turso/libSQL instead**. Do not use `better-sqlite3` on an ephemeral filesystem and assume data will persist.
- Pick one database adapter per deployment. Keep database-specific calls behind `src/lib/db/`; do not mix `better-sqlite3` and Turso APIs throughout feature code.
- Do not add an ORM by default. Use explicit SQL and small typed repository functions. Add an ORM only when the user explicitly requests one or the project already uses one.

When the repository already has a working stack, inspect `package.json`, lockfile, and existing patterns first. Preserve compatible choices; do not perform a dependency migration just to match this template.

## 2. Commands

Use the scripts actually defined in `package.json`. For a fresh npm project, keep the following script names and wire them to the chosen tools:

```bash
npm install
npm run dev
npm run build
npm run start
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:status
```

Expected script behavior:
- `dev`: run Next.js locally.
- `build` / `start`: production build and server.
- `lint`: run ESLint.
- `typecheck`: run `tsc --noEmit`.
- `test`: run Vitest.
- `db:migrate`: apply pending committed migrations in order.
- `db:status`: show applied and pending migrations without changing the database.

If a script or tool does not exist yet, do not pretend it passed. Add the minimal configuration needed when asked to set up the project, or report the missing script clearly. Before finishing a code task, run the narrowest relevant test, then `npm run typecheck` and `npm run lint` when available. Run `npm run build` for changes that affect routing, server/client boundaries, configuration, or production compilation.

## 3. Project structure

Prefer feature-oriented code for product behavior and a small shared `lib` for infrastructure:

```text
src/
  app/
    (marketing)/
      page.tsx
    (app)/
      layout.tsx
      dashboard/
        page.tsx
    api/
      health/
        route.ts
    layout.tsx
    globals.css
  components/
    ui/                 # shadcn/ui primitives; keep generated primitives here
    shared/             # truly cross-feature components only
  features/
    billing/
      actions.ts        # server actions for this feature
      components/
      schemas.ts        # Zod input/output schemas
      service.ts        # use cases and business rules
      repository.ts     # feature data access
      types.ts
    projects/
      actions.ts
      components/
      schemas.ts
      service.ts
      repository.ts
      types.ts
  lib/
    auth/               # authentication and authorization helpers
    db/
      client.ts         # one adapter entry point
      migrations/
        0001_initial.sql
      migrate.ts
      repositories/     # shared repositories only when genuinely shared
    env.ts
    errors.ts
    logger.ts
    utils.ts
  test/
    setup.ts
    factories/
    integration/
```

Rules:
- `app/` owns routing, layouts, loading/error boundaries, and route handlers; it does not own business logic.
- `features/<feature>/` owns behavior specific to that feature. Keep a feature's schema, service, repository, actions, and UI close together.
- `components/ui/` contains low-level reusable primitives, not product-specific workflows.
- `lib/` is for infrastructure and genuinely cross-feature utilities. Do not turn it into a dumping ground.
- Keep `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, and `route.ts` as Next.js entry points; delegate complex logic to named modules.
- Do not create every possible folder up front. Add a folder when it has a real file to contain.

## 4. Naming and TypeScript

- React components and component files: `PascalCase` (for example, `ProjectCard.tsx`).
- Non-component TypeScript files: `kebab-case` or the existing repository convention; choose one convention and keep it consistent.
- Functions and variables: `camelCase`; types, interfaces, and Zod schemas: `PascalCase` (`CreateProjectInput`, `createProjectSchema`).
- Database tables and columns: `snake_case`, plural table names (`projects`, `created_at`).
- Environment variables: `UPPER_SNAKE_CASE`. Parse and validate them once in `src/lib/env.ts`; avoid scattered `process.env` access.
- Prefer `type` for data shapes and unions. Use `interface` when declaration merging or an established project convention makes it useful.
- Avoid `any`. Use `unknown` at trust boundaries and narrow it with validation.
- Do not add `// @ts-ignore`, broad lint disables, or unsafe casts to make errors disappear. Fix the underlying type or explain the narrow exception.
- Use named exports for reusable modules. Use a default export only where Next.js requires one or the existing codebase consistently expects it.

## 5. Architecture and request flow

Follow this direction:

`Page / Route Handler / Server Action → feature service → repository → database adapter`

- **Server Components are the default.** They can fetch data directly through services/repositories without an internal HTTP request to the app's own API.
- Add `"use client"` only for browser APIs, local interactive state, effects, or event handlers. Keep the client boundary as low in the tree as practical.
- Do not call `fetch("/api/...")` from a Server Component to reach your own app. Call the service directly; this avoids an unnecessary network hop and duplicate validation.
- Route Handlers are for HTTP interfaces, webhooks, health endpoints, and external clients—not as mandatory wrappers around every query.
- Server Actions are mutation entry points, not a replacement for a service layer. Validate inputs, authenticate, authorize, call a service, and return a small serializable result.
- A service contains business rules and use-case orchestration. A repository contains SQL and persistence mapping. Components must not contain SQL.
- Use `import "server-only"` in modules that must never enter a client bundle, especially database and secret-bearing modules.
- Return plain serializable values across Server/Client Component boundaries. Never pass database handles, prepared statements, or server-only objects to client components.
- Keep errors actionable and safe: log useful server-side context, but do not expose SQL, secrets, stack traces, or internal infrastructure details to users.

## 6. Components, forms, and UI

- Prefer small components with one clear responsibility. Extract a component when it has a meaningful name, reuse, or independent behavior—not merely to reduce line count.
- Keep server-rendered UI on the server. Add client-side state only when the interaction needs it.
- Use semantic HTML, keyboard-accessible controls, visible focus states, and accessible names. Prefer shadcn/ui primitives for complex accessible interactions.
- Use a `<form>` with a Server Action for ordinary mutations when appropriate. Validate on the server even if the browser also validates.
- Show explicit pending, success, empty, and error states for user-facing asynchronous actions.
- Do not use `useEffect` to copy props into state, derive values that can be computed during render, or fetch data that belongs in a Server Component.
- Do not put secrets, authorization decisions, or trusted user identity in client state. Client UI can improve usability but is never an authorization boundary.
- Use `revalidatePath` or `revalidateTag` deliberately after mutations. Do not blanket-disable caching without understanding the data freshness requirement.

## 7. SQLite, SQL, and migrations

### Database safety

- All database access goes through `src/lib/db/` and typed repository functions. Never open a second ad hoc connection inside a feature.
- Use prepared statements / parameterized queries for all values. **Never interpolate user-controlled values into SQL strings.**
- SQL identifiers such as table or column names cannot generally be bound as parameters. For dynamic identifiers, use a fixed allowlist.
- Use explicit column lists in `SELECT`, `INSERT`, and `UPDATE`; avoid `SELECT *` so schema changes do not silently alter application behavior.
- Add `NOT NULL`, `UNIQUE`, `CHECK`, and foreign-key constraints where they express real invariants. Enable SQLite foreign-key enforcement for every connection.
- Store timestamps in a documented, consistent UTC representation (ISO-8601 UTC text is the default). Do not mix local time, Unix seconds, and milliseconds in the same column.
- Store money as integer minor units (for example, cents) plus an explicit currency code; do not use floating-point values for monetary amounts.
- Use transactions for multi-step writes that must succeed or fail together. Keep transactions short; do not perform network calls inside a transaction.
- Create indexes for real query patterns and foreign-key access. Verify index choices against queries instead of adding indexes to every column.
- For `better-sqlite3`, use its synchronous API only in server-only code and keep operations short. Do not assume a single SQLite file is a safe shared write store across multiple serverless instances.
- For Turso/libSQL, use its supported client and deployment configuration. Do not copy `better-sqlite3` connection code into the Turso adapter.

### Migration policy

- Every schema change is a new, numbered SQL migration under `src/lib/db/migrations/`, for example `0002_add_project_slug.sql`.
- Migration files are immutable once applied or merged. Never edit an old migration to change a deployed schema; add a new migration instead.
- Migrations run in ascending order and are recorded in a migration ledger table with a unique migration identifier and application timestamp.
- The migration runner must be idempotent with respect to already-recorded migrations, stop on the first failure, and report which migration failed. Do not silently skip failed migrations.
- Apply each migration transactionally when the statements and chosen SQLite/Turso environment support it. If a migration cannot be transactional, document the reason and make it safely resumable.
- Prefer additive, backward-compatible changes: add a nullable column or a column with a safe default, deploy compatible code, backfill, then enforce constraints or remove old fields in a later release.
- Do not rename or drop a column in the same release that first stops using it if old application instances may still run.
- Never run destructive migrations automatically on application startup in production. Run migrations as an explicit deployment step with a single migration runner.
- Before a destructive migration, require a verified backup and a rollback/recovery plan. SQLite schema changes may require rebuilding a table; inspect foreign keys, indexes, triggers, and data before doing so.
- Keep development/test databases separate from production. Tests must not point at production credentials or production database files.
- Commit migration SQL and migration-runner changes together with the application code that depends on the new schema.
- A fresh database must be buildable from the full migration history. Test both a fresh install and an upgrade from the previous schema when practical.

## 8. Authentication, authorization, and security

- Authentication answers **who is the user**; authorization answers **what may this user do**. Perform both checks on the server for every protected read or mutation.
- Never trust a user ID, role, tenant ID, price, or permission supplied by the client. Derive identity from the authenticated session and scope database queries to that identity/tenant.
- Validate every Server Action and Route Handler input with a Zod schema. Treat URL params, headers, cookies, webhook bodies, and database content as untrusted until validated.
- Keep secrets in environment variables and out of source control, client components, logs, and error messages. Provide `.env.example` with names and safe placeholders only.
- Use constant-time or library-provided verification for credentials/tokens; do not invent authentication or cryptography primitives.
- Verify webhook signatures before processing events and make webhook handlers idempotent.
- Use least privilege for database credentials and external service tokens. Do not add a dependency or external service without a clear need.
- Never run destructive shell commands, migrations against production, or data deletion without explicit confirmation from the user.

## 9. Validation, errors, and observability

- Parse environment variables at startup and fail fast with a clear message when required configuration is missing.
- Validate input at the boundary once, then pass typed data into services. Do not scatter slightly different validation rules through UI, actions, and repositories.
- Use domain errors for expected failures (for example, not found, conflict, forbidden) and map them to safe UI or HTTP responses at the boundary.
- Do not catch an error only to ignore it. Add context, handle it meaningfully, or let it reach the established error boundary.
- Log unexpected server errors with a request/correlation ID when available. Never log passwords, access tokens, session cookies, or full sensitive payloads.
- Make health checks lightweight; do not expose environment variables, database contents, or internal diagnostics from public endpoints.

## 10. Testing expectations

- Unit-test business rules in services without requiring a browser.
- Integration-test repositories against a temporary test database created from the real migration history. Do not mock SQL for tests intended to verify SQL behavior.
- Test authorization failures as well as successful requests: unauthenticated, wrong tenant/user, invalid input, missing records, and duplicate/conflict cases.
- Test migration behavior: fresh database, migration ledger, repeated run, and failure handling.
- Add Playwright coverage for high-value user journeys when the project has Playwright configured.
- Tests must be deterministic and must not depend on production services or real user data.
- When fixing a bug, add a regression test that would have failed before the fix.
- Report exactly which commands ran and whether they passed. Never claim tests, lint, typecheck, or build passed unless they were actually executed.

## 11. Anti-patterns we avoid (and why)

- **No database access in React components or Server Actions directly.** It couples UI to storage and makes business rules hard to test; call a service.
- **No giant `page.tsx`, `route.ts`, or `actions.ts` files.** Entry points should wire dependencies and handle transport concerns, not become the whole application.
- **No `any`, blanket lint suppression, or ignored type errors.** These hide defects instead of resolving them.
- **No string-concatenated SQL with untrusted values.** It creates SQL-injection risk.
- **No hand-edited production schema or untracked migration.** Environments drift and fresh installs break.
- **No automatic production migration on every app instance boot.** Concurrent instances can race and failures can take the app down.
- **No `SELECT *` or implicit column ordering.** Schema changes can unexpectedly break mapping and data exposure assumptions.
- **No secrets or privileged logic in client components.** Client code is visible and controllable by the user.
- **No internal API fetches from Server Components.** Direct service calls are simpler and avoid unnecessary network hops.
- **No premature abstractions, generic repository frameworks, or speculative folder trees.** Keep the codebase understandable until a real use case justifies abstraction.
- **No dependency for a trivial helper.** Each dependency adds maintenance, supply-chain, and upgrade cost.
- **No broad `force-dynamic` or cache disabling by default.** It can throw away performance; choose caching behavior based on data freshness and authorization.
- **No floating-point money, ambiguous timestamps, or missing foreign-key constraints.** These create subtle data-integrity bugs.
- **No “success” response after swallowing an error.** Callers must be able to distinguish success from failure.

## 12. How Claude should work

1. Inspect the relevant files, `package.json`, lockfile, environment example, migrations, and tests before editing. Preserve established patterns unless they are unsafe or inconsistent.
2. For a non-trivial task, state a short plan and identify any schema, security, or compatibility implications before changing files.
3. Make the smallest complete change. Do not rewrite unrelated code, upgrade packages, or reformat the repository unnecessarily.
4. If requirements are ambiguous, choose the defaults in this file when safe. Ask a question only when a decision changes product behavior, risks data loss, affects security, or cannot be inferred responsibly.
5. For database changes, add a migration and update repositories, validation, tests, and any affected UI in the same change.
6. Run relevant tests, typecheck, lint, and build when available. If a command cannot run, say why; do not invent a passing result.
7. Review the diff for leaked secrets, unsafe SQL, missing authorization, accidental generated files, and unrelated changes.
8. Summarize what changed, key design decisions, tests actually run, and any remaining risks.

## 13. Greenfield defaults

If starting from an empty repository and no product requirements are supplied:

- Use `src/`, TypeScript strict mode, npm, App Router, Tailwind CSS, and ESLint.
- Choose `better-sqlite3` for a persistent Node.js server; choose Turso/libSQL when deployment is serverless or needs a remotely hosted database.
- Use explicit SQL migrations and small typed repositories; do not add an ORM.
- Use Server Components by default and Server Actions for ordinary form mutations.
- Include `.env.example`, a README with setup commands, a migration runner, and tests for core service and repository behavior.
- Do not invent a product domain, authentication provider, billing provider, or cloud vendor. Build the smallest coherent foundation and ask only if one of those choices is necessary to implement the requested feature.

## 14. Concrete implementation recipes

These examples establish the expected shape of new code. Adapt names to the feature, but preserve the validation, authorization, and parameterization rules.

### Add a migration

Create a new file such as `src/lib/db/migrations/0002_create_projects.sql`:

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY NOT NULL,
  owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 120),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX projects_owner_id_idx ON projects(owner_id);
```

Why: constraints protect data even when a write bypasses a form, and the owner index supports the common per-user listing query. Use `ON DELETE CASCADE` only when deleting the parent should truly delete its children.

### Query through a repository

```ts
// src/features/projects/repository.ts
import "server-only";
import { db } from "@/lib/db/client";

export type Project = {
  id: string;
  owner_id: string;
  name: string;
  created_at: string;
};

export function listProjectsForOwner(ownerId: string): Project[] {
  return db
    .prepare(
      `SELECT id, owner_id, name, created_at
       FROM projects
       WHERE owner_id = ?
       ORDER BY created_at DESC, id DESC`,
    )
    .all(ownerId) as Project[];
}
```

Why: the owner filter is part of the query, not an optional UI filter; the selected columns and deterministic ordering make the result contract explicit. Keep the type aligned with the actual schema and adapter return types—do not use a cast to hide a mismatch.

### Validate a mutation at the boundary

```ts
// src/features/projects/schemas.ts
import { z } from "zod";

export const createProjectSchema = z.object({
  name: z.string().trim().min(1).max(120),
});

export type CreateProjectInput = z.infer<typeof createProjectSchema>;
```

```ts
// src/features/projects/actions.ts
"use server";

import { createProjectSchema } from "./schemas";
import { createProject } from "./service";
import { requireUser } from "@/lib/auth/require-user";

export async function createProjectAction(formData: FormData) {
  const user = await requireUser();
  const parsed = createProjectSchema.safeParse({
    name: formData.get("name"),
  });

  if (!parsed.success) {
    return { ok: false as const, error: "Check the project name." };
  }

  await createProject({ ownerId: user.id, name: parsed.data.name });
  return { ok: true as const };
}
```

Why: the action is an untrusted entry point. Authentication happens before the write, input is parsed on the server, and the owner ID comes from the authenticated session—not from `FormData`. The `requireUser` and `createProject` functions are examples of expected project modules; create them following the existing auth and service conventions rather than copying unresolved imports blindly.

### Review checklist for every database change

- [ ] New schema change is a new numbered migration; no applied migration was edited.
- [ ] SQL values are bound parameters, not concatenated into the query.
- [ ] Authorization and tenant/owner scoping happen on the server.
- [ ] Foreign keys, uniqueness, nullability, and checks express the intended invariants.
- [ ] Indexes support the actual filtering, joining, and ordering patterns.
- [ ] Repository tests use a disposable database created from the committed migrations.
- [ ] A fresh database and an upgrade path both work.
- [ ] Rollback/recovery implications are documented for destructive changes.

## 15. First-session smoke test

After adding this file to a fresh project, ask Claude Code:

> Read `CLAUDE.md` and inspect the repository. Do not edit files yet. Tell me the stack defaults, proposed feature folder structure, how a schema change must be migrated, which checks you would run before finishing, and three anti-patterns you will avoid. Then propose the smallest implementation plan for adding a `projects` table with owner-scoped listing and creation. Use the defaults in `CLAUDE.md`; do not ask me to choose an ORM, package manager, auth provider, or database adapter unless the repository or deployment requirements make that choice necessary.

Pass criteria:

- Claude identifies the project as Next.js 15 App Router + TypeScript + SQLite and notes the `better-sqlite3` versus Turso deployment distinction.
- It puts SQL in a repository, business rules in a service, and routing/UI in `app/` or feature components.
- It proposes a new numbered migration and never edits an applied migration.
- It validates input on the server and derives the owner ID from the authenticated session.
- It reports only commands actually available in `package.json` and does not claim unrun tests passed.
- It proceeds using stated defaults instead of asking unnecessary setup questions.

Record the actual result honestly in the PR description. This checklist is a test protocol, not evidence that Claude Code was run; do not claim the smoke test passed until you run it in a real Claude Code session.
