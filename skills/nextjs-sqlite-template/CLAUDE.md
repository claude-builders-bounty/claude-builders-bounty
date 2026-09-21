# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Contract

- Build a TypeScript-strict Next.js 15 App Router application on the Node.js runtime with SQLite through `better-sqlite3`. **Reason:** one explicit stack prevents incompatible framework, runtime, and database assumptions.
- Prefer the smallest server-first change that satisfies the request. **Reason:** narrow changes reduce shipped JavaScript and regression risk.
- Before editing, inspect `package.json`, the nearest route/layout, schema, and latest migration. **Reason:** repository evidence must override assumptions.
- Never invent tables, environment variables, or commands. **Reason:** fabricated contracts make generated changes fail in a fresh checkout.

Every enforceable rule in this file carries an explicit **Reason** so an assistant can apply the intent when the exact example does not fit.

## Stack and versions

- Use Next.js 15 App Router, React 19, and TypeScript 5 in strict mode. **Reason:** pinning the major stack removes version ambiguity from generated APIs.
- Use the Node.js 20+ runtime for every database path (`export const runtime = "nodejs"`). **Reason:** native SQLite cannot run in Edge middleware or Edge route handlers.
- Use `better-sqlite3` with one process-local connection, and treat SQL migrations as the schema authority. **Reason:** a single connection avoids reload churn while one schema authority prevents drift.
- Validate every untrusted boundary with Zod; use Vitest for unit/integration tests and Playwright only for critical browser paths. **Reason:** boundary validation protects domain code while the test split keeps feedback fast.
- Use Server Components by default, adding `"use client"` only at the smallest interactive leaf. **Reason:** client boundaries increase shipped JavaScript and cannot import the database.

## Canonical structure

```text
app/
  (marketing)/page.tsx       # public Server Components
  (app)/dashboard/page.tsx   # authenticated Server Components
  api/<resource>/route.ts    # HTTP boundary only; no business logic
  layout.tsx
components/
  ui/                        # reusable presentational components
  <feature>/                 # feature-specific components
lib/
  db/index.ts                # singleton connection + pragmas
  db/queries/<resource>.ts   # typed prepared queries
  validation/<resource>.ts   # Zod input schemas
  services/<resource>.ts     # authorization + business rules
migrations/
  0001_initial.sql           # immutable, ordered, forward-only SQL
scripts/migrate.ts
tests/
  unit/  integration/  e2e/
data/                        # local DB files; gitignored
```

- Keep HTTP parsing in routes, authorization/business rules in services, and SQL in `lib/db/queries`. **Reason:** this separation lets tests exercise policy without starting Next.js and prevents database code from leaking into Client Components.

## Naming rules

- Name files/folders and route segments in `kebab-case`, React components and exported types in `PascalCase`, and functions/variables in `camelCase`. **Reason:** consistent casing makes symbol kind and filesystem location predictable.
- Name SQLite tables/columns/indexes in `snake_case`; use plural tables, `<singular>_id` foreign keys, and UTC ISO-text timestamps named `<event>_at`. **Reason:** one SQL vocabulary keeps migrations and queries easy to compare.
- Prefix boolean columns with `is_`/`has_`, indexes with `idx_<table>_<columns>`, and unique indexes with `uq_<table>_<columns>`. **Reason:** descriptive constraint names make failures searchable.
- Export verbs that state effects, such as `getUserById`, `listInvoices`, and `createInvoice`; avoid vague names such as `handle`, `process`, or `data`. **Reason:** call sites should reveal reads, writes, and returned concepts.

## Database connection

```ts
// lib/db/index.ts
import Database from "better-sqlite3";

const globalForDb = globalThis as unknown as { db?: Database.Database };
export const db = globalForDb.db ?? new Database(process.env.DATABASE_PATH ?? "data/app.db");
if (process.env.NODE_ENV !== "production") globalForDb.db = db;
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");
db.pragma("busy_timeout = 5000");
```

- Use prepared statements with bound parameters and explicit selected columns. **Reason:** binding prevents injection, and explicit columns make data exposure reviewable.
- Wrap multi-write invariants in transactions. **Reason:** partial writes corrupt application state.
- Keep the process-local singleton and the shown pragmas. **Reason:** the singleton avoids development-reload churn, WAL improves reader/writer coexistence, and SQLite foreign keys require per-connection enforcement.

## SQL and migration rules

1. Add one numbered migration for every schema change, and never edit a merged migration. **Reason:** deployed databases may already have applied the original bytes.
2. Keep migrations forward-only, deterministic, and transaction-safe; never read the network, current time, or application state from migration scripts. **Reason:** the same migration must produce the same schema in every environment.
3. For destructive changes, use expand/migrate/contract: add nullable structure, backfill observably, switch reads/writes, and remove old structure in a later release; explicitly recreate indexes, constraints, and triggers during SQLite table rebuilds. **Reason:** staged changes keep old and new application versions operable and preserve hidden schema objects.
4. Declare intentional `ON DELETE` behavior for every foreign key, index foreign keys and measured query predicates, and verify non-trivial queries with `EXPLAIN QUERY PLAN`. **Reason:** explicit referential and query behavior prevents accidental scans and orphan policy.
5. Record each migration filename and SHA-256 in `schema_migrations`, abort on an applied checksum change, and apply pending files lexically inside an exclusive transaction. **Reason:** checksum and ordering rules detect history edits and concurrent migration races.
6. Include migration, query/type updates, fresh-database proof, upgrade-from-previous proof, and rollback/restore notes in every SQL-changing PR; never migrate during a web request or production build. **Reason:** schema changes need reproducible evidence and a controlled operational boundary.

Example:

```sql
-- migrations/0002_create_projects.sql
CREATE TABLE projects (
  id INTEGER PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
  created_at TEXT NOT NULL
);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
```

## Request and component patterns

```ts
// app/api/projects/route.ts
import { NextResponse } from "next/server";
import { createProjectInput } from "@/lib/validation/project";
import { createProject } from "@/lib/services/project";
export const runtime = "nodejs";

export async function POST(request: Request) {
  const parsed = createProjectInput.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return NextResponse.json({ error: "invalid_request", issues: parsed.error.flatten() }, { status: 400 });
  const project = await createProject(parsed.data); // service performs auth/ownership checks
  return NextResponse.json({ project }, { status: 201 });
}
```

- Let Server Components call services directly instead of calling the app's own API over HTTP. **Reason:** an internal HTTP hop adds latency and duplicates authentication/error handling.
- Return stable error codes rather than stack traces; translate known conflicts to 409 and missing records to 404, while sending unexpected errors to centralized logging. **Reason:** clients need durable contracts without receiving implementation details.
- Treat `params`, cookies, headers, forms, JSON, webhooks, and environment variables as untrusted; validate before authorization and authorize before mutation. **Reason:** malformed input must not reach policy or state changes.
- Use Server Actions only for UI-coupled mutations, revalidate the narrowest tag/path after success, and redirect only after the transaction commits. **Reason:** narrow invalidation avoids stale UI without discarding unrelated caches, and commit-first navigation prevents false success.
- Make billing, webhook, and job-creation retries safe with unique constraints or idempotency keys. **Reason:** networks retry requests and duplicate writes can create charges or work twice.

## Commands

```bash
npm run dev                  # Reason: run the local Next.js server.
npm run lint                 # Reason: catch static defects before runtime.
npm run typecheck            # Reason: enforce the strict TypeScript contract.
npm test                     # Reason: exercise unit and integration behavior.
npm run test:e2e             # Reason: exercise only critical browser paths.
npm run db:migrate           # Reason: apply reviewed migrations explicitly.
npm run db:check             # Reason: prove fresh and previous-version databases.
npm run build                # Reason: verify production compilation.
```

- Use only commands present in `package.json`; add a script and document its dependency before relying on a missing command. **Reason:** template examples must not become fabricated project capabilities.

## Patterns to follow

- Return typed domain objects from query modules rather than raw `any` rows. **Reason:** schema drift should fail during development.
- Wrap related writes in `db.transaction`, assert affected-row counts, and test the failure path. **Reason:** partial writes corrupt SaaS invariants.
- Pass the database into services in tests. **Reason:** temporary per-test databases are deterministic and parallel-safe.
- Cache only explicitly public/read-mostly data; leave user-specific or mutable SQLite reads uncached and invalidate deliberately after writes. **Reason:** implicit caching can expose stale or cross-user state.
- Keep secrets server-only and fail startup clearly when required configuration is absent. **Reason:** missing configuration should stop safely rather than leak secrets or fail later.

## What we do not do (and why)

- **No database import in Client Components or Edge code. Reason:** native SQLite requires the Node runtime and server-only filesystem access.
- **No string-built SQL. Reason:** parameter binding prevents injection and preserves query-plan reuse.
- **No schema mutation with `db.exec` at startup. Reason:** concurrent instances race and unreviewed changes bypass migration evidence.
- **No automatic `SELECT *`. Reason:** explicit columns make data exposure and type changes reviewable.
- **No swallowed exceptions or success-shaped fallback data. Reason:** false success hides outages and can trigger duplicate writes.
- **No global `force-dynamic` or blanket `no-store`. Reason:** caching should be chosen per data boundary rather than disabled everywhere.
- **No SQLite file on ephemeral/serverless filesystems. Reason:** local writes disappear; self-host with a persistent volume or use Turso/libSQL behind the same query/service boundaries.
- **No Prisma/Drizzle beside direct SQL without an explicit migration-authority decision. Reason:** two schema authorities drift.

## Definition of done

- Require lint, typecheck, relevant tests, applicable migration checks, and `npm run build`; cover authorization and error paths; keep README/env examples accurate; and exclude generated databases, credentials, debug logs, and unrelated edits. **Reason:** completion means reproducible product evidence, not only plausible code.
- Report every check that could not run instead of replacing it with a readiness claim. **Reason:** unknown validation must remain visible to reviewers.
