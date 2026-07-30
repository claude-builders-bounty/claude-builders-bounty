# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace Overview

This is a **Next.js 15 App Router + SQLite** SaaS starter. It uses `better-sqlite3` for the database, `drizzle-orm` as the query builder, and `next-auth` for authentication.

**Key paths:**
- `src/app/` — App Router pages and layouts
- `src/components/` — React components
- `src/lib/` — utilities, database client, auth
- `src/migrations/` — SQLite migration files
- `drizzle/` — generated schema snapshots

## Development Commands

```bash
# Install dependencies
pnpm install

# Run dev server
pnpm dev

# Run tests
pnpm test

# Lint
pnim lint

# Database migrations
pnpm db:generate   # generate migration from schema
pnpm db:migrate    # apply pending migrations
pnpm db:studio     # open Drizzle Studio
```

## Coding Conventions

### Project Structure
- All route handlers go in `src/app/<route>/route.ts`
- Server components by default; client components need `'use client'`
- Database queries go through `src/lib/db/index.ts` — never import `better-sqlite3` directly
- Types go in `src/types/`

### Naming
- Routes: kebab-case directories (`/user-settings`)
- Files: PascalCase for components (`UserCard.tsx`), camelCase for utilities (`formatDate.ts`)
- Database tables: snake_case (`user_settings`)
- API routes: RESTful plural nouns (`/api/organizations`)

### Database Rules
- **Always use migrations.** Never modify the schema inline.
- Migrations are in `src/migrations/` — one file per change set
- Use `drizzle-orm` for all queries; no raw SQL unless absolutely necessary
- If raw SQL is needed, use parameterized queries only
- Each table must have `created_at` and `updated_at` timestamps

### Patterns to Follow
- **Server components first.** Only use client components for interactivity.
- **Route handlers** should be thin — delegate to service functions in `src/lib/services/`
- **Error handling:** use custom `AppError` class from `src/lib/errors.ts`
- **Validation:** use Zod schemas in `src/lib/validators/`
- **Auth:** protect routes with `getServerSession()` in server components or `auth()` in route handlers

### Anti-Patterns
- **Don't** put business logic in route handlers — move to services
- **Don't** create client components unnecessarily — they break streaming
- **Don't** store secrets in `.env.local` without checking `.env.example`
- **Don't** import from `node_modules` directly if a project utility exists
- **Don't** skip type safety — avoid `any`, use `unknown` if truly unknown
- **Don't** mutate database rows directly — use update functions

## Testing

- Unit tests: `src/**/*.test.ts`
- Integration tests: `src/**/*.integration.test.ts`
- Run `pnpm test:watch` during development
- Aim for 80%+ coverage on business logic

## Deployment

- Build: `pnpm build`
- Output: `.next/` directory
- SQLite DB: ensure `prisma/dev.db` or `better-sqlite3` file is writable in production
- Use `start` script for production: `pnpm start`

## AI Coding Rules

When generating code:
1. Follow the patterns above exactly
2. Include types for all function parameters and returns
3. Add JSDoc comments for public APIs
4. Write tests for new functionality
5. Update this file if you introduce a new pattern
