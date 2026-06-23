# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS

## Project Structure

```
my-saas/
├── src/
│   ├── app/              # App Router pages & layouts
│   │   ├── (auth)/       # Auth group (login, register)
│   │   ├── (dashboard)/  # Dashboard group (protected)
│   │   ├── api/          # Route handlers (REST endpoints)
│   │   └── layout.tsx    # Root layout with providers
│   ├── components/       # React components
│   │   ├── ui/           # Base UI primitives (button, card, etc.)
│   │   └── features/     # Feature-specific components
│   ├── db/               # Database layer
│   │   ├── schema.ts     # Drizzle schema definitions
│   │   ├── migrations/   # Auto-generated migrations
│   │   └── queries.ts    # Reusable query helpers
│   ├── lib/              # Shared utilities and config
│   └── middleware.ts     # NextAuth / auth middleware
├── drizzle.config.ts     # Drizzle ORM config
├── package.json
└── CLAUDE.md             # This file
```

## Dev Commands

- `pnpm dev` — Start dev server
- `pnpm build` — Type-check + build
- `pnpm lint` — ESLint + Prettier
- `pnpm test` — Vitest (unit)
- `pnpm test:e2e` — Playwright (E2E)
- `pnpm db:generate` — Drizzle: generate migration
- `pnpm db:push` — Drizzle: push schema to local SQLite
- `pnpm db:studio` — Drizzle Studio GUI
- `pnpm type-check` — tsc --noEmit

## DB Migration Rules

1. **NEVER edit existing migration files.** Generate new ones with `pnpm db:generate`.
2. Each schema change = one new migration file.
3. Test migrations locally with `pnpm db:push` before committing.
4. Use `sqlite` driver in Drizzle (not `better-sqlite3` directly).
5. Keep schema in a single `src/db/schema.ts` file until >15 tables.

## Coding Conventions

### Naming
- Files: `kebab-case.ts` for utilities, `PascalCase.tsx` for components
- Routes: `[param]` for dynamic, `(group)` for route groups, `_prefix` for private
- Functions: `camelCase`, exported as named exports
- DB tables: `snake_case` (Drizzle convention)
- Environment variables: `NEXT_PUBLIC_` prefix only for client-safe vars

### Patterns to Follow
- **Server-first**: Fetch data in Server Components, pass down as props
- **Server Actions**: Use for mutations, never write raw API routes for CRUD
- **Validate inputs**: Always use Zod in Server Actions
- **Error boundaries**: One per route segment, with `error.tsx`
- **Loading states**: One `loading.tsx` per route segment
- **Drizzle**: Use `prepared` statements for hot queries
- **Auth**: Use NextAuth v5 with credentials + session callbacks
- **SQLite**: Use WAL mode for better concurrent reads

### Anti-Patterns to Avoid
- ❌ `useEffect` for data fetching — use Server Components
- ❌ Raw SQL strings — always use Drizzle ORM
- ❌ `any` types — use `z.infer<typeof schema>` or explicit types
- ❌ `'use client'` on the root layout — keep it server by default
- ❌ Storing files in SQLite — use S3/R2 and store URLs
- ❌ Missing `await` on `db.execute()` — Promises won't warn

## Architecture Decisions

### Why Drizzle + SQLite (not Prisma + Postgres)?
- Zero-infrastructure: SQLite file fits in the repo for local dev
- Drizzle's schema-first approach means migrations are predictable
- Turso for production: drop-in replacement, same Drizzle API
- Cost: $0 for SQLite vs $15+/mo for managed Postgres

### Why pnpm (not npm/yarn)?
- Faster installs, disk-efficient, strict dependency isolation
- Required for Turborepo if the project grows to monorepo

## CLAUDE.md Maintenance

When updating this file:
1. Every rule MUST have a concrete reason
2. Delete any rule that is no longer actively enforced
3. Add new rules only after seeing >2 violations in PR review
