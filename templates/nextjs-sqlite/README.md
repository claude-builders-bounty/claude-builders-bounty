# Next.js 15 + SQLite SaaS Template for Claude Code

A battle-tested, opinionated `CLAUDE.md` architecture template designed for modern, high-performance SaaS applications built with **Next.js 15 App Router**, **SQLite (better-sqlite3 / Turso)**, and **Drizzle ORM**.

---

## 🚀 Quickstart Setup (3 Steps)

### Step 1: Copy `CLAUDE.md` into your greenfield project
```bash
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-saas-project/CLAUDE.md
```

### Step 2: Install the curated core dependencies
```bash
pnpm add drizzle-orm better-sqlite3 zod lucide-react
pnpm add -D drizzle-kit @types/better-sqlite3 tsx
```

### Step 3: Launch Claude Code
Open your project directory in your terminal:
```bash
claude
```
Claude Code automatically discovers `CLAUDE.md`, adopts the architecture conventions, uses Server Actions with Zod validation, enforces SQLite WAL mode pragmas, and avoids anti-patterns without asking clarifying questions.

---

## 🧪 Verification & Acceptance Testing

Run the automated verification suite to validate all architectural rules:
```bash
python templates/nextjs-sqlite/tests/verify_template.py
```
Outputs:
- ✅ All 6 required sections verified
- ✅ Mandatory stack requirements confirmed (Next.js 15, SQLite, better-sqlite3, Drizzle, WAL pragmas, Server Components, Server Actions, Zod, No Prisma)
- ✅ Anti-pattern justifications validated
