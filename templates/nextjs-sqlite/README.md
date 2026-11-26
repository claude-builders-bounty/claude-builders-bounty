# Next.js 15 + SQLite SaaS — CLAUDE.md template

An opinionated, production-ready `CLAUDE.md` for a Next.js 15 (App Router) + SQLite SaaS.
Every rule has a stated reason; it is meant to be used **without modification** on a
greenfield project.

## Use it (2 steps)

```bash
# 1. copy into your project root
curl -fsSL https://raw.githubusercontent.com/anlogrian-rgb/nextjs-sqlite-claude-md/main/CLAUDE.md -o CLAUDE.md
# 2. start Claude Code in that repo — it reads CLAUDE.md automatically
claude
```

## What's inside (sections)

- **Stack & versions** — pinned, one router, one data story
- **Folder structure** — colocate by feature
- **SQL & migration conventions** — migrations only, parameterised queries only
- **Data access patterns** — reads/actions split, defense-in-depth authz
- **Component patterns** — Server Components by default
- **Anti-patterns table** — 10 rules, each with the failure it prevents
- **Dev commands** + **Definition of done**

## Consistency check

`sample-project/` mirrors the exact folder layout and two convention examples
(`lib/db/schema.ts`, `lib/env.ts`) described in `CLAUDE.md`, demonstrating the template
describes a real, buildable structure.

## License

MIT
