# Next.js 15 + SQLite SaaS CLAUDE.md Template ⚡

A battle-tested, highly opinionated `CLAUDE.md` tailored specifically for Next.js 15 App Router applications using embedded SQLite (`better-sqlite3`) or distributed edge SQLite (`@libsql/client` / Turso) with Drizzle ORM.

---

## 🎯 Purpose & Design Philosophy

When Claude Code works in a Next.js repository without strict boundary instructions, it often falls back to legacy anti-patterns:
- Inappropriate `'use client'` tags across entire pages.
- Client-side data fetching waterfalls via `useEffect`.
- Unindexed SQLite foreign keys causing sequential table scan performance degradation.
- API route handlers for internal mutations instead of type-safe Server Actions.

This `CLAUDE.md` sets strict architectural rules and concrete conventions so Claude Code writes clean, production-grade code on the first attempt without asking clarifying questions.

---

## 🚀 How to Use in Greenfield Projects

Simply copy [`CLAUDE.md`](CLAUDE.md) directly into the root of your Next.js project:

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/my-new-saas/CLAUDE.md
```

Claude Code will automatically detect and adhere to all conventions:
- Enforcing Drizzle schema type inference (`$inferSelect`, `$inferInsert`).
- Enforcing WAL mode (`journal_mode = WAL`) and foreign key pragmas on SQLite connections.
- Enforcing Zod input validation on Server Actions with `revalidatePath()` cache invalidation.

---

## 🧪 Validation & Testing

Run the automated specification test suite:

```bash
python3 tests/test_nextjs_sqlite_template.py
```
