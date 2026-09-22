# Next.js 15 + SQLite SaaS Template (`CLAUDE.md`)

A production-ready, opinionated `CLAUDE.md` template designed for SaaS projects built with **Next.js 15 App Router**, **SQLite (Turso / better-sqlite3)**, and **Drizzle ORM**.

## Why This Template?
Claude Code works best when given strict, opinionated architectural guardrails. This template ensures that Claude Code:
1. Always leverages React Server Components (RSC) by default.
2. Properly manages SQLite concurrency with WAL mode and singleton connection caching.
3. Enforces strict input validation on all Server Actions with Zod.
4. Prevents common pitfalls like client-side database queries and unparameterized SQL.

## How to Use in 2 Steps

### 1. Copy `CLAUDE.md`
Copy `CLAUDE.md` into the root directory of your Next.js project.

### 2. Launch Claude Code
Start Claude Code in your project directory:
```bash
claude
```
Claude Code will immediately detect `CLAUDE.md`, understand your stack and folder conventions, and generate consistent, type-safe code without asking clarifying questions.
