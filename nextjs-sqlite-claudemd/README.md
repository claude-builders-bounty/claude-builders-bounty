# CLAUDE.md for Next.js 15 + SQLite SaaS

An opinionated `CLAUDE.md` template for greenfield Next.js 15 + SQLite SaaS projects using Drizzle ORM.

## Setup — 2 steps

**Step 1:** Copy `CLAUDE.md` to your project root.

**Step 2:** Adjust the stack section to match your actual dependencies (auth library, ORM, etc.).

Done. Claude Code will read this file automatically and follow the conventions in every session.

## What's covered

- Stack: Next.js 15 App Router, SQLite + Drizzle ORM, next-auth v5, Tailwind CSS v4, Vitest, Playwright
- All `pnpm` commands (dev, build, test, db:migrate, db:studio)
- Project structure with route groups and separation of concerns
- File naming conventions (PascalCase components, kebab-case actions)
- Server Action pattern with Zod validation and structured return values
- DB singleton setup with WAL mode and foreign keys
- Component boundary rules (Server vs Client)
- Unit test setup with in-memory SQLite
- E2E test patterns with Playwright
- Environment variable reference
- Deployment checklist
- 5 common pitfalls with fixes
