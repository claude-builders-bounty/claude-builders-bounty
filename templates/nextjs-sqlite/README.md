# Next.js 15 + SQLite SaaS — CLAUDE.md Template (Bounty #2)

Opinionated, production-ready `CLAUDE.md` for a greenfield SaaS built with **Next.js 15 App Router** and **SQLite** (`better-sqlite3` locally, Turso in prod) via **Drizzle ORM**.

## What's inside the CLAUDE.md

- Stack & pinned versions with reasons
- Dev commands and required commit gate
- Folder structure (one place per kind of code)
- SQLite pragmas (WAL, foreign_keys, busy_timeout) + schema & migration discipline
- Naming conventions (files, components, DB)
- Server Components first + Server Actions for mutations + zod validation
- Auth/session rules, testing strategy, anti-patterns table
- When to leave SQLite, CI gate, quick start

Every rule has a `reason:` — Claude Code can apply the template without asking clarifying questions.

## Usage

```bash
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir false
cp templates/nextjs-sqlite/CLAUDE.md my-saas/CLAUDE.md
# then in Claude Code: "follow CLAUDE.md and scaffold auth + db + dashboard"
```

## Greenfield smoke test (2026-09-28)

1. `npx create-next-app@15.5.2 my-smoke --typescript --tailwind --eslint --app`
2. Copied `CLAUDE.md` unchanged to `my-smoke/CLAUDE.md`.
3. Prompted Claude Code (plan mode, read-only): _"Read CLAUDE.md and describe the stack, DB pragmas, migration discipline, and component boundaries you will follow."_
4. Result: Claude identified Next.js 15 + better-sqlite3/Turso + Drizzle + zod, the four WAL pragmas, append-only migrations, and Server Component / Server Action boundaries without asking a clarifying question. No files were edited or created beyond the pasted `CLAUDE.md`.

> AI-assisted drafting was used; all technical choices were reviewed against current Next.js 15 and Drizzle documentation.

## Verification

See [`verification/claude-code-greenfield-smoke.md`](./verification/claude-code-greenfield-smoke.md).
