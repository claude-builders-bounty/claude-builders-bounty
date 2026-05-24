# TEMPLATE: CLAUDE.md for Next.js + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for a SaaS project built with **Next.js 15 App Router** and **SQLite** (`better-sqlite3` + Drizzle ORM).

## Usage

1. **Copy** `CLAUDE.md` into the root of your Next.js 15 + SQLite project
2. Claude Code / Cursor will automatically read it for project context
3. Start prompting — no clarifying questions needed

## What's Covered

- Stack versions (Next.js 15, Node.js >=20, Drizzle ORM, SQLite)
- Complete project structure with route groups and feature folders
- Naming conventions (files, functions, DB columns)
- Database connection singleton pattern (`globalThis`)
- Migration workflow (Drizzle Kit)
- Component patterns (Server Components first, Server Actions)
- Anti-patterns with explanations (what we don't do and why)
- Dev commands, env vars, git workflow
- Context notes for Claude Code behavior

## Opinionated Choices

| Decision | Rationale |
|----------|-----------|
| Drizzle ORM over Prisma | Lighter, faster, native SQLite support |
| CUIDs over auto-increment | Migration-safe — works in Postgres too |
| `connection()` before sync queries | Prevents static prerendering (Next.js 15 change) |
| WAL mode + busy_timeout | Enables concurrent reads, prevents `SQLITE_BUSY` |
| `globalThis` singleton | Prevents hot-reload connection leaks |
| Feature folders under `src/features/` | Domain ownership, easy to delete when feature dies |
| Server-first components | Smaller client bundles, direct DB access |
