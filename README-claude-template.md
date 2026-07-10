# Next.js 15 App Router + SQLite SaaS Starter

Opinionated, production-ready CLAUDE.md reference for building SaaS applications with:

- **Next.js 15** App Router (React 19, Server Components, Server Actions)
- **SQLite** via Prisma (Turso/LibSQL or better-sqlite3)
- **TypeScript** (strict mode)
- **Tailwind CSS** + shadcn/ui

## Quick Start

```bash
# 1. Copy CLAUDE.md to your project root
cp CLAUDE.md /path/to/your-project/CLAUDE.md

# 2. Your AI assistant (or you) now has full context on:
#    - Project structure conventions
#    - Naming rules with reasons
#    - Database migration workflow
#    - Dev commands & CI pipeline
#    - Patterns to follow (Server Components, Server Actions, optimistic updates)
#    - Anti-patterns to avoid (client-side fetching, useEffect for data, etc.)

# 3. Start building
npm run dev
```

## What's Inside

| Section | Content |
|---|---|
| **Project Structure** | Directory layout with rationale for every folder |
| **Naming Conventions** | File naming, component naming, export rules |
| **Database Rules** | 10 mandatory rules for Prisma + SQLite migrations |
| **Dev Commands** | All dev/build/test commands with CI pipeline |
| **Patterns** | Server Components first, Server Actions, `useOptimistic`, error handling, loading states, auth middleware, env validation |
| **Anti-Patterns** | 9 common mistakes with explained consequences |
| **Templates** | Copy-paste file templates for pages, actions, queries, and components |

## Design Philosophy

Every rule in CLAUDE.md includes a **reason** — the "why" behind each convention. This makes it usable as onboarding material for both AI assistants and human developers. The template is self-contained: copy it into a greenfield Next.js 15 project and start working immediately, no modification needed.

## License

MIT — use freely in any project.
