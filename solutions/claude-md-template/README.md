# CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a typical SaaS project built with Next.js 15 App Router and SQLite (better-sqlite3).

## What it covers

- **Project structure** — App Router folder conventions, separation of concerns
- **Naming conventions** — Files, components, functions, DB schema, env vars
- **DB migration rules** — Safe migration workflow, soft deletes, indexing
- **Dev commands** — Complete pnpm script reference
- **Patterns to follow** — Server-first, thin route handlers, proper auth checks
- **Anti-patterns to avoid** — 10 specific don'ts with explanations
- **What we don't do (and why)** — Architectural decisions with rationale

## How to use

```bash
# 1. Create a new Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app

# 2. Copy the CLAUDE.md to the project root
cp /path/to/CLAUDE.md my-saas/

# 3. Start Claude Code — it will use the template as project context
cd my-saas && claude
```

That's it. Claude Code will understand the project structure, conventions, and constraints immediately — no clarifying questions needed.

## Why this exists

Most `CLAUDE.md` files are either:
- Too generic ("write clean code")
- Too minimal (just the folder structure)
- Missing opinionated rules that prevent common mistakes

This template is different: **every rule has a reason**. Anti-patterns explain WHY not to do something, not just "don't do this."
