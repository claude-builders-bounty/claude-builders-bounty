# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the project instruction source for a production-minded SaaS built with **Next.js 15 App Router**, **TypeScript**, and **SQLite** via `better-sqlite3` locally or Turso/libSQL in hosted environments.

## Stack and version assumptions

- Next.js 15 App Router, React 19, TypeScript strict mode.
- SQLite for transactional product data.
- `better-sqlite3` for local/single-node deployments; Turso/libSQL for serverless or multi-region deployments.
- Tailwind CSS for styling unless the repository already uses another system.
- Zod for runtime validation at every request boundary.
- Vitest for unit tests and Playwright for end-to-end flows.

Reason: this stack is fast to ship, easy to inspect, and keeps the database simple enough that schema changes stay reviewable.

## Project structure

```text
app/                    # Route segments, layouts, pages, route handlers
app/(marketing)/         # Public landing/pricing/docs pages
app/(app)/               # Authenticated product UI
app/api/                 # Route handlers only; keep business logic outside
components/              # Reusable UI components
components/ui/           # Primitive UI components
features/                # Product features grouped by domain
features/<name>/actions.ts
features/<name>/queries.ts
features/<name>/schema.ts
features/<name>/components/
lib/                     # Shared infrastructure helpers
lib/db/                  # SQLite connection, migrations, query helpers
lib/auth/                # Auth/session helpers
lib/validation/          # Shared Zod schemas
migrations/              # Ordered SQL migration files
tests/                   # Unit/integration tests
e2e/                     # Playwright specs
scripts/                 # Repo maintenance scripts
```

Reason: route files stay thin, features remain discoverable, and database code is not scattered through UI components.

## Naming conventions

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts`.
- Server actions: verb-first names like `createWorkspace`, `archiveProject`.
- Database tables: plural snake_case, e.g. `users`, `workspaces`, `billing_events`.
- Database columns: snake_case.
- TypeScript variables: camelCase.
- Environment variables: UPPER_SNAKE_CASE.

Reason: database names remain SQL-native while TypeScript names remain idiomatic.

## Dev commands

Prefer these scripts in `package.json`:

```bash
npm run dev          # Start Next.js locally
npm run build        # Production build
npm run typecheck    # tsc --noEmit
npm run lint         # ESLint
npm run test         # Vitest
npm run test:e2e     # Playwright
npm run db:migrate   # Apply migrations
npm run db:studio    # Optional DB browser/studio
```

When changing code, run at minimum:

```bash
npm run typecheck && npm run lint && npm run test
```

Reason: most SaaS regressions are type, validation, or data-shape mistakes that these catch early.

## Database rules

### Migrations

- Every schema change must be a new migration file in `migrations/`.
- Use monotonically increasing names: `0001_initial.sql`, `0002_add_workspaces.sql`.
- Never edit an already-applied migration unless the project has not shipped and the team explicitly agrees.
- Include both schema and important indexes in the same migration that needs them.
- Prefer explicit constraints: `NOT NULL`, `CHECK`, `UNIQUE`, and foreign keys.

Reason: SQLite is reliable when the schema history is boring and deterministic.

### Query patterns

- Put read queries in `features/<name>/queries.ts`.
- Put writes in server actions or service functions, not React components.
- Validate all external input with Zod before it reaches SQL.
- Use prepared statements; never concatenate untrusted strings into SQL.
- Wrap multi-step writes in transactions.

Reason: this prevents injection, partial writes, and UI-driven data coupling.

### SQLite-specific guidance

- Enable WAL mode for local/server deployments where supported.
- Enable foreign keys on every connection.
- Store timestamps as ISO-8601 text or integer epoch consistently; do not mix.
- Use integer cents for money, never floats.
- Add indexes for every foreign key and common lookup path.

Reason: SQLite performs well for SaaS workloads when writes are deliberate and indexes match access patterns.

## App Router patterns

- Default to Server Components for data loading.
- Use Client Components only for interactivity, browser APIs, or local state.
- Keep `page.tsx` and `layout.tsx` small; delegate feature UI to components.
- Route handlers in `app/api/**/route.ts` should validate, call a feature/service function, and return typed JSON.
- Use `notFound()` and `redirect()` deliberately; do not hide authorization failures as generic crashes.

Reason: Server Components reduce client JavaScript and make data access easier to reason about.

## Auth and authorization

- Check authentication at the boundary of every protected route/action.
- Check authorization next to the data operation, not only in the UI.
- Model membership explicitly with tables like `workspace_members`.
- Never trust workspace IDs, user IDs, roles, or prices from the client.

Reason: SaaS bugs are usually authorization bugs, not rendering bugs.

## Validation and error handling

- Use Zod schemas for forms, route handlers, webhooks, and server actions.
- Return user-safe errors; log internal details server-side only.
- Treat webhooks as untrusted: verify signature, validate payload, then process idempotently.
- Add idempotency keys for billing and background operations.

Reason: production systems fail at boundaries; make boundaries explicit.

## Component patterns

- Keep components small and single-purpose.
- Use accessible HTML first; add custom UI only when needed.
- Forms should have visible labels, loading state, error state, and success feedback.
- Extract repeated product flows into `features/<name>/components/`.
- Do not fetch from the database inside arbitrary leaf components.

Reason: UI remains maintainable and testable as the SaaS grows.

## Testing rules

- Unit-test pure business logic and validation schemas.
- Integration-test database writes that affect billing, permissions, or destructive actions.
- E2E-test signup, login, create workspace, core paid flow, and cancellation.
- Every bugfix should include a regression test when practical.

Reason: these are the paths that cost money or trust when broken.

## Anti-patterns to avoid

- Do not put SQL directly in React components.
- Do not use `any` to silence type errors around API or database results.
- Do not create a migration that depends on local machine state.
- Do not store secrets in `.env.example`, docs, tests, or seed files.
- Do not call payment APIs from Client Components.
- Do not implement role checks only by hiding buttons.
- Do not add a generic `utils.ts` dumping ground; create named modules.
- Do not build a custom auth or billing system unless the issue explicitly requires it.

Reason: these shortcuts become security and maintenance debt quickly.

## Environment variables

Document required variables in `.env.example` without real secrets:

```bash
DATABASE_URL="file:./dev.db"
AUTH_SECRET="replace-me"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
STRIPE_SECRET_KEY=""
STRIPE_WEBHOOK_SECRET=""
```

Rules:

- `NEXT_PUBLIC_` variables are public. Never put secrets there.
- Server-only secrets must be read only in server files.
- Validate environment at startup if the project has an env helper.

## Pull request checklist

Before opening a PR:

- [ ] `npm run typecheck` passes.
- [ ] `npm run lint` passes.
- [ ] `npm run test` passes.
- [ ] Migrations are included for schema changes.
- [ ] New user-facing behavior has screenshots or a short demo note.
- [ ] Security-sensitive changes mention authorization and validation checks.

## How Claude should work in this repo

1. Read this file, then inspect the relevant `features/<name>/` folder before editing.
2. Make the smallest change that satisfies the issue.
3. Preserve existing patterns unless they violate a rule above.
4. Run the relevant checks and include exact command output in the final handoff.
5. If requirements conflict, stop and ask one concrete question.

Reason: small, verified changes ship faster and are easier to review.
