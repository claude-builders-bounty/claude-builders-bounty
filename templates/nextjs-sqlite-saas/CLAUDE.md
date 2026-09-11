# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated operating manual for this stack. Prefer these rules over generic Next advice.

## Stack (locked)
- **Next.js 15** App Router only (`app/`). No Pages Router files.
- **React Server Components default.** Add `"use client"` only for interactivity (forms with local state, charts, drag/drop).
- **SQLite** via `better-sqlite3` (local/dev) or **Turso/libSQL** (prod). One DB access module; never open ad-hoc connections in components.
- **Auth** lives in `lib/auth.ts` (session cookies). No client-readable secrets.
- **Validation** with Zod at every server action / route boundary.

## Tree
```
app/
  (marketing)/          # public pages
  (app)/                # authed product shell
    layout.tsx
    page.tsx
  api/                  # route handlers only when actions are insufficient
  layout.tsx
components/             # UI only; no direct DB
lib/
  db.ts                 # single getDb() singleton
  auth.ts
  validations/          # zod schemas
db/
  migrations/           # numbered SQL: 001_init.sql, 002_....sql
  migrate.ts            # applies migrations in order
scripts/
```

## Naming
- Files: `kebab-case.ts`. Components: `PascalCase.tsx`.
- Server actions: `verbNounAction` in `app/**/actions.ts`.
- DB tables: `snake_case` plural (`users`, `billing_events`).
- Columns: `snake_case`; booleans `is_`/`has_`; timestamps `*_at` UTC ISO.

## Database rules
1. **All schema changes are migrations.** No `CREATE TABLE` in app boot except migrate runner.
2. Migrations are **forward-only** numbered SQL; never edit a shipped migration—add a new one.
3. Use **transactions** for multi-statement writes (`db.transaction(() => { ... })()`).
4. **Prepared statements only** — no string-concat SQL.
5. Read path: prefer plain SQL in `lib/` repositories (`lib/repos/users.ts`), not ORM magic.
6. SQLite: `PRAGMA foreign_keys = ON;` on every connection.
7. Turso prod: same SQL dialect; `lib/db.ts` switches driver via `DATABASE_URL`.

## Data flow
- Browser → Server Action or Route Handler → Zod parse → repo/db → return plain DTO.
- **Never** import `better-sqlite3` from a Client Component.
- Prefer Server Actions for mutations; Route Handlers for webhooks/webhooks signatures and external APIs.

## UI patterns
- Server Components fetch data; pass serializable props to clients.
- Forms: `<form action={serverAction}>` + `useFormStatus` for pending.
- Errors: return `{ ok: false, error: string }` from actions; don't throw for expected validation fails.
- Loading: `loading.tsx` per segment; avoid full-app spinners.

## Dev commands
```bash
npm run dev              # next dev
npm run build && npm start
npm run db:migrate       # node db/migrate.ts
npm run db:studio        # optional sqlite viewer
npm run lint
npm run test             # unit tests for repos + zod
```

## Env
- `DATABASE_URL` — file path (`file:./data.db`) or libSQL URL
- `SESSION_SECRET` — 32+ bytes
- Never commit `.env*`; provide `.env.example` only

## Anti-patterns (do not)
- `useEffect` data fetch when a Server Component can load it
- Client-side SQL or exposing DB URL
- Storing sessions only in localStorage
- Giant `utils.ts` god files — split by domain
- Disabling ESLint to ship
- Editing old migrations
- Catch-all `any` on action inputs

## Why these rules
- SQLite + serverless edge is painful if you open many write connections — **one module, short transactions**.
- App Router mental model breaks when client components become data gateways — **keep IO on the server**.
- Migrations-as-code keeps Turso/local parity and reviewable schema history.

## When unsure
1. Check `lib/repos/*` for an existing query.
2. Add a migration + repo method + zod schema + server action.
3. Only then add UI.
