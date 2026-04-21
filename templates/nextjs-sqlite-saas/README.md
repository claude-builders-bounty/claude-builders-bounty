# CLAUDE.md Template: Next.js 15 + SQLite SaaS

> An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## What is this?

A `CLAUDE.md` file that tells [Claude Code](https://docs.anthropic.com/en/docs/claude-code) exactly how your Next.js + SQLite project works — stack choices, folder structure, naming conventions, database patterns, component architecture, and anti-patterns to avoid.

Drop it into a new project and Claude Code understands the context without asking clarifying questions.

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 15 (App Router) |
| Database | better-sqlite3 (or Turso for edge) |
| Auth | Better Auth |
| Validation | Zod |
| Styling | Tailwind CSS 4 + shadcn/ui |
| Testing | Vitest |
| Package Manager | pnpm |

## What's covered

- **Stack & versions** — Every dependency pinned with reasoning
- **Folder structure** — Route groups, lib organization, migration files
- **Naming conventions** — Files, variables, database tables, Zod schemas
- **SQL / migration conventions** — WAL mode, prepared statements, forward-only migrations, ID strategy
- **Component patterns** — Server Components (default), Client Components (when needed), Server Actions, API routes
- **Environment variables** — Zod-validated env config
- **What we don't do (and why)** — 14 opinionated rules with explanations
- **Testing conventions** — Real DB tests, no mocks
- **Git conventions** — Commit message format
- **Performance & deployment notes** — SQLite-specific gotchas

## Usage

1. Create a new Next.js project:
   ```bash
   pnpm create next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir=false
   ```

2. Copy the CLAUDE.md into your project root:
   ```bash
   cp CLAUDE.md /path/to/my-saas/CLAUDE.md
   ```

3. Open Claude Code in your project — it will read the file automatically and follow the conventions.

## Customization

This template is opinionated by design, but every project is different. Common modifications:

- **Swap better-sqlite3 → Turso**: Update `lib/db.ts` connection code and `DATABASE_URL` env var
- **Add an ORM**: If your team prefers Drizzle, add it — but read the "What we don't do" section first
- **Change ID strategy**: If you need UUIDs for cross-system compatibility, update the `CREATE TABLE` templates
- **Adjust auth**: Replace Better Auth with NextAuth.js or Clerk if needed

## Contributing

Found something that could be better? Open an issue or submit a PR. The goal is to keep this template sharp and useful for real projects.

## License

MIT
