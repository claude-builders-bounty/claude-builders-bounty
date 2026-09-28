# Greenfield Smoke Test — CLAUDE.md (Bounty #2)

**Date:** 2026-09-28  
**CLAUDE.md:** `templates/nextjs-sqlite/CLAUDE.md` (this PR, commit on `bounty-2-claude-template`)  
**Model:** Claude Code (Fable) — read-only plan mode

## Procedure

1. Created a fresh project:
   ```bash
   npx create-next-app@15.5.2 smoke-next-sqlite --typescript --tailwind --eslint --app --src-dir false --import-alias "@/*"
   cp templates/nextjs-sqlite/CLAUDE.md smoke-next-sqlite/CLAUDE.md
   ```
2. Opened `smoke-next-sqlite` in Claude Code (plan mode, no edits allowed).
3. Prompt:
   > Read CLAUDE.md and describe the stack, SQLite pragmas, migration discipline, and component/data-fetching boundaries you will follow. Do not edit any files.

## Result (read-only, no files were edited)

Claude correctly reported:

- **Stack:** Next.js 15 App Router (React 19 Server Components), TypeScript strict, better-sqlite3 locally / Turso libSQL in prod, Drizzle ORM + drizzle-kit, Tailwind v4 + shadcn/ui, zod, pnpm, Node 22.
- **SQLite pragmas:** `journal_mode = WAL`, `synchronous = NORMAL`, `foreign_keys = ON`, `busy_timeout = 5000`, set at connection open in `lib/db/client.ts`.
- **Migration discipline:** append-only SQL migrations, never edit a merged migration, `db:push` only on unpushed local branches, `db:migrate` dry-run in CI.
- **Component boundaries:** pages/layouts are Server Components by default; `"use client"` only for state/browser APIs; reads via `db.query` in Server Components; writes only through `lib/actions/*.ts` Server Actions with `unknown` + `zod.safeParse`, returning `{ success, data|error }` and calling `revalidatePath`.
- **Anti-patterns:** no `useEffect` fetching, no `db` import in Client Components, no `fetch("/api")` from Server Components to self, no `SELECT *`, no `any`.

No clarifying questions were asked. No files were created or modified beyond the pre-placed `CLAUDE.md`.

## Scope Limitation

This is a read-only comprehension smoke test. It does not claim a full build, migration, lint, typecheck, or Playwright run inside the fresh scaffold. A future iteration may attach those run logs; the current evidence is the plan-modeTranscript showing zero-clarification comprehension.

## AI Disclosure

AI-assisted drafting was used for this template; every technical choice was reviewed against the current Next.js 15 and Drizzle ORM documentation.
