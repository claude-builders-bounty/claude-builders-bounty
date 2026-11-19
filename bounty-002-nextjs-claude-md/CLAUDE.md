# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack & versions
- Next.js 15.2+ App Router (React Server Components by default, Server Actions enabled)
- Node ≥ 20 (LTS), pnpm 9
- SQLite via `better-sqlite3` v11 (sync API, single connection per process). Turso is only used when a replica is needed for read scaling.
- TypeScript strict mode, `noEmit: true`, ESLint flat config, Prettier 3 with `singleQuote: true`.

## Golden rules
1. Server Actions are the only mutation path. No `pages/api/*`.
2. Every direct SQL statement lives in a repository module, never inline in components.
3. Migrations are append-only. Never edit a committed migration.
4. No client-side package can import another client bundle. Server code never imports browser-only utilities.
5. New dependencies require a review note in `docs/decisions/NNN-why-<name>.md`.

## Folder structure
```
src/
  app/                  routes (route groups by domain)
    dashboard/(…)/page.tsx
    api/                 ONLY: webhooks, health, edge routes
  components/           shared UI (components/lib for primitive wrappers)
  lib/
    db/                  sqlite.ts, schema.ts, migrate.ts
    repositories/        user.ts, subscription.ts, billing.ts
    auth/                session.ts, roles.ts
    logger.ts
  types/                shared DTOs
  styles/               global.css, tokens.css
tests/                  colocated unit + Playwright e2e
scripts/                maintenance only
migrations/             NNNN-description.sql, supabase-style names
docs/decisions/         kebab-case decision notes
```

## SQL / migration conventions
- Files are `NNNN-<verb>-<noun>.sql` (`0001-create-users.sql`), numbered monotonically, never edited.
- Column types: `INTEGER PRIMARY KEY` for ids, `TEXT` for enums, `INTEGER` for unix epoch, `REAL`/`INTEGER` for money-as-cents (integer cents, never floats).
- Foreign keys must declare `ON DELETE CASCADE` or `RESTRICT` explicitly — no implicit defaults.
- Indexes are created in the same migration as the table they cover; never in a later standalone migration unless documented in `docs/decisions/`.
- Migrations run inside a transaction; the runner refuses to apply if `schema-migrations` hash changes mid-run.

## Development commands
```
pnpm dev             # next dev --turbopack
pnpm validate        # typecheck + lint + unit tests
pnpm db:migrate      # apply pending migrations
pnpm db:reset        # drops ./data/dev.sqlite and rebuilds from migrations
pnpm db:studio       # drizzle-studio if wired, otherwise `sqlite3 data/dev.sqlite`
pnpm build           # next build
```

## Component patterns
- Prefer Server Components by default; `"use client"` only at DOM/behavior boundaries.
- Data fetching happens in `async` Server Components, not in `useEffect`.
- Shared hooks live under `src/hooks/`; shared stores (if any) use React Context or Zustand, not Redux.
- Forms: `react-hook-form` + Zod schema shared between client validation and server action input parsing. One schema module, not duplicated shapes.

## What we don't do (and why)
- **No ORM.** better-sqlite3 with hand-written SQL gives deterministic plans and zero ORM upgrade risk. If you cannot express a query without SQL, ask before writing it.
- **No global mutable singletons.** Every DB connection goes through the `getDb()` lazy singleton to keep dev hot-reload safe and to make transaction scoping explicit.
- **No `process.env` reads outside `src/lib/env.ts`.** Untyped env access caused three production outages last quarter.
- **No `any` in repository return types.** DTOs map 1:1 to tables; if you need a join, make an explicit view.
- **No floating-point money.** Store cents as integers; format at the edge.
- **No blocking work inside Server Actions.** Long jobs go to a `queue` table polled by a Worker script; the action returns `202` with a job id.
- **No feature branches living longer than 3 days.** Squash-merge to keep history reviewable; Rebase only locally before push.
- **No secrets in git history.** Any accidental commit triggers rotation immediately and is treated as an incident, not a git revert.

## Claude Code guidance
- When asked for a new table, sketch the migration SQL first, get confirmation, then write the repository.
- When asked to “make it faster”, measure with `EXPLAIN QUERY PLAN` before changing indexes.
- When touching billing, add a unit test covering idempotency and duplicate-webhook safety.
- Use `pnpm validate` before declaring done.

## Greenfield checklist (paste into a fresh repo)
- [ ] `data/dev.sqlite` in `.gitignore`
- [ ] `src/lib/db/schema.ts` exports table types
- [ ] `scripts/migrate.ts` is executable and idempotent
- [ ] At least one `docs/decisions/001-init.md` exists
- [ ] CI runs `pnpm validate && pnpm build`
