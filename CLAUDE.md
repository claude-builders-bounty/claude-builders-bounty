# CLAUDE.md — Next.js + SQLite Project Guide

## Stack & versions

Use this baseline for a new project:

- Next.js 15+ with App Router
- React 19+
- TypeScript with strict mode enabled
- Node.js 20+
- SQLite
- Drizzle ORM with `better-sqlite3`
- Zod for validation
- ESLint

Prefer Server Components by default. Add `"use client"` only when browser APIs, client-side state, effects, or event handlers are required.

## Development commands

```bash
npm install
npm run dev
npm run lint
npm run build
npx drizzle-kit generate
npx drizzle-kit migrate


## Folder structure
- `app/` — routes, layouts, server components and route handlers.
- `components/ui/` — reusable presentation components.
- `components/features/` — feature-specific components.
- `db/` — SQLite connection, schema and migrations.
- `lib/services/` — business logic.
- `lib/validation/` — Zod schemas.
- `public/` — static assets.

Keep database and business logic out of presentation components.

## SQL / migration conventions
Use Drizzle ORM or parameterized queries; never concatenate user input into SQL.
Enable SQLite foreign keys and use explicit primary, foreign, unique and NOT NULL constraints.
Every schema change must have a migration.
Never rewrite an already-applied shared migration; create a new one.
Use transactions when related writes must succeed or fail together.

## Component patterns
Prefer Server Components for rendering and data access.
Use `"use client"` only for browser APIs, state, effects or event handlers.
Keep components small and focused.
Validate external input with Zod on the server.
Perform authentication and authorization on the server.

## What we don't do (and why)
- No direct SQLite access from Client Components — database access stays server-side.
- No SQL string concatenation — prevents injection vulnerabilities.
- No `any` as an escape hatch — preserve TypeScript type safety.
- No business logic inside presentation components — keeps logic reusable and testable.
- No client-only validation — client input cannot be trusted.
- No editing old applied migrations — migration history must remain reproducible.
- No committed secrets, `.env.local`, local databases or `.next` output.

## Definition of done
Before merging, validate inputs, review migrations, run `npm run lint` and `npm run build`, and inspect the diff for secrets or unrelated generated files.
