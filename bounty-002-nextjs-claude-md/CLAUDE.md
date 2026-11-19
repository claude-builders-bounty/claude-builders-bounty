# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Conventions for this project. Claude Code should follow these; ask before deviating.

## Project anatomy

```
src/
  app/               App Router pages + route handlers (no pages/ dir)
  components/         Server Components by default; "use client" inside/ leaves to .client.tsx
  lib/               pure logic, DB access, env parsing — no React imports
  server/            server-only: auth, cron, external API clients
  types/              shared TypeScript types across DB <-> API <-> UI
prisma/                schema + migrations (SQLite)
public/               static assets
```

## Commands

- `npm run dev` — local dev (SQLite file in `prisma/dev.db`, seeded).
- `npm run db:migrate` — `prisma migrate dev`.
- `npm run db:push` — prototype branch only; never on staging/prod.
- `npm run lint` / `npm run typecheck` / `npm test` — must pass before any PR.
- `npm run build` — production build (catches RSC/client boundary bugs).

## DB migration rules

- One migration per schema change. SQLite forbids destructive `ALTER`; prefer additive columns, then a backfill step in the same migration.
- Never `DROP` a column used by a shipped route. Deprecate (soft-delete / nullable) for at least one release, then drop.
- All tables: `id TEXT PRIMARY KEY` (cuid2), `createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`, `updatedAt DATETIME NOT NULL`.
- Raw SQL only in `lib/db`; no SQL strings in components or route handlers.
- Money/quantity columns: INTEGER cents (or DECIMAL strings); never float.

## Patterns to follow

- **Server Components by default.** Only add `"use client"` when you need hooks/event handlers. Every `"use client"` must be justified by an interactive reason.
- Fetch in Server Components (or route handlers) and pass data down. No `useEffect` data fetching.
- Env vars read once, in `server/env.ts`, with `zod` validation.
- DB client is a singleton in `lib/db` (module-scope instance) — never construct per request.
- Auth via an edge-compatible session cookie; middleware only redirects, never reaches into the DB.
- Errors: throw typed errors in server code, map to status codes in route handlers / error.tsx.
- Filenames, table names, components: kebab-case; types PascalCase; hooks `useXxx`.

## Anti-patterns (do not)

- Using `fetch` client-side when a Server Component could do it.
- Putting DB access in a component or `use client` file.
- `any`; use `unknown` + narrowed type. Where Prisma types exist, reuse them.
- Catching errors and returning `200` anyway — log + rethrow handled layers.
- CSS-in-JS that breaks RSC streaming (styled-components is out; Tailwind or CSS Modules in).
- Mutating state during render; effects with no cleanup when subscribed.

## Why these rules (rationale)

- Server-first keeps the whole page tree streaming and reduces client JS. Every `"use client"` boundary doubles as a streaming cutoff.
- SQLite + Prisma is great for SaaS scale but unforgiving with destructive migrations; additive + backfill protects shipping data.
- CENT against float prevents money bugs that Vercel/Stripe audits flag.
- Singleton DB client avoids SQLite `SQLITE_BUSY` / connection leaks under serverless cold starts.
- Zod-validated env means a missing var fails at boot with a clear message, not at runtime mid-request.