# Next.js 15 + SQLite SaaS Template for Claude Code

This template provides a battle-tested, opinionated `CLAUDE.md` architecture guide for building modern SaaS products using **Next.js 15 (App Router)** and **SQLite** (better-sqlite3 / Turso).

## 🎯 Purpose
When Claude Code enters a new or existing repository, having a precise `CLAUDE.md` eliminates hallucinations, enforces clean architectural boundaries, and ensures code is generated following exact project standards without needing prompt repetitions.

## 📦 How to Use in a New Project

1. Copy `CLAUDE.md` into the root directory of your Next.js project:
   ```bash
   cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/my-saas/CLAUDE.md
   ```
2. Start Claude Code in that project:
   ```bash
   claude
   ```
3. Ask Claude Code to create features or scaffold routes. It will automatically adhere to:
   - React Server Components by default
   - Drizzle ORM queries with SQLite WAL mode
   - Zod-validated Server Actions
   - Strict TypeScript types without `any`

## 🛡️ Key Architectural Guardrails
- **WAL Mode & Busy Timeout**: Guarantees zero "database locked" errors under concurrency.
- **Server Actions Over REST**: Eliminates boilerplate API routes and serialization friction.
- **Anti-Pattern Guard**: Explicitly prohibits bloated ORMs (e.g. Prisma binary engine) and client-side credential leaks.
