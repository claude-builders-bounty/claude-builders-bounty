# 📋 CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite (better-sqlite3 via Drizzle ORM).

> Bounty submission for [Issue #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

## 🎯 What's Covered

- **Stack & Versions** — Exact technologies and why each was chosen
- **Folder Structure** — Opinionated project layout with rules
- **Dev Commands** — All scripts a developer needs
- **DB & Migration Conventions** — Schema patterns, query patterns, naming rules
- **Component Patterns** — Server vs Client components, Server Actions, validation
- **Naming Conventions** — Consistent rules for files, functions, types, DB
- **What We Don't Do** — 10 explicit anti-patterns with reasoning
- **Error Handling** — Custom errors, error boundaries, not-found pages
- **Environment Variables** — Template and access rules
- **Performance Rules** — SQLite WAL mode, streaming, image/font optimization

## ⚡ Usage

```bash
# Copy into any new Next.js 15 + SQLite project
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your/project/CLAUDE.md
```

Then start Claude Code in your project — it will read `CLAUDE.md` automatically and follow all conventions without asking clarifying questions.

## ✅ Tested

Created a new `npx create-next-app@latest` project, dropped in the CLAUDE.md, and verified Claude Code:
1. Follows the folder structure conventions
2. Uses Server Components by default
3. Creates Server Actions (not API routes) for mutations
4. Uses Drizzle ORM (not Prisma) for database access
5. Applies Zod validation on all inputs
6. Uses cuid2 text IDs (not auto-increment integers)
7. Follows all naming conventions correctly

## 📄 License

MIT
