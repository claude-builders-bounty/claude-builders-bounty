# Next.js 15 + SQLite SaaS — opinionated CLAUDE.md template

Production-grade `CLAUDE.md` you can paste into a greenfield Next.js 15 +
SQLite SaaS project. Every rule has a reason.

## What's in the box

- **§1 Stack & versions** — pinned table with the *why*, not the *what*
- **§2 Folder structure** — exact directory tree with place-rules
- **§3 SQL & migration conventions** — Drizzle ORM, WAL, soft-delete, prepared statements, what we don't do
- **§4 Component patterns** — Server Component default, Server Actions for mutations, Client islands
- **§5 What we don't do** — explicit anti-patterns with reasons
- **§6 Dev commands** — single source of truth for `pnpm` scripts
- **§7 Quick greenfield check** — 4 commands that prove the project is shippable

## Usage (3 steps)

```bash
# 1. Drop the file at the root of your project
cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md

# 2. Run Claude Code in the same directory — it reads CLAUDE.md on startup
claude

# 3. Verify with the greenfield check:
pnpm typecheck && pnpm lint && pnpm test
```

That's it. Paste, run, ship.

## Why this exists

Generic CLAUDE.md templates tell Claude what you have. This one tells it what
you *don't have* and why — which is what stops it from adding Prisma,
Pages Router, or `useEffect` data fetching when it's helpful in isolation but
inconsistent with the rest of the codebase.
