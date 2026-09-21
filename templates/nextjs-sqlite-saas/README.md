# Next.js 15 + SQLite SaaS Template for Claude Code 🚀

An opinionated, production-ready `CLAUDE.md` rulebook and architecture blueprint designed for building multi-tenant SaaS applications using Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite (via Drizzle ORM + better-sqlite3 / Turso).

Bounty #2 submission for **Claude Builders Bounty** ($75 — powered by Opire).

---

## 📋 Features & Acceptance Criteria Checklist

- [x] **Stack & Versions**: Next.js 15 (App Router, React 19), TypeScript 5 (strict), Tailwind CSS, SQLite (`better-sqlite3` / Turso `libsql`), Drizzle ORM, Zod.
- [x] **Dev Commands**: Full suite from `pnpm dev`, `pnpm build`, `pnpm test`, `pnpm typecheck` to database workflows (`db:generate`, `db:migrate`, `db:studio`, `db:seed`).
- [x] **Project Structure**: Clean layout separating route groups `(auth)`, `(dashboard)`, atomic UI components, migrations, and Server Actions.
- [x] **SQLite Conventions**: Mandated WAL mode (`pragma journal_mode = WAL`), foreign keys enforcement, busy timeout, and multi-tenant scoping (`organization_id`).
- [x] **Component Patterns**: Server Components by default, minimal leaf Client Components, Server Actions for mutations.
- [x] **What We Don't Do (And Why)**: 6 opinionated rules explaining why to avoid traditional API route mutations, `any` casts, Prisma binary bloat, edge synchronous locks, etc.
- [x] **Naming Conventions**: Strict standards for files, components, database identifiers, and actions.

---

## ⚡ Quick Start for New Projects

To use this in any new or existing SaaS project:

```bash
# 1. Copy CLAUDE.md into your project root
curl -o CLAUDE.md https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-saas/CLAUDE.md

# 2. Launch Claude Code in your project directory
claude
```

Claude Code will automatically detect `CLAUDE.md` and follow all architectural rules, naming conventions, and database patterns without asking clarifying questions.
