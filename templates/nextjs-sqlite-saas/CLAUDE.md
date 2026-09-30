# CLAUDE.md — Next.js + SQLite SaaS

> Project context for Claude Code. Read this before making changes.

## 1. Project Overview
A multi-tenant SaaS web app built with **Next.js (App Router)**, **TypeScript**, and a local **SQLite** database accessed through **Drizzle ORM** over **better-sqlite3**. Auth via **NextAuth**. Styling with **Tailwind CSS**.

## 2. Stack
| Layer      | Choice                                   |
|------------|------------------------------------------|
| Framework  | Next.js 14 (App Router, RSC)             |
| Language   | TypeScript (strict)                      |
| Database   | SQLite (better-sqlite3)                  |
| ORM        | Drizzle ORM + drizzle-kit                |
| Auth       | NextAuth (credentials + OAuth)           |
| Styling    | Tailwind CSS                             |
| Tests      | Vitest (unit) + Playwright (e2e)         |
| Package mgr| npm                                      |

## 3. Directory Map
```
app/                 # App Router: routes, layouts, server actions
  (auth)/            # auth-gated route group
  (marketing)/       # public pages
  api/               # route handlers (webhooks, REST)
components/          # shared React components
  ui/                # primitives (Button, Input, ...)
lib/
  db/
    schema.ts        # Drizzle table definitions
    index.ts         # db client (server-only)
    migrations/      # generated SQL migrations (append-only)
  auth.ts            # NextAuth config
  actions/           # server actions ("use server")
drizzle.config.ts
```

## 4. Commands
```bash
npm run dev            # start dev server (localhost:3000)
npm run build          # production build
npm run lint           # ESLint — MUST pass before PR
npm run test           # Vitest unit tests
npm run test:e2e       # Playwright e2e
npm run db:generate    # generate migration from schema changes
npm run db:migrate     # apply migrations
npm run db:seed        # seed dev data
npm run db:studio      # Drizzle Studio
```

## 5. Code Conventions
- **Server vs Client components**: default to Server Components. Add `"use client"` only when you need hooks/events/browser APIs.
- **Data mutations**: use Server Actions in `lib/actions/*` marked `"use server"`. Never call the DB directly from a client component.
- **DB access**: import the client from `lib/db` (server-only). All queries go through Drizzle — no raw SQL strings in components.
- **Typing**: `strict` mode is on. No `any` — use `unknown` + narrowing or define interfaces.
- **Errors**: return typed result objects from actions (`{ ok: true, data } | { ok: false, error }`); never throw across the client boundary.
- **Imports**: use the `@/` path alias (maps to project root).

## 6. Database Rules
- **Migrations are append-only.** Never edit a migration that has been applied. To change a table, update `schema.ts` then run `npm run db:generate`.
- Always **parameterize** queries (Drizzle does this for you — don't interpolate user input).
- Every tenant-scoped table MUST include a `tenantId` column and every query MUST filter by it.
- Add indexes for columns used in `WHERE`/`JOIN` on large tables.

## 7. Testing & Quality Gates
- New logic → add a Vitest unit test.
- New user flow → add a Playwright e2e test.
- Before opening a PR: `npm run lint && npm run test` must both pass.

## 8. Do / Don't
**Do**
- Keep secrets in server-only env vars; access via `process.env` only in server code.
- Co-locate route-specific components under the route folder.
- Prefer small, composable functions.

**Don't**
- Don't expose secrets, tokens, or the SQLite file path to the client bundle.
- Don't use `any` or disable type checks.
- Don't import server-only modules (`lib/db`, `lib/auth`) into client components.
- Don't commit `.env`, `*.sqlite`, or `node_modules`.

## 9. Environment Variables
```
DATABASE_URL=./data/app.sqlite
NEXTAUTH_SECRET=<random-32-bytes>
NEXTAUTH_URL=http://localhost:3000
```
