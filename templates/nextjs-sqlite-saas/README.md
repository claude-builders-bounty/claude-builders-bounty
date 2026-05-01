# Next.js 15 + SQLite SaaS — CLAUDE.md Template

> Opinionated, production-ready CLAUDE.md for SaaS projects built with Next.js 15 App Router and SQLite.

## What's Included

- **Stack decisions** — Every choice has a reason
- **Folder structure** — Routes are thin, logic lives in `lib/`
- **Database rules** — Drizzle ORM patterns, migration workflow, query conventions
- **Component patterns** — Server vs Client components, API routes
- **Naming conventions** — Files, components, DB tables, API routes
- **Anti-patterns** — What NOT to do and why
- **Dev commands** — All the commands you need
- **Testing rules** — What to test, what to skip
- **Git workflow** — Branch naming, PR rules

## Usage

1. Copy `CLAUDE.md` to your project root
2. Adjust the stack table if you use different tools
3. Claude Code will understand your project context without asking clarifying questions

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 15 App Router |
| Database | better-sqlite3 / Turso |
| ORM | Drizzle ORM |
| Auth | better-auth |
| Styling | Tailwind CSS 4 + shadcn/ui |
| Validation | Zod |
| Testing | Vitest + Playwright |

## License

MIT
