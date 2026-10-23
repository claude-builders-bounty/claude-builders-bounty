# Next.js 15 + SQLite SaaS Template for Claude Code

A drop-in `CLAUDE.md` blueprint designed to guide Claude Code when bootstrapping or maintaining a SaaS application built with Next.js 15 (App Router), TypeScript, and SQLite.

## How to Use

1. Copy `CLAUDE.md` to the root of your Next.js project:
   ```bash
   cp templates/nextjs-sqlite/CLAUDE.md /path/to/your/project/CLAUDE.md
   ```
2. Start Claude Code in that project:
   ```bash
   claude
   ```
3. Claude Code will automatically read `CLAUDE.md` and enforce React Server Component boundaries, SQLite WAL mode pragmas, Drizzle schemas, and clean architectural separation.
