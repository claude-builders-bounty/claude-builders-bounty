# Next.js 15 + SQLite SaaS — CLAUDE.md template

A drop-in `CLAUDE.md` for a greenfield Next.js 15 App Router project that
uses SQLite (better-sqlite3 locally, Turso/libSQL in production) via
Drizzle ORM. Paste it at the repo root and Claude Code will know the
project's stack, conventions, and the things it must not do — without
having to ask.

**Implements issue #2 of the [claude-builders-bounty repo](https://github.com/claude-builders-bounty/claude-builders-bounty).**

## What's inside

- `CLAUDE.md` — the template itself (~9 KB, ~1500 words)
- `test_template.py` — a smoke test that verifies every required section
  and must-mention term is present
- This README

The template covers all five sections the bounty lists as required:

1. **Stack & versions** — Node 22, Next 15, TypeScript 5.5, Drizzle,
   better-auth, Tailwind 4, zod, Vitest + Playwright.
2. **Folder structure** — exact layout with a one-line rationale per
   directory, plus the three "no" rules (no `src/`, no barrel
   re-exports, no premature extraction).
3. **SQL & migration conventions** — seven rules covering Drizzle as
   source of truth, append-only migrations, mandatory `id`/`createdAt`/
   `updatedAt` columns, no native enums in SQLite, soft-delete policy,
   no `SELECT *`, and indexes-in-the-same-file.
4. **Component patterns** — Server Components by default, client at the
   leaf, react-hook-form + zod, the shadcn-only button rule, lucide
   icons, date-fns formatting.
5. **What we don't do (and why)** — eleven explicit "no"s, each with
   the one-line reason. This is the section that does the most work in
   practice: it stops the next contributor from re-debating
   `pages/` vs App Router, Prisma vs Drizzle, `next-auth` vs
   `better-auth`, and the rest of the load-bearing decisions.

## How to use

1. Create a new Next.js 15 + SQLite project as you normally would
   (`pnpm create next-app@latest`, add Drizzle, set up `lib/db/`, etc.)
2. Copy `CLAUDE.md` from this directory to the project root.
3. Open the project in Claude Code. The agent will read the file as
   project context and stop asking the questions it would otherwise
   ask about stack, structure, and conventions.

If the project diverges from the assumptions baked into the template
(say, you switched to Prisma), edit the file in place — the template
is a starting point, not a contract. Keep the "What we don't do"
section even if you change the rest; the negative constraints are
what saves the most review cycles.

## Verify it works

```bash
# Smoke test — exits 0 if every required section and must-mention
# term is present, 1 otherwise.
python3 templates/nextjs-sqlite-saas/test_template.py
```

For a deeper test, run the template against a real Claude Code session
on a fresh project: ask Claude to "add a `posts` table with a
`published_at` timestamp, a server action to publish, and a page that
lists published posts ordered by date." If it gets the file right on
the first try without asking about Drizzle, App Router, or
`pnpm`-vs-`npm`, the template is doing its job.

## Why this exists

CLAUDE.md files in the wild tend to be one of two things:

1. **Empty / aspirational.** "Write clean code." "Follow best
   practices." The agent ignores them because they have no actionable
   signal.
2. **Kitchen-sink dumps.** Every rule any contributor ever argued for,
   in no particular order. The agent skims and misses the load-bearing
   constraints.

This template tries to thread the needle: opinionated enough to be
useful, short enough to actually be read (~1500 words), structured so
that the agent can grep for the section it needs, and explicit about
the *non-negotiables* (no `pages/`, Drizzle only, `better-auth` only)
so reviewers don't have to re-debate them in every PR.
