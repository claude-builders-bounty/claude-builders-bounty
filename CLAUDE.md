# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Structure
```
app/          — App Router pages & API routes
components/  — Reusable React components
lib/         — Utility functions, db client, auth
db/          — Migrations, seeds, schema
public/      — Static assets
```

## Commands
```bash
npm run dev       # Next.js dev server (localhost:3000)
npm run build     # Production build
npm run lint      # ESLint + type-check
npm run test      # Vitest
npm run db:migrate  # Run pending migrations
npm run db:studio  # Open Drizzle Studio
```

## DB Rules
- **Every change** needs a migration file in `db/migrations/`
- **NO raw SQL** in app code — use Drizzle ORM
- **Foreign keys** must be indexed
- **Soft deletes** (`deleted_at`) preferred over DROP
- **Row-level security** via `tenant_id` on every table

## Anti-patterns
- ❌ `'use client'` on server components — waterfall loading
- ❌ `fetch()` in `useEffect` — use Server Actions or RSC
- ❌ `DELETE FROM` without `WHERE` — blocks in CI
- ❌ `any` type — use `z.infer<typeof schema>`
- ❌ Direct SQL strings — use Drizzle typed queries
- ❌ `process.env` in client components — use `NEXT_PUBLIC_` prefix

## Naming
```
files:       kebab-case.ts, snake_case.sql
components:  PascalCase.tsx
functions:   camelCase()
types:       PascalCase (interface), TypeName (type alias)
env vars:    UPPER_SNAKE_CASE
migrations:  YYYYMMDD_description.sql
```

## PR Checklist
- [ ] No secrets in code (check `.env` not committed)
- [ ] Migration is reversible (`down.sql` exists)
- [ ] Type safety: no `any` or `as unknown as X`
- [ ] Error boundary or try/catch on API routes
- [ ] Test covers the happy path
