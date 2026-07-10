# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated guidance for Claude Code (or any agentic coder) working in this
> repository. Edit to match your project's conventions. Keep it short and true.

## Project
- **Stack:** Next.js 15 (App Router), React 19, TypeScript, SQLite (via `better-sqlite3`).
- **Purpose:** [One sentence: what this SaaS does for the user.]
- **Runtime:** Node 20+, npm. Local dev: `npm run dev` → http://localhost:3000.

## Commands
- `npm run dev` — start dev server with hot reload.
- `npm run build` — production build.
- `npm run lint` — ESLint (next/core-web-vitals).
- `npm run test` — run unit tests (Vitest).
- `npm run db:migrate` — apply SQLite migrations in `db/migrations/`.
- `npm run db:seed` — load development seed data.

## Architecture
- `app/` — App Router routes, layouts, and server components.
- `app/api/` — Route Handlers (REST endpoints). Validate input at the edge.
- `lib/db.ts` — single SQLite connection + typed query helpers. **Never open a
  second connection per request.**
- `lib/auth.ts` — session/cookie auth. Do not store secrets in code.
- `components/` — client components (`"use client"` only when needed).

## Database (SQLite)
- All schema lives in `db/migrations/` with sequential `NNN_*.sql` files.
- Use parameterized queries **only** — never string-interpolate user input.
- The DB file is `data/app.db` (gitignored). Never commit it.
- Writes: wrap multi-statement changes in a transaction.

## Conventions
- TypeScript strict mode is on. No `any` without a comment explaining why.
- Server-side code must not import `"use client"` components.
- Prefer Server Components; reach for client components only for interactivity.
- Errors: return structured JSON `{ error: string }` from Route Handlers (HTTP 4xx/5xx).
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`).

## Security
- Secrets come from `.env.local` (never committed). Use `process.env.*`.
- Validate all external input with `zod` at API boundaries.
- Set `httpOnly`, `sameSite: lax` cookies for sessions.
- Don't log secrets, tokens, or full request bodies.

## Testing
- Unit tests beside source as `*.test.ts`. Mock the DB layer, don't hit the file.
- Add a test when fixing a bug (regression coverage).
- Run `npm run test` before opening a PR.
