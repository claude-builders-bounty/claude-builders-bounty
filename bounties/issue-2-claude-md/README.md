# CLAUDE.md Template — Next.js 15 + SQLite SaaS

## Setup

1. Copy `CLAUDE.md` to your project root
2. Start Claude Code in the project directory
3. Claude Code will automatically read the file and follow all conventions

## What it covers

- **Stack & versions** — Node 20, Next.js 15, TypeScript strict, Drizzle ORM, Tailwind 4
- **Folder structure** — App Router layout with auth groups, API routes, components
- **Naming conventions** — PascalCase components, snake_case DB, UPPER_SNAKE env vars
- **SQL / migration rules** — Never edit migrations, parameterized queries, every table has id/created_at/updated_at
- **Component patterns** — Server Components by default, Client Components only when needed, Server Actions for forms
- **Anti-patterns** — 10 specific patterns to avoid with reasons (no useEffect fetching, no Prisma, no barrel exports, etc.)
- **Dev commands** — Complete npm script reference
- **Auth pattern** — Session in SQLite, middleware redirects, server-side checks
- **Error handling** — error.tsx boundaries, not-found.tsx, loading.tsx, action return types

## Design philosophy

Every rule has a reason. This isn't a generic template — it's opinionated based on production experience with the Next.js 15 + SQLite stack. Claude Code understands these conventions without asking clarifying questions.
