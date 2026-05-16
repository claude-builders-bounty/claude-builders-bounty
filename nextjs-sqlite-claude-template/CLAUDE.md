# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the operating manual for Claude Code in a production-oriented SaaS app built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite via `better-sqlite3` or Turso/libSQL.

## Stack and versions

- Runtime: Node.js 22 LTS.
- Package manager: `pnpm`.
- Framework: Next.js 15 App Router only. Do not use the Pages Router.
- Language: TypeScript with `strict: true`.
- UI: React 19, Server Components by default, Client Components only at interaction boundaries.
- Database: SQLite in development and small production deployments.
  - Local default: `better-sqlite3`.
  - Hosted/edge default: Turso/libSQL.
- Styling: Tailwind CSS plus small local components. Avoid large UI frameworks unless the project already uses one.
- Validation: Zod at all external boundaries.
- Auth: cookie-backed sessions or Auth.js. Never invent a custom password/session system unless the existing app already has one.
- Tests: Vitest for unit tests, Playwright for smoke/e2e tests.

Reason: this stack keeps the app deployable, easy to reason about, and cheap to run. SQLite is a feature, not a toy, but it needs explicit migration and write-path discipline.

## Commands

Use these commands unless `package.json` defines different names:

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

Before marking work complete, run at minimum:

```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

If a command is missing, add the script instead of silently skipping verification.

## Folder structure

Use this structure for greenfield work:

```text
.
├── app/
│   ├── (marketing)/
│   ├── (dashboard)/
│   ├── api/
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/
│   └── feature-name/
├── db/
│   ├── client.ts
│   ├── migrations/
│   ├── schema.ts
│   └── queries/
├── lib/
│   ├── auth/
│   ├── env.ts
│   ├── errors.ts
│   └── utils.ts
├── server/
│   ├── actions/
│   └── services/
├── tests/
│   ├── unit/
│   └── e2e/
└── scripts/
```

Rules:

- `app/` contains routing, layouts, route handlers, and page composition.
- `components/ui/` contains reusable dumb UI primitives.
- `components/feature-name/` contains feature-specific presentational components.
- `db/queries/` contains typed SQL access functions. Pages and components must not contain raw SQL.
- `server/services/` contains business workflows that combine auth, validation, and db calls.
- `server/actions/` contains Server Actions that validate input, call services, and return serializable results.
- `lib/env.ts` is the only place that reads `process.env` directly.

Reason: this separation prevents the common SaaS failure mode where pages become untestable mixtures of SQL, auth, validation, and JSX.

## Naming conventions

- Files and directories: kebab-case (`billing-portal.tsx`, `user-menu.tsx`).
- React components: PascalCase (`BillingPortal`).
- Server actions: verb-object names ending in `Action` (`createWorkspaceAction`).
- DB query functions: explicit verb phrases (`getUserByEmail`, `insertSubscriptionEvent`).
- Zod schemas: `SomethingInputSchema`, `SomethingOutputSchema`.
- Environment variables: uppercase snake case, validated in `lib/env.ts`.
- Database tables: snake_case plural nouns (`users`, `workspace_members`).
- Database columns: snake_case (`created_at`, `workspace_id`).

Reason: predictable names let Claude search and modify code without guessing.

## Environment variables

Create a typed env module:

```ts
// lib/env.ts
import { z } from "zod";

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
});

export const env = EnvSchema.parse(process.env);
```

Rules:

- Never read `process.env` outside `lib/env.ts`.
- Never commit `.env`.
- Update `.env.example` whenever adding a variable.
- Prefer failing at boot over allowing undefined config at runtime.

## SQLite and migration rules

### Migration policy

- Every schema change gets a new migration file in `db/migrations/`.
- Migration filenames use sortable timestamps:

```text
YYYYMMDDHHMM_describe_change.sql
```

- Migrations are append-only after merge. Do not edit old migrations; create a new one.
- Every migration must be safe to run once in order on a fresh database.
- For destructive changes, use a two-step migration:
  1. Add new table/column and backfill.
  2. Remove old table/column only after code no longer depends on it.

Reason: SQLite has limited `ALTER TABLE`; careful append-only migrations make rollouts predictable.

### SQL style

- Always use parameterized queries. Never concatenate user input into SQL.
- Prefer explicit column lists over `SELECT *`.
- Store timestamps as ISO-8601 UTC text unless the existing app standard says otherwise.
- Use foreign keys and enable them at connection startup:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

- Add indexes for foreign keys and high-cardinality lookup columns.
- Keep transactions short. SQLite allows many readers but one writer.
- Wrap multi-step writes in transactions.

### Query layer pattern

```ts
// db/queries/users.ts
import { db } from "../client";

export type UserRow = {
  id: string;
  email: string;
  created_at: string;
};

export function getUserByEmail(email: string): UserRow | null {
  return db.prepare<UserRow>(
    `SELECT id, email, created_at FROM users WHERE email = ? LIMIT 1`,
  ).get(email) ?? null;
}
```

Rules:

- Query functions return plain serializable data, not framework objects.
- Convert database errors into domain errors in services, not in pages.
- Keep raw SQL inside `db/` only.

## App Router patterns

### Server Components by default

Use Server Components for data loading and page composition:

```tsx
// app/(dashboard)/workspaces/page.tsx
import { listWorkspacesForCurrentUser } from "@/server/services/workspaces";

export default async function WorkspacesPage() {
  const workspaces = await listWorkspacesForCurrentUser();
  return <WorkspaceList workspaces={workspaces} />;
}
```

Only add `'use client'` when the component needs state, effects, browser APIs, or event handlers.

Reason: defaulting to Server Components reduces client JavaScript and avoids leaking secrets.

### Route handlers

Use route handlers for webhooks, third-party callbacks, and non-UI HTTP APIs:

```ts
// app/api/webhooks/stripe/route.ts
export async function POST(request: Request) {
  const rawBody = await request.text();
  // verify signature before parsing or mutating state
  return Response.json({ ok: true });
}
```

Rules:

- Validate all input with Zod.
- Authenticate before reading protected data.
- Return consistent error shapes.
- For webhooks, verify signatures before processing.

### Server Actions

Server Actions are allowed for form mutations, not for complex hidden APIs.

```ts
"use server";

import { z } from "zod";
import { createWorkspace } from "@/server/services/workspaces";

const CreateWorkspaceInput = z.object({
  name: z.string().min(2).max(80),
});

export async function createWorkspaceAction(input: unknown) {
  const parsed = CreateWorkspaceInput.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Invalid input" } as const;
  }

  const workspace = await createWorkspace(parsed.data);
  return { ok: true, workspace } as const;
}
```

Rules:

- Validate input inside the action even if the form validates client-side.
- Return serializable objects.
- Do not expose stack traces to the client.

## Component patterns

### Presentational components

```tsx
type EmptyStateProps = {
  title: string;
  description: string;
  action?: React.ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <section className="rounded-lg border p-8 text-center">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </section>
  );
}
```

Rules:

- Props are typed with `type`, not `interface`, unless extending external types.
- Do not fetch data inside generic UI components.
- Keep class names readable. Extract repeated variants into helper functions.

### Client components

```tsx
"use client";

import { useState } from "react";

export function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
  }

  return <button onClick={onCopy}>{copied ? "Copied" : "Copy"}</button>;
}
```

Rules:

- Place Client Components at the smallest possible leaf.
- Pass data into Client Components as serializable props.
- Do not import server-only modules into Client Components.

## Auth and authorization

Rules:

- Authentication answers "who is this user?" Authorization answers "may they do this?" Keep both checks explicit.
- Protect every dashboard page at the layout or service layer.
- Check ownership or membership inside services before returning or mutating records.
- Never trust a `workspaceId`, `userId`, or `role` from the client without verifying it against the database.
- For admin features, require server-side role checks even if the UI hides admin links.

Service pattern:

```ts
export async function updateWorkspaceName(userId: string, workspaceId: string, name: string) {
  const membership = getMembership(userId, workspaceId);
  if (!membership || membership.role !== "owner") {
    throw new ForbiddenError("Only owners can rename a workspace");
  }

  return updateWorkspace(workspaceId, { name });
}
```

## Error handling

- Use typed domain errors in `lib/errors.ts`.
- Log unexpected server errors with enough context to debug, but never log secrets or full tokens.
- Show friendly user-facing messages.
- Do not catch errors just to rethrow them.
- Do not swallow failed writes.

Recommended domain errors:

```ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public status = 500,
  ) {
    super(message);
  }
}

export class ForbiddenError extends AppError {
  constructor(message = "Forbidden") {
    super(message, "FORBIDDEN", 403);
  }
}
```

## Testing rules

- Unit test pure services and query helpers with Vitest.
- Use a temporary SQLite database for tests. Never run tests against a developer's real database.
- Add Playwright smoke coverage for login, dashboard load, and one critical mutation.
- Every bug fix gets a regression test.
- Do not mock the database for query behavior; SQLite is cheap enough to run for real.

Example test database pattern:

```ts
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export function createTestDatabaseUrl() {
  const dir = mkdtempSync(join(tmpdir(), "saas-test-"));
  return join(dir, "test.db");
}
```

## Security rules

- Validate and normalize all external input with Zod.
- Escape or parameterize everything that reaches SQL.
- Verify webhook signatures before side effects.
- Use `httpOnly`, `secure`, and `sameSite` cookies for sessions.
- Do not put secrets in Client Components, logs, errors, or analytics.
- Do not use `dangerouslySetInnerHTML` unless sanitization is explicit and tested.
- Rate-limit auth, billing, invite, and webhook endpoints.

## Performance rules

- Avoid client-side fetching for initial dashboard data. Load it in Server Components.
- Add indexes before adding filters over large tables.
- Batch N+1 query loops into a single query.
- Use `revalidatePath` or `revalidateTag` after mutations that affect cached views.
- Keep expensive background work out of request/response paths.

## What we do not do

- Do not introduce Prisma by default. It adds migration and bundle complexity for simple SQLite apps. Use it only if the project already chose it.
- Do not put raw SQL in React components. It prevents reuse and testing.
- Do not add global state management for server data. Use Server Components and URL/search params first.
- Do not make every component a Client Component. That defeats App Router's main benefit.
- Do not silently edit old migrations after merge. Create a new migration.
- Do not add dependencies for small helpers that fit in 20 lines.
- Do not create custom auth crypto. Use boring, reviewed libraries.
- Do not store money as floating point. Use integer cents or provider-native amount fields.
- Do not ignore timezone handling. Store UTC; format in the user's locale at the edge/UI.

## Implementation checklist for Claude

Before changing code:

1. Read `package.json`, `next.config.*`, `tsconfig.json`, and existing `db/` files.
2. Identify whether the app uses `better-sqlite3`, Turso/libSQL, Drizzle, Kysely, or hand-written SQL.
3. Follow existing conventions unless they conflict with security or data-loss rules above.
4. If adding data, design the migration first.
5. If adding UI, decide which parts are Server Components and which tiny leaves need `'use client'`.

Before final response:

1. Run lint, typecheck, tests, and build.
2. Mention any command that was unavailable or failed.
3. Summarize changed files and risk areas.
4. Call out any migration or environment variable the human must apply.
