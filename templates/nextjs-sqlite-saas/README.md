# Next.js 15 + SQLite SaaS — CLAUDE.md Template

An opinionated `CLAUDE.md` for greenfield SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3 / Turso).

## Setup (3 steps)

1. **Create your project:**
   ```bash
   npx create-next-app@latest my-saas --typescript --tailwind --app --eslint --src-dir=false
   cd my-saas
   ```

2. **Copy the CLAUDE.md into your project root:**
   ```bash
   curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-saas/CLAUDE.md
   ```

3. **Start Claude Code — it knows what to do:**
   ```bash
   claude
   ```

That's it. Claude Code will read the CLAUDE.md and understand your full stack context — folder conventions, database rules, component patterns, and what not to do.

## What's Included

| Section | Purpose |
|---|---|
| Stack & Versions | Exact tech choices with reasoning |
| Folder structure | Where everything goes (and doesn't) |
| Database & Migrations | Drizzle-first, SQLite-safe patterns |
| Component patterns | Server-first, client only when needed |
| Server actions | Validated mutations with proper error handling |
| Auth rules | Better Auth session strategy |
| Dev commands | One-liners for dev, test, lint, typecheck |
| Anti-patterns table | 10 things to never do (with alternatives) |
| Environment validation | Zod-gated env vars, fail-fast |
| Git conventions | Branch naming, commit style |

## Sample Output

When you ask Claude Code to build a feature with this CLAUDE.md active, it will:

- Create Drizzle schemas with proper IDs, timestamps, and cascade deletes
- Write server components by default, `"use client"` only for interactivity
- Validate all inputs with Zod before hitting the database
- Use Tailwind utilities, no CSS-in-JS
- Return structured error objects, never throw to the client
- Follow the folder structure without asking

## License

MIT
