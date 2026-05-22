# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack and fixed choices

Use this file as project instructions for a greenfield SaaS built with:

- Next.js 15 App Router
- TypeScript strict mode
- SQLite as primary database
- Drizzle ORM for schema, migrations, and typed queries
- better-sqlite3 for local/single-node deployments OR Turso/libSQL for remote/edge needs
- React Server Components by default
- Server Actions only for small trusted mutations
- Route Handlers for webhooks, public APIs, and third-party callbacks
- Tailwind CSS plus shadcn/ui-style components
- Zod for all untrusted input
- Vitest for unit tests, Playwright for critical user flows

Reason: this stack keeps local development fast, avoids premature distributed systems, and gives Claude clear boundaries for database, UI, and server code.

## Non-negotiable operating rules

1. Prefer boring code over clever code.
   Reason: SaaS apps need predictable maintenance more than novelty.

2. Keep database access on the server only.
   Reason: SQLite credentials and query logic must never enter client bundles.

3. Change schema only through migrations.
   Reason: SQLite is simple, but production data still needs reversible history.

4. Treat Server Components as default.
   Reason: less client JavaScript, fewer hydration bugs, safer data access.

5. Add a reason comment when breaking any rule in this file.
   Reason: future Claude sessions need context, not mystery exceptions.

## Folder structure

Create this structure unless task says otherwise:

```text
app/
  (marketing)/
    page.tsx
    pricing/page.tsx
  (app)/
    dashboard/page.tsx
    settings/page.tsx
  api/
    webhooks/
      stripe/route.ts
  layout.tsx
  globals.css
components/
  ui/
  forms/
  layout/
  domain/
db/
  schema.ts
  client.ts
  migrations/
  seed.ts
lib/
  auth/
  env.ts
  errors.ts
  ids.ts
  validation.ts
server/
  actions/
  queries/
  services/
tests/
  unit/
  e2e/
```

Rules:

- `app/` owns routes, layouts, metadata, and route handlers.
- `components/ui/` contains generic primitives only: buttons, dialogs, inputs.
- `components/domain/` contains business UI: billing cards, workspace switchers, usage charts.
- `server/queries/` contains read-only DB functions.
- `server/actions/` contains Server Actions that validate input and call services.
- `server/services/` contains business operations and transaction boundaries.
- `db/schema.ts` is sole source of truth for tables.
- `lib/env.ts` is only file that reads `process.env` directly.

Reason: route code stays thin, DB code stays findable, and Claude can place new code without asking where it belongs.

## Naming conventions

Files:

- React components: `PascalCase.tsx` only when component is exported and reused.
- Route-local components: `_components/name-card.tsx` with kebab-case.
- Server Actions: `server/actions/<domain>.ts`.
- Queries: `server/queries/<domain>.ts`.
- Services: `server/services/<domain>.ts`.
- Tests: `<subject>.test.ts` or `<flow>.spec.ts`.

Code:

- Components: `PascalCase`.
- Functions: verb-first camelCase, e.g. `createWorkspace`, `listInvoices`.
- Booleans: `is`, `has`, `can`, `should` prefixes.
- Zod schemas: `<Name>InputSchema` for incoming data.
- Inferred types: `<Name>Input`, `<Name>Result`.

Database:

- Tables: plural snake_case, e.g. `workspaces`, `workspace_members`.
- Columns: snake_case, e.g. `created_at`, `stripe_customer_id`.
- Primary keys: `id` text ULID unless external system requires different.
- Foreign keys: `<singular_table>_id`, e.g. `workspace_id`.
- Unique indexes: `<table>_<columns>_unique`.
- Normal indexes: `<table>_<columns>_idx`.

Reason: consistent names make schema, API, and UI searchable with low ambiguity.

## Dev commands

Assume these scripts exist or add equivalents:

```bash
pnpm dev                 # start Next.js dev server
pnpm build               # production build
pnpm start               # run built app
pnpm lint                # eslint
pnpm typecheck           # tsc --noEmit
pnpm test                # unit tests
pnpm test:e2e            # Playwright critical flows
pnpm db:generate         # drizzle-kit generate
pnpm db:migrate          # apply migrations
pnpm db:studio           # inspect local database
pnpm db:seed             # seed local fixtures
```

Before finishing any code task, run at minimum:

```bash
pnpm typecheck && pnpm lint && pnpm test
```

If task touches routes, layouts, env, or database schema, also run:

```bash
pnpm build
```

Reason: type safety catches most Claude mistakes before PR review.

## Environment rules

Create `lib/env.ts`:

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().min(1).optional(),
  STRIPE_WEBHOOK_SECRET: z.string().min(1).optional(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Never read `process.env` outside `lib/env.ts`.
- Prefix browser-safe variables with `NEXT_PUBLIC_` only.
- Never add secrets to `.env.example`; use placeholder names.
- Validate optional secrets at use site when feature is enabled.

Reason: centralized env parsing fails fast and prevents accidental secret exposure.

## Database schema conventions

Use Drizzle schema with explicit timestamps:

```ts
import { sqliteTable, text, integer, index, uniqueIndex } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const workspaces = sqliteTable(
  "workspaces",
  {
    id: text("id").primaryKey(),
    name: text("name").notNull(),
    slug: text("slug").notNull(),
    createdAt: integer("created_at", { mode: "timestamp" }).notNull().default(sql`CURRENT_TIMESTAMP`),
    updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => ({
    slugUnique: uniqueIndex("workspaces_slug_unique").on(table.slug),
    createdAtIdx: index("workspaces_created_at_idx").on(table.createdAt),
  }),
);
```

Rules:

- Every user-owned table has `created_at` and `updated_at`.
- Store money in integer cents, never floats.
- Store enum-like values as text with TypeScript unions and Zod validation.
- Use foreign keys where SQLite runtime supports them; enable `PRAGMA foreign_keys = ON`.
- Use transactions for multi-table writes.
- Do not hide DB writes inside React components.

Reason: SQLite has fewer guardrails than big client/server databases; conventions prevent silent data drift.

## Migration rules

Workflow:

1. Edit `db/schema.ts`.
2. Run `pnpm db:generate`.
3. Review generated SQL manually.
4. Run migration locally with `pnpm db:migrate`.
5. Add migration file to PR.

Rules:

- Never edit applied migration files.
- Never use destructive migration without explicit backup note.
- For column renames, use expand-copy-contract:
  1. add new column,
  2. backfill,
  3. read from new column,
  4. later remove old column.
- For SQLite table rebuilds, include exact generated SQL in PR description.
- Seed data belongs in `db/seed.ts`, not migrations.

Reason: SQLite supports limited `ALTER TABLE`; safe migrations need deliberate steps.

## Query and service patterns

Read-only query example:

```ts
// server/queries/workspaces.ts
import { db } from "@/db/client";
import { workspaces } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function getWorkspaceBySlug(slug: string) {
  return db.query.workspaces.findFirst({
    where: eq(workspaces.slug, slug),
  });
}
```

Mutation pattern:

```ts
// server/services/workspaces.ts
import { db } from "@/db/client";
import { workspaces } from "@/db/schema";
import { createId } from "@/lib/ids";

export async function createWorkspaceForUser(input: { name: string; slug: string; userId: string }) {
  return db.transaction(async (tx) => {
    const workspaceId = createId();

    await tx.insert(workspaces).values({
      id: workspaceId,
      name: input.name,
      slug: input.slug,
    });

    return { id: workspaceId };
  });
}
```

Rules:

- Queries return plain serializable objects.
- Services own transactions and cross-table invariants.
- Server Actions validate, authorize, call service, then revalidate path/tag.
- Route Handlers validate request body and return typed JSON.

Reason: this separation lets Claude modify one layer without guessing side effects.

## Server Action pattern

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { createWorkspaceForUser } from "@/server/services/workspaces";

const CreateWorkspaceInputSchema = z.object({
  name: z.string().min(2).max(80),
  slug: z.string().regex(/^[a-z0-9-]+$/).min(3).max(48),
});

export async function createWorkspaceAction(rawInput: unknown) {
  const input = CreateWorkspaceInputSchema.parse(rawInput);
  const user = await requireUser();

  const result = await createWorkspaceForUser({ ...input, userId: user.id });
  revalidatePath("/dashboard");

  return { ok: true, workspaceId: result.id } as const;
}
```

Rules:

- Server Actions accept `unknown` or `FormData`, never trusted typed input.
- Validate before authorization-dependent writes.
- Return small serializable results.
- Do not put long-running jobs in Server Actions.

Reason: Server Actions are convenient but easy to misuse as unvalidated RPC endpoints.

## Component patterns

Server Component default:

```tsx
export default async function DashboardPage() {
  const user = await requireUser();
  const workspaces = await listWorkspacesForUser(user.id);

  return <WorkspaceList workspaces={workspaces} />;
}
```

Client Component only when needed:

```tsx
"use client";

import { useState } from "react";

export function RenameWorkspaceForm() {
  const [pending, setPending] = useState(false);
  // interactive state lives here
}
```

Rules:

- Use Client Components for browser state, event handlers, animations, or browser APIs.
- Keep data fetching in Server Components or server modules.
- Pass serializable props from server to client.
- Avoid global client providers unless many routes truly need them.
- Prefer composition over prop drilling for page sections.

Reason: minimizing client boundaries improves performance and reduces accidental secret leaks.

## Route Handler pattern

Use Route Handlers for webhooks and public API endpoints:

```ts
import { NextResponse } from "next/server";
import { z } from "zod";

const PayloadSchema = z.object({
  eventId: z.string(),
});

export async function POST(request: Request) {
  const body = PayloadSchema.parse(await request.json());
  await processEvent(body);
  return NextResponse.json({ ok: true });
}
```

Rules:

- Verify webhook signatures before parsing business payloads.
- Return explicit status codes.
- Do not leak stack traces in responses.
- Keep handler thin; call service modules.

Reason: API edges receive hostile input and need small auditable code.

## Error handling

Use typed application errors:

```ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: "BAD_REQUEST" | "UNAUTHORIZED" | "FORBIDDEN" | "NOT_FOUND" | "CONFLICT",
  ) {
    super(message);
  }
}
```

Rules:

- Throw `AppError` for expected business failures.
- Let unexpected errors crash to logger/error boundary.
- Show user-safe messages only.
- Never swallow errors with empty `catch`.

Reason: clear failure modes keep UI and API behavior consistent.

## Auth and authorization

Rules:

- Authenticate at route/page/action boundary.
- Authorize inside service before mutating user-owned data.
- Never trust `workspaceId` or `userId` from client without membership check.
- Store roles as text union: `owner`, `admin`, `member`, `viewer`.
- Put reusable checks in `server/services/permissions.ts`.

Reason: most SaaS bugs are authorization bugs, not login bugs.

## Testing requirements

Unit tests:

- Validate Zod schemas reject bad input.
- Test service functions against temporary SQLite database.
- Test permission failures.

E2E tests:

- Sign up or mocked auth login.
- Create workspace.
- Invite/member permission path.
- Billing or plan gate if app has pricing.

Smoke prompt for Claude Code after pasting this file:

```text
Create initial workspace CRUD for this SaaS using existing conventions. Do not ask clarifying questions unless required secrets are missing.
```

Expected Claude behavior:

- Creates schema and migration.
- Adds server queries/services/actions.
- Adds App Router pages.
- Uses Server Components by default.
- Runs typecheck/lint/test.

Reason: tests enforce project boundaries and prove this CLAUDE.md is usable without extra explanation.

## What we do

- Use Server Components for read-heavy pages.
  Reason: server data access stays simple and safe.

- Use Zod at every input boundary.
  Reason: TypeScript does not validate runtime input.

- Use Drizzle migrations for every schema change.
  Reason: production data requires history.

- Use transactions for multi-step writes.
  Reason: partial writes corrupt SaaS state.

- Use route groups for marketing vs authenticated app.
  Reason: layouts and auth rules stay separate.

- Use small service functions with explicit inputs.
  Reason: Claude can test and modify them safely.

- Use integer cents for billing amounts.
  Reason: floats lose money.

- Use explicit cache revalidation after mutations.
  Reason: stale dashboards cause support issues.

## What we do not do

- Do not put database queries in Client Components.
  Reason: client bundles cannot access DB safely.

- Do not create generic `utils.ts` dumping grounds.
  Reason: unclear ownership makes future edits risky.

- Do not add Prisma unless requested.
  Reason: this project standardizes on Drizzle for SQLite-first migrations and typed SQL.

- Do not use `any` to silence errors.
  Reason: it removes TypeScript value exactly where Claude needs guardrails.

- Do not mutate data in GET handlers.
  Reason: crawlers, caches, and prefetchers can trigger GETs.

- Do not rely on local component state for server truth.
  Reason: refresh or multi-tab use will drift.

- Do not create migration SQL by memory.
  Reason: generated SQL plus manual review is safer.

- Do not add global state libraries for simple forms.
  Reason: React state and Server Actions are enough for most SaaS forms.

- Do not over-abstract before second use.
  Reason: premature abstractions confuse Claude and humans.

## PR checklist for Claude

Before opening a PR, confirm:

- [ ] Folder placement follows this file.
- [ ] New input boundaries use Zod.
- [ ] Schema changes include generated migration.
- [ ] Multi-table writes use transactions.
- [ ] Client Components are marked only where interactivity requires them.
- [ ] `pnpm typecheck`, `pnpm lint`, and `pnpm test` pass.
- [ ] `pnpm build` passes when app/db/env changed.
- [ ] PR description names any rule intentionally broken and why.
