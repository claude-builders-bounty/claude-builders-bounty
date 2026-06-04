# Next.js 15 + SQLite SaaS — Project Guide

## Tech Stack
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via Turso/libsql
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5
- **UI**: shadcn/ui + Tailwind CSS
- **Language**: TypeScript (strict mode)

## Project Structure
```
src/
  app/          # App Router pages & API routes
  components/   # React components
  db/           # Drizzle schema & migrations
  lib/          # Shared utilities, auth config
  actions/      # Server actions
```

## Naming
- **Files**: kebab-case.ts, PascalCase.tsx
- **Routes**: app/api/[resource]/route.ts
- **DB**: snake_case, plural tables
- **Components**: PascalCase, one per file

## Dev Commands
```
npm run dev        # Start dev server
npm run build      # Production build
npm run db:push    # Push schema
npm run lint       # ESLint
npm run type-check # tsc --noEmit
```

## DB Rules
- Create migration before pushing schema changes
- Never drop columns without deprecation
- Specify columns in SELECT, never *
- Soft deletes preferred

## Patterns
- Server Components by default
- try/catch in every API route
- auth() at top of protected routes
- Prepared statements for DB
- React Server Actions for forms

## Anti-Patterns
- useEffect for data fetching
- Direct DB from client
- Secrets in .env.local without docs
- Mixing Pages/App Router
