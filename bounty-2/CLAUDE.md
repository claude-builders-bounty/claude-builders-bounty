# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the operating contract for this repository. Follow it before writing code. When a request is underspecified, use these defaults and proceed. Ask only when a choice changes product behavior, security, billing, or irreversible data handling.

## 1. Fixed stack and deployment contract

Use **Next.js 15 App Router**, React 19, TypeScript strict mode, Node.js 22 LTS, pnpm, Tailwind CSS, Zod, Drizzle ORM, `better-sqlite3`, Vitest, and Playwright.

Do not add Pages Router, another ORM, another package manager, or a client state library without an explicit product need. Prefer platform APIs and existing dependencies.

SQLite is a deployment choice, not a placeholder. Production must run as one application writer against one database file on persistent local/block storage. Do not put the database on an ephemeral filesystem, serverless function filesystem, or network share. Scale reads/capacity by upgrading the node or moving deliberately to a client/server database; do not run independent writers against copied files.

## 2. Repository structure

```text
src/
  app/
    (app)/                 # authenticated product routes
    (marketing)/           # public pages
    api/                   # external HTTP/webhook boundaries only
    layout.tsx
  components/
    ui/                    # reusable presentational primitives
  features/
    <feature>/
      actions.ts           # Server Actions
      authorization.ts
      components/
      mutations.ts
      queries.ts
      schemas.ts
      types.ts
  lib/
    env.ts
    errors.ts
    ids.ts
  server/
    auth/
    db/
      client.ts
      schema/
      migrations/
scripts/
  migrate.ts
  seed.ts
tests/
  e2e/
```

Routes compose features; they do not own business rules. `src/features/<feature>` owns feature behavior. `src/server` owns cross-feature server infrastructure. `src/components/ui` contains no database, auth, or product policy.

## 3. Naming and module rules

- Files and directories: `kebab-case`; React component files may match the exported component in `PascalCase.tsx`.
- React components and types: `PascalCase`.
- Functions, variables, and TypeScript fields: `camelCase`.
- SQL tables/columns: plural `snake_case`; map them explicitly to camelCase in Drizzle.
- Server Actions: verb first (`createProject`, `archiveWorkspace`).
- Queries: `get`, `list`, or `find` first. Mutations: domain verb first.
- Zod schemas: `<operation>Schema`. Result types: `<Operation>Result`.
- One default export only where Next.js requires it; use named exports elsewhere.
- Import through `@/`; do not create barrel files that hide server/client boundaries.
- Add `import "server-only"` to database, secret, authorization, query, and mutation modules.
- No `any`, non-null assertion, or `@ts-ignore` without a local explanation and a narrower boundary.

## 4. App Router and server/client boundaries

Server Components are the default. Fetch directly in Server Components through feature queries. Do not call an internal Route Handler from server code; that adds latency and duplicates an in-process call.

Use Client Components only for browser APIs, event handlers, or local interactive state. Put `"use client"` at the smallest leaf possible. Pass only serializable props across the boundary; never pass database clients, class instances, functions, secrets, or raw errors.

Use Route Handlers for public APIs, webhooks, downloads, or protocols that require HTTP. Use Server Actions for first-party UI mutations. Any route that touches SQLite must export:

```ts
export const runtime = "nodejs";
```

Never import the database from Edge middleware. Middleware may make cheap routing decisions from signed session metadata, but authoritative authorization belongs beside the protected read or write.

## 5. Reads, writes, caching, and forms

A feature query returns a deliberate view model, not a raw row dump. Select only needed columns, use explicit `orderBy`, avoid N+1 reads, and include tenant scope in SQL.

A Server Action must, in order:

1. load the session;
2. parse untrusted input with a named Zod schema;
3. authorize the actor for the resource;
4. execute a tenant-scoped mutation;
5. return a serializable typed result for expected errors;
6. invalidate only the affected tag/path.

Use `useActionState` for action forms and `useFormStatus` in a nested submit control. Render field errors beside fields and provide an accessible summary. Use URL search parameters for shareable filters, sort, pagination, and selected tabs; local React state is for transient UI only.

Authenticated or tenant-specific data is dynamic unless a cache key explicitly contains every authorization-relevant dimension. Use narrow tags such as `workspace:<id>:projects`. Never cache secrets, session objects, permission checks, or mutable billing state. Never call `revalidatePath("/")` after a local mutation.

## 6. Database contract

Create one process-level connection in `src/server/db/client.ts`. Configure at startup:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

Do not open a connection per request. Do not share one connection across processes through a network filesystem.

Database rules:

- Primary keys are text CUID2 values generated before insert.
- Foreign keys are `<entity>_id` and indexed when used for joins/filtering.
- Money is integer minor units, e.g. `amount_cents`; never floating point.
- Timestamps are UTC integer milliseconds and formatted at the UI boundary.
- Required values use `NOT NULL` plus a database default where appropriate.
- JSON is for opaque/non-relational payloads only and must be Zod-validated after decoding.
- Use parameterized Drizzle queries; never interpolate user input into SQL.
- Transactions contain database work only. Never call email, storage, or external APIs while holding a SQLite write lock.
- Record an outbox item in the same transaction for external side effects.

Every tenant-owned table carries `workspace_id` (or the chosen tenant key). Every tenant-owned read, update, and delete includes that key in the SQL predicate even after authorization succeeds. This prevents an ID mix-up from becoming cross-tenant access.

## 7. Migration rules

Every schema change is a reviewed, committed, forward migration.

1. Edit the Drizzle schema.
2. Run `pnpm db:generate`.
3. Read the generated SQL line by line.
4. Add bounded backfill or compatibility SQL when needed.
5. Commit schema and migration together.
6. Apply with `pnpm db:migrate` during release before serving code that depends on it.

Never use `drizzle-kit push` in production. Never edit, reorder, rename, or delete a migration that may have run. Add a new migration.

For a required column on populated data: add it nullable or with a safe default, backfill in bounded work, then enforce the constraint. For rename/drop: use expand-and-contract across releases so old and new code overlap safely. Back up the database before destructive/table-rebuild migrations and describe restore/rollback in the PR. Treat SQLite table rebuilds as potentially locking operations. Keep migrations deterministic and free of application-time values.

## 8. Validation, errors, and results

Parse environment variables once in `src/lib/env.ts` with Zod. Do not scatter `process.env` reads.

Validate every untrusted boundary: forms, URL parameters, cookies, headers, webhooks, API bodies, and decoded JSON. Expected validation/auth/conflict failures return a typed serializable result:

```ts
export type ActionResult<T> =
  | { ok: true; data: T }
  | {
      ok: false;
      code: "VALIDATION" | "UNAUTHORIZED" | "FORBIDDEN" | "CONFLICT";
      message: string;
      fieldErrors?: Record<string, string[]>;
    };
```

Throw unexpected infrastructure/programmer errors so error boundaries and observability capture them. Never send stack traces, raw database errors, provider errors, or secrets to the client. Log an operation name and correlation ID, not tokens, cookies, full webhook bodies, or personal data.

## 9. Authentication and authorization

Session presence is authentication, not authorization. Centralize session loading under `src/server/auth`. Put resource authorization near the relevant query/mutation and recheck it inside every mutation. Never trust hidden fields, disabled buttons, middleware redirects, or client state as authorization.

Use secure, HTTP-only, same-site cookies. Never expose session tokens through `NEXT_PUBLIC_*`. Hash one-time tokens at rest and compare in constant time. Verify webhook signatures against the raw request body before parsing or mutating data. Rate-limit login, invite, reset, and expensive public endpoints.

Authorize before revealing whether a protected resource exists when existence itself is sensitive.

## 10. Environment and secrets

Local convention:

```dotenv
DATABASE_URL=file:./data/app.db
APP_URL=http://localhost:3000
SESSION_SECRET=replace-with-at-least-32-random-bytes
```

Commit `.env.example`; never commit `.env`, database/WAL/SHM files, credentials, exports, or production data. Prefix with `NEXT_PUBLIC_` only when intentionally public. Keep development and test databases at separate paths.

## 11. Required package scripts

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
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:studio": "drizzle-kit studio",
    "db:seed": "tsx scripts/seed.ts"
  }
}
```

Keep these names stable. Update this file and the README when a command changes.

## 12. Development commands

Run from the repository root:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

Apply pending migrations before schema-dependent development. Run only checks relevant to the touched behavior unless CI requires more.

## 13. Approved patterns

Tenant-scoped query:

```ts
import "server-only";
import { and, eq } from "drizzle-orm";
import { db } from "@/server/db/client";
import { projects } from "@/server/db/schema/projects";

export function getProject(input: { projectId: string; workspaceId: string }) {
  return db.query.projects.findFirst({
    columns: { id: true, name: true, updatedAt: true },
    where: and(
      eq(projects.id, input.projectId),
      eq(projects.workspaceId, input.workspaceId),
    ),
  });
}
```

Server Action shape:

```ts
"use server";

export async function renameProject(rawInput: unknown): Promise<ActionResult<{
  projectId: string;
}>> {
  const session = await requireSession();
  const parsed = renameProjectSchema.safeParse(rawInput);
  if (!parsed.success) return validationResult(parsed.error);

  const result = await updateProjectName({
    actorUserId: session.user.id,
    ...parsed.data,
  });
  if (!result.ok) return result;

  revalidateTag(`workspace:${result.data.workspaceId}:projects`);
  return { ok: true, data: { projectId: parsed.data.projectId } };
}
```

The mutation owns resource authorization and uses both resource ID and tenant ID in its SQL predicate.

## 14. Rejected anti-patterns and reasons

| Do not | Reason |
|---|---|
| Add `src/pages` | Two routing models duplicate conventions and data flow. |
| Mark a page `"use client"` for one button | It expands the client bundle and risks server-only imports; isolate the button. |
| Fetch an internal Route Handler from a Server Component | It adds latency and duplicates an in-process call. |
| Import `db` in client code or Edge middleware | It crosses runtime/security boundaries. |
| Read `process.env` outside `env.ts` | It bypasses startup validation and hides dependencies. |
| Concatenate SQL strings | It creates injection risk; use parameters. |
| Use production schema push | It removes reviewed, repeatable migration history. |
| Edit an applied migration | Environments then disagree under the same migration ID. |
| Store money as float | Binary floats cannot represent many decimal amounts exactly. |
| Put business logic in `page.tsx` or a route | It becomes hard to reuse, authorize, and maintain. |
| Authorize only in middleware/UI | Direct requests bypass presentation controls. |
| Call external APIs inside a transaction | Network latency holds the SQLite write lock. |
| Deploy SQLite on ephemeral storage | Restarts can erase the database. |
| Run independent writers against one file | Locking/filesystem semantics make correctness deployment-dependent. |
| Load ordinary server data with `useEffect` | Server Components avoid a client waterfall. |
| Invalidate the whole site after a write | It destroys cache locality and causes avoidable load. |
| Log tokens, cookies, webhook bodies, or PII | Logs are broad, durable data exposure. |
| Add a dependency before checking platform APIs | Dependencies add security, upgrade, and bundle cost. |

## 15. Change workflow for Claude Code

For each request:

1. Read this file, `package.json`, relevant route/feature modules, and schema.
2. Infer routine defaults from this contract and existing code; do not ask permission to follow established patterns.
3. State one sentence of implementation intent, then make the complete change.
4. Keep the diff inside the owning feature plus genuinely shared infrastructure.
5. Add a forward migration when the schema changes.
6. Update user-facing docs when behavior/setup changes.
7. Report changed files, delivered behavior, and any real product decision still requiring an owner.

Do not return a feasibility essay when the behavior is implementable. Do not leave required behavior as a TODO, stub, placeholder, or speculative framework.

## 16. Definition of done

A change is complete only when server/client and feature boundaries are preserved; untrusted input is validated; protected resources are authorized; tenant SQL is scoped; schema changes include a forward migration and deployment note; expected errors are useful without leaking internals; accessibility and loading/error states are handled for changed UI; docs match commands/environment requirements; and no secrets, database files, generated local artifacts, unrelated refactors, or TODO substitutes are included.

When tradeoffs remain, prefer explicitness, data safety, and a narrow reversible change over cleverness.
