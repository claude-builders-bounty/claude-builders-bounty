# Bounty #2: CLAUDE.md for Next.js 15 + SQLite SaaS

Production-ready, opinionated `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## What's included

The `CLAUDE.md` covers:

- **Stack & versions**: Next.js 15, SQLite, Drizzle ORM, better-auth, Tailwind + shadcn/ui
- **Project structure**: App Router layout with auth groups, versioned API, co-located components
- **Database conventions**: Schema rules, migration workflow, query patterns with Drizzle
- **Component patterns**: Server-first rendering, Server Actions for mutations, form handling
- **Auth patterns**: Cookie-based sessions, role-based access, middleware checks
- **Anti-patterns**: 10 things we don't do, each with a concrete reason
- **Testing strategy**: Vitest + Playwright, co-located test files

## Setup

1. Copy `CLAUDE.md` to your project root:
   ```bash
   cp CLAUDE.md /path/to/your/nextjs-project/CLAUDE.md
   ```

2. Open Claude Code in your project — it will automatically pick up the context.

## Design decisions

Every rule in this file exists because of a real problem:

- **Drizzle over Prisma**: Prisma's SQLite support is slow and generates heavy clients. Drizzle is SQL-native and produces zero overhead.
- **Server Components by default**: Eliminates the need for client-side data fetching libraries and global state.
- **UUIDs over autoincrement**: Prevents ID enumeration attacks. Text IDs work naturally with SQLite.
- **No barrel exports**: They cause circular dependencies and slow down builds. Direct imports are explicit and fast.
- **Server Actions over API routes for forms**: Less boilerplate, automatic revalidation, progressive enhancement.

## Tested

Created a fresh Next.js 15 project, pasted the CLAUDE.md, and confirmed Claude Code:
- Understood the stack without clarifying questions
- Generated Drizzle schema following the conventions
- Created Server Components with direct DB access (no unnecessary API routes)
- Used Server Actions for form submissions
- Applied the correct file naming and directory structure
