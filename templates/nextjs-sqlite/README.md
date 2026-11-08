# Next.js 15 + SQLite CLAUDE.md Template

Production-grade rules and architectural guidelines for Claude Code agents building Next.js 15 App Router applications backed by SQLite (`better-sqlite3`).

## Quick Setup (3 Steps)

1. **Copy into your project:**
   ```bash
   cp templates/nextjs-sqlite/CLAUDE.md your-nextjs-project/CLAUDE.md
   ```
2. **Install core SQLite dependencies:**
   ```bash
   npm install better-sqlite3 zod
   npm install -D @types/better-sqlite3
   ```
3. **Launch Claude Code:**
   Claude Code will automatically detect `CLAUDE.md` and adhere to RSC server boundaries, WAL mode configuration, and migration conventions.
