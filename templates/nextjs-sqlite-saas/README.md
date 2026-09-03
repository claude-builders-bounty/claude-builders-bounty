# Next.js 15 + SQLite SaaS Template for Claude Code

An opinionated, production-ready `CLAUDE.md` configuration engineered for greenfield SaaS projects leveraging Next.js 15 (App Router, React 19) and SQLite (Drizzle ORM, Turso/better-sqlite3).

## Quick Setup (1 Step)

Copy `CLAUDE.md` into the root of your Next.js project:

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your/project/CLAUDE.md
```

Claude Code will automatically discover this configuration on start and adhere to all architectural boundaries, SQLite pragmas, and Server Action validation rules without asking clarifying questions.

## Highlights

- **SQLite-Specific Optimization**: Enforces WAL mode (`PRAGMA journal_mode = WAL;`) and busy timeouts to eliminate SQLite concurrency bottlenecks.
- **Strict Server/Client Boundaries**: Prevents layout `'use client'` pollution and enforces leaf-level client interactivity.
- **Drizzle Migration Discipline**: Clear migration lifecycle and automated type inference guidelines.
- **Anti-Pattern Prevention Matrix**: Concrete table explaining forbidden practices with their architectural rationales.
