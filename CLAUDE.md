# CLAUDE.md — Next.js 15 + SQLite SaaS

## Role and non-negotiable invariants
You maintain a **single-tenant-by-default**, server-rendered Next.js 15 App Router SaaS using TypeScript strict mode, SQLite and Drizzle ORM. If the project is multi-tenant, **every query for tenant-owned data must include the authenticated tenant ID**, not an ID supplied by the browser. Prefer small, reviewable changes, one focused migration per schema change, and measurable tests. Never infer permissions from a client-provided role.

## Stack and versions
- Node.js **22 LTS**, npm, Next.js **15.x**, React **19.x**, TypeScript **5.x** with `strict: true`.
- `drizzle-orm` + `drizzle-kit` for typed SQL migrations. Use **one** driver: `better-sqlite3` for a persistent Node process **or** `@libsql/client` for a remotely hosted Turso-compatible database. Do not mix dialects or adapters.
- `zod` for boundary validation; `vitest` for pure logic/database tests; `@playwright/test` for critical user flows.
- Pin major versions. Before adding packages check that they support Node 22, Next 15 and the selected SQLite runtime.
- SQLite writes require the Node.js runtime. No Edge route may import the database adapter.

## Expected structure (create missing folders, not fake placeholders)
```text
src/
  app/
    (auth)/login/page.tsx
    (dashboard)/layout.tsx
    (dashboard)/projects/page.tsx
    api/health/route.ts
    globals.css
    layout.tsx
  components/
    ui/                         # reusable presentational pieces
    projects/                   # domain-specific components
  db/
    client.ts                   # SERVER ONLY: creates the single DB connection
    schema.ts                   # Drizzle tables, indexes and relations
    migrations/                 # generated, committed SQL + Drizzle metadata
  features/
    projects/
      queries.ts                # reads scoped to authenticated principal
      mutations.ts              # validated writes + authorization
      validation.ts             # Zod schemas
      queries.test.ts
  lib/
    auth.ts                     # server-side session lookup
    env.ts                      # validates environment at startup
e2e/
drizzle.config.ts
.env.example
```

## Naming and boundaries
- Files: `kebab-case.ts`; React components/types: `PascalCase`; values/functions: `camelCase`; DB tables/columns: `snake_case` for ease of raw SQL inspection.
- Place each feature's validation, read and write functions together. Pages orchestrate data fetching and render UI; they do **not** contain SQL.
- Mark modules importing `src/db/client.ts`, credentials or sessions with `import 'server-only'`. Import such modules exclusively from Server Components, Server Actions or Node route handlers.
- Server Components are the default. Only add `'use client'` to the smallest leaf needing events, browser APIs or local state, to avoid needless JS and accidental secret bundling.
- Never send DB rows with secrets directly into Client Components. Map to explicit response DTOs.

## Authentication and authorization
- On every server mutation or sensitive read, call `requireSession()` **inside that operation**, not merely in a parent layout. Layout navigation can be stale.
- Validate inputs with Zod on the server even if the form validates in-browser.
- Authorize the resource and tenant in the same WHERE clause as the update/delete; check affected row count to fail closed. Do not fetch by public ID and then update without tenant scope.
- Error responses are stable generic messages. Log internal context server-side, but never passwords, sessions, tokens, or raw SQL parameters containing personal data.

## Database and migration policy
1. Change `src/db/schema.ts` first, including unique constraints, foreign keys and indexes for filter/join keys.
2. Generate a versioned migration: `npm run db:generate` (mapped to `drizzle-kit generate`), inspect the SQL, and commit migration + metadata with schema in one PR.
3. Apply with `npm run db:migrate` (mapped to `drizzle-kit migrate`) on a **disposable development database**; test both fresh DB creation and upgrade of a pre-change seeded DB.
4. Take a verified backup before production migrations. Never use `drizzle-kit push` in production: it bypasses reviewed, versioned SQL.
5. SQLite: enable `PRAGMA foreign_keys = ON` per connection; use `PRAGMA journal_mode = WAL` on locally managed file databases and set a nonzero busy timeout. Never assume WAL settings apply to Turso.
6. Group related writes in one transaction; handle unique-conflict errors as user-level validation failures. Keep transactions short; no network calls or AI provider requests while a transaction is open.
7. SQLite has limited ALTER TABLE support. For destructive migrations use a reviewed table-copy migration with explicit data verification and reversible backup, rather than dropping columns casually.
8. Never edit a migration already applied to a shared environment; create a follow-up migration.

## Server actions, routes and components
- Use Server Actions for first-party form mutations, and route handlers for webhooks or external clients. In both, check authentication, authorization, input size and Zod parsing.
- Verify webhook signatures using raw request bytes before JSON parsing, then enforce idempotency by provider event ID stored under a unique DB index.
- After a successful mutation, call `revalidatePath` or `revalidateTag` for affected views. Avoid `cache: 'force-cache'` for user-private data.
- Use `loading.tsx` and `error.tsx` where latency/failures matter; do not swallow database errors and show a success toast.
- Use semantic HTML, labelled inputs, keyboard-operable controls and server-rendered meaningful empty/error states.

## Standard commands
Define these aliases in `package.json` when bootstrapping a new project; do not pretend a command exists before checking:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate"
  }
}
```
**Next.js 15 caveat:** `next lint` is available in Next 15 but may be removed in newer Next versions. Keep the version pinned; migrate to explicit `eslint .` when upgrading.

Daily sequence: `npm ci` → `npm run db:migrate` (local disposable DB) → `npm run dev`. Before PR: `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`; run `npm run test:e2e` for changed user journeys. Report commands you actually executed and any blockers.

## Definition of done
- [ ] New behaviour covered by a failing-then-passing unit or integration test; user-facing change also has a browser smoke test.
- [ ] Session and tenant boundaries tested with a second account: no cross-tenant reads/writes.
- [ ] Schema changes ship reviewed, immutable migration SQL and a fresh/upgrade migration test.
- [ ] No personal or sensitive fields in logs, client bundles, test fixtures or snapshots.
- [ ] Typecheck, lint, unit tests, production build pass. Documentation and `.env.example` updated where relevant.

## Anti-patterns (and reasons)
- **No `'use client'` on entire pages/layouts:** multiplies shipped JS and encourages privileged logic in the browser.
- **No global mutable auth/tenant context:** concurrent requests can leak identities. Pass the authenticated principal explicitly.
- **No raw string-concatenated SQL:** injection risk; use Drizzle placeholders or bound prepared statements.
- **No write-then-check authorization:** unauthorized changes are already committed. Scope mutation queries first.
- **No schema auto-sync at app startup:** surprise destructive changes and multiple replica races. Run migrations as an explicit deploy step.
- **No in-memory production SQLite on serverless functions:** data does not persist or coordinate across instances. Use Turso or a durable single Node host.
- **No secrets with `NEXT_PUBLIC_`:** Next embeds them in browser bundles.
- **No broad catches returning empty arrays:** hides incidents as 'no data'. Log safe diagnostics and render an error.
- **No full test-suite claims based on targeted tests:** include exact commands and results in the PR.

## First response for any feature request
Identify the target route, feature files, database tables, auth boundary and tests. If the task specifies them, **begin implementation without clarification**. Ask only for genuinely missing product decisions. At completion describe changed files, migration strategy, tests run and any unverified behaviour.
