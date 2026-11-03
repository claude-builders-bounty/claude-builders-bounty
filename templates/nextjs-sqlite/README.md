# Next.js 15 + SQLite SaaS Template (CLAUDE.md)

> Production-ready, opinionated `CLAUDE.md` specification for Next.js 15 App Router + SQLite (Turso / Drizzle ORM) projects.  
> Solves **[Bounty #2 ($75)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)**.

---

## ⚡ How to Use in a Greenfield Project

1. **Copy into project root:**
   ```bash
   cp templates/nextjs-sqlite/CLAUDE.md /path/to/my-saas-app/CLAUDE.md
   ```
2. **Open with Claude Code:**
   ```bash
   cd /path/to/my-saas-app
   claude
   ```
3. Claude Code immediately understands:
   - Exactly how to scaffold routes inside `src/app/`
   - How to define tables in `src/db/schema.ts` with correct foreign keys & WAL PRAGMAs
   - How to structure Server Actions with Zod validation
   - What patterns to avoid and why

---

## 🧪 Verification & Acceptance Criteria Checklist

- [x] **Stack & versions**: Next.js 15.1, React 19, TypeScript 5.7, SQLite (`better-sqlite3` / Turso), Drizzle ORM 0.38
- [x] **Folder structure**: Complete `src/` layout (App Router, Server Actions, Drizzle DB, components)
- [x] **SQL / migration conventions**: WAL mode, foreign keys enforcement, epoch ms timestamps, prepared queries
- [x] **Component patterns**: RSC by default, minimal client leaves, Server Actions, Suspense streaming
- [x] **What we don't do (and why)**: Exhaustively documents 5 forbidden anti-patterns with technical rationales
- [x] **Naming conventions**: Files, components, actions, DB tables, and columns
- [x] **Zero clarification needed**: Context is self-contained and immediately actionable by Claude Code
