# Next.js 15 + SQLite SaaS CLAUDE.md Template

Bounty target: Claude Builders Bounty #2.

This is an opinionated `CLAUDE.md` for a greenfield SaaS built with:

- Next.js 15 App Router
- TypeScript
- SQLite via better-sqlite3 locally or Turso/libSQL in production
- Server Actions for mutations
- Route Handlers for external API/webhook boundaries
- Tailwind + shadcn/ui for UI

## Install

Copy the template into the root of a new project:

```bash
cp submissions/nextjs-sqlite-claude-template/CLAUDE.md ./CLAUDE.md
```

## Expected project bootstrap

```bash
npx create-next-app@latest my-saas --ts --tailwind --eslint --app --src-dir
cd my-saas
npm install better-sqlite3 zod
npm install -D @types/better-sqlite3
```

## Validation performed

The template was tested against a greenfield Next.js SaaS structure by checking whether it gives Claude Code enough context to proceed without asking clarifying questions for common tasks:

1. Add a waitlist table and signup form
2. Add a billing events table and Stripe webhook route
3. Add a dashboard server component that reads from SQLite
4. Add a migration file and explain rollback behavior

The template defines exact paths, conventions, migration rules, anti-patterns, and reasoning behind each rule.
