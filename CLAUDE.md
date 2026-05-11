# CLAUDE.md — Next.js 15 + SQLite SaaS

This file defines the default engineering rules for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted edge-friendly deployments.

Follow these rules unless the user explicitly overrides them. When a rule conflicts with existing code, preserve the existing behavior first, then propose the smallest safe migration.

## Stack & Versions

- Runtime: Node.js 22 LTS or newer.
- Framework: Next.js 15 with the App Router only.
- Language: TypeScript in `strict` mode.
- UI: React Server Components by default; Client Components only for browser state, effects, event handlers, or browser APIs.
- Database: SQLite via `better-sqlite3` for local/single-server apps, or Turso/libSQL when remote replication is required.
- Styling: Tailwind CSS plus small colocated components. Do not introduce a large component framework unless requested.
- Validation: Zod at every untrusted boundary: forms, route handlers, webhooks, environment variables, and imported CSV/JSON.
- Auth: use a maintained auth library or a small server-side session table. Never roll custom password crypto.
- Tests: use Vitest for unit tests and Playwright for critical user flows.

Reason: this stack optimizes for fast iteration, simple deploys, low operational cost, and code Claude can reason about without chasing framework magic.

## Dev Commands

Assume these scripts exist or add them when setting up the project:

```bash
npm run dev          # start local Next.js dev server
npm run build        # production build and type validation
npm run start        # run production build locally
npm run lint         # lint source files
npm run typecheck    # tsc --noEmit
npm run test         # unit tests
npm run test:e2e     # Playwright tests
npm run db:migrate   # apply pending SQL migrations
npm run db:studio    # optional local DB browser/studio
```

Before claiming work is done, run the narrowest relevant command. For code changes, prefer `npm run typecheck` plus the affected tests. For schema changes, also run `npm run db:migrate` against a disposable local database.

## Project Structure

Use this structure unless the existing repository already has a clear convention:

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
  api/
    health/route.ts
  layout.tsx
  globals.css
components/
  ui/                 # small reusable primitives
  forms/              # form-specific components
  charts/             # visualization-only components
features/
  billing/
    actions.ts        # server actions for this feature
    queries.ts        # read-only database access
    schema.ts         # zod schemas and domain types
    service.ts        # business logic
    components/
lib/
  auth/
  db/
    client.ts
    migrations.ts
    queries.ts
  env.ts
  logger.ts
  utils.ts
migrations/
  0001_initial.sql
  0002_add_customers.sql
public/
tests/
  unit/
  e2e/
```

Reason: `app/` stays focused on routing, `features/` keeps business logic discoverable, and `lib/` holds cross-cutting infrastructure. Avoid dumping everything into `components/` or `utils.ts`; that turns future changes into archaeology.

## Naming Conventions

- Files and folders: kebab-case, except route files required by Next.js (`page.tsx`, `layout.tsx`, `route.ts`).
- React components: PascalCase exports from kebab-case files.
- Server actions: verb-first names, e.g. `createInvoice`, `updateWorkspaceName`.
- Database tables: snake_case plural nouns, e.g. `users`, `workspaces`, `audit_events`.
- Database columns: snake_case, e.g. `created_at`, `stripe_customer_id`.
- TypeScript variables and functions: camelCase.
- Environment variables: SCREAMING_SNAKE_CASE.

Reason: matching SQL conventions in SQL and TypeScript conventions in TypeScript removes translation confusion and keeps generated types predictable.

## Environment Variables

Create `lib/env.ts` and validate all environment variables with Zod. Import configuration from `lib/env.ts`; do not read `process.env` throughout the codebase.

```ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  SESSION_SECRET: z.string().min(32),
});

export const env = envSchema.parse(process.env);
```

Reason: failing fast at boot is cheaper than discovering a missing secret during checkout, login, or a customer demo.

## SQLite & Migration Rules

- Migrations are append-only SQL files in `migrations/`.
- Name migrations with zero-padded numbers and a short action: `0003_add_workspace_members.sql`.
- Never edit a migration that has been merged or applied outside your machine. Add a new migration instead.
- Every table must have:
  - `id` as `TEXT PRIMARY KEY` unless there is a strong reason for integer IDs.
  - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`.
  - `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP` when records can change.
- Store timestamps as ISO-8601 text in UTC.
- Enable foreign keys on every connection with `PRAGMA foreign_keys = ON`.
- Prefer explicit transactions for multi-step writes.
- Add indexes for foreign keys and common lookup columns.
- Do not use SQLite for high-write, multi-region workloads without a clear Turso/libSQL plan.

Reason: SQLite is extremely capable when schema changes are boring, explicit, and reversible. Most SaaS bugs here come from casual migrations, missing foreign keys, or unindexed tenant queries.

## Database Access Pattern

Keep database code server-only. Client Components must never import database clients, queries, or secrets.

Use three layers:

1. `queries.ts` for read-only SQL.
2. `service.ts` for business rules and transactions.
3. `actions.ts` or `route.ts` for framework entry points.

Example:

```ts
// features/workspaces/service.ts
export function createWorkspace(input: CreateWorkspaceInput, userId: string) {
  return db.transaction(() => {
    const workspace = insertWorkspace(input.name);
    insertWorkspaceMember(workspace.id, userId, "owner");
    return workspace;
  })();
}
```

Reason: Server Actions and route handlers should be thin. Business logic hidden inside route files is hard to test and easy to duplicate.

## Server Components vs Client Components

Default to Server Components.

Use Client Components only when the component needs:

- `useState`, `useEffect`, or browser-only APIs.
- Event handlers such as `onClick` or `onSubmit`.
- Client-side animation or optimistic UI.
- A third-party library that requires the DOM.

Keep Client Components at the leaves of the tree. Pass serialized data from Server Components into Client Components.

Reason: Server Components reduce bundle size, keep secrets on the server, and make database access straightforward.

## Forms, Actions & Validation

- Validate form input with Zod inside the server action or route handler.
- Return typed field errors, not raw exceptions.
- Re-check authorization inside every mutation. UI hiding is not security.
- Use idempotency keys for payments, imports, and webhook-like actions.
- Use `revalidatePath` or `revalidateTag` after mutations that affect cached views.

Reason: forms are an attack surface and a reliability boundary. Treat them like APIs because they are APIs.

## Auth & Authorization

- Keep authentication and authorization separate.
- Authentication answers: who is this user?
- Authorization answers: can this user do this action to this resource?
- Put authorization helpers near the resource, e.g. `features/workspaces/permissions.ts`.
- Check tenant/workspace membership on every workspace-scoped query and mutation.
- Never trust `userId`, `workspaceId`, role, or price values supplied by the browser.

Reason: multi-tenant SaaS failures are usually authorization bugs, not login bugs.

## API Routes & Webhooks

- Route handlers live under `app/api/**/route.ts`.
- Keep route handlers thin: parse, authenticate, call service, return response.
- Verify webhook signatures before parsing business data.
- Store inbound webhook events with a unique provider event ID before processing.
- Make webhook handlers idempotent.

Reason: external systems retry, users double-click, and providers send the same event more than once. Idempotency is not optional.

## Component Patterns

- Keep reusable UI primitives in `components/ui`.
- Keep feature-specific components under `features/<feature>/components`.
- Prefer composition over large prop-driven components.
- Do not put database calls in components marked `"use client"`.
- Do not fetch the same data separately in sibling components; fetch once in the parent Server Component and pass data down.
- Accessibility is part of done: labels, keyboard navigation, focus states, and semantic HTML.

Reason: component boundaries should follow product boundaries, not aesthetic guesses.

## Error Handling & Logging

- Show users safe, actionable messages.
- Log internal details on the server with request context.
- Do not leak stack traces, SQL, secrets, tokens, or provider responses to the browser.
- Use typed result objects for expected failures, exceptions for unexpected failures.
- Add an `audit_events` table for sensitive business actions such as billing changes, role changes, exports, and deletes.

Reason: logs are for operators; UI messages are for users. Mixing them creates security leaks and terrible UX.

## Security Defaults

- Treat every browser input as hostile.
- Keep secrets server-only.
- Use parameterized SQL only. Never concatenate user input into SQL strings.
- Set secure cookie flags: `httpOnly`, `sameSite`, `secure` in production, and a narrow path when possible.
- Rate-limit login, signup, password reset, imports, and expensive AI/API routes.
- Add CSRF protection when using cookie-based auth with non-idempotent requests outside Server Actions.
- Do not add dependencies for trivial helpers. Every dependency is supply-chain risk.

Reason: small SaaS apps do not get a security exemption. They just get fewer people watching the blast radius.

## Testing Rules

- Put pure business logic under `features/<feature>/service.ts` and unit test it.
- Use a disposable SQLite database for tests. Never run tests against development or production data.
- Test migrations from an empty database and, when possible, from a previous schema snapshot.
- Cover critical flows with Playwright: signup/login, create workspace, billing action, primary CRUD flow.
- Add regression tests for every bug fix.

Reason: tests should protect revenue paths and data integrity, not chase 100% coverage theater.

## Performance Rules

- Avoid client-side fetching for data needed at page load.
- Use pagination for tables and activity feeds.
- Add indexes before shipping filters or sorts on large tables.
- Avoid N+1 query loops; batch by IDs.
- Cache read-heavy, user-independent data with Next.js cache primitives.
- Do not cache tenant-private data unless the cache key includes tenant and user authorization context.

Reason: SQLite is fast; careless query patterns are faster at making it look slow.

## AI Feature Rules

If this SaaS includes AI features:

- Put prompts in versioned files or constants, not scattered inline strings.
- Log model name, prompt version, latency, and token/cost metadata when safe.
- Never log sensitive customer input unless explicitly required and disclosed.
- Add spending limits and per-tenant rate limits before launch.
- Treat AI output as untrusted text. Validate before using it as SQL, code, JSON, or business decisions.

Reason: AI features fail operationally before they fail magically: cost spikes, bad parsing, and unreviewed output.

## What We Do Not Do

- No Pages Router. Mixing App Router and Pages Router doubles mental overhead.
- No ORM by default. For SQLite SaaS, explicit SQL is easier to inspect, migrate, and optimize. Add Drizzle only if typed query composition becomes worth the extra layer.
- No premature microservices. A modular monolith is the default until deployment pain proves otherwise.
- No global state library by default. URL state, Server Components, and small Client Components cover most needs.
- No custom auth crypto. Use proven primitives and maintained libraries.
- No destructive schema changes without a migration plan, backup plan, and rollback note.
- No broad `any`, blanket `eslint-disable`, or ignored TypeScript errors. Fix the types or isolate the boundary with validation.
- No hidden background jobs in request handlers. Use an explicit queue or scheduled job when work can outlive the request.

Reason: these choices keep the app boring, inspectable, and cheap to maintain. Boring is a feature when customers and money are involved.

## Done Definition

A change is done when:

- It satisfies the user request without unrelated rewrites.
- Types pass.
- Relevant tests pass, or the reason they cannot run is documented.
- Database changes include migrations and indexes where needed.
- Auth and tenant checks are present for protected data.
- Error states and empty states are handled.
- The README or this file is updated if commands or conventions changed.

## How Claude Should Work In This Repo

- Start by reading this file, `README.md`, `package.json`, and the relevant feature folder.
- Make the smallest coherent change.
- Prefer editing existing patterns over inventing new architecture.
- Before adding a dependency, explain why the platform or existing code is insufficient.
- After changes, report:
  - files changed,
  - commands run,
  - tests passed or skipped,
  - risks or follow-ups.

Reason: the best assistant behavior for a SaaS codebase is predictable, narrow, and evidence-backed. Heroics are how regressions put on a fake mustache.
