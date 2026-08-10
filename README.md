# CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a SaaS project built with
Next.js 15 App Router and SQLite (`better-sqlite3`).

## What's inside

- **Stack & versions** — pinned choices with a "why" for each
- **Folder structure** — feature-owned folders, explicit anti-patterns
  (no barrels, no `utils.ts` graveyard)
- **SQL / migration conventions** — append-only migrations, named
  parameters, FKs with `ON DELETE CASCADE`, transaction rules
- **Component patterns** — Server Components by default, thin `"use client"`
  leaves, Server Actions + `useActionState` for forms
- **What we don't do (and why)** — 7 explicit anti-patterns with reasons
- **Dev commands** — the full command reference plus the completion gate
- **Working agreement** — migration-first, one-feature-one-PR

## Install (3 steps)

1. `npx create-next-app@latest my-saas --typescript --tailwind --app`
2. Copy `CLAUDE.md` to the project root.
3. Run `npm run dev` once so Claude Code picks up the project context.

The template is written to be usable **without modification** on a greenfield
Next.js + SQLite project: it assumes only what the scaffold ships plus
`better-sqlite3` and `zod`.

## Why opinionated?

Every rule in this file exists because a real project burned the team once:
editing old migrations corrupted staging data, a `useEffect` fetch waterfall
added 400ms of TTFB, and `any` crept into a payment path. Each rule carries
its reason so Claude Code (and new teammates) follow it instead of
negotiating with it.

## Compatibility

- Next.js **15.x** App Router (Server Components, Server Actions)
- `better-sqlite3` 11.x (file-backed SQLite; works on macOS/Linux CI,
  needs `npm install better-sqlite3` on Windows for local dev)
- Auth.js v5 with database sessions
- Tailwind CSS 4.x, zod for validation, vitest for tests
