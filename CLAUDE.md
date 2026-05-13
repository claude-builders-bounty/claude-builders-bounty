# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the default working agreement for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and server-first React.

## Stack & versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in `strict` mode.
- SQLite for the primary relational store.
- Use `better-sqlite3` for a single-process Node runtime, or Turso/libSQL when deployment needs a remote SQLite-compatible database.
- Auth, billing, and email are integration boundaries: wrap vendors behind local service modules so they can be replaced.

Reason: this stack is simple enough to ship quickly while still giving strong data ownership, transactional writes, and low operational cost.

## Folder structure

```text
app/
  (marketing)/
    page.tsx
    pricing/page.tsx
  (app)/
    dashboard/page.tsx
    settings/page.tsx
  api/
    webhooks/stripe/route.ts
components/
  ui/                 # generic reusable UI only
  forms/              # form components with validation wiring
  marketing/          # landing/pricing sections
features/
  accounts/
    actions.ts        # server actions for this feature
    queries.ts        # read helpers
    schema.ts         # zod/domain validation
    components/
  billing/
  projects/
db/
  index.ts            # DB connection singleton
  migrations/
  schema.sql          # canonical current schema snapshot
  migrate.ts
lib/
  auth.ts
  env.ts
  errors.ts
  ids.ts
  logger.ts
  routes.ts
services/
  email.ts
  payments.ts
  storage.ts
tests/
  unit/
  integration/
```

Rules:
- Keep route files thin. They should call feature functions, not contain business logic.
- Put domain logic under `features/<domain>/` because SaaS products grow by domain, not by framework primitive.
- Use `components/ui` only for generic presentational pieces. Anything that knows about billing, users, or projects belongs in a feature folder.

## Naming conventions

- Files: kebab-case for components and utilities, e.g. `project-card.tsx`.
- React components: PascalCase exports, e.g. `ProjectCard`.
- Server actions: verb phrases ending in `Action`, e.g. `createProjectAction`.
- Query helpers: `getProjectById`, `listProjectsForUser`.
- Database tables: snake_case plural nouns, e.g. `projects`, `team_members`.
- IDs: use stable text IDs (`usr_`, `team_`, `proj_`) instead of exposing autoincrement IDs.

Reason: predictable names reduce search time and avoid mixing UI language with persistence language.

## Environment configuration

Create `lib/env.ts` as the only place that reads `process.env`.

- Validate env vars at startup with Zod or a small explicit parser.
- Never read `process.env` directly inside feature code.
- Keep client-exposed env vars prefixed with `NEXT_PUBLIC_` and treat them as public.

Reason: central validation prevents half-configured deploys and keeps secrets out of client bundles.

## SQL / migration conventions

- Every schema change gets a timestamped migration file:
  - `db/migrations/202605130900_create_projects.sql`
- Migrations must be append-only after merge. Never edit an already-applied migration; add a new one.
- Each migration should be idempotent when practical, but do not hide destructive changes.
- Keep `db/schema.sql` updated as the readable snapshot of current schema.
- Enable foreign keys on every connection: `PRAGMA foreign_keys = ON`.
- Use transactions for multi-step writes.
- Prefer explicit columns over `SELECT *` in app queries.

Reason: SQLite is reliable when schema history is boring, explicit, and reproducible.

### Table pattern

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(owner_user_id, slug)
);

CREATE INDEX idx_projects_owner_user_id ON projects(owner_user_id);
```

Rules:
- Store timestamps as ISO-compatible UTC text unless there is a strong reason not to.
- Add indexes for every foreign key and common list/filter path.
- Use `ON DELETE CASCADE` only when deleting the parent should clearly remove children.

## Data access patterns

- Server Components may call read-only query helpers directly.
- Mutations go through Server Actions or Route Handlers.
- Queries return plain objects, not database driver rows leaked through the app.
- Validate all external input before it reaches SQL.
- Use prepared statements. Never interpolate user input into SQL strings.

Reason: a small data boundary makes security review and testing much easier.

## Component patterns

- Default to Server Components.
- Add `'use client'` only for state, effects, browser APIs, or event handlers.
- Keep client components leaf-level when possible.
- Forms should have:
  - a server-side validation schema,
  - user-visible error messages,
  - loading/disabled states,
  - success navigation or optimistic refresh.
- Do not fetch from internal API routes from Server Components; call the underlying function directly.

Reason: Server Components reduce bundle size and avoid unnecessary client/server round trips.

## Server Actions

Server Actions must:
- authenticate first,
- authorize against the resource being changed,
- validate input,
- perform the DB write inside a transaction when multiple rows change,
- return a typed result object instead of throwing expected validation errors.

Example shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; fieldErrors?: Record<string, string[]> };
```

Reason: predictable action results make forms and tests simpler.

## Route Handlers

Use `app/api/**/route.ts` for:
- third-party webhooks,
- public API endpoints,
- streaming responses,
- integrations that require raw request access.

Rules:
- Verify webhook signatures before parsing business data.
- Return minimal error details to callers, but log enough context internally.
- Keep handlers thin; call `services/*` or `features/*`.

## Authentication & authorization

- Authentication answers “who is this?”
- Authorization answers “can they do this to this resource?”

Rules:
- Never rely on client-side checks for authorization.
- Every mutation must check ownership/member role on the server.
- Prefer helper functions like `requireUser()` and `assertCanEditProject(userId, projectId)`.
- Store sessions securely using the chosen auth provider’s recommended cookie strategy.

Reason: most SaaS security bugs are missing authorization checks, not missing login checks.

## Error handling

- Expected user errors return typed results.
- Unexpected errors are logged and surfaced as generic messages.
- Do not leak SQL errors, stack traces, tokens, or provider responses to users.
- Use a single `AppError` type only if it stays simple.

## Testing expectations

Minimum test coverage for new work:
- Unit tests for pure domain logic and validation.
- Integration tests for database queries/actions that affect money, permissions, or ownership.
- Webhook tests with valid and invalid signatures.
- Regression tests for every fixed bug.

Commands should be documented in `package.json`:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
```

Reason: small SaaS apps fail when billing/auth/data edge cases are only manually tested.

## Dev commands

Assume pnpm unless the repo has already chosen npm/yarn/bun.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:reset
```

If a command does not exist, add it before relying on it in docs or CI.

## Patterns to follow

- Server-first data loading.
- Feature folders for domain ownership.
- Prepared SQL statements.
- Small server actions with explicit validation.
- Centralized env parsing.
- One migration per schema change.
- Vendor wrappers in `services/`.
- Clear empty/loading/error states for every dashboard page.

## Anti-patterns to avoid

- Do not put business logic in `page.tsx` or `route.ts`.
  - Reason: it becomes untestable and hard to reuse.
- Do not create a generic `utils.ts` dumping ground.
  - Reason: unclear ownership leads to accidental coupling.
- Do not use `any` for request bodies, DB rows, or payment events.
  - Reason: these are trust boundaries.
- Do not call internal HTTP routes from server-side code.
  - Reason: it adds latency and bypasses type checking.
- Do not mutate the database outside migrations.
  - Reason: deploys must be reproducible.
- Do not make every component a Client Component.
  - Reason: it bloats JavaScript and weakens the App Router model.
- Do not store money as floats.
  - Reason: use integer cents or provider amount units.

## Pull request checklist

Before opening a PR:
- [ ] New env vars are documented and validated in `lib/env.ts`.
- [ ] DB changes include a migration and updated `db/schema.sql`.
- [ ] New mutations authenticate and authorize server-side.
- [ ] SQL uses prepared statements.
- [ ] Tests cover the important success and failure paths.
- [ ] `pnpm lint`, `pnpm typecheck`, and `pnpm test` pass or the PR explains why not.

## Claude Code behavior for this project

When working in this repo:
1. Inspect existing conventions before adding files.
2. Prefer small, reviewable changes.
3. Explain schema changes before applying them.
4. Never invent env vars without adding validation and docs.
5. Never skip auth/authorization on mutations.
6. If requirements are ambiguous, choose the safer SaaS default and document the assumption in the PR.

This template is intentionally opinionated for a small production SaaS: boring database rules, thin framework files, server-side trust boundaries, and low operational complexity.
