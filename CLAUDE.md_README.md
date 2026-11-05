# CLAUDE.md Template — Next.js 15 + SQLite SaaS

Production-ready `CLAUDE.md` for a typical SaaS project.

## How to use (3 steps)

```bash
# 1. Start a new project
pnpm create next-app@latest my-saas --typescript --tailwind --eslint
cd my-saas
pnpm add drizzle-orm better-sqlite3 @libsql/client

# 2. Drop in CLAUDE.md
cp path/to/CLAUDE.md ./CLAUDE.md

# 3. Edit only the "Project Identity" section at the top
# Done — Claude Code will follow all conventions automatically
```

## What's inside

- **Folder structure** with purpose annotations
- **Naming conventions** — table of patterns with examples
- **SQL / migration rules** — drizzle-first, immutable migrations, SQLite gotchas
- **Component patterns** — Server vs Client, Route Handlers, Server Actions
- **Anti-patterns table** — 8 common mistakes + why to avoid
- **Auth rules** — protected route groups, re-verify server-side
- **SQLite gotchas** — INTEGER IDs, no BOOLEAN, WAL mode
- **Feature flags** — one-release expiry rule

## Opinionated, not generic

Every rule has a reason. Example:

> *Why "Components under 200 lines"?* — Because files over 200 lines have statistically 3× more bugs and take 2× longer to review (Google code review data).
>
> *Why drizzle schema as single source?* — Schema-first means TypeScript types are auto-generated from your DB definition, guaranteeing column names never drift from code.
