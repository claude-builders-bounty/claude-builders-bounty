# Next.js 15 + SQLite CLAUDE.md Template

> A production-ready `CLAUDE.md` for Claude Code that understands your Next.js + SQLite SaaS project from day one.

## Install

```bash
# 1. Download into your project root
curl -o CLAUDE.md https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite/CLAUDE.md

# 2. Done. Claude Code reads it automatically on next session.
```

## What's included

- **Stack & Versions** — Every tool pinned with a reason why
- **Folder Structure** — Where everything lives and why
- **Dev Commands** — `pnpm dev`, `pnpm db:migrate`, `pnpm test`, etc.
- **SQL/Migration Conventions** — Column naming, soft deletes, timestamp format, ID strategy
- **Component Patterns** — Server Components (default), Client Components (opt-in), Server Actions, Forms
- **What We Don't Do** — 11 anti-patterns with reasons (no Prisma, no `any`, no auto-increment IDs, etc.)
- **Naming Conventions** — Files, directories, components, env vars
- **Error Handling** — Server Actions, API routes, validation
- **Security** — Auth middleware, webhook verification, rate limiting

## Customization

Edit these sections to match your project:

1. **Stack & Versions** — Change ORM (Drizzle → Kysely), auth provider, styling
2. **Folder Structure** — Add/remove route groups
3. **What We Don't Do** — Adjust rules to team preferences

## Testing

```bash
# Create a new Next.js project
pnpm create next-app@latest my-saas --typescript --tailwind --app --src-dir

# Drop the CLAUDE.md in
curl -o my-saas/CLAUDE.md https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite/CLAUDE.md

# Open with Claude Code and verify it understands the context without asking questions
cd my-saas && claude
```

## License

MIT
