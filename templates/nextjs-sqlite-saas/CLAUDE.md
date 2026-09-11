# Next.js 15 + SQLite SaaS — Claude Code Context

Production defaults for a greenfield B2B SaaS using **Next.js 15 App Router**, **TypeScript strict**, and **SQLite** via **better-sqlite3** (local) or **Turso/libSQL** (hosted). Follow every rule unless the user explicitly overrides it in the current task.

## Stack and versions

| Layer | Choice | Why |
| --- | --- | --- |
| Framework | Next.js 15 App Router | Server Components by default; colocate route handlers |
| Language | TypeScript `strict: true` | Fail at compile time, not in production |
| Database | SQLite 3 | Single-tenant SaaS MVP; zero ops; easy local dev |
| Driver | `better-sqlite3` (local) / `@libsql/client` (Turso) | Sync local DX; edge-compatible hosted path |
| ORM | Drizzle ORM | Type-safe SQL; SQL-first migrations |
| Auth | Auth.js (NextAuth v5) | Session cookies; adapter maps to SQLite |
| Validation | Zod | Shared schemas for forms + server actions |
| Styling | Tailwind CSS 4 + `clsx` | Utility-first; no CSS-in-JS runtime |
| Tests | Vitest + Playwright | Unit near code; e2e for critical flows |

Pin majors in `package.json`; bump minors in dedicated PRs only.

## Folder structure

```text
src/
  app/                 # routes, layouts, loading/error.tsx
    (marketing)/       # public pages
    (app)/             # authenticated product shell
    api/               # route handlers (webhooks, cron)
  components/
    ui/                # dumb primitives (Button, Input)
    features/          # feature-specific composition
  db/
    schema/            # Drizzle table definitions (one file per domain)
    migrations/        # generated SQL — never hand-edit
    client.ts          # db singleton (server-only)
  lib/                 # pure helpers (no React)
  server/              # server-only modules (actions, services)
  types/               # shared types without runtime imports
drizzle.config.ts
.env.example
```

Rules:

- **Server-only** code imports `server-only` at top (`db/client.ts`, `server/*`).
- No database imports in Client Components.
- Co-locate feature code under `components/features/<domain>/` before extracting packages.

## SQL and migration conventions

- Table names: `snake_case` plural (`workspace_members`).
- Columns: `snake_case`; primary keys `id TEXT` (UUID v7 string) unless legacy.
- Timestamps: `created_at`, `updated_at` as ISO text or integer unix ms — pick one project-wide.
- Foreign keys: explicit `ON DELETE CASCADE` only when product requires cascade; otherwise `RESTRICT`.
- Migrations flow: edit `schema/` → `pnpm drizzle-kit generate` → review SQL → `pnpm drizzle-kit migrate`.
- Never mutate production DB manually; no `ALTER` in hotfix scripts without a migration file.
- Seed data lives in `db/seed.ts`; idempotent upserts only.

## Component patterns

- Default to **Server Components**; add `"use client"` only for event handlers, browser APIs, or hooks.
- Mutations use **Server Actions** in `src/server/actions/<domain>.ts` with Zod input parsing.
- Route handlers (`app/api/**`) only for webhooks, file uploads, or third-party callbacks — not CRUD.
- Forms: `<form action={action}>` + progressive enhancement; avoid uncontrolled mega-forms.
- Error boundaries per route segment; log server-side with request id, never expose stack traces to users.

## Dev commands

```bash
pnpm install
cp .env.example .env.local   # fill DATABASE_URL, AUTH_SECRET
pnpm db:migrate && pnpm db:seed
pnpm dev                      # http://localhost:3000
pnpm lint && pnpm typecheck && pnpm test
pnpm build                    # must pass before PR merge
```

## What we do

- Validate all external input with Zod at the server boundary.
- Use explicit transaction boundaries for multi-step writes (`db.transaction`).
- Feature-flag risky launches in `workspace_settings` JSON column.
- Write ADR snippets in `docs/adr/` when choosing non-obvious architecture.

## What we don't do (and why)

| Anti-pattern | Why |
| --- | --- |
| `useEffect` data fetching in client | Use Server Components or TanStack Query with clear cache rules |
| Raw SQL strings in components | Drizzle query builder keeps types and migrations aligned |
| Global mutable singletons in client | Causes stale state and hydration bugs |
| `any` / `@ts-ignore` | Fix the type or narrow the boundary |
| SQLite for heavy write fan-out | Plan Turso/hosted libSQL before multi-region scale |
| Storing secrets in repo | `.env.local` only; CI uses repository secrets |

## Working with Claude Code

When starting a task:

1. Identify whether it touches `schema/`, `server/actions`, or UI only.
2. If schema changes: generate migration in the same PR.
3. If auth-related: check session in server layer, not client guards alone.
4. Prefer extending existing feature folders over new top-level abstractions.

When uncertain, ask **one** clarifying question about tenant scope (single-workspace vs multi-tenant) before coding.
