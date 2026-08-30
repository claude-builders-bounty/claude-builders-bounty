# Next.js 15 + SQLite SaaS CLAUDE.md Template

A production-ready, highly opinionated `CLAUDE.md` specification designed for greenfield and enterprise Next.js 15 App Router applications backed by SQLite (better-sqlite3 / Turso) and Drizzle ORM.

---

## 3-Step Setup Guide

### 1. Copy `CLAUDE.md` to Project Root
```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your-nextjs-app/CLAUDE.md
```

### 2. Verify Stack Dependencies
Ensure your `package.json` includes:
```bash
npm install drizzle-orm better-sqlite3 zod @radix-ui/react-slot clsx tailwind-merge
npm install -D drizzle-kit @types/better-sqlite3
```

### 3. Run Claude Code
Launch Claude Code in your project directory:
```bash
claude
```
Claude Code automatically indexes `CLAUDE.md` and follows all architectural conventions, Server Action patterns, and migration safety rules without prompting for clarification.
