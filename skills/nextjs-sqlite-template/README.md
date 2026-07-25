# CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a Next.js 15 SaaS project with SQLite (better-sqlite3 / Turso).

## Setup

```bash
# 1. Add to your project
cp CLAUDE.md /path/to/your/project/CLAUDE.md

# 2. Claude Code will now understand your project conventions
#    without asking clarifying questions.

# 3. Create a new greenfield project with these conventions:
npx create-next-app@latest my-saas --typescript --tailwind --app
cp CLAUDE.md my-saas/
```

## What's Included

- **Stack & versions** — Next.js 15, better-sqlite3, Drizzle ORM, NextAuth v5
- **Folder structure** — opinionated but flexible `src/` layout
- **SQL/migration conventions** — SQLite-safe patterns (no enums, no PG syntax)
- **Component patterns** — Server Components by default, Client when needed
- **Anti-patterns** — exactly what NOT to do (and why)

## Tested

Create a new Next.js project, paste this `CLAUDE.md`, then ask Claude Code:
- "Add a teams table with members and roles"
- "Create a server action to invite a user"
- "Build a settings page with theme toggle"

Claude Code will follow the conventions without asking for clarification.
