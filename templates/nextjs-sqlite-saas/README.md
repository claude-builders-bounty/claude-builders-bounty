# Next.js 15 + SQLite SaaS CLAUDE.md Template ⚡

> An opinionated, production-ready `CLAUDE.md` engineering guide designed for SaaS applications built with **Next.js 15 (App Router)** and **SQLite (Turso / LibSQL / better-sqlite3)**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![SQLite](https://img.shields.io/badge/SQLite-LibSQL-blue.svg)](https://turso.tech/)
[![Bounty Issue #2](https://img.shields.io/badge/Bounty-%2475%20USDC-green.svg)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

---

## 🎯 Purpose

When building complex full-stack web applications with Claude Code, ambiguous prompts often lead to:
- Mixed App Router / Pages Router conventions
- Accidental client-side database calls
- Raw SQL injections or messy migrations
- Spaghetti state management with cascading `useEffect` hooks

This `CLAUDE.md` sets explicit, non-negotiable boundaries so Claude Code writes consistent, clean, and secure code from day one.

---

## 🚀 How to Use in Your Project (1 Step)

Simply copy `CLAUDE.md` into the root directory of your Next.js project:

```bash
# In your project root:
cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md
```

Claude Code will automatically detect this file and align every subsequent generation with:
1. Server Components vs Client Components rules
2. Drizzle ORM + SQLite migration commands
3. Type-safe Server Actions with Zod validation
4. Strict anti-patterns and performance guardrails

---

## 📄 License

MIT License. Built for the Claude Code Builders Community.
