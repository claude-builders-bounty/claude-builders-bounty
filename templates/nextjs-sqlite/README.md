# Next.js 15 App Router + SQLite SaaS Template

> Opinionated, production-ready `CLAUDE.md` architecture template for greenfield SaaS projects using Next.js 15 App Router, React 19, SQLite (better-sqlite3 / Turso), and Drizzle ORM.

## 🚀 Quickstart in 3 Steps

### 1. Copy `CLAUDE.md` to Project Root
```bash
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-new-project/CLAUDE.md
```

### 2. Verify Claude Code Recognition
Open your greenfield Next.js 15 project with Claude Code:
```bash
claude
```
Claude Code will automatically ingest `CLAUDE.md` as the root context file, understanding the Drizzle schema rules, WAL pragmas, Server Action wrappers, and naming conventions without asking clarifying questions.

### 3. Initialize SQLite with Required Pragmas
Follow the connection singleton pattern defined in section 4.1 of `CLAUDE.md` to guarantee non-blocking WAL concurrency and enforced foreign key constraints.

---

## 📋 Features & Design Choices

- **Next.js 15 App Router & React 19:** Server components by default with minimal `'use client'` boundaries.
- **SQLite Performance Optimized:** Configured for WAL mode, `busy_timeout = 5000`, and `synchronous = NORMAL`.
- **Drizzle ORM:** Ultra-low latency, zero heavy binary cold starts (avoids Prisma overhead).
- **Safe Server Actions:** Built-in `createSafeAction` wrapper with Zod contract validation.
- **Anti-Pattern Guardrails:** Explicitly documents what *not* to do with technical justifications.
