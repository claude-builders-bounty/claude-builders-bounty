# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the project instruction source for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, and SQLite. Follow these rules unless a task explicitly changes the product requirement.

## Stack And Versions

- Next.js 15 App Router, React 19, TypeScript strict mode, Tailwind CSS, ESLint, Prettier, Vitest, Playwright.
  Reason: App Router gives server-first routing and React Server Components; strict TypeScript catches broken contracts before runtime.
- SQLite is the system of record. Use `better-sqlite3` for a Node runtime, single-region app. Use Turso/libSQL with `@libsql/client` when the app must run in serverless or multi-region environments.
  Reason: both options keep the schema portable while making the deployment constraint explicit.
- Use raw SQL plus a tiny repository layer. Do not introduce Prisma, Drizzle, or an ORM unless the task explicitly asks for one.
  Reason: the app should teach Claude the actual SQL shape and avoid hidden migration behavior.
- Runtime target is Node.js for routes that touch local SQLite. Edge runtime is allowed only for stateless reads that do not import the database client.
  Reason: `better-sqlite3` is a native synchronous Node package and will not run in Edge.

## Dev Commands

Use `pnpm` unless the repository already has a different lockfile.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
pnpm build
```

Expected scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "db:migrate": "tsx src/db/migrate.ts",
    "db:studio": "sqlite-web data/app.db"
  }
}
```

If a command is missing, add it before using it in documentation or CI. Do not ask which package manager to use when a lockfile already answers that question.

## Folder Structure

```text
.
├── app/
│   ├── (marketing)/
│   │   ├── page.tsx
│   │   └── pricing/page.tsx
│   ├── (app)/
│   │   ├── dashboard/page.tsx
│   │   └── settings/page.tsx
│   ├── api/
│   │   └── webhooks/stripe/route.ts
│   ├── layout.tsx
│   └── error.tsx
├── components/
│   ├── ui/
│   ├── forms/
│   └── charts/
├── src/
│   ├── actions/
│   ├── auth/
│   ├── db/
│   │   ├── client.ts
│   │   ├── migrate.ts
│   │   ├── queries/
│   │   └── schema/
│   │       ├── 0001_initial.sql
│   │       └── 0002_add_billing.sql
│   ├── lib/
│   ├── validators/
│   └── env.ts
├── tests/
│   ├── unit/
│   └── e2e/
└── data/
    └── .gitkeep
```

Rules:

- Route folders own pages, layouts, loading states, and error boundaries only.
  Reason: colocating business logic inside route folders makes features hard to reuse and test.
- `src/db/queries` owns database access. Pages, Server Components, Server Actions, and Route Handlers call query functions instead of writing inline SQL.
  Reason: one repository layer keeps transactions and auth filters consistent.
- `src/actions` owns Server Actions that mutate data. Each action validates input, checks authorization, performs a transaction, and returns a typed result.
  Reason: mutations need the same security path whether they are called from forms or client components.
- `src/env.ts` is the only module that reads `process.env`.
  Reason: central validation prevents silent production misconfiguration.
- `components/ui` contains unopinionated primitives. Product-specific components live outside `ui`.
  Reason: shared primitives stay reusable and product components can depend on domain data.

## Naming Conventions

- Files and folders use kebab-case: `billing-summary.tsx`, `user-menu.tsx`.
  Reason: imports stay readable on case-sensitive filesystems.
- React components use PascalCase exports: `BillingSummary`.
  Reason: JSX and React DevTools show component identity clearly.
- Server Actions end with `Action`: `updateWorkspaceNameAction`.
  Reason: callers can distinguish mutations from pure helpers.
- Query functions start with a verb and include the entity: `getWorkspaceBySlug`, `listInvoicesForWorkspace`, `insertAuditEvent`.
  Reason: SQL side effects are obvious at call sites.
- Database tables use plural snake_case nouns: `users`, `workspaces`, `workspace_members`.
  Reason: SQL reads naturally and avoids mixed naming conventions.
- Primary keys are `id TEXT PRIMARY KEY`. Foreign keys are `<entity>_id`.
  Reason: IDs are stable across local SQLite and remote Turso/libSQL.
- Date columns use `created_at`, `updated_at`, and `deleted_at` as ISO-8601 UTC text.
  Reason: text timestamps sort correctly and are portable across SQLite providers.

## SQLite And Migration Rules

- Every schema change is an append-only SQL file in `src/db/schema` named `NNNN_short_description.sql`.
  Reason: deterministic files make review and rollback possible.
- Never edit a migration after it has shipped to main. Add a new migration instead.
  Reason: production databases may already have recorded the old checksum or applied SQL.
- The migration runner stores applied files in `_migrations(filename TEXT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)`.
  Reason: a durable migration ledger prevents accidental replays and drift.
- Enable SQLite safety settings on every connection:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

Reason: foreign keys protect integrity, WAL improves concurrent reads, and busy timeout avoids transient lock failures.

- Use `BEGIN IMMEDIATE` for multi-statement writes.
  Reason: the app should fail early when it cannot obtain the write lock.
- Every user-owned table includes `workspace_id` or an equivalent tenant key.
  Reason: SaaS data must be filterable by tenant at the SQL layer.
- Soft-delete user-generated business records with `deleted_at`; hard-delete join rows and short-lived tokens.
  Reason: auditability matters for billing and support, but temporary secrets should not linger.
- Use parameterized statements only. Never interpolate user input into SQL strings.
  Reason: SQLite accepts stacked expressions and user input must never become SQL syntax.
- Add indexes in the same migration as the query pattern that needs them.
  Reason: performance requirements should be reviewable with the feature that creates them.
- Do not use `SELECT *` outside throwaway scripts.
  Reason: explicit columns make schema changes less likely to break serialized responses.

## Data Access Pattern

`src/db/client.ts` creates exactly one database access surface.

```ts
import Database from "better-sqlite3";

export const db = new Database(process.env.DATABASE_URL ?? "data/app.db");

db.pragma("foreign_keys = ON");
db.pragma("journal_mode = WAL");
db.pragma("busy_timeout = 5000");
```

Queries return domain types, not raw driver rows.

```ts
export type Workspace = {
  id: string;
  slug: string;
  name: string;
  createdAt: string;
};

export function getWorkspaceBySlug(slug: string): Workspace | null {
  const row = db
    .prepare(
      `SELECT id, slug, name, created_at AS createdAt
       FROM workspaces
       WHERE slug = ? AND deleted_at IS NULL`,
    )
    .get(slug);

  return row ? WorkspaceRow.parse(row) : null;
}
```

Reason: validation at the database boundary catches drift before bad rows reach components.

## Server Components, Actions, And Routes

- Server Components are the default. Fetch data directly in pages and layouts through query functions.
  Reason: this reduces client JavaScript and keeps credentials on the server.
- Add `"use client"` only for browser state, event handlers, effects, or browser-only APIs.
  Reason: unnecessary client components increase bundle size and leak server-only imports.
- Server Actions validate with Zod, authorize using the current session, perform one transaction, and call `revalidatePath` or `revalidateTag`.
  Reason: mutations must be atomic and reflected in cached UI.
- Route Handlers are for external integrations, webhooks, file downloads, and public API boundaries.
  Reason: internal form mutations are simpler and safer as Server Actions.
- Webhooks verify signatures before parsing trusted business fields.
  Reason: a JSON body alone does not prove the caller is the provider.

## Auth And Authorization

- Keep authentication in `src/auth` and authorization checks near the query or action that needs them.
  Reason: pages can be bypassed by direct calls to actions and routes.
- Use session helpers named `requireUser`, `requireWorkspaceMember`, and `requireWorkspaceRole`.
  Reason: call sites should reveal the required permission level.
- Never rely only on middleware for authorization.
  Reason: middleware is useful for navigation guards but not a complete security boundary.
- Audit billing, membership, and role changes in an `audit_events` table.
  Reason: support and incident response need a durable history.

## Component Patterns

- Page components compose layout and data. They should not contain complex form state or SQL.
  Reason: pages stay easy for Claude to modify without breaking cross-cutting logic.
- Forms use server actions with `useActionState` or progressive enhancement first.
  Reason: core SaaS workflows should work without fragile client-only request code.
- Keep component props serializable unless the component is server-only.
  Reason: React Server Components cannot pass functions or class instances across the boundary.
- UI components accept semantic props and className extension points; they do not fetch data.
  Reason: presentation stays separate from product state.
- Loading, empty, and error states are part of the feature, not follow-up polish.
  Reason: SaaS screens are used repeatedly under real network and data conditions.

## Validation And Testing

- Unit-test pure validators, price calculations, permission helpers, and query mappers with Vitest.
  Reason: these functions carry business risk and are cheap to test.
- Add integration tests for migrations and important query functions against a temporary SQLite database.
  Reason: SQL correctness cannot be proven by TypeScript alone.
- Add Playwright tests for signup, login, workspace creation, billing handoff, and the primary dashboard flow.
  Reason: SaaS value depends on full workflows, not isolated components.
- Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build` before a PR.
  Reason: lint catches consistency, typecheck catches contracts, tests catch behavior, and build catches App Router/runtime mistakes.

## Pull Request Rules

- Include the migration file, query functions, UI changes, tests, and documentation for the same feature in one PR.
  Reason: reviewers need the full behavior change to judge correctness.
- Describe data model changes in the PR body, including new tables, columns, indexes, and backfill behavior.
  Reason: schema changes are the hardest part of a SaaS app to undo.
- For risky changes, include manual verification steps with exact commands and expected output.
  Reason: maintainers should be able to reproduce the result without guessing.

## What We Do Not Do And Why

- Do not put secrets in `.env.local.example`, tests, screenshots, or docs.
  Reason: example files are copied and public artifacts are hard to purge.
- Do not call the database from Client Components.
  Reason: database clients and credentials must never ship to the browser.
- Do not use Edge runtime with `better-sqlite3`.
  Reason: native SQLite bindings require Node.js APIs.
- Do not skip tenant filters in queries and "filter later" in JavaScript.
  Reason: accidental cross-tenant reads are a severe SaaS security bug.
- Do not create generic catch-all abstractions before two real call sites exist.
  Reason: early abstractions hide product logic and make Claude edit the wrong layer.
- Do not accept unvalidated `FormData`, URL params, headers, or webhook payloads.
  Reason: every external boundary is untrusted input.
- Do not use optimistic UI for billing, role, or destructive changes unless the rollback path is tested.
  Reason: these flows need correctness more than perceived speed.
- Do not add an ORM migration system beside SQL migrations.
  Reason: two schema authorities create drift.
- Do not hide SQLite write contention by retrying forever.
  Reason: persistent lock failures indicate a design or deployment problem that needs to be fixed.
- Do not leave TODO comments in committed security, billing, or migration code.
  Reason: placeholders in critical paths become production behavior.

## Claude Operating Instructions

- Before editing, identify which layer owns the change: route, component, action, query, migration, or test.
- Prefer the smallest change that preserves the conventions in this file.
- If a task needs a new table or column, write the migration before writing the feature code.
- If a task changes authorization, add or update tests before declaring the work done.
- If a request conflicts with these rules, explain the conflict and choose the safer SaaS behavior.
