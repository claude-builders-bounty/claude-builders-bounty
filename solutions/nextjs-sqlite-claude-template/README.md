# Next.js 15 + SQLite CLAUDE.md Template

This solution provides a production-ready, highly opinionated `CLAUDE.md` template for Next.js 15 App Router and SQLite (Drizzle ORM + better-sqlite3/Turso) SaaS projects.

## Installation

### Step 1: Copy to your project root
Simply copy the `CLAUDE.md` file from this folder into the root directory of your Next.js 15 + SQLite project:

```bash
cp solutions/nextjs-sqlite-claude-template/CLAUDE.md /path/to/your/project/CLAUDE.md
```

### Step 2: Open Claude Code or Antigravity
Launch Claude Code or any agent in your project root. It will read the `CLAUDE.md` automatically and align perfectly with all database migration workflows, project folder patterns, and server/client component rules.

## Key Guidelines Provided
- Modular folder structure enforcing server/client segregation.
- Drizzle ORM schema modifications and code-driven migrations workflow.
- Strict data fetching rules using React Server Components directly.
- Secure data mutations using Server Actions with Zod validations.
- Anti-patterns list highlighting SQL injection prevention and client-side database isolation.
