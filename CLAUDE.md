# CLAUDE.md

## Mission
Build and maintain a production SaaS on Next.js 15 App Router with SQLite. Prefer explicit, boring, testable code over clever abstractions. Every change must keep the app runnable, migrations reproducible, and server/client boundaries obvious.

## Greenfield defaults (no clarification needed)
- In a new project, use npm, TypeScript, App Router, and the Node.js runtime. Default to `better-sqlite3` and a local `data/app.db`; a single explicit default avoids asking the user to choose an adapter before useful work can begin.
- If the repository already uses Turso/libSQL, keep that adapter. Existing deployed data and configuration take precedence over greenfield defaults.
- Honor an existing `src/` directory: the structure below is relative to `src/` when present. Keep migrations and tests at the repository root. This makes the template work with either create-next-app layout without editing it.
- Read package.json and the lockfile before running commands. Do not claim a check passed when its script is absent; add the smallest appropriate check as part of implementation and state what remains unverified.
- Never ask for a production secret to understand this template. Local development uses disposable data; production authentication, billing, and deployment require explicit project configuration.

## Stack and versions
- Next.js 15 with App Router and React Server Components by default.
- TypeScript in strict mode; do not introduce `any` to bypass type errors.
- SQLite defaults to `better-sqlite3` on the Node.js runtime; preserve Turso/libSQL when already configured. Do not mix adapters or use native `better-sqlite3` in an Edge runtime, because their execution and connection models differ.
- Validation at trust boundaries with a schema library such as Zod.
- Package scripts are the source of truth for dev, test, lint, typecheck, migration, and build commands.

Reason: a small fixed stack reduces hidden runtime differences and makes local reproduction match production.

## Project structure
```
app/
  (public)/          # public routes
  (app)/             # authenticated product routes
  api/               # Route Handlers only when an HTTP boundary is required
components/
  ui/                # reusable presentational components
  features/          # feature-level composed components
lib/
  db/
    index.ts          # one database entry point
    schema.ts         # typed schema definitions
    queries/          # domain-specific queries
  actions/            # Server Actions
  auth/
  validation/
migrations/           # immutable numbered SQL migrations
tests/
```

Rules:
- Route-specific code stays beside its route until it is reused.
- Shared business logic belongs in `lib/`, not React components.
- Database access never lives in client components.
- Use `@/` imports for cross-folder imports; relative imports are for nearby files only.

Reason: ownership stays visible and server-only code cannot drift into browser bundles.

## Naming conventions
- React components and exported types: `PascalCase`.
- Functions and variables use `camelCase`; utility filenames use `kebab-case.ts`. This removes ambiguous naming choices.
- Server Actions use verb-first names: `createWorkspace`, `updateProfile`.
- Database tables are plural `snake_case`; columns are `snake_case`.
- Booleans start with `is`, `has`, `can`, or `should`.
- Environment variables are `SCREAMING_SNAKE_CASE`.

Reason: names should reveal layer and intent without opening the file.

## Server and client boundaries
- Start with Server Components. Add `"use client"` only for browser APIs, local interactive state, effects, or event handlers.
- Keep client component props serializable.
- Read secrets and the database only on the server.
- Use Server Actions for authenticated mutations originating in the app UI.
- Use Route Handlers for webhooks, public APIs, callbacks, downloads, or non-React clients.
- Revalidate the smallest affected path/tag after mutations.

Reason: minimizing client JavaScript improves security, startup cost, and data consistency.

## Database rules
- Export one database singleton/factory from `lib/db/index.ts`.
- Use parameterized queries only. Never concatenate user input into SQL.
- Wrap multi-step writes that must succeed together in a transaction.
- Add indexes for foreign keys and measured hot lookup paths, not speculatively.
- Store timestamps in UTC ISO-8601 or integer epoch consistently.
- Enforce important invariants with database constraints in addition to application validation.

Reason: SQLite is reliable when writes and invariants are explicit.

## SQL and migration conventions
- Every schema change gets a new numbered migration such as `0007_add_workspace_slug.sql`.
- Applied migrations are immutable. Fix a bad migration with a new migration.
- Each migration must be safe on the expected previous schema and include both schema changes and required data backfill.
- Never run destructive schema changes implicitly during application startup.
- Before merging a migration: apply all migrations to an empty database and to a copy at the previous schema version.
- Prefer additive evolution: add nullable/defaulted column, backfill, switch code, then tighten constraints/remove legacy fields in a later release.
- Turso/libSQL production migrations run through the documented deployment path; `better-sqlite3` migrations run before the new app process receives traffic.

Reason: reproducible migrations are the recovery plan for persistent data.

## Validation and errors
- Validate form, URL, webhook, and API input at the boundary.
- Return field-level validation errors for user-correctable input.
- Log unexpected server errors with a request/correlation identifier, never secrets.
- Do not expose raw SQL, stack traces, tokens, or internal identifiers to clients.
- Treat missing records and unauthorized records as separate cases internally.

Reason: predictable error contracts prevent accidental information leaks.

## Component patterns
- UI primitives are stateless where practical and accept semantic props.
- Feature components compose primitives; they do not reach directly into the database.
- Forms use progressive enhancement: server mutation works without client-side orchestration, while client code may improve pending/error UX.
- Avoid global state for server-owned data. Fetch it on the server and pass only what the interactive leaf needs.
- Accessibility is part of done: labels, keyboard operation, focus states, semantic elements, and useful error text.

Reason: components remain portable and behavior stays testable.

## Authentication and authorization
- Authentication proves identity; authorization is checked again at each server mutation/query boundary.
- Never trust tenant/workspace IDs received from the browser without checking membership.
- Session-derived user IDs override client-supplied ownership fields.
- Keep admin-only operations behind server-side role checks, not hidden buttons.

Reason: UI visibility is not an authorization boundary.

## Dev commands
Inspect the scripts that actually exist before running them (`npm run`). The following are target names, not a claim that create-next-app supplies all of them. On a new project, add missing scripts as their implementation is introduced; never run a nonexistent script or silently omit a required check:
```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:check
npm run build
```

For TypeScript, `typecheck` should run `tsc --noEmit`. Use the installed linter and test runner rather than assuming one is available. Implement `db:migrate` and `db:check` with the selected adapter before claiming database readiness. Do not point tests or migration checks at production data.

Before a PR is ready, run lint, typecheck, tests, migration checks when schema changed, and production build; report any unavailable check explicitly.

## Change workflow
1. Read the nearest route, feature, query, and tests before editing.
2. State the smallest behavior change and its trust boundaries.
3. Change the minimum files needed.
4. Add or update a regression test for behavior changes.
5. Run focused tests, then typecheck/lint/build as appropriate.
6. For DB changes, add a migration and verify empty + upgrade paths.
7. Summarize what changed, validation run, and any remaining risk.

## Patterns to follow
- Thin Route Handlers and Server Actions calling typed domain/query functions.
- Transactions for related writes.
- Explicit cache/revalidation decisions.
- Schema validation at external boundaries.
- Small components with clear server/client ownership.
- Tests that assert behavior, permissions, and failure cases.

## What we do not do (and why)
- No SQL string interpolation — it creates injection risk.
- No database calls from client components — secrets and authorization belong on the server.
- No `useEffect` for initial server data fetching — Server Components already solve it with less client code.
- No giant `utils.ts` or catch-all service layer — domain ownership becomes unclear.
- No editing previously applied migrations — deployed databases would diverge.
- No `any`, ignored TypeScript errors, or disabled lint rules as a shortcut — defects move to runtime.
- No secrets in `NEXT_PUBLIC_*`, logs, fixtures, or committed `.env` files.
- No destructive production data command in a normal app startup path.
- No premature abstraction: duplicate a small pattern twice before extracting a shared layer.

## Definition of done
A change is done when behavior is implemented, authorization is enforced server-side, relevant tests pass, migrations are reproducible, typecheck/lint are clean, production build succeeds, and the implementation can be understood without undocumented assumptions.
