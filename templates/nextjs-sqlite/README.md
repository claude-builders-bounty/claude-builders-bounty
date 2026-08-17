# Next.js 15 + SQLite SaaS Template (CLAUDE.md) 🚀

> Opinionated, production-grade `CLAUDE.md` template designed for building SaaS projects with Next.js 15 App Router, React 19, TypeScript, and SQLite (Drizzle ORM / Turso).

## Quickstart in 2 Steps

### 1. Copy `CLAUDE.md` to your project root
```bash
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-project/CLAUDE.md
```

### 2. Run Claude Code
Open your project in Claude Code or Antigravity IDE. The AI agent will automatically detect the architectural rules, SQLite WAL conventions, Server Action validation patterns, and anti-patterns.

---

## Included Architecture Standards
- **Stack**: Next.js 15, React 19, TypeScript strict mode, SQLite (better-sqlite3 / Turso), Drizzle ORM, Tailwind CSS 4.
- **Concurrency & WAL Mode**: Preconfigured PRAGMA settings for high-throughput concurrent SQLite operations.
- **Security**: Strict Zod validation on Server Actions, HTTP-only cookie sessions, zero client-side database access.
- **Clean Patterns**: Explains exact rationale for avoiding heavy ORMs and barrel exports.
