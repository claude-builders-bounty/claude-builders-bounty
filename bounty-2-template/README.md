# CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with
Next.js 15 App Router and SQLite (better-sqlite3).

## Usage

1. Copy `CLAUDE.md` into the root of your Next.js project
2. Start Claude Code in your project directory
3. Claude will follow the conventions automatically — no configuration needed

## What's Covered

- **Stack & versions** — Next.js 15, TypeScript strict, SQLite WAL mode, Tailwind 4, shadcn/ui
- **Folder structure** — flat layout, no `src/`, no barrel exports
- **Database conventions** — numbered SQL migrations, prepared statements, no ORM
- **Component patterns** — Server Components by default, named exports, Server Actions for mutations
- **Anti-patterns** — what to avoid and *why* (Prisma, Redux, CSS Modules, etc.)
- **Dev commands** — every script a developer needs
- **Commit conventions** — Conventional Commits
- **Deployment** — persistent-volume SQLite (not serverless)

## Design Principles

Every rule has a reason. This template is opinionated because generic guidance
produces generic code. The choices reflect real-world experience building SaaS
products with this stack:

- **Raw SQL over ORM** — SQLite queries are simple; an ORM adds complexity without value
- **Server Components first** — minimize client JS bundle
- **No barrel exports** — they break tree-shaking and create circular dependency traps
- **Flat structure** — fewer directories = less time navigating, more time building
