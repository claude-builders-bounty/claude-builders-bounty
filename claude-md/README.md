# CLAUDE.md Template — Next.js 15 + SQLite SaaS

A production-ready `CLAUDE.md` for typical SaaS projects built with **Next.js 15 App Router** and **SQLite (better-sqlite3)**.

## Files

- **CLAUDE.md** — The template. Copy this into your project root.

## Usage

1. Create a new Next.js 15 + SQLite project
2. Copy `CLAUDE.md` to project root
3. Open with Claude Code — it will understand your entire project context without asking clarifying questions.

## Stack Assumptions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Latest stable |
| Database | better-sqlite3 / Turso | Zero-config local, serverless prod |
| ORM | Drizzle ORM | Type-safe, SQLite-native |
| Auth | NextAuth v5 | Mature, SQLite adapter available |
| UI | shadcn/ui + Tailwind | Radix primitives, minimal bundle |
| Validation | Zod | Type inference, react-hook-form support |
| Package Manager | pnpm | Strict, fast, disk-efficient |
