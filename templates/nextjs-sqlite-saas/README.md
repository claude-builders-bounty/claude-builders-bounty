# Next.js 15 + SQLite CLAUDE.md Template

Production-ready `CLAUDE.md` for Next.js 15 App Router + SQLite (better-sqlite3 / Turso).

## Setup (3 steps)

1. Copy `CLAUDE.md` to your project root.
2. Install: `npm i drizzle-orm drizzle-kit better-sqlite3 @libsql/client zod`
3. Run: `npm run db:generate && npm run db:migrate`

## What it covers

- App Router structure (`app/` routes only, logic in `lib/`)
- SQLite via drizzle-orm — `better-sqlite3` locally, `@libsql/client` in prod
- Typed migrations, seed, and env switch (`DATABASE_URL`)

## Test

Paste into a greenfield `npx create-next-app@latest --ts` + `npm run build` — builds with no extra config.

## Why

$0 infra (SQLite file, no Postgres), edge-ready via Turso, typed SQL without surprises.
