# CLAUDE.md — Next.js 15 + SQLite SaaS Playbook

This file defines how we build in this repo so Claude can act without repeated clarification.

## 1) Stack and versions
- Next.js 15 (App Router), React 19, TypeScript strict
- SQLite via better-sqlite3 for local/dev and CI
- Optional production DB: Turso/libSQL using same SQL schema files
- Drizzle ORM plus drizzle-kit migrations
- Zod for runtime validation at API boundaries

Reason: one language plus one SQL source keeps app and data model in lockstep.

## 2) Folder structure
```text
/app
  /(marketing)
  /(auth)
  /(app)
    /dashboard
    /settings
  /api
    /billing
    /projects
/components
  /ui
  /forms
  /dashboard
/lib
  /auth
  /db
  /billing
  /validators
/db
  /schema
  /migrations
  /seed
/tests
```

Rules:
- Route handlers live only in app/api/**/route.ts.
- Shared server utilities go in lib/**.
- SQL schema is defined in db/schema/**; migrations in db/migrations/**.
- Never place DB access in client components.

## 3) Naming conventions
- Files: kebab-case (project-card.tsx)
- React components: PascalCase exports
- Server actions: verb-first (createProject, archiveProject)
- DB tables: snake_case plural (projects, team_members)
- DB columns: snake_case; timestamps always created_at, updated_at

## 4) DB and migration rules
1. Schema changes require a migration in the same PR.
2. Migrations are append-only; never edit old migration files.
3. Use explicit constraints: PK for every table, FK with delete rule, unique indexes for user identifiers.
4. Destructive changes use expand-contract: add nullable column, backfill, switch reads/writes, drop old later.
5. Seed data must be idempotent.

## 5) Component patterns
- Default to Server Components.
- Use Client Components only for interactivity.
- Data fetching happens server-side close to route segment.
- Validate input with Zod in route handlers and server actions.
- Return typed domain objects from lib/**; avoid raw SQL rows in UI layer.

## 6) Dev commands
```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm test
pnpm lint
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

## 7) What we do not do
- No direct SQL in React components.
- No any in domain or API code.
- No migration rewrites after merge.
- No force-push to shared main branches.
- No business logic inside route files.

## 8) PR expectations
- If touching db/schema, include migration plus rollback note.
- If touching billing/auth, include at least one test.
- If introducing new env var, update .env.example and README.
- Every PR summary includes risk level and manual test steps.

## 9) Claude operating rules
When asked to implement:
1. Propose file plan first (3 to 7 bullets).
2. Make smallest coherent change-set.
3. Run typecheck then tests before final response.
4. For DB changes, show migration filename and SQL diff summary.

If requirements conflict with this file, ask once, then proceed with explicit assumption.
