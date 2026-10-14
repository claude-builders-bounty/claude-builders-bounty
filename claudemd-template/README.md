# CLAUDE.md — opinionated Next.js 15 + SQLite SaaS template

A production-ready `CLAUDE.md` for a small-team SaaS built on Next.js 15
(App Router) and SQLite (better-sqlite3). Drop it into a greenfield project
and Claude Code immediately knows the stack, the folder layout, the migration
rules, the component patterns, and — most importantly — what *not* to do, and
why.

## The opinion (one paragraph)

better-sqlite3 with raw SQL and a thin typed query layer, no ORM. At SaaS
scale the ORM's abstraction costs more than it saves: migrations drift from
the schema, N+1 queries hide behind pretty methods, and the type layer lies
about nullability. Every other rule in the file follows from that stance —
Server Components by default, route files under 40 lines, one query module
per domain, forward-only numbered SQL migrations.

## Sections

- **Stack & versions** — exact pins and the no-ORM reasoning
- **Folder structure** — where new code goes (never in route files)
- **SQL / migration conventions** — numbering, transactions, required
  columns, foreign keys, bound parameters only
- **Component patterns** — server-first, data fetching location, mutation
  paths
- **Naming conventions** — files, components, functions, tables, booleans,
  dates
- **Dev commands** — dev, db:migrate, db:new, test, lint
- **What we don't do (and why)** — no Prisma/Drizzle, no pages/, no fetch in
  client components, no CSS-in-JS, no barrel files, no `any`, no secrets in
  code
- **When the user asks you to...** — the standing order of operations for
  "add a feature", "fix a bug", "refactor"

## Tested

See `examples/PROVENANCE.md`: the template was dropped into a greenfield
Next.js + better-sqlite3 scaffold and a fresh Claude Code session, given only
the task "add a projects feature", created the correct migration (correct
numbering, transaction, columns, foreign key) and the correct typed query
module — **without asking a single clarifying question**. The files it
produced are included verbatim in `examples/`.

## Files

- `CLAUDE.md` — the template (copy this into your project root)
- `examples/` — the comprehension-test scaffold output + provenance
