# Opinionated Next.js 15 + SQLite SaaS Template (`CLAUDE.md`)

A production-ready, highly opinionated `CLAUDE.md` context definition designed specifically for greenfield SaaS projects powered by **Next.js 15 (App Router)** and **SQLite** (via `better-sqlite3` or Turso `@libsql/client` with Drizzle ORM).

---

## 🚀 Quick Start (Usable in Any Project)

Copy `CLAUDE.md` directly into the root directory of your Next.js + SQLite project:

```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite/CLAUDE.md -o CLAUDE.md
```

Once pasted, Claude Code will immediately adopt:
- App Router folder structure and naming conventions
- SQLite WAL mode and concurrency pragmas (`synchronous = NORMAL`, `busy_timeout = 5000`)
- Drizzle ORM schema-first migration workflow
- React Server Component data fetching patterns
- Strict avoidance of anti-patterns (no Prisma, no client-side `useEffect` waterfalls, no `any`)

---

## 📋 Acceptance Criteria Verification

- [x] **Project Structure & Naming**: Detailed directory tree covering route groups `(auth)`, `(dashboard)`, Server Actions `src/actions`, and Drizzle schemas.
- [x] **Database & Migrations**: Prescribes explicit SQLite connection pragmas (WAL mode, foreign keys, busy timeout), sequential migration rules, and UUID/CUID primary keys.
- [x] **Dev Commands**: Pre-configured commands for `pnpm` (`dev`, `build`, `db:generate`, `db:migrate`, `db:studio`, `test`).
- [x] **Patterns to Follow**: React Server Components by default, typed Server Actions with Zod validation, and leaf Client Components.
- [x] **What We Don't Do (and Why)**: Comprehensive anti-pattern table explaining technical justifications (why Drizzle beats Prisma in SQLite, why client data fetching is prohibited, etc.).
- [x] **Zero Modification Needed**: Drops cleanly into any greenfield Next.js + SQLite repo.

---

## 🧪 Verification

Run the validation script to verify all required sections and guidelines:

```bash
python templates/nextjs-sqlite/tests/verify_template.py
```
