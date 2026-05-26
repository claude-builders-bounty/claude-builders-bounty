# Next.js 15 + SQLite SaaS CLAUDE.md Template

A production-grade, highly opinionated `CLAUDE.md` template designed for Next.js 15 App Router applications using SQLite (better-sqlite3 or Turso) and Drizzle ORM.

## Setup Instructions

1. Copy the `CLAUDE.md` file from this directory into the root of your greenfield Next.js + SQLite SaaS project:
   ```bash
   cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your/project/CLAUDE.md
   ```
2. Start Claude Code in your project root:
   ```bash
   claude
   ```
3. Claude Code will automatically read the `CLAUDE.md` context and adhere to the project's folder structure, coding conventions, SQLite transaction constraints, and security guards.

## Validation Smoke Prompts

To test that the context is fully understood without manual clarification, try running the prompts found in [smoke-prompts.md](./smoke-prompts.md).
