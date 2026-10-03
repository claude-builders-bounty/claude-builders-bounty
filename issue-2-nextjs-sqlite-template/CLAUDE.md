# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack and versions
- Next.js 15 App Router, TypeScript strict mode, React Server Components by default.
- SQLite through `better-sqlite3` for a single-node/local deployment, or Turso/libSQL when remote/multi-region access is required.
- Zod at every untrusted boundary.
- Server Actions for first-party mutations; Route Handlers only for public/webhook/API boundaries.
- Vitest for unit/integration tests; Playwright for critical user flows.

**Why:** one canonical stack reduces accidental client/server mixing and keeps database semantics explicit.

## Project structure
```
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  feature/
lib/
  db/
    schema.ts
    migrations/
    index.ts
  auth/
  validation/
  services/
tests/
```

Rules:
- `app/` owns routing and composition, not reusable business logic.
- `lib/services/` owns use-cases and transaction boundaries.
- `lib/db/` is the only place allowed to construct/import the database client.
- `components/ui/` contains dumb reusable UI; feature components may know feature DTOs but never the DB.

## Server/client boundary
- Default to Server Components. Add `"use client"` only for browser state, effects, event handlers, or browser-only APIs.
- Never import `lib/db/*`, secrets, filesystem modules, or privileged services into a Client Component.
- Add `import 'server-only'` in DB/auth/privileged service entrypoints.
- Pass serializable DTOs from server to client; never pass DB rows with implementation-specific objects.

**Why:** client boundaries are security boundaries, not styling choices.

## Database rules
- No ad-hoc SQL in pages/components/actions. SQL belongs in `lib/db/` repositories or focused service functions.
- Use prepared statements/placeholders for every dynamic value. Never string-concatenate user input into SQL.
- Keep transactions in service-layer use-cases so multi-step writes are atomic.
- Store timestamps as UTC ISO strings or integer epoch consistently; pick one and do not mix formats.
- Foreign keys must be enabled and enforced.
- Prefer explicit columns over `SELECT *` in application queries.

## Migrations
- Every schema change gets a new immutable migration file. Never edit an already-shipped migration.
- Naming: `YYYYMMDDHHMM_description.sql`.
- A migration must be deterministic, idempotence-aware where practical, and safe on existing data.
- Destructive changes require: backfill/move data first, application compatibility window second, removal last.
- Schema changes and the code that depends on them ship together.
- Never call schema-creation code from a request path.

**Why:** SQLite makes local experimentation easy; disciplined migrations prevent production drift.

## Turso/libSQL vs better-sqlite3
- Use `better-sqlite3` only in runtimes with a persistent local filesystem and a single writer model you understand.
- Use Turso/libSQL for serverless/edge/multi-region deployments.
- Do not pretend local SQLite files are durable on ephemeral serverless filesystems.
- Keep repository interfaces narrow enough that switching drivers does not leak into UI code.

## Data validation
- Validate `FormData`, JSON bodies, URL params, webhook payloads, env vars, and external API responses with Zod.
- Treat TypeScript types as compile-time only; they do not validate runtime input.
- Return field-level validation errors for user mistakes; log internal errors without leaking secrets or SQL details.

## Server Actions
- Server Actions must authenticate/authorize internally; UI visibility is not authorization.
- Validate input before touching the DB.
- Revalidate only the paths/tags affected by the mutation.
- Keep actions thin: parse -> authorize -> call service -> return typed result.

## Naming conventions
- Components: `PascalCase.tsx`.
- Functions/variables: `camelCase`.
- DB tables/columns: `snake_case`.
- Zod schemas: `<Thing>Schema`; inferred types: `<Thing>Input` / `<Thing>DTO`.
- Service functions use verbs: `createWorkspace`, `archiveProject`, `inviteMember`.

## Commands
Use the package manager already locked by the repo. Typical commands:
```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run test:e2e
npm run db:migrate
```
Before declaring work complete, run lint + typecheck + relevant tests. For schema changes, run migrations against a fresh DB and a copy of a populated fixture DB.

## Testing rules
- Unit-test pure validation and business rules.
- Integration-test repository/service code against a temporary SQLite DB.
- Every bug fix gets a regression test reproducing the prior failure.
- E2E-test only critical flows (sign-in, billing boundary, primary create/edit path); do not make E2E the only coverage.
- Tests must not depend on execution order or a developer's local database.

## Error handling and observability
- Expected domain failures return typed results/errors; unexpected failures are logged once at the boundary.
- Never expose stack traces, SQL, tokens, cookies, connection strings, or raw third-party errors to users.
- Include request/operation identifiers in logs where available.

## Security defaults
- Authorization is checked server-side on every mutation/read of protected data.
- Secrets stay in server-only modules and environment variables.
- Rate-limit public mutation/webhook endpoints where abuse is plausible.
- Verify webhook signatures before parsing business meaning.
- Do not log passwords, session tokens, authorization headers, or full payment payloads.

## Component patterns
- Prefer composition over giant configurable components.
- Keep fetching in Server Components/services, not `useEffect`, unless the data is truly browser-driven/live.
- Client components receive minimal DTOs and callbacks/actions, not entire ORM/database objects.
- Loading/error/empty states are part of the feature, not follow-up polish.

## What we do not do (and why)
- **No database imports in Client Components** — prevents secret/runtime leakage.
- **No SQL in UI files** — keeps persistence testable and replaceable.
- **No schema mutation at runtime** — avoids races and drift.
- **No `any` to silence type errors** — fix the contract or narrow `unknown`.
- **No blind `catch {}`** — swallowed failures make production debugging impossible.
- **No client-side authorization** — users control the client.
- **No local SQLite file on ephemeral serverless storage** — writes may disappear or diverge.
- **No premature generic repository framework** — start with feature-specific functions; abstract after repeated shape appears.
- **No mutation followed by full-page cache invalidation by default** — revalidate only affected data.
- **No new dependency for a trivial helper** — every dependency adds maintenance and supply-chain cost.

## Rule rationale ledger

- **Stack and versions:** one fixed baseline avoids framework/runtime ambiguity and lets Claude make changes without repeatedly asking which conventions apply.

- **Project structure:** routing, services, persistence, validation, and UI have distinct homes so code ownership is obvious and coupling stays low.

- **Server/client boundary:** privileged code stays server-only to prevent secrets, filesystem access, or DB behavior from leaking into browser bundles.

- **Database rules:** prepared statements, explicit columns, enforced foreign keys, and service-owned transactions preserve correctness and reduce injection/data-integrity risk.

- **Migrations:** immutable, staged migrations make schema history reproducible and protect existing production data during destructive changes.

- **Deployment driver choice:** better-sqlite3 assumes durable local storage; Turso/libSQL avoids pretending ephemeral serverless files are durable.

- **Runtime validation:** TypeScript disappears at runtime, so Zod guards every untrusted boundary before business logic or persistence.

- **Server Actions:** authentication, authorization, validation, and narrow invalidation belong inside the server mutation boundary because client visibility is never security.

- **Naming conventions:** predictable names make files, schemas, DTOs, and use-cases discoverable without extra project-specific explanation.

- **Commands and completion checks:** lint, typecheck, tests, and migration checks convert assumptions into executable proof before work is declared done.

- **Testing rules:** regression and integration coverage verify behavior closest to the risk while keeping slower E2E coverage focused on critical flows.

- **Error handling and observability:** typed expected failures plus boundary logging preserve debuggability without leaking sensitive internals.

- **Security defaults:** server-side authorization, secret isolation, rate limits, and webhook verification defend boundaries the client cannot be trusted to enforce.

- **Component patterns:** Server Components and composition minimize unnecessary client JavaScript and keep data access near trusted server code.

- **Anti-patterns:** every prohibited practice listed below corresponds to a concrete security, reliability, maintainability, or deployment failure mode stated inline.



## Change protocol for Claude Code
1. Read the closest existing implementation and tests before editing.
2. State the smallest coherent change; avoid unrelated refactors.
3. Preserve public behavior unless the task explicitly changes it.
4. Add/update tests with the implementation.
5. Run lint/typecheck/relevant tests and report exactly what ran.
6. If an expected tool/service is unavailable, say so; never claim a test you did not execute.

## Definition of done
- Requested behavior works.
- Authorization and runtime validation are present where required.
- Migration exists for schema changes.
- Regression coverage exists for fixes.
- Lint/typecheck/relevant tests pass, or the exact unrun check and reason is documented.
- No secrets, generated caches, or local DB files are committed.
