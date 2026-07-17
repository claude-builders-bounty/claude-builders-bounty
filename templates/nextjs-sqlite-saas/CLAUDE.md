# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated agent instructions for a greenfield SaaS app using **Next.js 15 App Router** and **SQLite** (`better-sqlite3` locally; Turso/`@libsql/client` in production if you need multi-region).

Paste this at the repo root. Do not invent a second architecture.

---

## Stack & versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router only) | RSC + route handlers are the product surface |
| Language | TypeScript strict | Fail at compile time, not in prod |
| DB | SQLite via `better-sqlite3` (dev) / Turso optional (prod) | Zero ops for v1; one file you can ship |
| Migrations | SQL files in `db/migrations/` applied by a tiny script | No magic ORM migrations you cannot read |
| Auth | Session cookies (Better Auth / Auth.js style) | SaaS needs users; API keys are additive later |
| Styling | Tailwind + one component kit (shadcn-style) | Ship UI without painting every pixel |
| Validation | Zod at boundaries | Trust nothing from `req` / forms |
| Payments | Stripe or Polar behind a thin adapter | Keep billing out of UI components |

Pin major versions in `package.json`. Do not upgrade Next mid-feature.

---

## Folder structure

```text
app/                 # App Router only — no pages/
  (marketing)/       # public site
  (app)/             # authenticated product shell
  api/               # route handlers only (no business logic dumps)
  layout.tsx
  globals.css
components/
  ui/                # primitives
  features/          # feature-bound composites (billing/, dashboard/)
db/
  migrations/        # 001_init.sql, 002_....sql
  schema.sql         # optional current dump for humans
  client.ts          # single DB entry
lib/
  auth.ts
  env.ts             # zod-parsed env
  money.ts           # cents helpers — never float for money
  errors.ts
scripts/
  migrate.ts
  seed.ts
tests/               # real entrypoints, no reimplementation theater
```

**Rule:** route handlers and server actions call `lib/*` and `db/*`. They do not open SQL ad hoc.

---

## Naming conventions

- Files: `kebab-case.ts` for modules; `PascalCase.tsx` for React components.
- DB tables: `snake_case` plural (`users`, `subscriptions`).
- Columns: `snake_case`; money as **integer cents** (`amount_cents`).
- Env vars: `SCREAMING_SNAKE`; parse once in `lib/env.ts`.
- Server-only modules: import `server-only` at the top when they touch secrets/DB.

---

## SQL / migration rules

1. **Migrations are append-only SQL.** Never edit a shipped migration; add `00N_next.sql`.
2. Every migration is **idempotent where practical** (`CREATE TABLE IF NOT EXISTS`) but still ordered.
3. Apply with `pnpm db:migrate` → runs `scripts/migrate.ts` against `DATABASE_URL` or `./data/app.db`.
4. Foreign keys: `PRAGMA foreign_keys = ON` on every connection.
5. Soft-delete only when product needs restore; prefer hard delete + audit log for secrets.
6. No raw string concat for user input — always bound parameters.
7. Schema changes that need backfill: migration + one-shot `scripts/backfill_*.ts`, not silent half-states.

---

## Component patterns

**Do**
- Server Components by default; `"use client"` only for interactivity.
- Load data in the nearest server parent; pass plain props down.
- Forms: server actions + Zod. Return field errors as data, not thrown HTML.
- Feature folders own their UI + hooks; shared primitives live in `components/ui`.

**Don't**
- Fetch half a page in a client `useEffect` when RSC can do it.
- Put Stripe/secret keys in client bundles.
- Build a global state manager for server data you already have on the tree.

---

## Dev commands

```bash
pnpm install
pnpm dev                 # next dev
pnpm build && pnpm start # prod smoke
pnpm db:migrate          # apply db/migrations
pnpm db:seed             # optional local data
pnpm test                # unit/integration against real modules
pnpm typecheck           # tsc --noEmit
pnpm lint
```

After any DB or auth change: migrate → typecheck → hit the real route once (browser or curl).

---

## Patterns to follow

1. **Money:** store cents, format at the edge. Never `price * 100` with floats mid-calc without integer path.
2. **Auth:** `getSession()` on the server; redirect unauthenticated users before render of private layouts.
3. **Errors:** map known domain errors to HTTP 4xx; log 5xx with request id; never leak stacks to clients.
4. **Idempotency:** webhooks and checkout completes are idempotent by event id.
5. **Feature flags:** simple env or DB flag table; no third platform until you need it.
6. **Logging:** structured JSON lines; no PII in logs.

---

## What we don't do (and why)

| Don't | Why |
|-------|-----|
| Pages Router | Split-brain routing; App Router is the product |
| Prisma/Drizzle required on day one | Fine later; SQL files keep the mental model small for agents |
| Mongo for this SaaS | Relational billing + users; SQLite is enough |
| Microservices for v1 | One deployable beats distributed debugging |
| Client-side secret config | Trivial leak |
| Brochure-copy components | Ship working flows; polish copy when the path converts |

---

## Agent workflow (non-negotiable)

1. Read this file + `package.json` + `db/migrations/` before editing.
2. Prefer the smallest change that satisfies the request.
3. After code changes: `pnpm typecheck` (and `pnpm test` if tests exist).
4. For DB: add migration, run `pnpm db:migrate`, verify with a real query or UI path.
5. Do not invent cash, fake orders, or commit secrets.
6. PR description: what changed, how you verified, migration notes if any.

---

## Anti-patterns to reject

- `any` to silence TypeScript.
- Catching errors and returning `{}` / silent nulls.
- Copy-pasting Stripe samples into React components.
- One mega `utils.ts` that imports the world.
- “Temporary” env defaults that ship to production.

---

## Greenfield bootstrap (3 steps)

1. `npx create-next-app@15 . --ts --app --tailwind --eslint --src-dir=false`
2. Add SQLite client + `db/migrations/001_init.sql` + `scripts/migrate.ts`; set `DATABASE_URL=file:./data/app.db`
3. Drop this `CLAUDE.md` at repo root; run `pnpm dev` and build the first authenticated route

If Claude Code still asks for stack clarification after reading this file, the instructions failed — tighten the stack table, do not add more vague prose.
