# CLAUDE.md — Next.js + SQLite Project

## Project Overview
- Framework: Next.js (App Router)
- Database: SQLite (better-sqlite3)
- Styling: Tailwind CSS
- Language: TypeScript

## Commands
```bash
npm run dev          # localhost:3000
npm run build        # production build
npm run lint         # ESLint
npm run test         # Vitest
npm run db:migrate   # SQLite migrations
npm run db:seed      # seed database
```

## Architecture
```
src/
  app/            # Pages & API routes
  components/     # Reusable components
  lib/            # SQLite helpers, schema
  hooks/          # Custom React hooks
  types/          # TypeScript types
```

## Database
- SQLite file: ./data/app.db
- lib/db.ts exports singleton connection
- Migrations in migrations/ run sequentially
- Parameterized queries only — never string interpolation

## Code Style
- Functional components with hooks
- Server components by default; use client only when needed
- API routes in app/api/ using route handlers
- DB queries in lib/ — never in components
- Zod schemas for API validation

## Key Dependencies
- better-sqlite3, drizzle-orm, tailwindcss, zod, next-auth
