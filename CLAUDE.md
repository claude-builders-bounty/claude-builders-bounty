# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the operating manual for Claude Code in this repository. Follow it before changing code.

## Stack & versions

- Next.js 15 App Router, React 19, TypeScript `strict: true`.
- SQLite via `better-sqlite3` for local/serverful deploys, or Turso/libSQL when the app must run at the edge.
- Drizzle ORM is preferred for typed schema + migrations. Raw SQL is allowed only for queries that Drizzle cannot express clearly.
- Tailwind CSS for styling. Server Components by default.

Reason: this stack keeps the SaaS small, fast, inspectable, and cheap to operate.

## Project structure

```text
app/                    # routes, layouts, server actions close to the route
  (marketing)/          # public pages
  (app)/                # authenticated product UI
  api/                  # route handlers only when HTTP boundary is required
components/             # reusable UI, no DB access
components/ui/          # primitive design-system components
lib/                    # shared server/client-safe utilities
lib/server/             # server-only helpers; may read env, auth, DB
lib/db/                 # schema, migrations, query helpers
lib/auth/               # auth/session helpers
features/<feature>/     # feature-specific components, actions, validators
drizzle/ or migrations/ # generated SQL migrations
tests/                  # unit/integration/e2e tests
```

Use feature folders when code is cohesive and product-facing. Use `lib/` only for genuinely shared primitives.

## Naming conventions

- Files: `kebab-case.tsx`; React components: `PascalCase`; functions/vars: `camelCase`.
- Server actions end with `.action.ts`; validation schemas end with `.schema.ts`.
- DB tables use plural snake_case: `users`, `team_members`, `billing_events`.
- DB columns use snake_case. TypeScript fields may use camelCase only at API/UI boundaries with explicit mapping.

Reason: predictable names reduce navigation cost and prevent accidental client/server imports.

## Server/client boundaries

- Default to Server Components. Add `'use client'` only for browser state, effects, refs, or event handlers.
- Never import `lib/server/*`, DB clients, secrets, or Node-only packages from Client Components.
- Put mutations in Server Actions unless a third-party webhook or public API requires a route handler.
- Validate all action inputs with Zod before touching the DB.

## SQL / migration conventions

- Every schema change gets a migration committed with the code that depends on it.
- Migrations are append-only after merge. Do not edit a migration that may have run elsewhere; create a new one.
- Prefer explicit constraints: `not null`, `unique`, `check`, foreign keys with named `on delete` behavior.
- Add indexes for foreign keys and frequent lookup columns. Avoid speculative indexes.
- Store timestamps as ISO text or integer epoch consistently; default to UTC.
- Wrap multi-step writes in transactions.
- Never concatenate user input into SQL. Use parameters or ORM bindings.

Reason: SQLite is reliable when schema ownership is disciplined; migration drift is the real risk.

## Data access patterns

- Keep DB access in `lib/db/queries/*` or feature-local `*.queries.ts` files.
- Query functions return domain objects, not raw driver rows, when consumed by UI.
- Server Actions call validation → auth/authorization → query/mutation → revalidate/redirect.
- Do not query the DB directly inside generic UI components.

## Component patterns

- Pages compose data-loading Server Components and small interactive Client Components.
- Components accept explicit props; avoid global stores unless state crosses distant UI branches.
- Use optimistic UI only after the Server Action is idempotent or has a safe rollback path.
- Accessibility is required: labels for inputs, keyboard-operable controls, semantic HTML first.

## Auth & authorization

- Authentication answers “who are you?” Authorization answers “can you do this?” Check both.
- Every mutation must verify ownership/team membership server-side.
- Never trust IDs from the client without checking access in the same request.
- Keep session reads in `lib/server/auth.ts` or equivalent.

## Environment variables

- Define all env vars in a typed/env validation module.
- Public browser env vars must start with `NEXT_PUBLIC_`; secrets never do.
- Fail fast at startup/build when required env vars are missing.

## Dev commands

Use these names unless the project documents alternatives:

```bash
pnpm dev          # local dev server
pnpm build        # production build
pnpm lint         # lint + format check
pnpm typecheck    # TypeScript no-emit
pnpm test         # unit/integration tests
pnpm db:generate  # generate migration from schema
pnpm db:migrate   # apply migrations
pnpm db:studio    # inspect local DB
```

Before PR: run `pnpm lint && pnpm typecheck && pnpm test && pnpm build`.

## Testing rules

- Unit-test pure business logic and validation schemas.
- Integration-test DB queries against a temporary SQLite database.
- E2E-test critical SaaS paths: signup/login, create core resource, billing/settings if present.
- Do not mock authorization in mutation tests; assert denied paths.

## What we do not do

- No generic “utils” dumping ground. If a helper has no clear owner, name the domain first.
- No DB calls from Client Components. It leaks architecture and risks secrets.
- No migration rewrites after merge. Create follow-up migrations.
- No hidden `any`. If a type is hard, model it or isolate the unsafe boundary with a comment.
- No premature microservices, queues, or distributed caches. SQLite SaaS wins by staying simple.
- No broad catch-and-ignore error handling. Surface actionable messages and log server details.

## PR checklist for Claude

1. Explain the product intent in one sentence.
2. List changed routes, DB tables, and env vars.
3. Confirm migrations are included for schema changes.
4. Confirm authz checks for every mutation.
5. Run or honestly report: lint, typecheck, tests, build.
6. Mention risks and follow-ups without hiding blockers.
