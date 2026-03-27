# CLAUDE.md Template — Next.js + SQLite SaaS

Production-ready CLAUDE.md for a SaaS project built with Next.js 15 App Router and SQLite.

## Usage

```bash
cp CLAUDE.md /path/to/your/nextjs-project/CLAUDE.md
```

That's it. Claude Code reads it automatically.

## What's Covered

- Stack & versions (Next.js 15, TypeScript, SQLite, Drizzle, Tailwind)
- Folder structure with explanations
- Dev commands
- Database schema conventions (nanoid IDs, timestamps, indexes)
- Server Action patterns (auth-first, validation, revalidation)
- Component patterns (Server Components default, colocated, no barrels)
- Naming conventions (files, components, actions, tables, columns, env)
- Validation with Zod
- Anti-patterns with reasons (no raw SQL, no API routes for CRUD, no any, etc.)

## Opinionated by Design

Every rule has a reason. This isn't a generic template — it's how a production SaaS should be structured.
