# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> Copy this into your repo root as `CLAUDE.md`. Edit the **Project Identity** section only.

## Project Identity (EDIT ME)

- **Project**: [Name]
- **Stack**: Next.js 15 (App Router) · TypeScript · better-sqlite3 · Tailwind v3
- **Runtime**: Node 20 LTS
- **Package Mgr**: pnpm
- **DB**: SQLite local dev · Turso production

---

## Commands

```bash
pnpm dev        # dev server http://localhost:3000
pnpm build      # production build
pnpm start      # serve production build
pnpm lint       # ESLint
pnpm typecheck  # tsc --noEmit
pnpm test       # vitest
pnpm db:migrate # run pending migrations (drizzle-kit)
pnpm db:seed    # seed dev DB
```

## Folder Structure

```
src/
├─ app/                    # App Router — one folder = one route segment
│  ├─ layout.tsx           # root layout (keep it lean)
│  ├─ page.tsx             # home page
│  ├─ api/                 # Route Handlers (server-only, no UI)
│  │  └─ v1/resource/
│  │     └─ route.ts       # GET/POST/PUT/DELETE
│  └─ (auth)/login/        # route groups (no URL segment)
├─ components/
│  ├─ ui/                  # shadcn/ui primitives (no business logic)
│  ├─ shared/              # reused across pages
│  └─ feature/             # co-located with feature code
├─ lib/
│  ├─ db.ts                # drizzle client — ONE connection pool
│  ├─ auth.ts              # auth helpers (better-auth or custom)
│  ├─ http.ts              # fetch wrapper, timeout, error handling
│  └─ utils.ts             # pure functions only
├─ server/                 # server-only code (never import in client components)
│  ├─ queries/             # parameterized DB queries
│  ├─ actions/             # Server Actions — one file per action
│  └─ services/            # domain logic, called by actions/handlers
├─ types/                  # shared TS types (no runtime value)
└─ constants/              # magic strings, feature flags
```

## Naming Conventions

| Thing | Pattern | Example |
|-------|---------|---------|
| Files | kebab-case | `user-profile.tsx` |
| Components | PascalCase | `UserProfile.tsx` |
| Functions/ vars | camelCase | `fetchUserById()` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Types/ interfaces | PascalCase | `type UserProfile` |
| DB tables | snake_case plural | `user_profiles` |
| DB columns | snake_case | `created_at` |

## SQL / Migrations

- **Single source of truth**: drizzle schema at `src/db/schema.ts`
- Never write raw SQL in components. Use `src/server/queries/`
- Every schema change = new migration file in `drizzle/000X_*.sql`
- Migrations are **immutable** — never edit a committed migration
- Run migrations before writing code that uses new columns
- SQLite gotcha: no `ALTER TABLE ADD COLUMN` with default+NOT NULL in one step — do it in two migrations

## Component Patterns

### Server Components (default)
- Fetch data directly with `db.query()` in the component
- Pass data to child client components as props
- **Don't** pass raw DB objects — shape them first

### Client Components ("use client")
- Mark at the top of file
- Import only from `components/`, `lib/`, `react` — never `server/`
- Fetch with SWR or TanStack Query (not `useEffect` + raw fetch)
- Keep under 200 lines — extract hooks/helpers when it grows

### Route Handlers
- Live in `app/api/**/route.ts`
- Return `Response` object (not NextResponse unless you need cookies/headers)
- One handler file per HTTP verb if logic diverges

### Server Actions
- Live in `src/server/actions/` — **not** in route handler files
- Mark `"use server"` at the top of the function
- Wrap all mutation actions in DB transactions
- Validate all inputs with zod before touching the DB

## Anti-Patterns (DO NOT DO THESE)

| ❌ Don't | ✅ Do | Why |
|----------|-------|-----|
| Import `server/*` in client components | Keep server code isolated | Breaks at build time, leaks secrets |
| Put DB queries in route handlers | Use `src/server/queries/` | Testability + reuse |
| `useEffect` + `fetch` for data | SWR or TanStack Query | Race conditions + stale cache |
| Magic strings ("pro", "admin") | `constants/roles.ts` | Typos = silent bugs |
| Big bang components (>300 lines) | Extract to `components/feature/` | Readability + reusability |
| Direct `INSERT`/`UPDATE` in multiple places | Server Actions as single entry | Data consistency |
| Forget `await` on async DB calls | Always `await` | Silent data loss |
| Hardcode localhost:3000 | `process.env.NEXT_PUBLIC_APP_URL` | Breaks in preview/prod |

## Auth Rules

- All protected routes live under a `(protected)/` route group with a `layout.tsx`
- Check auth in the layout — redirect to `/login` if unauthenticated
- Never trust client-side auth checks alone; re-verify on every Server Action/API route
- User ID comes from `session.user.id`, never from URL params or client state

## Database Gotchas (SQLite-specific)

- `INTEGER PRIMARY KEY` autoincrement — but `BIGINT` doesn't. Use `INTEGER` for IDs
- No native BOOLEAN — use `INTEGER` (0/1)
- DateTime = Unix epoch seconds (INTEGER) in production, ISO strings during dev
- Enums = CHECK constraints + a tiny lookup table
- WAL mode for better concurrent reads: `PRAGMA journal_mode = WAL;`

## Feature Flags

- Live in `constants/flags.ts` as `const FEATURE_X = process.env.FEATURE_X === "1"`
- Check once at server boot, not per-request
- Remove flag + old code after 1 release cycle — no permanent flags
