# CLAUDE.md — Next.js 15 + SQLite SaaS Project

This file gives Claude Code (and human teammates) the operating rules for this
codebase. **Read it before writing any code.** Every rule here exists because
violating it caused a real incident or a structural headache.

---

## 1. Stack & Versions (locked)

| Layer | Choice | Why (and why not alternatives) |
|---|---|---|
| Framework | Next.js 15 (App Router) | RSC + server actions are the default; Pages Router is legacy |
| Language | TypeScript strict | `strict: true`, no `any` escapes |
| Database | SQLite via `better-sqlite3` | Zero-ops, synchronous, transactional; **no ORM** |
| Migrations | Hand-written SQL files in `db/migrations/` | ORMs hide schema truth; SQL files are reviewable and reversible |
| Auth | `next-auth` v5 (Auth.js) | App Router native; sessions in DB, not JWT (revocable) |
| Validation | `zod` at every boundary | One schema = API input + form + DB row shape |
| Styling | Tailwind CSS v4 | Utility-first; no CSS-in-JS runtime cost |
| Tests | `vitest` + `@testing-library/react` | Fast; no Jest config hell |

**Do not introduce:** Prisma (magic + codegen drift), tRPC (unnecessary for
server actions), Redux (React state + URL search params cover 99%).

---

## 2. Folder Structure

```
app/                    # App Router routes (colocate everything)
  (auth)/               # login/signup — route group, no URL prefix
  (dashboard)/          # authed pages — group with layout that checks session
  api/                  # route handlers ONLY for non-RSC needs (webhooks, uploads)
  layout.tsx            # root layout: fonts, providers
components/
  ui/                   # dumb, presentational (Button, Input, Dialog)
  features/             # smart, feature-bound (billing/, projects/, auth/)
  shared/               # cross-feature (empty state, error boundary)
db/
  migrations/           # 001_*.sql, 002_*.sql ... (never edited after apply)
  schema.ts             # types derived from SQL, kept in sync by hand (reviewed)
  index.ts              # better-sqlite3 singleton + WAL pragma
lib/
  auth.ts               # auth config (next-auth v5)
  validations/          # zod schemas, one file per domain
  utils.ts              # tiny helpers only (cn, formatDate) — no business logic
public/
tests/
  unit/                 # vitest: components + pure functions
  integration/          # DB + server actions
.env.example            # committed; .env* gitignored
```

**Rule:** a file's location must be predictable from its name. If you can't
guess where a file lives in 5 seconds, the structure is wrong.

---

## 3. SQL / Migration Conventions

- **One migration = one logical change.** No bundling schema + seed + backfill.
- File format: `db/migrations/001_create_users.sql`, sequential, never renumbered.
- Every table gets `created_at TEXT NOT NULL DEFAULT (datetime('now'))` and
  `updated_at TEXT NOT NULL DEFAULT (datetime('now'))`.
- Foreign keys: `PRAGMA foreign_keys = ON;` at connection, enforced in SQL.
- **No `ALTER TABLE` in application code.** Schema changes are migrations only.
- Never store money as `REAL`. Use `INTEGER` cents / smallest unit, or `TEXT` for crypto.
- `db/index.ts` opens **one** singleton connection with `journal_mode = WAL`
  and `busy_timeout = 5000`. Never open a second connection in the same process.
- Server Actions touch the DB **synchronously** (better-sqlite3 is sync — embrace
  it, don't wrap it in `async` pretend-work).
- Every query that writes goes through a transaction if it touches ≥2 tables.

---

## 4. Component Patterns

- **Server Component by default.** If a component needs `useState`/`useEffect`,
  add `"use client"` deliberately — not by habit.
- Data fetching in RSC: `async function` components calling `lib/` directly. No
  `fetch` wrappers for internal data (DB is local; skip HTTP round-trip).
- Mutations go through **Server Actions** in `app/` colocated files
  (`actions.ts` next to the route), validated with zod, then `revalidatePath()`.
- Buttons that trigger actions: use `useActionState` (Next 15) for pending state —
  no bespoke `isLoading` flags.
- Error handling: route-level `error.tsx` + `not-found.tsx`. Never throw raw
  `Error` to the UI; map to user messages.
- Forms: uncontrolled + `useActionState`, not controlled + `useState` soup.

---

## 5. What We Don't Do (and why)

| Don't | Why |
|---|---|
| `useEffect` + `fetch` for data that RSC can provide | Double network round-trips, loading flicker, stale state |
| Import server-only code into client components | Next.js bundle leaks secrets; use `server-only` package |
| Store secrets in `.env.local` uncommitted and undocumented | `.env.example` documents every var; deploy uses real env |
| Delete migrations to "clean up" | History is the source of truth for DB state |
| Write a migration without a down-path (at least a note) | Rollbacks are rare but impossible without the note |
| Use `any` for "speed" | Every `any` is a runtime bug waiting for production |
| Add a dependency to avoid 10 lines of code | Each dep = supply chain + bundle + API drift surface |
| Query the DB from a Client Component | Client can't touch `better-sqlite3` (server-only); do it in a Server Action |
| Commit generated files (`next-env.d.ts` updates ok; `dist`, `.next` never) | CI must build from source only |

---

## 6. Dev Commands

```bash
npm install          # install deps
npm run dev          # dev server (http://localhost:3000)
npm run db:migrate   # apply pending migrations (db/migrations/*.sql in order)
npm run db:seed      # idempotent seed (dev only)
npm run test         # vitest run
npm run test:watch
npm run lint         # eslint + tsc --noEmit (must pass before push)
npm run build        # production build (validates types + RSC boundaries)
```

**Definition of done:** `npm run lint && npm run test && npm run build` all green.

---

## 7. Conventions Summary (the 30-second version)

1. TypeScript strict, zod at every boundary, no `any`.
2. Server-first: RSC + Server Actions + better-sqlite3 (sync).
3. SQL migrations hand-written, sequential, immutable once applied.
4. Colocate: files live with the feature they serve.
5. Every rule above has a "why" — if you disagree, open a discussion, don't silently deviate.
