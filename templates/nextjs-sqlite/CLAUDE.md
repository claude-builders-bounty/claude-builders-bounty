# CLAUDE.md — Next.js 15 + SQLite SaaS Project

This file tells Claude Code how this project works. Read it before touching anything.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js 15 (App Router) | RSC, streaming, server actions |
| Database | SQLite via `better-sqlite3` | Zero-ops, embedded, fast for <100k MAU |
| ORM | None — raw SQL only | Migrations are explicit; no magic |
| Auth | `jose` + cookies | Stateless JWT, no external service |
| Styles | Tailwind CSS 4 | Utility-first, no CSS files |
| Deployment | Fly.io (volume-mounted SQLite) | Persistent disk, single-region |

---

## Folder Structure

```
app/
  (auth)/              # Route group — login, register, logout
  (dashboard)/         # Route group — all authed pages
    [teamId]/          # Dynamic segment, always present for authed routes
  api/                 # API routes only when client fetch is unavoidable
  layout.tsx           # Root layout, font loading, metadata defaults
  globals.css          # Tailwind @import only — no custom CSS here
components/
  ui/                  # Dumb, presentational — no data fetching
  [feature]/           # Feature-scoped: components + hooks together
lib/
  db.ts                # Single DB connection singleton (see DB section)
  auth.ts              # Session helpers: getSession(), requireSession()
  [domain].ts          # Domain logic — pure functions, no HTTP, no DB
db/
  migrations/          # Numbered SQL files: 0001_init.sql, 0002_add_teams.sql
  seed.ts              # Dev seed only — never runs in production
types/
  index.ts             # Shared TypeScript types — no inline type declarations
```

**Rules:**
- No `src/` wrapper — app lives at root
- No barrel files (`index.ts` re-exports) — import the file directly
- No `utils/` catch-all — name it after what it does (`lib/email.ts`, not `lib/utils.ts`)

---

## Database & Migrations

**Connection singleton** (`lib/db.ts`):
```ts
import Database from 'better-sqlite3'
import path from 'path'

const DB_PATH = process.env.DB_PATH ?? path.join(process.cwd(), 'data/app.db')

const db = new Database(DB_PATH)
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')

export default db
```

**Migration rules:**
- Files live in `db/migrations/` named `NNNN_description.sql` (zero-padded 4 digits)
- Migrations run on startup via `lib/migrate.ts` — never manually
- Never edit an existing migration file — add a new one
- Every `ALTER TABLE` gets its own migration, even if trivial
- Column defaults must be specified for all new columns added to existing tables

**Query patterns:**
```ts
// Good — typed, prepared
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId) as User | undefined

// Bad — string concat, no types
db.query(`SELECT * FROM users WHERE id = ${userId}`)
```

- Always type the return with `as YourType | undefined` for `.get()`, `as YourType[]` for `.all()`
- Use `.run()` for mutations, check `.changes` when you need to detect no-op updates
- Transactions via `db.transaction(() => { ... })()` — not manual BEGIN/COMMIT

---

## Server Actions & Data Fetching

- Page data: fetch in the Server Component, pass as props — no client-side loading states for initial data
- Mutations: Server Actions in `app/(dashboard)/[teamId]/actions.ts` co-located with the route
- Client-side fetching: only for real-time or user-triggered (search, polls) — use SWR, not `fetch` directly
- Never import server-only code (`lib/db.ts`, `lib/auth.ts`) from a `'use client'` component

**Server Action template:**
```ts
'use server'
import { requireSession } from '@/lib/auth'
import db from '@/lib/db'
import { revalidatePath } from 'next/cache'

export async function updateThing(formData: FormData) {
  const session = await requireSession()  // throws redirect if unauthed
  const name = formData.get('name') as string
  db.prepare('UPDATE things SET name = ? WHERE id = ? AND team_id = ?')
    .run(name, id, session.teamId)
  revalidatePath('/dashboard')
}
```

---

## Component Patterns

**Server Components** (default):
```tsx
// app/(dashboard)/[teamId]/page.tsx
export default async function Page({ params }: { params: { teamId: string } }) {
  const session = await requireSession()
  const data = db.prepare('SELECT ...').all() as Thing[]
  return <ThingList items={data} />
}
```

**Client Components** (only when necessary — interactivity, browser APIs):
- Put `'use client'` as the very first line
- Prefix filename with the route or domain: `ThingForm.tsx`, not `Form.tsx`
- Never do data fetching in a Client Component for initial render

**What we don't do:**
- No `useEffect` for data fetching — that's what RSC is for
- No Redux, Zustand, or global state — server state is the source of truth
- No `getServerSideProps` or `getStaticProps` — App Router only
- No default exports from `components/ui/` — named exports only

---

## Auth

Session is a signed JWT stored in an httpOnly cookie named `session`.

```ts
// lib/auth.ts
import { getSession } from '@/lib/auth'
import { redirect } from 'next/navigation'

export async function requireSession() {
  const session = await getSession()
  if (!session) redirect('/login')
  return session
}
```

- Call `requireSession()` at the top of every protected Server Component and Server Action
- Never trust `session.teamId` from the client — always derive from the server session
- Passwords: `bcrypt` with cost 12, never store plaintext or MD5

---

## Dev Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed dev database (resets data)
npm run build        # Production build
npm run typecheck    # tsc --noEmit (run before every PR)
npm run lint         # eslint (auto-fix with --fix)
```

**Before committing:** `npm run typecheck && npm run lint`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DB_PATH` | No | Path to SQLite file. Defaults to `./data/app.db` |
| `JWT_SECRET` | Yes | 32+ char secret for signing session tokens |
| `NEXT_PUBLIC_APP_URL` | Yes | Full URL of the app (used in emails, OAuth) |

Copy `.env.example` to `.env.local` and fill in values. Never commit `.env.local`.

---

## Anti-Patterns — Don't Do These

| Don't | Do Instead |
|---|---|
| `db.exec(sql)` with user input | Prepared statements with `?` placeholders |
| Inline CSS or `style={}` | Tailwind classes |
| Multiple DB files / connections | Single `lib/db.ts` singleton |
| `any` type | Explicit types or `unknown` + type guard |
| `console.log` left in code | Remove before committing |
| New migration editing old file | New numbered migration file |
| Client Component for static data | Server Component |
| Catch-all `try/catch` silencing errors | Let it throw; handle at boundary |

---

## Git Conventions

- Branch: `feat/short-description`, `fix/short-description`
- Commits: Conventional Commits — `feat:`, `fix:`, `chore:`, `docs:`
- PRs must pass `typecheck` + `lint` in CI before merge
- Squash merge only — no merge commits on `main`
