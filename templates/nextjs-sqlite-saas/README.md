# Next.js 15 + SQLite SaaS Template `CLAUDE.md`

An opinionated, production-ready `CLAUDE.md` configuration engineered specifically for greenfield and scalable SaaS applications built with **Next.js 15 App Router**, **React 19 Server Components**, and **SQLite (better-sqlite3 / Turso libSQL via Drizzle ORM)**.

---

## 📦 What's Included

1. **Stack & Versions**: Strict pinning for Next.js 15, React 19, TypeScript strict, Drizzle ORM, better-sqlite3 / libSQL, Zod, and Tailwind CSS v4.
2. **Deterministic Folder Structure**: App Router route groupings `(auth)`, `(dashboard)`, atomic components hierarchy, server actions vs query separation.
3. **SQLite Engine Conventions**: Mandatory WAL mode (`PRAGMA journal_mode = WAL`), busy timeouts, foreign key enforcement, and Drizzle migration workflows.
4. **Component & Data Patterns**: Server Component defaults, Server Actions with Zod validation contracts, and cache revalidation semantics.
5. **Anti-Patterns & Architectural Guardrails**: Explicit "What We Don't Do (and Why)" section preventing client waterfall fetches, unparameterized SQL, ephemeral storage pitfalls, and secret leakage.

---

## 🚀 How to Use

1. Copy `CLAUDE.md` to the root directory of your Next.js 15 + SQLite SaaS repository.
2. Launch Claude Code (`claude`).
3. Claude Code immediately understands the database architecture, RSC conventions, migration rules, and coding standards without prompting for clarification.
