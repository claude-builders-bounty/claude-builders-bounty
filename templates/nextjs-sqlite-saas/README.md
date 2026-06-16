# CLAUDE.md template — Next.js 15 (App Router) + SQLite SaaS

An opinionated, production-ready [`CLAUDE.md`](./CLAUDE.md) for a greenfield SaaS
built with **Next.js 15 App Router** and **SQLite** (better-sqlite3 locally,
Turso/libSQL when you need replicas), using **Drizzle ORM**, **Auth.js (NextAuth
v5)**, **Tailwind**, **Zod**, and **pnpm**.

## Use it

Copy [`CLAUDE.md`](./CLAUDE.md) to the root of your project:

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-saas/CLAUDE.md
```

Then open the repo in Claude Code. It's usable as-is on a fresh project — no
placeholders to fill in. Adjust the stack table only if you swap a library.

## What it covers

- Stack & pinned versions (with the reason for each choice)
- Folder structure and the route-group security boundary
- Naming conventions (routes, components, DB tables/columns, env vars)
- Data layer: the single Drizzle client, WAL + foreign_keys pragmas, tenant scoping
- SQL / migration conventions (generate → review → migrate; never hand-edit applied migrations)
- Component patterns (Server Components by default; Server Actions for mutations)
- Auth (Auth.js v5, route-group protection, server-derived user)
- Dev commands and the pre-commit check
- Testing (in-memory SQLite for units, Playwright for the auth flow)
- **What we don't do (and why)** — the anti-patterns, each with its reason

Every rule states its reason, so Claude follows the intent, not just the letter.
