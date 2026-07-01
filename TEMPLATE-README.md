# CLAUDE.md for Next.js + SQLite SaaS

Production-ready CLAUDE.md template for SaaS projects built with Next.js 15 App Router and SQLite.

## Features

- Complete project structure guide
- Naming conventions for all file types
- Database rules (Drizzle ORM + migrations)
- Patterns to follow (Server Components, Server Actions, etc.)
- Anti-patterns to avoid with examples
- Deployment checklist
- Testing guidelines

## Usage

1. Copy `CLAUDE.md` to your project root
2. Adjust the tech stack section if needed (e.g., swap Turso for PlanetScale)
3. Claude Code will automatically read it for context

## Why This Works

Every rule has a reason:
- **Server Components by default** → Better performance, smaller bundles
- **Drizzle ORM** → Type-safe queries, no SQL injection
- **UUID primary keys** → Safe for distributed systems
- **snake_case DB columns** → SQLite convention, avoids quoting issues
- **HttpOnly cookies** → XSS protection for auth tokens
