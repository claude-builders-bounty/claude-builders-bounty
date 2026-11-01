# Opinionated CLAUDE.md for Next.js 15 + SQLite SaaS (#2)

> 💰 Bounty: $75 — powered by [Opire](https://opire.dev)

A complete, battle-tested, highly opinionated `CLAUDE.md` configuration template tailored specifically for building full-stack SaaS products with **Next.js 15 (App Router)** and **SQLite (better-sqlite3 / Turso)** using **Drizzle ORM** and **Tailwind CSS**.

---

## 🚀 How to Use on Greenfield Projects

1. Copy `CLAUDE.md` into the root directory of your Next.js project:
   ```bash
   cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md
   ```
2. When launching Claude Code (`claude`), it automatically reads `CLAUDE.md` on startup.
3. Claude will immediately understand:
   - Your exact folder layout and naming rules
   - Mandatory SQLite WAL pragmas (`PRAGMA journal_mode = WAL`)
   - Server Component vs. Server Action boundaries
   - Zero-REST mutation patterns via `"use server"`
   - Prohibited anti-patterns (no Prisma, no client DB access, no `useEffect` waterfalls)

---

## 📂 Key Sections Covered

1. **Stack & Pinned Versions**: Next.js 15, React 19, TypeScript 5.6+, SQLite (better-sqlite3 / Turso), Drizzle ORM, Tailwind CSS v4.
2. **Directory & File Conventions**: `app/` structure, `lib/actions/` Server Actions, `lib/db/` Drizzle schema, `kebab-case` naming.
3. **Essential Developer Commands**: Turbopack dev, `drizzle-kit generate/migrate/studio`, linting, strict typecheck.
4. **SQLite Concurrency & WAL Pragmas**: Mandatory WAL mode, busy timeout, foreign key indexing.
5. **Architectural Patterns**: Server Components by default, leaf client components, Server Actions with Zod validation.
6. **What We DON'T Do (and Why)**: Explicit justification for every forbidden pattern (no Prisma cold starts, no raw unparameterized SQL, no `any`).

---

## 🧪 Verification Test

Run the validation suite to ensure all required sections and guidelines are present:
```bash
pytest templates/nextjs-sqlite-saas/tests/test_template.py -v
```
