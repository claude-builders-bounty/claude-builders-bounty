# CLAUDE.md

This file is the operating manual for a greenfield SaaS app built on **Next.js 15 App Router** and **SQLite** (`better-sqlite3` locally, Turso-compatible schema in production).

The goal is not to be generic. The goal is to make fast, boring, safe decisions.

---

## Stack & Versions

- **Framework:** Next.js 15 App Router
- **Language:** TypeScript with `strict` enabled
- **Runtime:** Node.js 22 LTS
- **Database:** SQLite for local development via `better-sqlite3`
- **Production DB option:** Turso/libSQL, but schema must stay SQLite-compatible
- **Styling:** Tailwind CSS
- **Validation:** Zod at all request boundaries
- **Tests:** Vitest for unit tests, Playwright for critical user flows

Why:
- Next.js 15 App Router gives us stable server components, route handlers, and streaming primitives.
- SQLite keeps local setup near-zero. If the schema already works on SQLite, we avoid accidental Postgres-only drift.
- TypeScript strict mode and Zod catch the class of bugs that usually show up as SaaS data corruption and bad admin states.

---

## Folder Structure

Do this:

- `app/` for routes, layouts, and route handlers
- `components/` for reusable UI
- `features/` for domain-specific modules that own their server actions, validators, and view logic
- `lib/` for shared infrastructure: db client, auth helpers, env parsing, feature flags
- `db/` for schema, migrations, and seed scripts
- `tests/` for integration and contract coverage

Recommended structure:

```text
app/
  (marketing)/
  (app)/
  api/
components/
features/
  billing/
  auth/
  teams/
lib/
  db/
  auth/
  env/
db/
  migrations/
  schema.ts
tests/
```

Why:
- We separate shared primitives from domain ownership.
- We do not dump all business logic into `app/` because App Router files should stay thin and navigational.

---

## Naming Conventions

Do this:

- React components: `PascalCase`
- Hooks: `useSomething`
- Server functions/actions: verb-first names like `createWorkspace`, `updateBillingEmail`
- Zod schemas: `workspaceInputSchema`, `inviteMemberSchema`
- Database tables: singular or plural is acceptable, but pick one once and stay consistent across all migrations

Do not:

- Mix route-only names with business names
- Create files called `utils2.ts`, `helpers.ts`, or `misc.ts`
- Use abbreviations unless they are industry standard (`id`, `url`, `api`)

Why:
- Most SaaS maintenance pain is caused by unclear ownership, not raw code volume.

---

## Dev Commands

Do this:

- Install dependencies: `pnpm install`
- Start dev server: `pnpm dev`
- Run unit tests: `pnpm test`
- Run lint: `pnpm lint`
- Run typecheck: `pnpm typecheck`
- Run Playwright smoke tests: `pnpm test:e2e`
- Generate or apply a migration: `pnpm db:migrate`
- Seed local database: `pnpm db:seed`

Why:
- Claude should prefer commands that are deterministic and already scripted in `package.json`.
- We do not ask contributors to remember long ad-hoc CLI invocations when a script can name the intent clearly.

---

## SQL & Migration Rules

Do this:

- Keep every migration **forward-only**
- Write migrations so they run on vanilla SQLite first
- Add columns as nullable or with safe defaults before enforcing stricter assumptions
- Backfill in an explicit step when shape changes require data movement
- Keep foreign keys enabled and intentional

Do not:

- Edit old migration files after they have landed
- Depend on database-specific features that break SQLite compatibility
- Combine schema changes and unrelated feature work in one migration
- Rename or drop columns casually without a clear backfill and rollback story

Why:
- SQLite is forgiving until it isn’t. Small shortcuts around schema changes tend to surface later as broken local environments, failed previews, or production drift.

Rules:

1. A migration must explain **what changed** and **why the change is safe**.
2. If a field becomes required, first ship the field as optional, backfill it, then make it required in a later migration.
3. If Turso compatibility matters, avoid SQL that assumes server-side procedural features.

---

## Component Patterns

Do this:

- Keep server components as the default
- Use client components only when interactivity, browser APIs, or local state actually require them
- Co-locate feature-specific UI with the feature module
- Validate form input on both client hints and server boundaries
- Pass plain serializable data into UI; keep DB objects and secrets on the server side

Do not:

- Turn an entire route tree into client components for convenience
- Fetch directly from the database inside leaf presentational components
- Hide data mutation in random click handlers without an explicit server action or route contract

Why:
- The fastest way to make a Next.js SaaS fragile is to blur the line between rendering, fetching, and mutation.

---

## API & Server Action Rules

Do this:

- Put all env parsing in one place
- Parse all request bodies with Zod before doing work
- Return typed success/error shapes
- Treat auth and tenancy checks as the first line of every mutation

Do not:

- Trust raw `FormData` or JSON payloads
- Read `process.env` throughout the codebase
- Build “admin-only” shortcuts without an explicit authorization check

Why:
- SaaS bugs are usually permission bugs, billing bugs, or tenant-isolation bugs. The safest path is to make every entry point validate, authorize, then mutate.

---

## What We Don't Do

Do not:

- Use Prisma/Postgres-only assumptions in a SQLite-first template
- Introduce global singleton state for tenant or request context
- Write raw SQL inline inside UI files
- Put billing logic inside React components
- Ship “temporary” any-typed request parsing

Why:
- These shortcuts feel fast in week one and become the long-term source of data bugs, auth leaks, and upgrade pain.

If a change makes the app easier to demo but harder to migrate, test, or reason about, reject it.

---

## Default Delivery Rules For Claude

When changing code in a project that uses this template:

1. Prefer the smallest safe change.
2. Add or update tests when behavior changes.
3. Keep route files thin.
4. Explain schema changes clearly.
5. Never invent commands that are not already present in the project scripts.

Why:
- Claude should optimize for maintainability and clean handoff, not for cleverness.
