# CLAUDE.md for a Next.js 15 + SQLite SaaS

You are working in a production-minded SaaS codebase built with Next.js 15 App Router and SQLite.
Default to clarity, small diffs, and boring reliability. If a choice is unclear, pick the simplest
option that preserves correctness and can be explained in one sentence.

## Stack and Versions

- Next.js 15 App Router only.
- TypeScript everywhere.
- SQLite via `better-sqlite3` for local dev and CI, or Turso when the project explicitly uses hosted SQLite.
- Use Server Components by default. Reach for Client Components only when interactivity requires them.
- Prefer Node.js APIs that are stable and boring. Avoid experimental features unless the repo already uses them.

Why:

- A narrow stack keeps the app easy to onboard, debug, and deploy.
- SQLite gives the SaaS a simple migration story and fast local setup.
- App Router and Server Components reduce client-side complexity.

## Folder Structure

- `app/` for routes, layouts, loading states, and route handlers.
- `components/` for reusable UI pieces that are not route-specific.
- `lib/` for domain logic, database access, helpers, and shared utilities.
- `db/` for SQL schema, migrations, and seed data.
- `actions/` or `app/**/actions.ts` for server actions that mutate data.
- `types/` only when a type is shared across multiple domains.

Why:

- Route code stays close to the route.
- Shared logic stays outside React trees.
- Database files remain easy to review and version.

Example skeleton:

```text
app/
  (marketing)/
  (app)/
  api/
components/
lib/
db/
  migrations/
  seed/
```

Why:

- A visible skeleton removes ambiguity when the repo is brand new.
- Route groups keep marketing and authenticated surfaces separated without extra tooling.

## Naming Conventions

- Use `kebab-case` for files and folders.
- Use `PascalCase` for React components.
- Use `camelCase` for functions, variables, and hooks.
- Name server actions by intent, not implementation: `createInvoice`, `updateProfile`, `archiveProject`.
- Name database tables in plural lowercase: `users`, `organizations`, `subscriptions`.

Why:

- Predictable names reduce context switching.
- Intent-based names make code easier to search and review.

## Database and Migration Rules

- Treat SQL schema changes as first-class code changes.
- Every schema change gets a migration file with a timestamped name.
- Never edit a past migration after it has shipped.
- Keep migrations small and reversible when possible.
- Add indexes deliberately for query paths that exist now, not hypothetical future ones.
- Use transactions for any multi-step write.
- Prefer explicit column lists in `SELECT`, `INSERT`, and `UPDATE`.

Why:

- SQLite is simple, but schema drift is still the fastest way to create bugs.
- Reversible, timestamped migrations make reviews and rollbacks safer.
- Explicit SQL is easier to reason about than `SELECT *`.

## Dev Commands

- `pnpm dev` to run the app locally.
- `pnpm lint` before opening a PR.
- `pnpm test` for unit or integration tests if the project defines them.
- `pnpm db:migrate` to apply migrations.
- `pnpm db:seed` only if seed data is part of the project flow.
- `pnpm db:reset` only when the repo explicitly documents a safe reset flow.

Why:

- One obvious command per job keeps the repo approachable.

## Repo Discovery Order

- Check `package.json` first for the actual package manager and scripts.
- Inspect `app/` before introducing new route patterns.
- Inspect `db/` before changing schema or writing SQL.
- Check `README.md` or existing docs for any project-specific conventions before inventing new ones.

Why:

- Greenfield guidance should still adapt to the repo that exists in front of you.
- The right conventions are usually already visible in the codebase.

## Component Patterns

- Prefer Server Components for data fetching and page composition.
- Use Client Components only for stateful UI, browser APIs, or event-heavy interactions.
- Keep component props small and explicit.
- Co-locate tiny route-specific UI near the route when it improves readability.
- Extract reusable presentational components only after they are used in at least two places or are clearly complex.
- Keep forms accessible by default with labels, errors, and keyboard support.

Why:

- Server-first architecture cuts bundle size and data-fetch duplication.
- Over-extraction too early makes a greenfield app harder to follow.

## Server Actions and Route Handlers

- Use Server Actions for in-app mutations.
- Use Route Handlers when the endpoint is public, external, webhook-driven, or needs a stable API surface.
- Validate every input at the boundary.
- Return structured errors, not plain strings, for anything user-facing.
- Keep side effects behind a clear function boundary so they can be tested.

Why:

- Boundary validation prevents UI bugs from becoming data bugs.
- Structured errors make UI and tests easier to write.

## SQLite Conventions

- Prefer one table per feature area when the schema is still young and the data model is simple.
- Keep foreign keys explicit and name them after the referenced entity.
- Store timestamps in UTC.
- Use `INTEGER PRIMARY KEY AUTOINCREMENT` only when the project already relies on it; otherwise prefer explicit IDs that match the app's needs.
- Keep seed data minimal and representative.

Why:

- SQLite works best when schema choices stay simple and explicit.
- UTC timestamps avoid timezone confusion across environments.

## What We Don't Do

- We do not scatter database logic across React components.
- We do not introduce a new state library unless the app truly needs it.
- We do not use client-side fetching for data that can be loaded on the server.
- We do not add abstractions before a second concrete use case exists.
- We do not optimize prematurely.
- We do not ask clarifying questions when the repo conventions already imply the answer.

Why:

- The fastest way to slow a SaaS down is to make every feature invent its own pattern.

## Working Style

- Make the smallest change that solves the task.
- Prefer updating existing files over creating new patterns.
- When editing code, keep unrelated formatting noise out of the diff.
- If you need to choose between two valid implementations, prefer the one with fewer moving parts.
- If a task touches database behavior, update the migration and the code together.

Why:

- Small, focused diffs are easier to review and less risky to ship.

## Defaults

- Use `strict` TypeScript if the repo is configured for it.
- Use `zod` or a similar schema validator at the boundary if validation is needed.
- Prefer `fetch` on the server and native platform APIs before adding dependencies.
- Prefer simple SQL over an ORM unless the repo already standardizes on one.

Why:

- The default path should be the easiest path to maintain.
