# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS

Opinionated, production-ready guidance for AI agents and contributors working in this SaaS codebase.

## Project Structure

```
/
├── src/
│   ├── app/                      # Next.js App Router (routes, layouts, pages)
│   │   ├── (auth)/               # Route group: login, register, forgot-password
│   │   ├── (dashboard)/          # Route group: authenticated app shell
│   │   ├── api/                  # Route Handlers (REST endpoints)
│   │   ├── layout.tsx            # Root layout
│   │   └── page.tsx              # Landing / home
│   ├── components/               # Shared UI (server + client)
│   │   ├── ui/                   # Primitive components (Button, Input, Card)
│   │   └── *.tsx
│   ├── lib/
│   │   ├── db.ts                 # SQLite client (better-sqlite3 or Turso @libsql/client)
│   │   ├── auth.ts               # Session / password hashing helpers
│   │   └── validators.ts         # zod schemas shared by API + forms
│   ├── migrations/               # SQL migration files (numbered, ordered)
│   └── styles/                   # globals.css, tailwind entry
├── public/                       # Static assets
├── tests/                        # Unit + integration tests
├── migrations/                   # (alt) migration scripts if not under src/
├── package.json
├── next.config.ts
├── tsconfig.json
└── tailwind.config.ts            # or .ts if using Tailwind v4
```

## Naming Conventions

- **Files:** `kebab-case.ts(x)`. Route folders may use `(group)` and `[param]` / `[...slug]`.
- **Components:** `PascalCase.tsx`, one component per file, default export.
- **Functions:** `camelCase`. `async` functions prefix intent, not `get`/`do` noise.
- **Types:** `PascalCase`, co-located with usage or in `src/lib/types.ts`.
- **DB tables:** `snake_case`, plural (`users`, `subscription_plans`). Columns `snake_case`.
- **Env vars:** `UPPER_SNAKE_CASE`, prefixed by concern (`DB_`, `AUTH_`, `STRIPE_`). Never commit `.env`.

## Database Migration Rules (SQLite)

- **Never edit a committed migration.** Write a new, ordered, idempotent migration (`0003_add_invoices.sql`).
- Migrations run oldest → newest; keep them small and reversible where possible.
- Use `better-sqlite3` for local dev; `Turso` (`@libsql/client`) for prod — same SQL dialect, so avoid vendor-only pragmas.
- Always wrap multi-statement schema changes in a transaction.
- After adding a column/table, update the corresponding zod validator and the TypeScript type.
- Run `pnpm db:migrate` (or `npm run db:migrate`) before starting the dev server on a fresh clone.

## Dev Commands

```bash
pnpm install            # install deps
pnpm dev                # next dev (hot reload, :3000)
pnpm build              # production build
pnpm start              # serve production build
pnpm lint               # eslint
pnpm test               # vitest / jest
pnpm db:migrate         # apply pending SQL migrations
pnpm typecheck          # tsc --noEmit
```

## Patterns to Follow

- **Server Components by default.** Only add `'use client'` when you need state, effects, or browser APIs.
- **Validate at the edge:** parse all request input with `zod` in Route Handlers before touching the DB.
- **Parameterized queries only.** Never interpolate user input into SQL strings — use prepared statements.
- **Auth:** verify session in a shared middleware/helper; never trust client-sent `userId`.
- **Errors:** return structured JSON (`{ error: string }`) with correct HTTP status; let the global error boundary render.
- **Secrets:** read from env at runtime; fail fast on missing required vars.

## Anti-Patterns to Avoid

- ❌ Mutating committed migrations to "fix" a mistake — add a new one.
- ❌ Raw SQL string concatenation with user input (SQL injection).
- ❌ Putting secrets in client components or committing `.env*`.
- ❌ `any` for DB rows — define explicit types.
- ❌ Fetching in a Server Component when the data is per-request user input best handled in a Route Handler.
- ❌ Silent `catch {}` that swallows errors; log or rethrow.
- ❌ Mixing Tailwind v3 and v4 config styles without migrating consistently.

## Testing

- Unit-test pure helpers in `src/lib` (validators, auth hashing).
- Integration-test Route Handlers against a throwaway SQLite file.
- Keep tests hermetic: no real network, no real secrets.
