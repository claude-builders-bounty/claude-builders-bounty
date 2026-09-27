# CLAUDE.md

Guidance for Claude Code working in this repository. This is an opinionated,
**production-ready** setup for a **Next.js 15 (App Router) + SQLite** SaaS.
Every rule has a reason; follow them unless the user explicitly overrides.

> How to use this file: drop it at the repo root of a greenfield Next.js 15 +
> SQLite project. It is self-contained — Claude Code should be able to scaffold
> features, write migrations, and open PRs without asking clarifying questions.

---

## Stack & versions

- **Next.js 15**, App Router only (no `pages/`). **React 19** Server Components by default.
- **TypeScript**, `strict: true`. No `any` — use `unknown` + narrowing.
- **SQLite** via one of:
  - **better-sqlite3** — synchronous, single-node, fastest for a single server.
  - **Turso / libSQL** — hosted/edge, multi-region replicas.
  Pick **one per project**; never mix drivers. Default to better-sqlite3 unless
  the project needs edge/multi-region (then Turso).
- **Drizzle ORM** for schema + typed queries; **drizzle-kit** for migrations.
- **Tailwind CSS** for styling. **Zod** for validation. **Vitest** for tests.
- **Auth**: Lucia or Auth.js (session-based). Package manager: **pnpm** (lockfile committed).

Reason: pinning the stack keeps generated code consistent and stops Claude
guessing between App/Pages router, ORMs, drivers, or auth libraries.

---

## Dev commands

```bash
pnpm install            # install deps
pnpm dev                # dev server (localhost:3000)
pnpm build              # production build — MUST pass before any PR
pnpm lint               # eslint
pnpm typecheck          # tsc --noEmit
pnpm test               # vitest (unit + integration)
pnpm test:watch         # vitest watch mode
pnpm db:generate        # drizzle-kit generate — create migration from schema diff
pnpm db:migrate         # apply pending migrations
pnpm db:studio          # drizzle-studio (inspect data)
```

**Definition of done for any task:** `pnpm typecheck && pnpm lint && pnpm build && pnpm test`
all pass. Never declare a task complete without running these.

---

## Folder structure

```
app/                      # App Router routes (route groups in parentheses)
  (marketing)/            # public marketing pages
  (app)/                  # authenticated app (protected by middleware)
  api/
    webhooks/             # third-party callbacks ONLY (Stripe, etc.)
  layout.tsx, page.tsx, error.tsx, not-found.tsx
components/
  ui/                     # presentational, reusable, no data fetching
  <feature>/              # feature-specific components
lib/
  db/
    schema.ts             # Drizzle schema — SINGLE source of truth
    index.ts              # db client (singleton)
    migrations/           # generated SQL — NEVER hand-edit
  auth.ts                 # session helpers (getSession, requireUser)
  validation/             # zod schemas, one file per feature
  env.ts                  # zod-validated process.env (fail fast at boot)
server/
  actions/                # Server Actions ("use server"), one file per feature
  services/               # business logic, framework-agnostic, unit-tested
tests/
  unit/                   # services (no Next.js runtime)
  integration/            # actions + db (in-memory sqlite)
```

Reason: separating `server/services` (pure logic) from `server/actions`
(framework glue) makes business rules testable without booting Next.js, and
keeps the client bundle free of server code.

---

## Environment & config

Validate env at boot so a missing var fails fast, not at runtime in prod:

```ts
// lib/env.ts
import { z } from "zod";

const schema = z.object({
  DATABASE_URL: z.string().min(1),
  DATABASE_AUTH_TOKEN: z.string().optional(), // Turso only
  SESSION_SECRET: z.string().min(32),
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
});

export const env = schema.parse(process.env); // throws on boot if invalid
```

- Secrets live in `.env` (server only). **Never** `NEXT_PUBLIC_*` for anything secret —
  that prefix ships the value to the browser bundle.
- Import `env` from `lib/env.ts`; never read `process.env` directly elsewhere.

---

## SQL / migration conventions

- **Schema is the source of truth** (`lib/db/schema.ts`). Change schema → run
  `pnpm db:generate` → commit the generated migration. **Never hand-edit** files
  in `lib/db/migrations/` — it breaks drizzle's checksum tracking and desyncs envs.
- **Migrations are forward-only and reviewed.** For a destructive change
  (drop/rename column), write an **expand → migrate → contract** sequence across
  releases; never drop-and-recreate a populated table.
- **Never** run `DROP TABLE`, `TRUNCATE`, or `DELETE`/`UPDATE` without a `WHERE`
  against a real database.
- Naming: tables `snake_case` + plural (`users`, `api_keys`); TS fields `camelCase`
  (Drizzle maps them). Every table has `id`, `created_at`, `updated_at`.
- **Money as integer cents** (`integer`), never floats. **Timestamps stored UTC**
  as unix seconds or ISO text; convert at the display edge only.
- The db client is a **singleton** (`lib/db/index.ts`). Do not open a connection
  per request — better-sqlite3 is synchronous; one handle is correct and fastest.

Example schema (note the tenant scoping + indexes):

```ts
// lib/db/schema.ts
import { sqliteTable, text, integer, index, uniqueIndex } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),                 // UUID (crypto.randomUUID())
  email: text("email").notNull(),
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
}, (t) => ({
  emailIdx: uniqueIndex("users_email_idx").on(t.email),
}));

export const projects = sqliteTable("projects", {
  id: text("id").primaryKey(),
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
}, (t) => ({
  // Index the FK you filter by on every tenant-scoped query.
  userIdx: index("projects_user_id_idx").on(t.userId),
}));
```

Reason: migration-first prevents code/DB drift; expand-contract avoids downtime
and data loss; indexing the tenant FK keeps per-user queries fast as data grows.

### SQLite pragmas (better-sqlite3)

```ts
// lib/db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { env } from "@/lib/env";

const sqlite = new Database(env.DATABASE_URL);
sqlite.pragma("journal_mode = WAL");    // concurrent reads during writes
sqlite.pragma("foreign_keys = ON");     // enforce FK constraints (off by default!)
sqlite.pragma("busy_timeout = 5000");   // wait instead of throwing SQLITE_BUSY

export const db = drizzle(sqlite, { schema });
```

Reason: WAL enables concurrent reads; `foreign_keys` is **off by default** in
SQLite and must be turned on or `onDelete` cascades silently do nothing;
`busy_timeout` avoids spurious lock errors under load.

---

## Component & data patterns

- **Server Components by default.** Add `"use client"` only for state, effects, or
  browser APIs — and push it to the smallest leaf component.
- **Fetch data in Server Components / Server Actions**, never in client `useEffect`.
- **Mutations go through Server Actions**: validate input with Zod → check auth →
  call a `server/services` function → `revalidatePath`/`revalidateTag`.
- Route handlers (`app/api/*`) only for webhooks / third-party callbacks.

Canonical Server Action (copy this shape):

```ts
// server/actions/projects.ts
"use server";
import { z } from "zod";
import { requireUser } from "@/lib/auth";
import { createProject } from "@/server/services/projects";
import { revalidatePath } from "next/cache";

const Input = z.object({ name: z.string().min(1).max(80) });

export async function createProjectAction(formData: FormData) {
  const user = await requireUser();                 // 1. authenticate
  const parsed = Input.safeParse({ name: formData.get("name") }); // 2. validate
  if (!parsed.success) return { error: parsed.error.flatten() };
  const project = await createProject(user.id, parsed.data.name); // 3. service
  revalidatePath("/(app)/projects");                // 4. revalidate
  return { data: project };
}
```

Reason: this fixed order — auth → validate → service → revalidate — prevents the
two most common SaaS bugs: acting on unvalidated input, and IDOR (acting before
checking who the user is).

---

## Auth, security & multi-tenancy

- Session checks in `middleware.ts` **and** re-verified inside each Server Action
  (defence in depth). Never rely on the client to enforce access.
- **Every query is scoped by the authenticated user/tenant id.** Never accept a
  tenant/user id from the request body for authorization decisions:

```ts
// server/services/projects.ts — WRONG vs RIGHT
// WRONG: trusts client-supplied ownerId -> IDOR
// db.select().from(projects).where(eq(projects.userId, input.ownerId))
// RIGHT: use the authenticated user's id
export function listProjects(userId: string) {
  return db.select().from(projects).where(eq(projects.userId, userId));
}
```

- **No raw SQL string interpolation** — always parameterised Drizzle queries.
- Hash passwords with **argon2id** (or use a session library that does). Never
  store plaintext or fast hashes (md5/sha1).
- Rate-limit auth + mutation endpoints. Set secure cookies (`httpOnly`, `secure`,
  `sameSite: "lax"`).

Reason: tenant-scoping by the *authenticated* id is the single most effective
control against IDOR/broken-object-level-authorization, the #1 SaaS breach class.

---

## Error handling & observability

- Services throw typed domain errors; actions translate them into safe return
  values. **Never leak raw exception text / stack traces to the client** — log the
  detail server-side, return a generic message:

```ts
try {
  return { data: await doWork() };
} catch (e) {
  logger.error("createProject failed", { err: e });   // full detail server-side
  return { error: "Could not create project. Please try again." }; // generic to client
}
```

- Add `app/error.tsx` (route error boundary) and `app/not-found.tsx`.
- Log structured JSON with a request/user id; never `console.log` secrets or PII.

Reason: leaking exception text exposes stack traces, file paths, and query
internals — a recon gift to attackers.

---

## Testing strategy

- **Unit-test `server/services`** with an **in-memory SQLite** db (`:memory:`),
  migrated fresh per test file. No Next.js runtime needed → fast.
- **Integration-test Server Actions** by calling them directly with a stubbed
  session, asserting DB state and that auth/validation reject bad input.
- Every bug fix ships with a regression test. Coverage floor for `server/`: 80%.

```ts
// tests/unit/projects.test.ts
import { beforeEach, expect, test } from "vitest";
import { migrateTestDb, testDb } from "../helpers/db";

beforeEach(() => migrateTestDb());

test("listProjects only returns the caller's rows", async () => {
  // seed two users' projects, assert isolation
});
```

Reason: services-on-memory-db gives fast, deterministic tests of the business
rules that actually matter (auth scoping, validation), without flaky E2E.

---

## Performance

- Index every foreign key you filter by (see schema example). Verify with
  `EXPLAIN QUERY PLAN` — a `SCAN` on a hot query means a missing index.
- Avoid N+1: batch with a single `IN (...)` query or a join, not a loop of queries.
- Use `revalidateTag`/`revalidatePath` for cache invalidation; don't disable
  caching globally.
- Stream large lists with pagination (keyset pagination on `created_at,id`, not
  `OFFSET` for large tables).

---

## Git & PR workflow

- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- One logical change per PR. Include: what changed, why, and how it was tested.
- A PR is mergeable only if CI (`typecheck`, `lint`, `build`, `test`) is green and
  any schema change includes its generated migration.
- Never commit `.env`, `*.db`, `*.sqlite`, or `lib/db/migrations` edits by hand.

Suggested CI gate (`.github/workflows/ci.yml`):

```yaml
name: CI
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm lint
      - run: pnpm build
      - run: pnpm test
```

---

## What we DON'T do (and why)

- **No Pages Router / `getServerSideProps`** — App Router only; mixing confuses
  routing and data-fetching conventions.
- **No client-side fetching for first render** (`useEffect` + `fetch`) — causes
  waterfalls and leaks logic/secrets to the client.
- **No raw SQL string interpolation** — parameterised Drizzle queries only (SQLi).
- **No hand-edited migrations** — breaks drizzle checksums and desyncs environments.
- **No trusting client-supplied owner/tenant ids** for authorization — IDOR.
- **No leaking raw exceptions to the client** — log server-side, return generic.
- **No `any`, no non-null `!` to silence TS** — fix the type.
- **No floats for money, no local time stored** — integer cents + UTC only.
- **No `foreign_keys` left off** in SQLite — cascades silently no-op otherwise.
- **No new dependency without a reason** — prefer the stack above; pin versions.

Reason: these are the recurring ways SaaS codebases rot or get breached. Banning
them up front keeps Claude's output production-safe and consistent by default.
