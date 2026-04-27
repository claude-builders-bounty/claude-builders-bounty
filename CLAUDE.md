# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Latest stable, RSC native |
| Database | SQLite via better-sqlite3 (dev) / Turso (prod) | Zero-setup dev, edge-distributed prod |
| ORM | Drizzle ORM | Type-safe, SQL-like syntax |
| Auth | NextAuth v5 / Auth.js | Mature, supports credentials + OAuth |
| CSS | Tailwind CSS 4 | Utility-first, minimal config |
| Validation | Zod | Type inference, shared frontend/backend |
| Payments | Stripe | Industry standard |

## Folder Structure

```
src/
├── app/                    # App Router pages & API routes
│   ├── (auth)/             # Auth group (login, register)
│   ├── (dashboard)/        # Dashboard group (protected)
│   ├── api/                # Route handlers
│   └── layout.tsx
├── components/             # React components
│   ├── ui/                 # Primitives (Button, Input, etc.)
│   ├── forms/              # Form components
│   └── layouts/            # Page layouts
├── db/                     # Database
│   ├── schema/             # Drizzle schemas
│   ├── migrations/         # Auto-generated
│   └── index.ts            # DB client
├── lib/                    # Utilities
│   ├── auth.ts             # Auth config
│   ├── stripe.ts           # Stripe helpers
│   └── utils.ts            # Shared utils
└── types/                  # Shared types
```

## Commands

```bash
npm run dev                  # Start dev server
npm run db:generate          # Generate Drizzle migration
npm run db:migrate           # Apply migration
npm run db:studio            # Drizzle Studio (GUI)
npm run test                 # Vitest unit tests
npm run test:e2e             # Playwright e2e
npm run lint                 # Biome lint + format
npm run build                # Production build
```

## SQL / Migration Conventions

### DO ✅
- Use `drizzle-kit` for all migrations (never hand-write SQL)
- Foreign keys for relational integrity
- Timestamps: `created_at` (default `now()`), `updated_at` (auto `ON UPDATE`)
- Soft deletes with `deleted_at DATETIME` column
- Index frequently-queried columns

### DON'T ❌
- Never `SELECT *` — always specify columns
- Never cascade delete user data — use soft delete
- Never run migrations on production without a rollback plan

## Component Patterns

### Server Components (default)
```tsx
export default async function BountiesPage() {
  const bounties = await db.query.bounties.findMany();
  return <BountyList bounties={bounties} />;
}
```

### Client Components (when needed)
```tsx
'use client';
// Only for: interactivity, hooks, browser APIs, context
```

### Forms
- `react-hook-form` + `@hookform/resolvers/zod`
- Server actions for submission
- Client validation + server re-validation

## What We Don't Do (and Why)

| ❌ Pattern | Reason |
|------------|--------|
| Redux / Zustand | App Router + Server Actions make client state rarely needed |
| Prisma | Drizzle has smaller bundle, better edge support |
| Pages Router | App Router is the future; Pages Router is maintenance-only |
| Custom CSS | Tailwind covers 99%; custom CSS increases maintenance |
| Monorepo (turborepo) | Not justified until 3+ apps share code |

## Anti-Patterns

1. **Nested layouts with data fetching** — creates RSC waterfall
2. **Overusing `use cache`** — only cache what benchmarks say is slow
3. **Client components in layout** — whole layout becomes client-rendered
4. **Default exports everywhere** — named exports easier to refactor
5. **Magic strings for routes** — use constants or route files

## Code Style

- `import type` for type-only imports
- Async components return `Promise<JSX.Element>`
- Error boundaries per feature, not global
- `@/` absolute imports
- Biome for lint + format (no Prettier)

## Design Decisions

### SQLite over Postgres for MVP?
- Zero local dev setup
- Turso provides edge-distributed SQLite in production
- Cheaper at low scale; migrate to Postgres when >100 concurrent writes/s

### Drizzle over Prisma?
- Smaller bundle (important for edge)
- SQL-like API — your SQL knowledge transfers
- Better migration DX with drizzle-kit
- No schema engine running in production

### Soft Deletes?
- Data recovery without DB restore
- Built-in audit trail
- Simple `WHERE deleted_at IS NULL` filter
