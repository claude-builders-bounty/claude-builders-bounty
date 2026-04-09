# CLAUDE.md — Next.js + SQLite SaaS Project

## Project Overview
SaaS application built with Next.js (App Router) and SQLite as the database.

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript (strict) |
| Database | SQLite via better-sqlite3 |
| ORM | Drizzle ORM |
| Styling | Tailwind CSS + shadcn/ui |
| Auth | NextAuth.js v5 |
| Validation | Zod |
| Testing | Vitest + Playwright |

## Coding Conventions
- **No `any`** — use `unknown` with type guards
- **Server Components** by default; `'use client'` only when needed
- **Drizzle ORM** for all DB queries (no raw SQL)
- **Zod** for all request validation
- **Soft deletes** via `deletedAt` column
- **Multi-tenant**: all tables include `tenantId`

## Database
```typescript
export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').unique().notNull(),
  tenantId: text('tenant_id').notNull(),
  role: text('role').default('user').notNull(),
  createdAt: integer('created_at').notNull(),
  deletedAt: integer('deleted_at'),
});
```

## Testing
- Unit: Vitest for utilities
- Integration: Vitest with in-memory SQLite
- E2E: Playwright for critical flows

## Commands
```bash
npm run dev          # Dev server
npm run db:generate  # Drizzle migration
npm run db:migrate   # Run migrations
npm test             # All tests
npm run lint         # ESLint
```
