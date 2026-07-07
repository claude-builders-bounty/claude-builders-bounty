# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- **Framework**: Next.js 15 (App Router), React 19, TypeScript 5.x
- **Database**: better-sqlite3 (local dev) / Turso (production) via Drizzle ORM
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **CSS**: Tailwind CSS 4 + shadcn/ui components
- **Package manager**: pnpm

## Project Structure
```
src/
├── app/          # App Router pages
│   ├── (auth)/   # Auth group (login, register)
│   ├── (dashboard)/  # Dashboard group (layout with sidebar)
│   ├── api/      # Route handlers
│   └── layout.tsx
├── components/   # React components
│   ├── ui/       # shadcn/ui primitives
│   └── shared/   # App-specific shared components
├── db/           # Database
│   ├── schema/   # Drizzle schema definitions
│   ├── migrations/  # Auto-generated migrations
│   └── index.ts  # DB client
├── lib/          # Utilities
│   ├── actions/  # Server actions
│   └── utils.ts  # Shared helpers
└── middleware.ts  # Next.js middleware
```

## SQL / Migration Conventions
- Every schema change = one migration file (generated via `drizzle-kit`)
- Migrations are auto-generated — never hand-edit them
- Foreign keys are always explicit with `onDelete: 'cascade'` or `'set null'`
- Soft deletes preferred over hard deletes (add `deletedAt` column)
- Timestamps: `createdAt`, `updatedAt` (auto-set via `.default()` / `.$onUpdate()`)
- Run migrations: `pnpm db:migrate`
- Seed data lives in `src/db/seed.ts`, run via `pnpm db:seed`

## Component Patterns
- Server components by default; client components only when interactivity needed
- `'use client'` is a smell — extract interactive islands, not entire pages
- Form state: React 19 `useActionState` + Server Actions (no React Hook Form)
- Data fetching: fetch in server components, pass down as props
- Loading states: `loading.tsx` / `Suspense` boundaries per route segment

## What We Don't Do (And Why)
- No `any` types — use `unknown` + type guards (catches runtime bugs)
- No raw SQL strings — always use Drizzle query builder (migration safety)
- No `useEffect` for data fetching — Server Actions + server components suffice
- No `process.env` in client components — use `NEXT_PUBLIC_` prefix (bundler safety)
- No barrel exports (`index.ts` re-exports) — breaks tree-shaking

## Dev Commands
| Command | Description |
|---------|-------------|
| `pnpm dev` | Start dev server |
| `pnpm build` | Production build |
| `pnpm lint` | ESLint + Prettier |
| `pnpm test` | Vitest (unit) + Playwright (e2e) |
| `pnpm db:migrate` | Run Drizzle migrations |
| `pnpm db:seed` | Seed database |
| `pnpm db:studio` | Open Drizzle Studio |
