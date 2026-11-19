# Next.js 15 + SQLite SaaS Template for Claude Code

A complete, production-ready, opinionated `CLAUDE.md` template designed for SaaS projects built with Next.js 15 (App Router, React 19) and SQLite (`better-sqlite3` or Turso `@libsql/client`) with Drizzle ORM.

## Why this template?

When working with Claude Code or AI coding agents on Next.js 15 and SQLite projects, having clear architectural boundaries and conventions eliminates hallucinations, prevents anti-patterns (such as client-side data leaks or legacy API routes), and provides instant context for every new feature.

## What's Included in `CLAUDE.md`

- **Stack & Versions**: Locked versions and justifications (Next.js 15, Drizzle ORM, Tailwind v4, Zod, TypeScript strict).
- **Project Structure**: Clean layout separating Server Actions, route groups (`(auth)`, `(dashboard)`), domain schemas, and atomic UI components.
- **SQL & Migration Rules**: SQLite-specific rules (enabling `PRAGMA foreign_keys = ON;`, `WAL` mode, primary key conventions, case-insensitive collations).
- **Next.js 15 Patterns**: Server Components vs. Client Components guide and Server Actions with Zod validation.
- **What We Don't Do (And Why)**: 6 core anti-patterns and their modern replacements.

---

## 3-Step Setup for Any Greenfield Project

### Step 1: Copy `CLAUDE.md` to your project root
```bash
cp templates/nextjs-sqlite/CLAUDE.md path/to/your/new-project/CLAUDE.md
```

### Step 2: Initialize your Next.js + SQLite project
```bash
pnpm create next-app@latest my-saas --typescript --tailwind --app
cd my-saas
pnpm add drizzle-orm @libsql/client zod
pnpm add -D drizzle-kit
```

### Step 3: Start Claude Code
Launch Claude Code inside your project:
```bash
claude
```
Claude Code will automatically detect `CLAUDE.md` at the project root and start scaffolding your SaaS database, actions, and UI with zero ambiguities.
