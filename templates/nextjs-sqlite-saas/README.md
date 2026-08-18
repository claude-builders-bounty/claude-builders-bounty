# Next.js 15 + SQLite SaaS Template with CLAUDE.md 🚀

This repository provides an opinionated, production-tested `CLAUDE.md` and architecture blueprint for greenfield SaaS projects powered by **Next.js 15 App Router** and **SQLite** (via Drizzle ORM + better-sqlite3 or Turso).

---

## 📦 How to Use This Template

1. Copy [`CLAUDE.md`](./CLAUDE.md) to the root of your Next.js project.
2. Initialize your project with:
   ```bash
   npx create-next-app@latest my-saas --typescript --tailwind --app --src-dir=false
   pnpm add drizzle-orm better-sqlite3 @libsql/client zod
   pnpm add -D drizzle-kit @types/better-sqlite3
   ```
3. Open Claude Code or Antigravity and start prompting — Claude will immediately understand the entire directory structure, WAL SQLite conventions, Server Action rules, and anti-patterns without asking clarifying questions!

---

## 🌟 Key Highlights

- **Edge & Serverless Ready**: SQLite WAL mode local dev + seamless Turso / LibSQL deployment.
- **Strict End-to-End Type Safety**: Drizzle ORM schema inference + Zod validation.
- **Opinionated "What We Don't Do" Rules**: Eliminates bloated abstractions before they start.
