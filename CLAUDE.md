# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the project brain for Claude Code on a greenfield Next.js 15 + SQLite SaaS.

## Stack
- Next.js 15 (App Router)
- React Server Components by default; Client Components only when interactivity requires it
- SQLite via `better-sqlite3` or Drizzle ORM + `libsql`/`better-sqlite3`
- TypeScript strict
- Tailwind CSS optional but preferred for UI velocity

## Commands
```bash
npm install
npm run dev          # next dev
npm run build        # next build
npm run start        # next start
npm run db:migrate   # apply SQL migrations
npm run db:studio    # optional inspector
npm test             # vitest/jest
```

## Project layout
```
app/                 # App Router routes, layouts, server actions
lib/db.ts            # single SQLite connection helper
drizzle/ or db/migrations/  # ordered SQL migrations
components/          # UI
```

## Migration rules
1. Never edit applied migrations — add a new numbered file.
2. Every schema change ships with a forward migration.
3. Keep migrations idempotent where practical (`IF NOT EXISTS`).
4. Do not store secrets in SQLite; use env vars.
5. Use transactions for multi-statement migrations.

## Patterns
- Server Actions for mutations; validate input with zod
- One DB module; no ad-hoc `new Database()` scattered
- Prefer SQL / Drizzle queries over ORMs with magic
- Feature folders over giant `utils.ts`
- Explicit error boundaries for user-facing failures

## Anti-patterns
- Do not use the Pages Router for new code
- Do not put DB access in Client Components
- Do not commit `.env` or raw SQLite with PII into git
- Do not bypass migrations with manual prod ALTER
- Do not fetch in loops (N+1) — join or batch

## Reasons
Next.js 15 App Router keeps data fetching on the server. SQLite is ideal for single-node SaaS MVPs with zero ops. Migrations make schema history reviewable and reversible.

## Greenfield checklist
1. `npx create-next-app@15`
2. Add SQLite client + first migration creating `users` / `sessions` as needed
3. Wire `lib/db.ts`
4. Add this CLAUDE.md at repo root
5. Run `npm run build` before opening a PR
