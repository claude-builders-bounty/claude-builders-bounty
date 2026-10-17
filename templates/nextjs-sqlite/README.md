# Next.js 15 + SQLite SaaS `CLAUDE.md` Template 🚀

> Production-ready, opinionated Claude Code guidelines for modern SaaS applications built with **Next.js 15 (App Router)** and **SQLite (better-sqlite3 / Turso)**.

---

## ⚡ Quick Start (3 Steps)

1. **Copy `CLAUDE.md` into your project root:**
   ```bash
   cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-project/CLAUDE.md
   ```
2. **Install core SQLite & Drizzle dependencies:**
   ```bash
   npm install drizzle-orm better-sqlite3 zod
   npm install -D drizzle-kit @types/better-sqlite3
   ```
3. **Launch Claude Code:**
   ```bash
   claude
   ```
   Claude Code will automatically detect `CLAUDE.md` and build feature branches, database schemas, and Server Actions strictly adhering to Next.js 15 App Router standards without requiring clarifying questions.

---

## 📋 What's Covered in this Template

- **Stack & Versions:** Next.js 15 App Router, React 19, SQLite with WAL mode, Drizzle ORM, Zod, and Tailwind CSS.
- **Project Structure:** Domain-driven directory organization separating server-only actions (`src/actions/`), database singletons (`src/db/`), and leaf client components (`src/components/`).
- **Database Conventions:**
  - WAL journal mode (`PRAGMA journal_mode = WAL;`) and synchronous normal mode for high-throughput single-writer concurrency.
  - Foreign key enforcement enabled by default.
  - Non-enumerable string IDs (CUID2/Nanoid) to prevent ID enumeration.
  - Automated migration workflow via `drizzle-kit`.
- **Server Action Patterns:** Complete typed `ActionState<T>` mutation pattern with Zod safe-parsing, authentication check, transaction execution, and path revalidation.
- **Anti-Patterns & Rationale:** Explicit "What We Don't Do" table detailing why `useEffect` data fetching, internal `/api/` mutation routes, barrel re-exports, and raw SQL interpolation are forbidden.
