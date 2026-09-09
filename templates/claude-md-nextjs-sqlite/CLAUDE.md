# CLAUDE.md

> Guide for Claude Code working in this repository. Opinionated on purpose:
> every rule below exists because a specific failure mode was observed in
> production. Follow them; change them only with a PR that explains why.

## Stack & versions (do not drift)

- Next.js **15** (App Router), React 19, TypeScript 5, strict mode ON
- SQLite via **better-sqlite3** (local) or **Turso/libSQL** (cloud) — never both in one query path
- ORM: **Drizzle ORM** (`drizzle-orm` + `drizzle-kit`) for schema, migrations, and queries
- Styling: Tailwind CSS v4; shadcn/ui components
- Package manager: pnpm; Node 22 LTS

## Project structure

```
src/
  app/                 # routes only: page.tsx, layout.tsx, route.ts, actions.ts
    (auth)/            # auth group
    api/               # route handlers for external/webhook endpoints only
  components/
    ui/                # shadcn/ui primitives (generated, rarely edited)
    features/<x>/      # feature components, one folder per feature
  db/
    schema.ts          # Drizzle schema (single source of truth)
    index.ts           # client factory + query helpers
    migrations/        # drizzle-kit generated SQL (committed, never hand-edited)
  lib/                 # framework-agnostic helpers (auth, email, validation)
  server/              # server-only modules (queries, actions, jobs)
tests/                 # vitest unit tests, mirror src structure
```

## Rules

### Database

- Schema changes go through **Drizzle migrations only**: edit `src/db/schema.ts`,
  run `pnpm db:generate`, commit the generated SQL, run `pnpm db:migrate`.
  Never edit a committed migration file — write a new one.
- No raw SQL in components or actions. All queries live in `src/server/*` or
  `src/db/*` helpers. *Reason: keeps a single query layer for caching, tests,
  and future provider swaps.*
- No `db:push` against production, ever. *Reason: push can destroy data that
  migrations would preserve.*
- Every `DELETE`/`UPDATE` needs an explicit `WHERE`. *Reason: SQLite has no
  safety net; an unqualified write is data loss.*
- Wrap multi-statement writes in transactions (`db.transaction`).

### Components & data flow

- **Server Components by default.** Add `'use client'` only at the leaf that
  actually needs interactivity. *Reason: less client JS, faster TTFB, fewer
  hydration bugs.*
- Data fetching for internal data happens in Server Components or server
  actions — never from `useEffect` fetching your own API. *Reason: avoids
  client-side waterfalls and double-fetching; the router cache handles it.*
- Mutations go through **server actions** (`src/app/.../actions.ts`) with
  `useActionState`/`useTransition`, or `route.ts` handlers for external
  callers. *Reason: no hand-rolled API layer for internal mutations.*
- Business logic lives in `src/server/`, never inside components.
  *Reason: logic in components is untestable and gets duplicated.*

### Naming & conventions

- Files: kebab-case (`user-settings.tsx`, `create-org-action.ts`); components:
  PascalCase; functions/variables: camelCase; DB tables/columns: snake_case.
- Server actions: `verbNoun` (`createOrg`, `deleteMember`), one file per route.
- Validate all external input with Zod schemas shared between client and
  server (`src/lib/validators.ts`). *Reason: types alone don't survive a
  network boundary.*

### Environment & secrets

- Secrets live in `.env.local` (gitignored); `.env.example` documents keys.
- Server-only keys use the `server-only` package import in their module.
- Never reference `process.env.NEXT_PUBLIC_*` for anything secret.
  *Reason: `NEXT_PUBLIC_*` is inlined into the client bundle.*

### Dev commands

```bash
pnpm dev            # local dev server
pnpm build          # production build
pnpm lint           # eslint
pnpm typecheck      # tsc --noEmit
pnpm test           # vitest run
pnpm db:generate    # drizzle-kit generate (after schema.ts edits)
pnpm db:migrate     # apply migrations
pnpm db:seed        # seed dev database
```

### What we don't do (and why)

- **No ORM other than Drizzle.** *Two query layers = two failure modes.*
- **No client-side state library (Redux/Zustand) for server data.**
  URL + React state + server actions cover every SaaS screen we ship.
- **No `any` in new code.** *A single `any` invalidates a feature's types.*
- **No new runtime dependency without a stated reason in the PR.**
  *Every dependency is supply-chain risk and bundle weight.*
- **No API routes for internal mutations.** Server actions already type-safe.
- **No `useEffect` for derived state.** Compute during render.
- **No committing secrets, lockfiles drift, or hand-written SQL.**
- **No premature abstractions:** build the second use case before extracting
  a shared module. *Reason: speculative abstractions are the #1 source of
  churn in small SaaS codebases.*

### Tests

- Unit-test `src/server/` logic with vitest (`tests/` mirrors `src/`).
- Every migration ships with a smoke query test when it alters existing
  tables. *Reason: migrations are the only irreversible operation here.*
