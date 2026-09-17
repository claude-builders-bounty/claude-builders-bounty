# Next.js 15 App Router + SQLite SaaS — CLAUDE.md Template

> Production-ready, opinionated `CLAUDE.md` template tailored for SaaS applications using Next.js 15 App Router and SQLite (better-sqlite3 for local dev, Turso libSQL for production edge deployment).

## Quick Start

1. Create a Next.js 15 project:
   ```bash
   npx create-next-app@latest my-saas --typescript --tailwind --app --eslint
   cd my-saas
   ```

2. Copy this `CLAUDE.md` into your project root:
   ```bash
   curl -sSL https://raw.githubusercontent.com/Wawen22/claude-builders-bounty/feat/bounty-2-nextjs-sqlite-claude-md/templates/nextjs-sqlite-saas/CLAUDE.md -o CLAUDE.md
   ```

3. Launch Claude Code:
   ```bash
   claude
   ```

Claude Code will automatically detect the architectural rules, SQLite constraints, database migration workflows, and component boundaries without asking clarifying questions.

## Highlights
- **Strict Separation of Concerns**: Server Components by default, Client Components only when client interactivity is strictly required.
- **SQLite Concurrency & Migrations**: Configured for WAL mode, zero-downtime table migrations, and cascade deletes.
- **Defensive Type Safety**: Zod schema boundary validation for all Server Actions and route handlers.
- **Explicit Anti-Patterns**: Clear, reasoned rules preventing common SaaS pitfalls.
