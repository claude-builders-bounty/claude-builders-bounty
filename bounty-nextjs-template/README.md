# CLAUDE.md Template for Next.js + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` template for AI-assisted development of SaaS applications built with Next.js 15 and SQLite.

## Usage

1. Copy `CLAUDE.md` to your project root
2. Customize the tech stack and patterns as needed
3. Start developing with Claude Code

## What's Included

- **Tech Stack**: Next.js 15, SQLite (better-sqlite3), NextAuth.js, Tailwind CSS
- **Project Structure**: App Router conventions, component organization
- **Naming Conventions**: Files, code, database tables
- **Database Rules**: Migrations, query patterns
- **Development Commands**: All essential npm scripts
- **Patterns**: Server Components, data fetching, error handling
- **Anti-Patterns**: What to avoid and why
- **Auth Pattern**: NextAuth.js v5 integration
- **Testing Strategy**: Vitest + Playwright examples
- **Security Checklist**: Essential security measures

## Why This Template?

Every rule has a reason:

| Rule | Reason |
|------|--------|
| Server Components by default | Reduce client JS, direct DB access |
| better-sqlite3 over Prisma | No ORM magic, better performance |
| SQL migrations | Full control, easier debugging |
| Parameterized queries | SQL injection prevention |

## Customization

Modify the template to match your project:

- Replace tech stack choices
- Add your specific patterns
- Update database schema conventions
- Add your deployment instructions

## Bounty

Created for [$75 Bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2).

## License

MIT
