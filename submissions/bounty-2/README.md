# Bounty #2: CLAUDE.md for Next.js + SQLite SaaS

**Author**: MoneyKalle  
**Submitted**: 2026-08-11

## Solution

A comprehensive, opinionated `CLAUDE.md` covering:

- **Project Structure**: App Router layout with clear separation of server/client concerns
- **Naming Conventions**: Consistent kebab-case/PascalCase/camelCase rules
- **Database Rules**: Drizzle ORM with SQLite, migration workflow, schema design patterns
- **Dev Commands**: Full pnpm script reference
- **Patterns**: Server Components, Server Actions, Zod validation, optimistic updates
- **Anti-Patterns**: 10 common mistakes with explicit alternatives
- **Testing Strategy**: Vitest + Playwright setup
- **Environment Variables**: Required and optional with documentation
- **Deployment Checklist**: Production readiness steps

## Design Decisions

| Decision | Why |
|----------|-----|
| Drizzle over Prisma | 5-10x lighter, edge-compatible, no codegen |
| better-sqlite3 | Synchronous API = simpler Server Components, no connection pool issues |
| Server Components default | Reduced bundle size, direct DB access without API layer |
| Server Actions for mutations | Progressive enhancement, no client-side API logic |
| ULID primary keys | Non-enumerable, time-sortable, URL-safe |
| Zod at boundaries | Runtime type safety at every trust boundary |

## Usage

1. Copy `CLAUDE.md` to the root of any Next.js 15 + SQLite project
2. Claude Code reads it automatically as project context
3. All conventions, commands, and patterns are immediately understood
