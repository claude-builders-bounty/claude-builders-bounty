# Next.js 15 + SQLite SaaS Template for Claude Code

This template provides an opinionated, production-grade `CLAUDE.md` specification designed for modern SaaS web applications built with **Next.js 15 App Router** and **SQLite** (supporting both local `better-sqlite3` and distributed Turso/libSQL).

---

## 🚀 Quick Start (Greenfield Project)

1. **Bootstrap your Next.js application:**
   ```bash
   npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir
   cd my-saas
   ```

2. **Install core SQLite & Drizzle dependencies:**
   ```bash
   npm install drizzle-orm better-sqlite3 zod
   npm install -D drizzle-kit @types/better-sqlite3 vitest
   ```

3. **Install this `CLAUDE.md`:**
   Copy `CLAUDE.md` from this directory directly into the root of your new project:
   ```bash
   cp /path/to/templates/nextjs-sqlite/CLAUDE.md ./CLAUDE.md
   ```

4. **Launch Claude Code:**
   ```bash
   claude
   ```
   Claude Code will immediately detect `CLAUDE.md`, understand your architecture, enforce Server Component boundaries, follow Drizzle/SQLite conventions, and execute tasks without needing clarifying questions.

---

## 🎯 Key Design Choices
- **Next.js 15 Server-First Architecture**: RSCs by default, leaf Client Components, Server Actions for mutations.
- **SQLite Performance Discipline**: WAL pragma enforcement, foreign keys active, integer timestamp storage.
- **Strict Error Taxonomy**: No raw SQL errors exposed to clients; Zod-validated action responses.
