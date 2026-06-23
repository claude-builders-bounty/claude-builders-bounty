# CLAUDE.md - Next.js 15 SQLite SaaS

## Stack and versions

- Next.js 15 App Router with React Server Components by default.
- React 19 and TypeScript in strict mode.
- SQLite through one of two supported paths:
  - `better-sqlite3` for local-first or server-hosted deployments.
  - Turso/libSQL for hosted SQLite with remote replicas.
- Drizzle ORM is preferred for typed schema, migrations, and query composition.
- Tailwind CSS is allowed for styling, but keep business logic outside components.
- Zod is used for all external input validation.

Reason: this stack keeps the app small, deployable, and easy to reason about while preserving typed database boundaries.

## Project structure

Use this layout unless a task explicitly says otherwise:

```text
app/
  (marketing)/
  (dashboard)/
  api/
components/
  ui/
  forms/
  dashboard/
db/
  schema.ts
  client.ts
  migrations/
features/
  billing/
  accounts/
  projects/
lib/
  auth.ts
  env.ts
  errors.ts
  result.ts
server/
  actions/
  queries/
tests/
```

Rules:

- Put route files under `app/` only.
- Put reusable UI in `components/`.
- Put business workflows in `features/`.
- Put database schema and migration code in `db/`.
- Put server-only reads in `server/queries/` and server-only writes in `server/actions/`.

Reason: App Router files should stay thin. This makes route changes reviewable and keeps database writes out of UI components.

## Dev commands

Use these commands unless the project already defines different scripts:

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

When adding a new feature, run at least:

```bash
pnpm lint && pnpm typecheck
```

If the change touches database code, also run:

```bash
pnpm db:generate && pnpm db:migrate
```

Reason: SQLite migrations are easy to break silently if schema changes are not generated and applied in the same work cycle.

## SQL and migration conventions

- Never edit an already-applied migration unless the project is still pre-release and the task explicitly allows it.
- Add a new migration for every schema change.
- Name tables in plural snake_case: `users`, `projects`, `billing_events`.
- Name columns in snake_case: `created_at`, `updated_at`, `owner_id`.
- Always include `created_at` and `updated_at` on user-owned entities.
- Use foreign keys when SQLite deployment mode supports them, and document exceptions.
- Keep migration files deterministic and reviewable.
- Wrap multi-step writes in transactions.
- Prefer soft-delete columns only when the product needs recovery or audit history.

Reason: SQLite is reliable, but schema drift and manual migration edits create hard-to-debug production failures.

## Data access rules

- Server Components may call read-only query helpers from `server/queries/`.
- Server Actions may call write helpers from `server/actions/`.
- Client Components must not import `db/client.ts`, server actions, or environment secrets.
- Validate all action inputs with Zod before touching the database.
- Return typed success/error results instead of throwing for expected user-facing errors.
- Do not build SQL strings by concatenating user input.

Reason: separating reads, writes, and client UI prevents secret leakage and accidental database access from the browser bundle.

## Component patterns

- Use Server Components first.
- Add `use client` only for state, effects, browser APIs, or interactive controls.
- Keep form components small and pass only validated props.
- Use optimistic UI only after the server action has a clear rollback path.
- Keep loading and error states beside the route segment that owns the data.
- Prefer composition over large prop-heavy components.

Reason: App Router performs best when server-rendered data and client interactivity are separated deliberately.

## Naming conventions

- Components: `PascalCase.tsx`.
- Hooks: `useSomething.ts`.
- Server actions: `verbNounAction`, for example `createProjectAction`.
- Query helpers: `getProjectById`, `listProjectsForUser`.
- Zod schemas: `CreateProjectInput`, `UpdateAccountInput`.
- Route folders: lowercase kebab-case.

Reason: predictable names make it easier to find the owner of a behavior and avoid duplicate helper files.

## Environment variables

- Define all required environment variables in `lib/env.ts`.
- Validate environment variables at startup.
- Keep `.env.example` updated with safe placeholder values.
- Never put tokens, API keys, database URLs, cookies, or production secrets in examples or tests.

Reason: missing env validation causes late failures in deployment and can leak secrets through careless examples.

## Testing expectations

- Add unit tests for pure helpers and validation schemas.
- Add integration tests for server actions that touch database writes.
- Add route-level tests for auth redirects and important dashboard flows.
- Use a temporary SQLite database for tests.
- Reset database state between tests.

Reason: SaaS bugs often appear at the boundary between validation, auth, and persistence.

## What we do not do and why

- Do not put database calls in Client Components. It leaks server-only behavior into the browser path.
- Do not use raw SQL string concatenation. It risks injection and broken escaping.
- Do not mix auth checks across random files. Centralize auth in `lib/auth.ts` and route guards.
- Do not create one giant `utils.ts`. Split helpers by domain and responsibility.
- Do not add a new package before checking whether the current stack already solves the problem.
- Do not use `any` to bypass type errors. Fix the type boundary or add a narrow typed parser.
- Do not change schema and UI in the same large PR if they can be reviewed separately.

## Before changing code

Answer these silently before editing:

1. Which route, feature, or database table owns this behavior?
2. Is this a read path, write path, or UI-only change?
3. Does this require a migration?
4. Is the component server-only or client-interactive?
5. Which validation schema protects the input?
6. Which command proves the change is safe?

## PR checklist

- [ ] Route files stay thin.
- [ ] Database access stays server-side.
- [ ] Zod validates external input.
- [ ] Migration added for schema changes.
- [ ] `.env.example` updated if configuration changed.
- [ ] Lint and typecheck commands were run.
- [ ] Tests were added or updated for changed behavior.
