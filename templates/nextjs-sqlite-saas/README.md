# Next.js 15 + SQLite SaaS CLAUDE.md Template

This folder contains an opinionated `CLAUDE.md` for a greenfield SaaS app using Next.js 15 App Router and SQLite.

## Install

Copy the template into the root of a new app:

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md
```

## Smoke Test Used

The template was checked against a fresh App Router project shape with these assumptions:

- `app/`, `components/`, `lib/`, and `tests/` folders exist or can be created directly.
- SQLite is accessed through a single `db/client.ts`.
- Drizzle migrations live under `db/migrations`.
- Claude Code can answer where to place pages, server actions, migrations, query helpers, and tests without asking for more project structure.

## Why This Is Opinionated

The template intentionally chooses server-first App Router patterns, Drizzle migrations, explicit tenancy checks, and small domain-named modules. That prevents the common SaaS failure modes: unclear data ownership, hidden permission gaps, unreviewable migrations, and generic helper files that become hard to maintain.
