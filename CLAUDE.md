# CLAUDE.md

## Stack & Versions

- **Runtime**: Node.js 22 LTS
- **Framework**: Next.js 15 (App Router, Turbopack in dev)
- **Language**: TypeScript 5.7+ (strict mode, verbatimModuleSyntax)
- **Database**: SQLite via better-sqlite3
- **ORM**: Drizzle ORM (drizzle-orm/sqlite-core)
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Validation**: zod (server + client shared schemas)
- **Package manager**: pnpm

## Folder Structure

src/
  app/              # App Router pages (route groups, layouts)
  components/
    ui/             # shadcn/ui primitives
    forms/          # Form components (react-hook-form)
    layouts/        # Shell layouts (sidebar, header)
  db/
    schema/         # Drizzle table definitions (*.sql.ts)
    migrations/     # Auto-generated migrations
    queries/        # Raw SQL query wrappers
    seed.ts         # Dev seed data
  lib/              # Pure utilities, no React imports
    utils.ts        # cn() helper, formatters
    constants.ts    # Env vars, feature flags
  server/           # Server-only logic
    actions/        # Server Actions (one per domain)
    api/            # Route handler helpers
  middleware.ts     # Next.js middleware (auth, i18n, redirects)

## SQL & Migration Conventions

- Schema files named by domain: users.sql.ts, teams.sql.ts
- All tables: id (TEXT PK uuidv7), createdAt (integer unix ms), updatedAt (integer unix ms)
- Foreign keys explicit in Drizzle: references(() => users.id)
- Every migration reviewed before prod deploy
- No raw SQL strings outside src/db/queries/
- Never delete a migration file — write a new one to roll back
- drizzle-kit push in dev, drizzle-kit migrate in prod

## Component Patterns

- Server-first: data fetching in Server Components, pass down as props
- Client boundaries: 'use client' only when hooks, events, or browser APIs are needed
- No useEffect for data fetching: use Server Components, Server Actions, or TanStack Query
- Forms: react-hook-form + zod resolver, server action in src/server/actions/
- Composition over props drilling: use children, slot patterns, layout groups
- shadcn/ui in src/components/ui/ — customize via tailwind config, never edit source
- Page files (app/**/page.tsx) are thin — import from components, logic in actions

## Dev Commands

pnpm dev              # Start dev server (Turbopack)
pnpm build            # Production build
pnpm lint             # ESLint + type checks
pnpm test             # Vitest (unit + integration)
pnpm db:push          # Push schema to local DB
pnpm db:generate      # Generate migration
pnpm db:migrate       # Apply migrations
pnpm db:seed          # Insert seed data
pnpm typecheck        # tsc --noEmit
pnpm format           # Prettier

## Anti-Patterns (Don't Do These)

- 'use client' on root layout — breaches server component boundary
- fetch() in client components — Server Components have direct db access
- Barrel exports (index.ts re-exports) — breaks tree-shaking, slows HMR
- any type — use unknown + narrowing or define a type
- One giant migration file — each schema change gets its own migration
- Inline SQL in page components — SQL lives in src/db/queries/ only
- NEXT_PUBLIC_* for secrets — ships to browser, use server-only env vars
- Omitting error boundaries — every route group needs error.tsx

## Testing

- Unit tests next to source: src/lib/utils.test.ts
- Integration tests in tests/ (Vitest + MSW)
- E2E with Playwright in e2e/ (CI only)
- Snapshot tests strongly discouraged (brittle, low signal)

## Performance

- Dynamic imports for heavy client components: dynamic(() => import(...), { ssr: false })
- React.cache() for repeated db calls in same render pass
- No premature caching — prove slowness first
- Images: always provide width, height, priority for above-fold
- Use next/image for all user-facing images (automatic WebP, lazy loading)
