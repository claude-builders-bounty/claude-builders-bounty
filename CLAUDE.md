# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project instructions for Claude Code. Every rule has a reason.
> Drop this in your project root and Claude Code will follow it.

## Project Stack
- **Frontend**: Next.js 15 App Router, React 19, Tailwind CSS 4
- **Backend**: Next.js API routes, better-sqlite3 (single-file SQLite)
- **Auth**: next-auth v5 with Credentials provider
- **ORM**: Drizzle ORM (migrations managed via `drizzle-kit`)
- **Validation**: Zod schemas on all API boundaries
- **Testing**: Vitest + React Testing Library

## Directory Conventions (DO NOT DEVIATE)
```
src/
  app/           # App Router pages & API routes
    (auth)/      # Auth group: login, register, forgot-password
    (dashboard)/ # Authenticated routes: dashboard, settings, billing
    api/         # REST endpoints under /api/*
  components/    # Shared UI (Button, Card, Modal, FormField)
  db/
    schema.ts    # Drizzle table definitions — SINGLE SOURCE OF TRUTH
    index.ts     # Database connection singleton
  lib/           # Business logic, utilities, auth helpers
  hooks/         # Custom React hooks
  types/         # Shared TypeScript types
```
**Reason**: Route groups (`(dashboard)`) keep layout separation clean. Single `schema.ts` avoids circular imports.

## Commands
```bash
npm run dev          # Next.js dev server (port 3000)
npm run build        # Production build
npm run test         # Vitest — all tests
npm run test:watch   # Vitest — watch mode
npm run lint         # ESLint + Prettier
npm run db:generate  # Generate Drizzle migrations
npm run db:migrate   # Apply migrations
npm run db:studio    # Drizzle Studio (browser DB explorer)
```

## Coding Rules

### TypeScript
- **No `any`.** Use `unknown` and narrow with Zod.
- All API route handlers return typed responses: `NextResponse.json<T>(data)`
- Server Components by default; `'use client'` only when you need `useState`, `useEffect`, or event handlers.

### Database
- **Migrations always go through Drizzle.** Never edit the SQLite file directly.
- Every migration must be reversible. Test `down` migration before commit.
- Seed data goes in `src/db/seed.ts` — idempotent (safe to run repeatedly).

### API Routes
- **Every API route validates input with Zod.** No raw `req.body` access.
- Authentication check is the FIRST line of every protected route.
- Return structured errors: `{ error: string, code: string }`

### Components
- One component per file. File name = component name (PascalCase).
- Props interface exported, named `{ComponentName}Props`.
- No inline styles — Tailwind only.

### Security (NON-NEGOTIABLE)
- Passwords hashed with `bcryptjs` (12 rounds minimum).
- SQLite file outside `public/` directory — put in `data/` at project root.
- All user input sanitized via Zod before touching the database.
- CSRF protection via next-auth (enabled by default).

## Anti-Patterns to AVOID
- ❌ `SELECT *` — always specify columns in Drizzle queries
- ❌ Raw SQL via `db.run()` — use Drizzle query builder
- ❌ `fetch()` directly in Server Components — use Server Actions
- ❌ `useEffect` for data fetching — use Server Components or React Query
- ❌ Mutating state from child components — lift state up
- ❌ Hardcoded secrets — use `process.env` with Zod validation at startup

## Testing
- Unit tests for `lib/` functions — no mocking, use real SQLite in WAL mode
- API route tests via `next-test-api-route-handler`
- Integration tests for critical flows: signup → login → create → read
- Run before every commit: `npm run test && npm run lint`

## Git Workflow
- Branch naming: `feat/`, `fix/`, `refactor/` prefixes
- Commit messages: Conventional Commits (`feat:`, `fix:`, etc.)
- Squash-merge to main. Linear history.
