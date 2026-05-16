# Next.js 15 + SQLite SaaS — CLAUDE.md Template

An opinionated, production-ready [CLAUDE.md](https://docs.anthropic.com/en/docs/claude-code/overview) for a SaaS project built with Next.js 15 App Router and SQLite.

## Usage

1. Create a new Next.js 15 project
2. Copy `CLAUDE.md` into the project root
3. Start Claude Code — it reads the file automatically

The template covers:
- Project structure with domain grouping
- Drizzle ORM schema & migration conventions
- Server Components vs Client Components rules
- Server Action patterns
- What *not* to do (with reasons)
- Environment variables reference
- Testing strategy, error handling, accessibility
- Performance checklist
- Feature addition checklist

## Opinionated Choices

| Choice | Rationale |
|--------|-----------|
| Drizzle ORM > Prisma | No codegen, SQL-like, native SQLite/Turso support |
| better-sqlite3 + Turso | Single-file dev, scalable production |
| Better Auth > Clerk | SQLite-native, simpler billing model |
| pnpm > npm/yarn | Strict dep isolation, disk-efficient |
| shadcn/ui | Customizable, no dep lock-in |
| Domain grouping > file-type grouping | Easier to delete/modify features |
