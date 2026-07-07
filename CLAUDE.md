# CLAUDE.md - Next.js + SQLite SaaS Project Guide

## Project Overview
- **Framework**: Next.js 15 App Router (React Server Components)
- **Database**: SQLite via better-sqlite3 (local) or Turso (production)
- **Auth**: NextAuth.js / Auth.js with credentials + OAuth
- **ORM**: Drizzle ORM (type-safe SQLite queries)
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Package Manager**: pnpm
- **Runtime**: Node.js 20+ (local), Edge (Vercel)

## Directory Structure
```
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth pages (login, register)
│   ├── (dashboard)/       # Authenticated pages
│   ├── api/               # Route handlers (API routes)
│   └── layout.tsx         # Root layout
├── components/            # Reusable UI components
├── db/                    # Database layer
│   ├── schema/           # Drizzle schema definitions
│   ├── migrations/       # Database migrations
│   └── index.ts          # DB client initialization
├── lib/                   # Shared utilities
├── public/               # Static assets
└── middleware.ts          # Next.js middleware (auth checks)
```

## Development Commands
- `pnpm dev` - Start dev server on :3000
- `pnpm build` - Production build
- `pnpm test` - Run tests (vitest)
- `pnpm db:generate` - Generate new migration
- `pnpm db:push` - Push schema changes (dev only)
- `pnpm db:studio` - Open Drizzle Studio
- `pnpm lint` - ESLint + Prettier check
- `pnpm typecheck` - tsc --noEmit

## Database Conventions
- **NEVER** use `db.delete().where()` without a WHERE clause
- **ALWAYS** use prepared statements for user input
- Migration files are read-only after creation
- Prefix junction tables with `_` (e.g., `_userTeams`)
- Soft deletes preferred: add `deletedAt` column

## Code Style
- RSC (React Server Components) by default; add 'use client' only when needed
- Server actions in `app/actions/` using `"use server"`
- API routes use Next.js Route Handlers
- Error boundaries at each route segment
- Loading states use `loading.tsx` files

## Anti-Patterns
- ❌ `useEffect` for data fetching (use RSC or Server Actions)
- ❌ Direct DB access from client components
- ❌ Storing secrets in client-side code
- ❌ `any` types (use `unknown` + type guards instead)
- ❌ `rm -rf` in scripts (use `trash` or `rimraf`)
