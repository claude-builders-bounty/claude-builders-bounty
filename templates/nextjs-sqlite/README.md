# Next.js + SQLite Template for Claude Code

A robust, production-ready starter configuration and context guide for building Next.js App Router applications with SQLite (libSQL / better-sqlite3) and Drizzle ORM.

---

## 3-Step Quick Start Guide

### Step 1: Copy Template Files into Your Project

Copy `CLAUDE.md` and check the dependencies in `package.json` against your Next.js project:

```bash
# If using this repo directly
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your-nextjs-project/
```

### Step 2: Install Dependencies & Setup Environment

Ensure required dependencies (Drizzle ORM, SQLite driver) and dev tools are installed:

```bash
npm install drizzle-orm better-sqlite3 dotenv
npm install -D drizzle-kit @types/better-sqlite3 tsx
```

Set up your `.env.local`:
```env
DATABASE_URL="sqlite.db"
```

### Step 3: Run Database Migrations & Start Development

Generate schemas and start building with Claude Code:

```bash
npm run db:generate
npm run db:migrate
npm run dev
```

Claude Code will automatically discover `CLAUDE.md` at project root and follow all architecture, Server Action, and Drizzle SQLite conventions.
