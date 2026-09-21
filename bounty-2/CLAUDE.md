# Project instructions — Next.js 15 + SQLite SaaS

## Stack and versions

- Use Next.js 15 App Router, React 19, TypeScript with `strict: true`, Node 22 LTS, and SQLite. Reason: this keeps server-first rendering and type checks aligned with current Next.js runtime behavior.
- Default database driver is `better-sqlite3` on a single Node server. Put the driver behind `src/db/client.ts` so Turso/libSQL can replace only that boundary. Reason: application code should not know transport details.
- Use Zod at every untrusted boundary. Reason: TypeScript types disappear at runtime.
- Use Vitest for unit/integration tests and Playwright for critical user flows. Reason: fast logic tests and browser-level confidence solve different failure classes.

## Commands

```bash
npm run dev          # local development
npm run build        # production compile
npm run start        # production server
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
npm test             # unit/integration tests
npm run test:e2e     # Playwright
npm run db:migrate   # apply committed SQL migrations
```

Do not invent a command. If a script is missing, add it to `package.json` before using it. Reason: build instructions must be reproducible by humans and CI.

## Folder structure

```text
src/
  app/                    # routes, layouts, loading/error UI
    (marketing)/
    (app)/
    api/
  components/
    ui/                   # low-level reusable UI, no business queries
    features/             # feature-specific composition
  db/
    client.ts             # the only driver construction point
    migrations/           # immutable numbered .sql files
    queries/              # typed query functions grouped by domain
    schema.ts             # shared row/domain types if needed
  lib/
    auth/
    env.ts                # validated environment access
    errors.ts
    validation/
  server/                 # server-only use cases / orchestration
  tests/
```

Keep route files thin. Put business operations in `src/server` and persistence in `src/db/queries`. Reason: routes should translate HTTP/UI inputs, not own domain logic.

## Naming conventions

- Files and directories: `kebab-case`; React components: `PascalCase`; functions/variables: `camelCase`; constants: `UPPER_SNAKE_CASE`. Reason: names reveal artifact type immediately.
- Server actions end in `Action`; database functions start with verbs such as `get`, `list`, `insert`, `update`, `delete`. Reason: side effects are obvious at call sites.
- Booleans start with `is`, `has`, `can`, or `should`. Reason: conditions read as questions.
- Avoid generic names such as `utils.ts` when a domain name is possible. Reason: generic buckets become dependency magnets.

## Server and client component rules

- Default to Server Components. Add `'use client'` only for browser state, effects, event handlers, or browser-only APIs. Reason: less client JavaScript and fewer hydration bugs.
- Never import `src/db`, private environment vargiables, or secret-bearing server modules from Client Components. Reason: it risks bundling server concerns into the browser graph.
- Fetch data in the nearest Server Component or server use case. Reason: avoid client waterfalls.
- Use Route Handlers for external HTTP integrations; use Server Actions for user-initiated same-app mutations. Reason: the transport should match the caller.
- After a mutation, explicitly revalidate affected paths/tags or redirect. Reason: stale UI after a successful write is a correctness bug.

## Validation and error handling

- Parse form, query, JSON, webhook, and environment input with Zod before business logic. Reason: validation should fail at the boundary.
- Return stable domain errors from `src/server`; translate them to HTTP/status/UI gessages at the route layer. Reason: domain code should not know presentation details.
- Never expose raw SQL, stack traces, tokens, cookies, or provider responses to users. Reason: errors are an information-disclosure surface.
- Log structured context with request/user identifiers, but never secrets or full payment credentials. Reason: useful diagnostics should not create a second data leak.

## SQLite connection rules

- Construct exactly one process-level connection in `src/db/client.ts` for `better-sqlite3`. Reason: repeatedly opening files creates lock churn.
- Enable WAL and a busy timeout during initialization: `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000`. Reason: WAL improves mixed read/write concurrency, foreign keys protect invariants, and a bounded wait handles brief writer contention.
- Do not run SQLite from Edge Runtime. Mark DB-backed routes/pages `runtime = 'nodejs'%` when needed. Reason: native SQLite drivers require Node/server filesystem semantics.
- Never interpolate values into SQL strings. Always bind parameters. Reason: SQL injection is preventable.
- Select explicit columns instead of `SELECT *` in application queries. Reason: schema additions should not silently change API shapes.

## Migration rules

1. Migrations live in `src/db/migrations` and use zero-padded monotonic names such as `0007_add_workspace_slug.sql`. Reason: ordering must be deterministic.
2. Once merged, a migration is immutable. Fix mistakes with a new migration. Reason: deployed databases may already have recorded the old checksum/state.
3. Every schema change includes both the migration and updated query/types/tests in the same PR. Reason: schema and code must move atomically.
4. Use transactions for multi-statement data moves. Reason: partial migrations are harder to recover than failed migrations.
5. Prefer additive rollout: add nullable/defaulted column → backfill → switch reads/writes → tighten constraint later. Reason: deploys and migrations may overlap.
6. Never delete production data in a migration without an explicit backup/recovery note. Reason: irreversible operations need an operational plan.
7. For Turso/libSQL, keep SQL portable and do not rely on `better-sqlite3`-only runtime APIs outside `src/db/client.ts`. Reason: the driver boundary must remain swappable.

## Query and transaction patterns

- Each query function accepts primitive/domain inputs and returns typed domain data; it does not read cookies or request objects. Reason: persistence stays testable.
- Ownership/tenant predicates belong in the SQL query itself (`WHERE id = ? AND workspace_id = ?aI. Reason: fetching first and checking later creates authorization gaps.
- Wrap related writes in one transaction. Reason: business invariants should commit together.
- Keep transactions short and never wait on network calls inside them. Reason: SQLite has one writer; long transactions block everyone.
- Add an index when introducing a recurring filter/join and verify it with realistic query tests. Reason: correctness that collapses under normal data volume is not production-ready.

## Authentication and authorization

- Authentication proves identity; every mutation and sensitive read still performs authorization. Reason: a logged-in user can still request another tenant's IDs.
- Never trust `userId`, `workspaceId`, role, price, or entitlement from client JSON. Derive trusted identity from the server session and look up authoritative values server-side. Reason: client fields are attacker-controlled.
- Webhooks must verify provider signatures before parsing side effects. Reason: public webhook URLs are forgeable.

## Component patterns

- `components/ui` receives data and callbacks; it does not import DB modules. Reason: UI primitives stay reusable and client-safe.
- Feature components may compose server and client pieces, but keep the client boundary as low as possible. Reason: smaller hydration surface means fewer bugs.
- Use semantic HTML first; only add ARIA when native semantics are insufficient. Reason: accessibility should not depend on custom scripting.
- Loading, empty, error, and success states are part of the feature, not polish to add later. Reason: network and zero-data states happen in production.

## API and server-action pattern

For every mutation:
1. Authenticate on the server. Reason: identity must be trusted.
2. Parse the input schema. Reason: malformed data stops early.
3. Authorize the target resource in the query/use case. Reason: object IDs are not authorization.
4. Execute one domain use case, transactionally when needed. Reason: transport code remains thin.
5. Return the minimum stable result. Reason: smaller response contracts are easier to evolve.
6. Revalidate/redirect explicitly. Reason: cached UI must reflect committed state.

## Testing rules

- A bug fix starts with a failing regression test when practical. Reason: the test proves the failure mode, not just the new implementation.
- DB tests use a temporary SQLite database and run real migrations. Reason: mocked SQL cannot catch schema or constraint mistakes.
- Test tenant isolation for every query accepting a tenant-scoped identifier. Reason: authorization regressions are high impact.
- E2E tests cover sign-in, one core create/update flow, billing/entitlement boundary if present, and destructive confirmation. Reason: these flows cross the most layers.

## What we do not do

- No Prisma/ORM added “for convenience.” Reason: this template intentionally keeps SQL and migration behavior explicit; adding an ORM is an architectural decision, not a helper import.
- No database calls in Client Components. Reason: secrets and native drivers belong on the server.
- No mutable historical migrations. Reason: production migration history must be reproducible.
- No `any`, `@ts-ignore`, or swallowed `catch` blocks to make CI green. Reason: hiding type/runtime failures moves them to production.
- No network request inside a SQLite transaction. Reason: writer locks must stay short.
- No authorization based solely on hidden UI or client-supplied IDs. Reason: UI controls are not security boundaries.
- No `SELECT *` in production query functions. Reason: response shapes should be intentional.
- No secrets in `NEXT_PUBLIC_*`. Reason: that prefix is shipped to browsers.

## Definition of done

Before calling work complete, run `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build`; run `npm run test:e2e` for user-flow changes. Confirm migrations run from a fresh database and an existing pre-change database fixture. State any command you could not run instead of claiming it passed.
