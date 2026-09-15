# Next.js 15 + SQLite SaaS — CLAUDE.md Template

> Production-ready template and system instructions for building high-performance, cost-effective SaaS applications using **Next.js 15 (App Router)** and **SQLite** (via `better-sqlite3` or Turso).

---

## ⚡ Quick Setup (3 Steps)

### Step 1: Copy `CLAUDE.md` to Project Root
Place the `CLAUDE.md` file in the root of your Next.js project:

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md
```

### Step 2: Install Core Dependencies
Initialize your SQLite + Drizzle setup with `pnpm`:

```bash
pnpm add better-sqlite3 drizzle-orm zod lucide-react
pnpm add -D drizzle-kit @types/better-sqlite3
```

### Step 3: Launch Claude Code
Open your project in Claude Code:

```bash
claude
```
Claude Code will automatically detect `CLAUDE.md`, understand your stack (WAL mode, Drizzle, Server Actions, folder structure, and strict anti-patterns), and generate compliant code without asking clarifying questions.

---

## 🎯 Key Design Principles Covered

| Requirement | Implementation in `CLAUDE.md` |
|---|---|
| **Architecture** | Next.js 15 App Router, React 19 Server Components by default |
| **Database & Concurrency** | `better-sqlite3` with strict WAL mode (`PRAGMA journal_mode = WAL`), foreign keys ON, and 5000ms busy timeout |
| **Migrations** | Drizzle ORM schema-first workflow (`drizzle-kit generate` & `migrate`) |
| **Security & Validation** | Zod v3 validation on every Server Action, HTTP-only session cookies |
| **Anti-Patterns** | Documented rationale against Prisma bloat, client waterfalls, and unbounded reads |
