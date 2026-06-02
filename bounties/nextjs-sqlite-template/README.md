# Next.js + SQLite CLAUDE.md Template

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## What's Included

The template covers:

- **Stack & Versions**: Next.js 15, better-sqlite3/Turso, Drizzle ORM, NextAuth.js v5
- **Folder Structure**: Clear organization for App Router projects
- **Naming Conventions**: Consistent patterns for files, components, database tables
- **Database Rules**: Schema definitions, migrations, query patterns
- **Component Patterns**: Server vs Client components, Server Actions
- **API Routes**: RESTful patterns with proper error handling
- **Authentication**: NextAuth.js integration with database sessions
- **Anti-Patterns**: What to avoid and why

## Usage

1. Copy `CLAUDE.md` to your Next.js project root
2. Start using Claude Code - it will understand your project structure without clarifying questions

## Why Opinionated?

Generic templates require Claude to ask clarifying questions. This template makes specific choices:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | Drizzle | Type-safe, lightweight, SQLite-native |
| Auth | NextAuth.js v5 | Built for App Router, database sessions |
| Styling | Tailwind + shadcn/ui | Standard for modern Next.js |
| State | Server Components first | Faster, simpler, SEO-friendly |

## Testing

Create a new Next.js project and paste the CLAUDE.md. Ask Claude Code to:

- "Add a posts table with title and content"
- "Create a CRUD API for posts"
- "Add user authentication"

Claude should understand the project structure and follow conventions without asking for preferences.

## License

MIT
