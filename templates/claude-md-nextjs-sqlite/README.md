# CLAUDE.md — Next.js 15 + SQLite SaaS template

An opinionated, production-ready `CLAUDE.md` for greenfield SaaS projects on
Next.js 15 (App Router) + SQLite (better-sqlite3 / Turso).

## What's covered

- **Stack & versions** — Next.js 15, React 19, TypeScript strict, Drizzle ORM, Tailwind v4, pnpm
- **Folder structure** — route/feature/db/server split with one-line justifications
- **SQL & migration conventions** — Drizzle-only migrations, no `db:push` in prod, guarded writes
- **Component patterns** — Server Components by default, server actions for mutations, no client data waterfalls
- **Naming conventions** — kebab-case files, snake_case tables, `verbNoun` actions, Zod validation
- **Dev commands** — dev/build/lint/typecheck/test/db:generate/db:migrate/db:seed
- **Anti-patterns ("What we don't do and why")** — every negative rule carries its reason

## Usage

1. Copy `CLAUDE.md` into the root of your new Next.js project.
2. Start Claude Code — it reads the file automatically.
3. Ask for a feature; it will follow the stated structure and rules without clarifying questions.

The file is self-contained: all conventions are stated with reasons so it works
on a greenfield project with zero modification.
