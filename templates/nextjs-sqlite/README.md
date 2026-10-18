# Opinionated CLAUDE.md for Next.js 15 App Router + SQLite SaaS 🚀

> Production-ready `CLAUDE.md` blueprint designed specifically for building AI-assisted SaaS with Next.js 15, Drizzle ORM, and SQLite.

[![Bounty](https://img.shields.io/badge/bounty-%2475-success)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

---

## ⚡ Quick Start

Copy `CLAUDE.md` to the root of your new Next.js 15 project:

```bash
cp templates/nextjs-sqlite/CLAUDE.md ./CLAUDE.md
```

Claude Code will immediately adopt the architecture rules, folder conventions, and database patterns without asking clarifying questions.

---

## 🎯 Key Highlights

1. **Stack Alignment**: Next.js 15 App Router + React 19 + TypeScript 5.6 + Drizzle ORM + `better-sqlite3` / Turso.
2. **SQLite Production Pragmas**: Explicitly configures `WAL` journal mode, `foreign_keys = ON`, and `busy_timeout` to eliminate SQLite database locks.
3. **Strict Boundaries**: Enforces Server Components by default, leaf-only `'use client'`, and Zod-validated Server Actions for mutations.
4. **Opinionated Anti-Patterns Guide**: Clearly details forbidden practices (why not Prisma, why not client-side DB, why not `useEffect` fetches) with immediate alternatives.
