# Bounty #2 — CLAUDE.md Template: Next.js 15 + SQLite SaaS ($75)

An opinionated, production-ready `CLAUDE.md` for a greenfield SaaS built with
Next.js 15 App Router and SQLite (better-sqlite3 / Turso).

Drop this file as `CLAUDE.md` at the repo root. Every rule has a reason.

---

```markdown
# CLAUDE.md — Next.js 15 + SQLite SaaS

This file guides Claude Code on how to work in THIS repository. Follow it
exactly. When a rule conflicts with a lint error, fix the code, not the rule.

## Stack (do not deviate without asking)
- Next.js 15 App Router (app/ directory, no pages/)
- TypeScript strict mode (no `any` in committed code)
- SQLite via better-sqlite3 (local) or @libsql/client Turso (prod)
- Tailwind CSS for styling (no CSS modules unless component-scoped)
- zod for all runtime input validation

## Project structure (enforce)
app/
  (auth)/            # route group: login, signup
  api/               # route handlers (one file per endpoint)
  dashboard/         # authenticated area
  layout.tsx         # root layout — fonts, providers
  page.tsx           # marketing/home
components/          # shared UI, no business logic
lib/
  db.ts              # single SQLite connection + schema bootstrap
  auth.ts            # session helpers (never read cookies in components)
  validation.ts      # zod schemas, reused by routes
migrations/          # sequential .sql files, numbered 0001_, 0002_...
scripts/             # one-off CLI (seed, migrate)

## Database rules (CRITICAL)
- NEVER write raw SQL string concatenation with user input. Use prepared
  statements: `db.prepare("SELECT * FROM users WHERE id = ?").get(id)`.
  Reason: prevents SQL injection, the #1 SaaS breach vector.
- ALL schema changes go through migrations/ as numbered .sql files.
  Reason: reproducible across dev/prod, reviewable in PR.
- Run `npm run migrate` in every PR that touches schema. CI fails without it.
  Reason: catches missing migrations before deploy.
- One connection only (lib/db.ts). Do not call `new Database()` elsewhere.
  Reason: avoids file-lock contention on SQLite.

## Naming conventions
- Files: kebab-case.ts (e.g. user-profile.tsx)
- Components: PascalCase (e.g. UserProfile.tsx)
- DB tables: snake_case, plural (e.g. user_sessions)
- Env vars: UPPER_SNAKE (DATABASE_URL, not databaseUrl)

## Dev commands (run these, not ad-hoc)
- `npm run dev` — start dev server
- `npm run migrate` — apply pending migrations
- `npm run test` — vitest (must pass before commit)
- `npm run typecheck` — tsc --noEmit (must pass before commit)
- `npm run lint` — eslint (must pass before commit)

## Patterns to follow
- Validate every request body with zod at the route boundary.
  Reason: fail fast, keep handlers thin.
- Keep route handlers ≤ 40 lines; push logic into lib/ or services/.
  Reason: testable, reviewable.
- Use server components by default; add 'use client' only when interactive.
  Reason: smaller JS bundles, better Core Web Vitals.
- Return typed errors: `{ error: string }` with correct status code.
  Reason: predictable API contract for frontend.

## Anti-patterns to avoid
- ❌ `any` type — use proper types or `unknown` + narrowing.
- ❌ Inline SQL in a route handler — put queries in lib/db.ts or a service.
- ❌ Reading process.env outside lib/config.ts — centralize config.
- ❌ `console.log` in production paths — use the logger in lib/log.ts.
- ❌ Mutating shared module state — SQLite is the only source of truth.

## Before you commit
1. `npm run typecheck && npm run lint && npm run test` all green.
2. If schema changed: add migration + run `npm run migrate`.
3. PR title: `feat:`, `fix:`, `chore:`, or `refactor:` prefix.
4. PR body lists the migration file and the testing done.
```
