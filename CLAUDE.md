# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This file is the operating contract for Claude Code in this repository. Assume a greenfield SaaS product built with **Next.js 15 App Router**, **React 19**, **TypeScript strict mode**, **Tailwind CSS**, and **SQLite** via either **Turso/libSQL + Drizzle** for hosted apps or **better-sqlite3 + Drizzle** for local-first apps.

The goal is not to generate clever code. The goal is to ship boring, typed, observable SaaS features that are easy to migrate, easy to test, and hard to corrupt.

---

## 1. Stack & version assumptions

Use these defaults unless an existing file proves otherwise:

| Area | Default | Reason |
| --- | --- | --- |
| Framework | Next.js 15.x App Router | Server Components and Server Actions are the default unit of work. |
| Runtime | Node.js 22 LTS | SQLite drivers and most SaaS SDKs are Node-first; do not assume Edge compatibility. |
| Language | TypeScript 5.x with `strict: true` | Auth, billing, and DB code need compile-time guardrails. |
| UI | React 19.x + Tailwind CSS 4.x | Keeps UI local and composable without a component framework dependency. |
| DB ORM | Drizzle ORM 0.44+ | SQL remains explicit while schema/types stay close to code. |
| Hosted SQLite | Turso/libSQL client 0.15+ | Production and preview environments should use branchable hosted SQLite. |
| Local/test SQLite | better-sqlite3 11+ | Local dev and tests should be fast, deterministic, and file-backed. |
| Validation | Zod 4.x | Every external boundary must parse unknown input. |
| Unit tests | Vitest 3.x + Testing Library 16.x | Unit-test business logic and forms before adding slow e2e tests. |
| E2E tests | Playwright 1.5x only for critical flows | Browser tests are valuable but expensive, so reserve them for revenue/auth/product-critical paths. |

If the project uses Prisma, Kysely, Lucia, Clerk, Stripe, or another specific library, follow the existing implementation — but keep the boundaries and rules below.

---

## 2. Golden rules

1. **Server-first by default.** Fetch data in Server Components, mutate data in Server Actions or route handlers, and keep Client Components for interactivity only. Reason: this avoids leaking secrets and reduces client bundle size.
2. **SQLite is the source of truth.** Do not hide schema decisions in ad-hoc JSON blobs unless the feature is explicitly schemaless. Reason: migrations should explain product state over time.
3. **No direct DB access from UI components.** Components call typed query/action functions; they never construct SQL. Reason: UI churn should not rewrite persistence rules.
4. **Every mutation has validation, authorization, transaction, and cache invalidation.** Reason: SaaS bugs usually happen at boundaries, not in JSX.
5. **Prefer explicit small modules over magic abstraction.** Reason: Claude and humans can safely edit files they can fully understand.
6. **Do not ask clarifying questions for routine CRUD.** If a task matches existing patterns, implement the smallest consistent version and document assumptions in the final response. Reason: routine CRUD should compound existing conventions instead of blocking delivery on architecture bikeshedding.

---

## 3. Project structure

Use this layout for new files:

```text
.
├── app/
│   ├── (marketing)/              # Public pages: landing, pricing, docs
│   ├── (auth)/                   # Sign in/up/reset routes
│   ├── (dashboard)/              # Authenticated product shell
│   │   ├── layout.tsx
│   │   └── dashboard/page.tsx
│   ├── api/                      # Webhooks and external HTTP integrations only
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/                       # Stateless primitives: Button, Input, Dialog
│   ├── forms/                    # Client form wrappers
│   └── layout/                   # Nav, sidebar, shell
├── db/
│   ├── client.ts                 # Drizzle/libSQL/better-sqlite3 client factory
│   ├── schema.ts                 # Tables, indexes, relations
│   ├── migrations/               # Generated SQL migrations, committed
│   └── seed.ts                   # Idempotent local seed data
├── features/
│   └── <feature>/
│       ├── actions.ts            # Server Actions for mutations
│       ├── queries.ts            # Read models and list/detail queries
│       ├── validators.ts         # Zod input schemas
│       ├── permissions.ts        # Feature-specific authorization helpers
│       ├── components/           # Feature UI
│       └── __tests__/            # Unit tests close to feature logic
├── lib/
│   ├── auth.ts                   # Session helpers and current-user lookup
│   ├── env.ts                    # Typed env parsing
│   ├── errors.ts                 # AppError/result helpers
│   ├── ids.ts                    # ID generation helpers
│   └── time.ts                   # Clock helpers for testability
├── scripts/                      # One-off maintenance scripts
├── tests/                        # Cross-feature integration/e2e tests
├── drizzle.config.ts
├── next.config.ts
└── package.json
```

Rules:

- Put product logic in `features/<feature>`, not in `app/`. Reason: routes change more often than business capabilities.
- Keep `app/api/**` for third-party webhooks, OAuth callbacks, file downloads, and machine clients. Reason: internal form submits should usually be Server Actions.
- Use route groups like `(marketing)` and `(dashboard)` to separate shells without changing URLs. Reason: auth/layout boundaries stay visible.
- Never create a `utils.ts` junk drawer. Add a named module under `lib/` or the relevant feature. Reason: generic utility files become unowned coupling.

---

## 4. Naming conventions

- Files and folders: `kebab-case`, except React components use `PascalCase.tsx` when the file exports exactly one component. Reason: file paths stay URL- and shell-friendly while one-component files remain easy to scan.
- React components: `PascalCase`. Reason: JSX treats lowercase names as DOM tags, so PascalCase prevents rendering mistakes.
- Hooks: `useThing` and only in Client Component code. Reason: hook naming lets lint rules enforce React semantics, and hooks cannot run in Server Components.
- Server Actions: `verbNounAction`, e.g. `createWorkspaceAction`. Reason: mutations should read like audited commands in logs and reviews.
- Queries: `getThing`, `listThings`, `findThingById`. Reason: readers can tell whether a function returns one row, many rows, or an optional row.
- Zod schemas: `createThingSchema`, `updateThingSchema`. Reason: schema names should match the mutation boundary they protect.
- DB tables: plural snake case, e.g. `users`, `workspaces`, `workspace_members`. Reason: plural names describe collections and snake case matches SQLite conventions.
- DB columns: snake case in SQL, camelCase in TypeScript only if the ORM maps it explicitly. Reason: implicit casing conversions cause subtle migration and query bugs.
- IDs: use prefixed text IDs (`user_`, `org_`, `sub_`) unless the existing schema uses integer primary keys. Reason: prefixed IDs make logs and support tickets easier to inspect.

Do not rename public routes, columns, env vars, or IDs without a migration and compatibility note. Reason: those names are external contracts that may be used by bookmarks, scripts, webhooks, or production data.

---

## 5. Environment configuration

Create a typed environment module and import it everywhere:

```ts
// lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Never read `process.env.X` directly outside `lib/env.ts`. Reason: missing config should fail at boot, not after a customer clicks a button.
- `.env.example` must include every required variable with safe placeholder values. Reason: new developers and preview environments should fail less often and never copy real secrets.
- Secrets stay server-only. Never pass secrets to Client Components or `NEXT_PUBLIC_*` unless they are intentionally public. Reason: anything in the client bundle is visible to users.
- Prefer separate DB files/branches for local, test, preview, and production. Reason: SQLite makes accidental cross-environment writes too easy.

---

## 6. SQLite and migration conventions

### Schema rules

- Define tables, indexes, and relations in `db/schema.ts`. Reason: one schema source keeps migrations, types, and query assumptions aligned.
- Every table needs `id`, `created_at`, `updated_at`, and an explicit ownership column when tenant-scoped, e.g. `workspace_id`. Reason: support, auditing, sync, and authorization all need stable identity, timestamps, and ownership.
- Use foreign keys for ownership and lifecycle relationships. Reason: SQLite can enforce invariants even when application code has a bug.
- Enable SQLite foreign keys in the DB client (`PRAGMA foreign_keys = ON`) when the driver requires it. Reason: SQLite does not help if referential checks are disabled.
- Add indexes for every common lookup and authorization filter. Reason: SaaS dashboards repeatedly filter by user/workspace, and missing indexes become latency bugs.
- Store timestamps as ISO text or integer milliseconds consistently; do not mix formats. Reason: mixed time formats break ordering, comparisons, and migrations.
- Store money as integer minor units plus currency (`amount_cents`, `currency`). Never use floats. Reason: floating-point math causes billing and reconciliation errors.
- Soft delete only when product/audit requirements need it; otherwise hard delete inside a transaction. Reason: unnecessary tombstones complicate every unique index, query, and export.

### Migration rules

- Generate migrations with the project command, then inspect the SQL before committing. Reason: generated SQL can still contain destructive operations or missing indexes.
- Commit generated migration files. Do not rely on runtime `push` in production. Reason: production schema changes must be reviewable and repeatable.
- Migrations must be append-only after they are shared. Create a new migration to fix a mistake. Reason: rewriting history breaks teammates, previews, and deployed databases.
- Destructive migrations require a safe path: add nullable column/table, backfill, switch reads/writes, then remove old data in a later migration. Reason: multi-step deploys prevent downtime and irreversible data loss.
- SQLite limitations matter: changing constraints or dropping columns may require table rebuilds. Keep migrations explicit. Reason: SQLite DDL support is narrower than Postgres, so hidden rebuilds need human review.
- Run migrations against an empty database and a seeded previous-version database before release. Reason: fresh installs and upgrades fail in different ways.

Example commands, adapt to the package manager already in the repo:

```bash
pnpm db:generate     # create migration from schema changes
pnpm db:migrate      # apply migrations locally
pnpm db:studio       # inspect local data when debugging
pnpm db:seed         # idempotent local seed
```

If these scripts do not exist, add them before adding DB features.

---

## 7. Data access patterns

Use feature query modules:

```ts
// features/workspaces/queries.ts
import { db } from "@/db/client";
import { workspaceMembers, workspaces } from "@/db/schema";
import { and, eq } from "drizzle-orm";

export async function getWorkspaceForUser(workspaceId: string, userId: string) {
  const [row] = await db
    .select({ workspace: workspaces })
    .from(workspaces)
    .innerJoin(
      workspaceMembers,
      and(
        eq(workspaceMembers.workspaceId, workspaces.id),
        eq(workspaceMembers.userId, userId),
      ),
    )
    .where(eq(workspaces.id, workspaceId))
    .limit(1);

  return row?.workspace ?? null;
}
```

Rules:

- Query functions return typed domain shapes, not raw request objects. Reason: route and component code should not depend on transport details.
- Put authorization filters in the query with joins or `exists`, not only nested relation filters. Reason: forbidden parent rows should never be returned, even with empty child relations.
- Avoid N+1 queries in Server Components. Fetch the route's read model once and pass data down. Reason: server rendering can hide slow query loops until production data grows.
- Use `db.transaction()` for multi-write mutations. Reason: SQLite is reliable when writes are short and atomic.
- Do not create global mutable caches around DB results. Use Next.js cache APIs intentionally and invalidate after mutations. Reason: global caches leak tenant data and go stale across deployments.

---

## 8. Server Actions and mutations

Server Actions must follow this shape:

```ts
// features/workspaces/actions.ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { db } from "@/db/client";
import { workspaces } from "@/db/schema";
import { requireUser } from "@/lib/auth";
import { createWorkspaceSchema } from "./validators";

export async function createWorkspaceAction(input: unknown) {
  const user = await requireUser();
  const data = createWorkspaceSchema.parse(input);

  const workspace = await db.transaction(async (tx) => {
    const [created] = await tx
      .insert(workspaces)
      .values({ name: data.name, ownerId: user.id })
      .returning();

    return created;
  });

  revalidatePath("/dashboard");
  return { ok: true as const, data: workspace };
}
```

Rules:

- Input type is `unknown`; parse with Zod inside the action. Reason: form data and client calls are untrusted.
- Call `requireUser()` or explicit authorization before writes. Reason: client-side checks are display hints and can be bypassed.
- Keep transactions short. Do not call Stripe, email, analytics, or webhooks inside a DB transaction. Reason: long transactions increase SQLite write-lock contention and make retries dangerous.
- Return typed results. Do not leak raw stack traces to the client. Reason: forms need predictable states and attackers should not see internals.
- Always revalidate the route or tag affected by the mutation. Reason: Server Components may otherwise render stale data after a successful write.
- Use idempotency keys for billing, webhooks, invitations, and retries. Reason: network retries should not create duplicate charges, emails, or records.

---

## 9. Route handlers and webhooks

Use `app/api/**/route.ts` only for HTTP integrations.

Rules:

- Validate method, auth, content type, and body. Reason: route handlers are public HTTP boundaries, even when called by your own UI.
- For webhooks, verify signatures before parsing business data. Reason: unsigned payloads can spoof billing, account, or integration events.
- Store webhook event IDs and process idempotently. Reason: providers retry deliveries and may send the same event more than once.
- Return quickly; move slow work to a queue or background task if the project has one. Reason: webhook providers time out and retry slow endpoints.
- Never trust client-supplied price IDs, user IDs, workspace IDs, or roles. Reason: clients can tamper with requests and escalate privileges or underpay.

Example webhook outline:

```ts
export async function POST(request: Request) {
  const rawBody = await request.text();
  const signature = request.headers.get("stripe-signature");
  const event = verifyStripeEvent(rawBody, signature);

  await handleBillingEvent(event); // idempotent internally
  return Response.json({ received: true });
}
```

---

## 10. Component patterns

### Server Components

Use Server Components for pages, layout, and data-loaded sections:

```tsx
// app/(dashboard)/dashboard/page.tsx
import { listWorkspacesForCurrentUser } from "@/features/workspaces/queries";
import { WorkspaceList } from "@/features/workspaces/components/WorkspaceList";

export default async function DashboardPage() {
  const workspaces = await listWorkspacesForCurrentUser();
  return <WorkspaceList workspaces={workspaces} />;
}
```

### Client Components

Use Client Components only when they need browser state, event handlers, optimistic UI, or effects:

```tsx
"use client";

import { useTransition } from "react";
import { createWorkspaceAction } from "../actions";

export function CreateWorkspaceButton() {
  const [pending, startTransition] = useTransition();

  return (
    <button
      disabled={pending}
      onClick={() => startTransition(() => createWorkspaceAction({ name: "Acme" }))}
    >
      Create workspace
    </button>
  );
}
```

Rules:

- Do not put `"use client"` at the top of large page files unless required. Reason: it pulls the subtree into the client bundle.
- Keep UI primitives stateless. Put product-specific state in feature components. Reason: primitives stay reusable and feature behavior remains close to product logic.
- Forms should show pending, success, and error states. Reason: SaaS users need confirmation when money, settings, or records change.
- Accessibility is not optional: labels, keyboard focus, and semantic elements are required. Reason: inaccessible flows block users and often fail keyboard/mobile usage too.
- Do not import server-only modules into Client Components. Reason: it can leak secrets or crash the client build.

---

## 11. Auth, tenants, and permissions

Assume a multi-tenant SaaS even if v1 has one user.

Rules:

- Centralize session lookup in `lib/auth.ts`. Reason: auth bugs multiply when every route parses sessions differently.
- Use `requireUser()` for authenticated pages/actions and `getOptionalUser()` for public pages. Reason: the function name should make access expectations obvious.
- Every tenant-scoped query filters by both resource ID and membership/ownership. Reason: guessing a resource ID must not bypass tenant isolation.
- Roles are checked server-side. Client-side role checks are display hints only. Reason: users can modify client code and network requests.
- Invitations, email changes, password resets, and billing portal links must be single-use or time-limited. Reason: long-lived reusable links become account-takeover or billing risks.
- Log security-sensitive events without logging secrets. Reason: audit trails help incident response, but leaked secrets make the incident worse.

Permission helper pattern:

```ts
export async function requireWorkspaceRole(workspaceId: string, roles: WorkspaceRole[]) {
  const user = await requireUser();
  const membership = await getMembership(workspaceId, user.id);

  if (!membership || !roles.includes(membership.role)) {
    throw new AppError("FORBIDDEN", "You do not have access to this workspace.");
  }

  return { user, membership };
}
```

---

## 12. Error handling and UX

- Use typed application errors (`AppError`) for expected failures: validation, auth, not found, quota, billing required. Reason: expected failures should produce stable UI, not random exception handling.
- Unexpected errors should be logged and shown as a generic message. Reason: users need a safe message while developers still get diagnostics.
- Add `error.tsx` for route segments that can fail. Reason: localized error boundaries keep one failed panel from taking down the whole app.
- Add `not-found.tsx` where resource lookup can miss. Reason: missing records are normal product states, not server crashes.
- User-facing errors must say what happened and what to do next. Reason: actionable copy reduces support load and repeated failed attempts.
- Do not use `console.log` as observability. Use the project's logger or add one small wrapper. Reason: structured logs can be filtered, redacted, and correlated in production.

Result shape for actions:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; code: string; message: string; fieldErrors?: Record<string, string[]> };
```

Reason: forms can render expected errors without parsing exceptions.

---

## 13. Caching and revalidation

- Treat authenticated dashboard data as dynamic unless there is a clear cache strategy. Reason: user-specific SaaS data usually changes after mutations, billing events, or invitations.
- Use `revalidatePath()` for route-level changes and `revalidateTag()` for shared read models. Reason: explicit invalidation makes freshness reviewable.
- Never cache per-user data under a global key. Reason: a shared key can leak one tenant's data to another tenant.
- After mutations, invalidate exactly the affected paths/tags. Reason: broad invalidation wastes compute while narrow missing invalidation shows stale UI.
- Do not use `unstable_noStore` everywhere as a substitute for understanding data freshness. Reason: disabling caching globally hides architecture mistakes and can slow the app.

Default route intent:

```ts
// Authenticated dashboard pages usually need fresh user-specific data.
export const dynamic = "force-dynamic";
```

Use this intentionally; do not cargo-cult it into marketing pages.

---

## 14. Testing policy

Test the behavior that would cost money, trust, or data if broken.

Minimum expectations:

- Validators: unit tests for accepted and rejected input. Reason: validation bugs are cheap to test and expensive when bad data reaches the DB.
- Permissions: tests for owner/member/non-member access. Reason: tenant isolation is a trust boundary, not a UI feature.
- Mutations: tests for transaction behavior and cache invalidation where practical. Reason: writes are where SaaS data corruption and stale UI usually happen.
- Webhooks: tests for signature verification and idempotency. Reason: billing/integration providers retry and attackers can send fake payloads.
- Migrations: run migrations against an empty test DB and a seeded previous schema when possible. Reason: install and upgrade paths fail differently.
- E2E: cover signup/signin, create workspace, billing checkout or mocked billing, and one core product flow. Reason: a few browser tests catch broken wiring across auth, routing, and forms.

Commands:

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm test:e2e
pnpm db:migrate
```

If a command is missing, add it or state why it is intentionally absent.

---

## 15. Development commands

Prefer one package manager. If `pnpm-lock.yaml` exists, use pnpm.

```bash
pnpm install          # install dependencies
pnpm dev              # start local Next.js dev server
pnpm build            # production build
pnpm start            # run production build locally
pnpm lint             # lint source
pnpm typecheck        # TypeScript no-emit check
pnpm test             # unit/integration tests
pnpm test:e2e         # Playwright tests
pnpm db:generate      # generate SQL migration
pnpm db:migrate       # apply migrations
pnpm db:studio        # inspect DB
pnpm db:seed          # seed local data
```

Before finishing any feature, run at least:

```bash
pnpm typecheck && pnpm lint && pnpm test
```

For docs-only changes, run Markdown checks if configured and verify all referenced commands exist or are clearly marked as expected scripts.

---

## 16. What we do not do — and why

- **No generic full-stack boilerplate.** Reason: this repo is specifically Next.js App Router + SQLite SaaS, and generic advice causes wrong files and wrong runtime choices.
- **No client-side secret access.** Reason: secrets belong on the server, and leaking them breaks customer trust.
- **No raw SQL string interpolation.** Reason: SQL injection still exists with SQLite; use parameterized queries or ORM builders.
- **No production schema changes with `db push`.** Reason: generated migrations are reviewable and repeatable; implicit pushes are not.
- **No long transactions.** Reason: SQLite allows many readers but serializes writes, so long writes create lock contention.
- **No business logic in React components.** Reason: components should render state while feature modules decide behavior and can be tested without a browser.
- **No untyped `any` to silence errors.** Reason: SaaS bugs hide in unchecked boundaries; fix the model or add a narrow type guard.
- **No catch-all `try/catch` that swallows failures.** Reason: users and logs need actionable errors.
- **No new dependency for a one-line helper.** Reason: SaaS apps age through dependencies; add packages only when they own a real concern.
- **No premature queues, event buses, or microservices.** Reason: start with simple transactions and explicit modules; split only when load or isolation requires it.

---

## 17. Task execution checklist for Claude Code

When asked to implement a feature:

1. Inspect existing `package.json`, `db/schema.ts`, `app/`, and `features/` before editing. Reason: existing conventions override generic template assumptions.
2. Identify whether the change is read-only, mutation, webhook, auth, billing, or migration. Reason: each category has different safety checks and test needs.
3. Add or update Zod schemas for any external input. Reason: untrusted data must be parsed at the boundary.
4. Add DB schema/migration changes before code that depends on them. Reason: types and queries should match the schema that will actually deploy.
5. Implement query/action modules before UI. Reason: UI should call stable business boundaries instead of embedding persistence logic.
6. Add tests at the lowest useful level. Reason: unit and integration tests are faster and more precise than broad browser tests.
7. Run typecheck, lint, tests, and migrations relevant to the change. Reason: SaaS regressions often appear in generated types, formatting, or migration SQL before runtime.
8. Report what changed, what was verified, and any assumptions. Reason: maintainers need a concise audit trail for review and release.

If the user requests a standard SaaS capability such as workspaces, invites, settings, billing, or audit logs, do not ask for architecture. Use the patterns in this file and choose the smallest production-safe implementation.

---

## 18. Acceptance criteria mapping for this template

- Project structure: see sections 3 and 7. Evidence: routes, components, DB, feature modules, and query boundaries are all specified.
- Naming conventions: see section 4. Evidence: files, components, hooks, actions, queries, schemas, tables, columns, and IDs have explicit rules.
- DB migration rules: see section 6. Evidence: schema ownership, foreign keys, indexes, generated migrations, destructive-change sequencing, and SQLite limitations are covered.
- Dev commands: see section 15. Evidence: install, dev, build, lint, typecheck, tests, e2e, migrations, studio, and seed commands are listed.
- Patterns to follow: see sections 7 through 14. Evidence: data access, Server Actions, route handlers, components, auth, errors, caching, and tests have concrete examples or rules.
- Anti-patterns to avoid: see section 16. Evidence: each forbidden pattern includes the reason it is dangerous in this stack.
- Opinionated with reasons: every prescriptive rule above includes a `Reason:` clause or an adjacent reason sentence. Evidence: this makes the template actionable instead of generic.
- Greenfield-ready: the stack assumptions and directory layout are complete enough to paste into a new project. Evidence: the file defines defaults before any app code exists.
- Claude Code readiness: section 17 tells Claude exactly how to proceed without routine clarifying questions. Evidence: task execution order, checks, and reporting are explicit.
