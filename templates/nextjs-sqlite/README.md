# Next.js 15 + SQLite SaaS Template with CLAUDE.md

An opinionated, production-ready `CLAUDE.md` specification and architecture template for building SaaS projects with **Next.js 15 (App Router)**, **React 19**, and **SQLite (better-sqlite3 / Turso / Drizzle ORM)**.

---

## ⚡ Quick Start (2 Commands)

```bash
mkdir -p my-saas && cp CLAUDE.md my-saas/CLAUDE.md
# Open with Claude Code to scaffold your full-stack SaaS immediately
```

---

## 🎯 What This Template Solves

1. **Zero Clarification Overhead**: Claude Code reads this `CLAUDE.md` and immediately adopts strict patterns for App Router, Server Actions, SQLite WAL pragmas, and Drizzle migrations without asking clarifying questions.
2. **SQLite Production Hardening**: Preconfigures WAL mode, 5000ms busy timeout, foreign key enforcement, and normalized transaction wrappers.
3. **Type-Safe Full-Stack Mutations**: Enforces Zod-validated Server Actions returning standardized `ActionState` types.

---

## 🧪 Verification

Run the automated specification validator:

```bash
python3 tests/verify_template.py
```
