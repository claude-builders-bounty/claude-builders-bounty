# CLAUDE.md Template: Next.js + SQLite SaaS

A production-ready CLAUDE.md template for SaaS applications built with Next.js App Router and SQLite.

## What's Included

The template covers:
- **Project structure**: App Router conventions, route groups, component organization
- **Database patterns**: Drizzle ORM schema, migrations, query layer, transactions
- **Authentication**: NextAuth.js v5 setup, protected routes, middleware
- **Payments**: Stripe subscriptions, webhook handling, server-side verification
- **Styling**: Tailwind CSS + shadcn/ui conventions
- **Testing**: Vitest + React Testing Library + Playwright
- **Environment**: All required env vars documented with examples
- **Do NOT list**: Common anti-patterns to avoid

## Setup

1. Copy `CLAUDE.md` to your project root:
   ```bash
   cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your/project/CLAUDE.md
   ```

2. Customize the sections to match your specific project:
   - Update the tech stack if you use different libraries
   - Add project-specific conventions
   - Modify the directory structure to match yours

3. Claude Code will automatically read `CLAUDE.md` and follow the conventions.

## Tech Stack Covered

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 14+ (App Router) |
| Database | SQLite + better-sqlite3 + Drizzle ORM |
| Auth | NextAuth.js v5 (Auth.js) |
| Payments | Stripe |
| UI | Tailwind CSS + shadcn/ui |
| Testing | Vitest + RTL + Playwright |

## License

MIT
