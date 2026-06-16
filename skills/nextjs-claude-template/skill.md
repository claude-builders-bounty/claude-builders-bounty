# CLAUDE.md Template for Next.js + SQLite Projects

Generates a comprehensive `CLAUDE.md` file for Next.js + SQLite SaaS projects.

## Usage

```
/claude-init nextjs-sqlite
```

## Generated CLAUDE.md structure

```markdown
# Project Name

## Architecture
- Next.js 14 App Router
- SQLite via better-sqlite3
- API routes in `app/api/`
- Components in `components/`

## Commands
- `npm run dev` — Start dev server
- `npm run build` — Production build
- `npx prisma generate` — Regenerate DB client
- `npm test` — Run Vitest tests

## Conventions
- TypeScript strict mode
- Server Components by default, 'use client' only when needed
- API routes: one export per HTTP method
- DB queries in `lib/db.ts`, never inline

## Testing
- Vitest for unit tests
- Playwright for E2E
- Test files: `__tests__/` or `.test.ts`

## Dependencies
- next, react, typescript
- better-sqlite3, drizzle-orm
- tailwindcss, shadcn/ui
- zod (validation)
- next-auth (authentication)

## Security
- All user input validated with zod
- SQL queries use parameterized statements
- API routes validate session
- Environment variables in .env.local (never committed)
