# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This file is the project operating manual for Claude Code. Follow it before editing code.

## Stack and versions

- Framework: Next.js 15 with App Router.
- Language: TypeScript in strict mode.
- Runtime: Node.js 22 LTS or newer.
- Database: SQLite via `better-sqlite3` for local/self-hosted apps, or Turso/libSQL for hosted edge-friendly deployments.
- Styling: Tailwind CSS plus small colocated components. Avoid introducing a second design system.
- Auth: Prefer Auth.js or a minimal signed-session implementation. Never invent custom crypto.

Why: this stack is intentionally small. The app should be easy to run locally, cheap to deploy, and simple to reason about.

## Folder structure

```text
app/
  (marketing)/          # public landing/pricing/docs pages
  (app)/                # authenticated product screens
  api/                  # route handlers only, no business logic
  layout.tsx
  page.tsx
components/
  ui/                   # reusable presentational primitives
  forms/                # client components with form state
lib/
  auth/                 # session helpers and auth checks
  db/                   # db connection, schema helpers, migrations runner
  services/             # business use-cases; server-only
  validation/           # zod schemas shared by UI and API
migrations/             # numbered SQL migrations
scripts/                # CLI scripts: migrate, seed, backfill
tests/
  unit/
  integration/
```

Rules:

- Route handlers in `app/api/**/route.ts` should parse input, call `lib/services/*`, and return typed responses. Do not put core business logic in route handlers.
- Server Components are the default. Use Client Components only for browser state, effects, or event handlers.
- Keep database access inside `lib/db` and `lib/services`; UI components must not import database clients.

## Naming conventions

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts` and only in client-capable files.
- Server-only service files: `thing.service.ts`.
- Zod schemas: `thing.schema.ts`.
- Database tables: `snake_case` plural nouns, e.g. `users`, `billing_events`.
- TypeScript types: `PascalCase`, e.g. `BillingEvent`.
- Environment variables: `UPPER_SNAKE_CASE`; document every required variable in `.env.example`.

Why: predictable names let Claude navigate without asking clarifying questions.

## Development commands

Use these exact commands unless the project overrides them in `package.json`:

```bash
npm run dev          # local Next.js dev server
npm run lint         # eslint/next lint
npm run typecheck    # tsc --noEmit
npm run test         # unit/integration tests
npm run db:migrate   # apply migrations
npm run db:seed      # seed local development data
```

Before reporting completion, run the narrowest relevant command plus `npm run typecheck` when TypeScript changed.

## Database and migration rules

- All schema changes must be explicit SQL files in `migrations/`.
- Migration filenames use increasing numbers: `0001_create_users.sql`, `0002_add_plan_to_users.sql`.
- Never mutate old migrations after they may have run. Add a new migration instead.
- Every table needs:
  - `id` primary key
  - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
  - `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP` when rows are edited
- Use foreign keys and enable them on connection: `PRAGMA foreign_keys = ON`.
- Use transactions for multi-step writes.
- Never build SQL by string concatenation with user input. Use prepared statements or parameter binding.

Why: SQLite is reliable when schema history is deterministic and writes are small/transactional.

## Data access patterns

- Put the connection singleton in `lib/db/client.ts`.
- Put query functions in `lib/db/*.repo.ts`.
- Put workflows in `lib/services/*.service.ts`.
- Validate all external input with Zod before calling service functions.
- Return plain objects, not database driver rows with hidden prototypes.

Example flow:

```text
route.ts -> zod schema -> service -> repo -> SQLite
```

## Component patterns

- Prefer Server Components for data loading.
- Client Components must start with `'use client'` and should receive serializable props.
- Forms should use server actions or route handlers, but not both in one feature unless there is a clear reason.
- Keep loading and error UI close to the route segment using `loading.tsx` and `error.tsx`.
- Use semantic HTML first. Add ARIA only when native semantics are insufficient.

## Authentication and authorization

- Treat authentication as identity only. Authorization checks belong near the service/action that modifies data.
- Every mutation must verify the current user/session on the server.
- Never trust user IDs sent from the browser when the session already contains identity.
- Store secrets only in environment variables. Never commit `.env`.

## Error handling

- User-facing errors should be short and actionable.
- Server logs may include internal context but must not include tokens, cookies, passwords, or API keys.
- Use typed result objects for expected business failures, e.g. `{ ok: false, code: 'PLAN_LIMIT' }`.
- Throw only for unexpected failures.

## Testing rules

- Unit-test pure services and validation schemas.
- Integration-test database repos against a temporary SQLite file.
- Add at least one regression test for every bug fix.
- For route handlers, test success, validation failure, and unauthorized access.
- Do not snapshot large HTML trees; assert meaningful text, roles, and state transitions.

## Performance rules

- Avoid loading entire tables into memory. Add indexes for common filters.
- Keep Server Component queries close to the route and only fetch fields needed by the view.
- Use pagination for lists that can exceed 50 rows.
- Do not add caching until the correctness boundary is clear.

## Security rules

- Never interpolate untrusted data into SQL, shell commands, redirects, or HTML.
- Validate webhook signatures before processing payloads.
- For billing or account state, make mutations idempotent.
- Do not expose stack traces to users.
- Do not log request bodies for auth, billing, or webhook endpoints.

## What we do not do, and why

- Do not introduce Prisma by default. For SQLite SaaS projects, raw SQL plus small repo functions keeps migrations and deployment simpler.
- Do not create generic `utils.ts` dumping grounds. Helpers live next to the feature or in a clearly named `lib/*` module.
- Do not add global client state for server-owned data. Use server rendering and revalidation first.
- Do not put secrets or per-developer paths in committed config.
- Do not make route handlers call other route handlers. Share service functions instead.
- Do not skip validation because TypeScript types exist. Types do not validate runtime input.

## Completion checklist for Claude

Before saying the task is done:

1. Summarize the files changed.
2. Run relevant checks and paste the exact command results.
3. Confirm migrations are added when schema changed.
4. Confirm no secrets were added.
5. Mention any assumptions or follow-up risks.
