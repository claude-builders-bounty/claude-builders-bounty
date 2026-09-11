# CLAUDE.md — Next.js 15 SaaS + SQLite

Rules are opinionated because each one prevents a real, costly mistake we've hit.
If a rule sounds unnecessary, it probably saves you a debugging session later.

## Stack & versions (pin these)

- **Next.js 15 (App Router)**, React 19. No Pages Router in new code.
- **TypeScript strict**. `noUncheckedIndexedAccess: true`.
- **SQLite**: `better-sqlite3` (server-only) OR Turso/libSQL via `drizzle-orm`.
- **Drizzle ORM** for schema/migrations. Never write raw `CREATE TABLE` in app code.
- Tailwind v4 + shadcn/ui. No CSS-in-JS.

## Folder structure

```
app/
  (auth)/            # login/register, no marketing code
  (main)/            # authenticated routes; group layout holds sidebar
  api/               # route handlers ONLY (input → db → json)
lib/
  db/                # schema.ts, client.ts, migrations/
  server/            # server-only helpers (auth, rbac, billing)
  validators/        # zod schemas — one file per domain
components/
  ui/                # shadcn primitives (do not hand-edit without reason)
  forms/             # react-hook-form + zod resolver wrappers
  business/          # feature components; colocate with their route
services/            # side-effect boundaries (email, stripe, ai, uploads)
tests/
```

- One file → one concern. A file over ~300 lines must be split by a good reason.
- Feature colocation over global folders: a route's page/actions/utils live NEXT to it.

## SQL / migration conventions

- **Schema is the source of truth.** Migrations are generated (`drizzle-kit generate`), committed, and never edited by hand after review.
- Every table gets `id TEXT PRIMARY KEY (crypto random uuid)` and `createdAt`/`updatedAt` (UTC ISO).
- Foreign keys: always `references(..., { onDelete: 'cascade' | 'restrict' })` — never bare FK columns with implicit behavior.
- Soft-delete is opt-in (`deletedAt`), not default — prefer real deletes to avoid every query carrying a filter.
- Any change touching a revenue table (`subscriptions`, `credits`, `orders`) must update balances inside a **single `db.transaction`**. Partial writes = invoice bugs.
- Indexes: index every FK you filter/join on, and every unique constraint you enforce at app level.

## Component & data patterns

- Server Components by default. `'use client'` only for interactivity; keep client boundaries small and pass serializable props.
- `useActionState` + Server Actions for mutations; `Server Action` file per domain (`actions/` colocated). Never call a mutation from a `useEffect`.
- Data fetching: Server Component `await` directly; no SWR/React Query unless streaming a cross-section dashboard.
- Forms: `react-hook-form` + a zod schema from `lib/validators/`; show field errors from `zodResolver`; never trust the client — re-validate in the action.
- Money & rates: integer minor units (cents) stored as `INTEGER`. Never `float` for currency. Format only at render.

## What we don't do (and why)

- **No global `any`, no `@ts-ignore`.** Strict mode exists to catch migration & billing type errors. Silence = debt.
- **No ORM magic beyond Drizzle.** No Prisma/Sequelize/Mongoose: we need sync, typed, near-SQL control for SQLite perf.
- **No server-side `fetch` without timeout + retry.** AI/email/Stripe calls must not hang a request; use `AbortSignal.timeout` and a small retry wrapper.
- **No business logic in route handlers or components.** Actions/service layer only; routes stay dumb (parse → call → respond).
- **No `console.log` in production paths.** Use the logger with request ids.
- **No new global CSS or tailwind config tweaks** without discussing — theming is centralized in `globals.css` for a reason.
- **Booking/charging anything called "premium" behind a flag** without an associated payment path — gating a feature with no price = stranded code.

## Dev commands

```bash
npm run dev          # next dev
npm run db:generate  # drizzle-kit generate (after schema change)
npm run db:migrate   # apply pending migrations
npm run lint         # eslint . (must pass before PR)
npm run typecheck    # tsc --noEmit
npm test             # vitest (lib/ + services/ unit tests)
```

## Conventions checklist

- [ ] Feature has a zod input schema; action re-validates
- [ ] DB change has generated migration + index on new FKs
- [ ] Currency in minor units
- [ ] Mutations in transaction when multi-write
- [ ] lint + typecheck + tests green