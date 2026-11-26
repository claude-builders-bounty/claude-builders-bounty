# CLAUDE.md template — Next.js 15 + SQLite SaaS

An opinionated `CLAUDE.md` for a single-node SaaS built on Next.js 15 (App
Router) and SQLite (`better-sqlite3`). Every rule states the failure it prevents,
so Claude Code can follow it without asking what you "probably meant".

## Use it

```bash
# greenfield
pnpm create next-app@latest my-saas --ts --app --tailwind
cp CLAUDE.md my-saas/CLAUDE.md

# existing project: merge, do not overwrite — keep the sections you already obey
```

## Test it (the acceptance check, reproducible)

1. Create a fresh app with the command above. Nothing else — no schema, no auth,
   no components.
2. Paste `CLAUDE.md` at the repo root, open Claude Code, and give it a task that
   would normally force questions:
   > "Add a `projects` table with a name and an owner, a dashboard list page, and
   > a form that creates a project."
3. Watch for clarifying questions. With this file the answers are already
   decided: `projects` (plural snake_case), `name TEXT NOT NULL`,
   `owner_id` → `users(id) ON DELETE CASCADE`, timestamps as ISO-8601 `TEXT`,
   migration `0002_add_projects.sql`, query module
   `lib/db/queries/projects.ts`, Server Component page + `'use client'` form +
   Server Action with a Zod schema, `LIMIT 50`, `revalidatePath`.
   The only legitimate question left is the product one — what a project *is*.

If Claude asks about ORM choice, folder layout, migration naming, where to put
the query, or whether the form needs a client component, this template has a gap —
send a PR.

## What it pins down

| Area | Decision |
|---|---|
| Stack | Next 15 App Router, TS strict, Node 20, better-sqlite3 (WAL), Zod, Tailwind, pnpm |
| Structure | `app/` route groups, `components/{ui,<domain>}`, `lib/{db,auth}`, one feature = one folder, dependency direction `app → components → lib` |
| Naming | kebab-case files, PascalCase components, plural snake_case tables, zero-padded migration numbers |
| SQL | forward-only numbered migrations, FK `ON DELETE` explicit, ISO-8601 TEXT timestamps, integer cents, module-level prepared statements, `LIMIT` mandatory, indexes with the query |
| Components | Server Component by default, actions for writes, Zod at every boundary, ownership enforced in SQL |
| Anti-patterns | ORM, `pages/`, client-side fetching of own API, Redux for server state, `any`/`@ts-ignore`, per-component resets, unbounded lists |
| Done | lint + typecheck + unit + build + migration on fresh DB |

## Why this is not generic advice

Each rule names the alternative it rejects and the incident it prevents — e.g.
SQLite defaults `foreign_keys` to off, so the template makes `PRAGMA
foreign_keys = ON` a starting assumption and requires explicit `ON DELETE`
behaviour; `SELECT *` is banned outside the mapper so a new column cannot silently
reshape a payload.

Size: ~330 lines — long enough to remove ambiguity, short enough to stay in
context. Trim sections you genuinely do not need; do not trim the reasons.

MIT, same as the repository.
