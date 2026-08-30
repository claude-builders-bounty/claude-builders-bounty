# CLAUDE.md — Next.js 15 + SQLite SaaS

This file provides context for Claude Code when working on this Next.js 15 App Router + SQLite SaaS project.

## Stack & Versions

- **Runtime:** Node.js 22+ (LTS)
- **Framework:** Next.js 15.x (App Router, React Server Components by default)
- **Language:** TypeScript 5.x (strict mode enabled)
- **Database:** SQLite via `better-sqlite3` (synchronous, server-side only) or Turso (libsql, async edge-compatible)
- **ORM/Query:** Drizzle ORM 0.30+ with `drizzle-kit` for migrations
- **Styling:** Tailwind CSS 4.x with CSS variables for theming
- **Validation:** Zod 3.x for all external input and API boundaries
- **Auth:** Lucia Auth or NextAuth.js v5 (server sessions, no JWT unless required)
- **Package Manager:** pnpm 9.x (preferred) or npm 10.x

## Folder Structure

```
src/
├── app/                    # App Router routes (layout.tsx, page.tsx, route.ts)
│   ├── (auth)/             # Route group: auth pages (no layout nesting)
│   ├── (dashboard)/        # Route group: protected app pages
│   ├── api/                # API routes (route handlers only, no UI)
│   └── layout.tsx          # Root layout (html/body, fonts, global providers)
├── components/             # Reusable UI components
│   ├── ui/                 # Primitive atoms (Button, Input, Card)
│   └── features/           # Feature-scoped composite components
├── db/                     # Database layer
│   ├── schema.ts           # Drizzle table definitions (single source of truth)
│   ├── connection.ts       # DB client singleton (env-aware: local vs turso)
│   └── migrations/         # Generated SQL migration files
├── lib/                    # Shared utilities (pure functions, no React)
│   ├── auth.ts             # Session helpers, permission checks
│   ├── validators.ts       # Shared Zod schemas
│   └── utils.ts            # cn(), formatDate(), etc.
├── hooks/                  # Client-side React hooks only
└── types/                  # Shared TypeScript interfaces/types
```

## Naming Conventions

- **Files:** kebab-case (`user-profile.tsx`, `create-org.ts`)
- **Components:** PascalCase exports (`UserProfile`, `CreateOrgForm`)
- **Routes:** lowercase kebab-case segments (`/org-settings`, `/api/users/[id]`)
- **DB columns:** snake_case (`created_at`, `org_id`)
- **TypeScript types:** PascalCase for interfaces/types, camelCase for values
- **Env vars:** UPPER_SNAKE_CASE, prefixed `NEXT_PUBLIC_` only if client-exposed
- **Zod schemas:** camelCase with `Schema` suffix (`createUserSchema`)

## Database & Migration Rules

1. **Never edit migration files manually.** Use `pnpm drizzle-kit generate` then `pnpm drizzle-kit migrate`.
2. **All schema changes go through `src/db/schema.ts`.** This is the single source of truth.
3. **Every table must have:** `id` (text, nanoid), `created_at`, `updated_at` timestamps.
4. **Foreign keys are mandatory** for relational integrity. Use `references()` in Drizzle.
5. **No raw SQL in application code.** Use Drizzle query builder exclusively.
6. **Database calls are server-only.** Never import `db/` in client components or `"use client"` files.
7. **Wrap writes in transactions** when modifying multiple tables.
8. **Seed scripts live in `src/db/seed.ts`**, run via `pnpm db:seed`. Never seed in production.
9. **Connection string comes from env:** `DATABASE_URL` (local file path or Turso URL). No hardcoded paths.

## Component Patterns

- **Server Components by default.** Add `"use client"` only when interactivity requires it.
- **Data fetching happens in Server Components** or Server Actions. Never fetch in client components unless using SWR/TanStack Query for real-time data.
- **Forms use Server Actions** with Zod validation on both client (optimistic) and server (authoritative).
- **Props interfaces are co-located** with the component, exported as `ComponentNameProps`.
- **Avoid prop drilling > 2 levels.** Use composition or context for deeper trees.
- **UI primitives (`components/ui/`)** accept `className` and spread `...props` for extensibility.
- **Icons:** Use Lucide React or similar tree-shakeable library. No SVG imports as files.

## Dev Commands

```bash
pnpm dev              # Start dev server (Turbopack)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint check
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest run
pnpm db:generate      # Generate new migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:push          # Push schema directly (dev only, never prod)
pnpm db:seed          # Run seed script
pnpm db:studio        # Open Drizzle Studio (visual DB browser)
```

## Anti-Patterns (Do NOT Do)

- ❌ **Don't use `getServerSideProps`/`getStaticProps`.** These are Pages Router APIs; use App Router patterns.
- ❌ **Don't put business logic in route handlers.** Extract to `lib/` or feature modules; routes should be thin adapters.
- ❌ **Don't use `any` type.** If the type is complex, define an interface. `unknown` + type guard is acceptable.
- ❌ **Don't fetch data in `useEffect`.** Use Server Components, Server Actions, or a proper data-fetching library.
- ❌ **Don't store secrets in `NEXT_PUBLIC_*` vars.** These are embedded in the client bundle.
- ❌ **Don't skip Zod validation on server.** Client validation is UX; server validation is security.
- ❌ **Don't use ORM relations without indexes.** Always add `.index()` on foreign key columns.
- ❌ **Don't commit `.env` files.** Use `.env.example` with placeholder values.
- ❌ **Don't use `dangerouslySetInnerHTML`** without DOMPurify sanitization.
- ❌ **Don't create barrel exports (`index.ts`) for large directories.** They kill tree-shaking and slow builds.

## Testing Expectations

- **Unit tests:** Vitest for pure functions in `lib/` and Zod schemas.
- **Component tests:** React Testing Library for interactive client components only.
- **API tests:** Test route handlers with mocked DB (not real SQLite in CI).
- **E2E:** Playwright for critical user flows (auth, billing, core CRUD).
- **Coverage target:** 80%+ for `lib/` and `db/`, 60%+ overall.

## Environment Variables Required

```env
DATABASE_URL=file:./local.db          # Local dev
# DATABASE_URL=libsql://...           # Turso production
AUTH_SECRET=                          # openssl rand -base64 32
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

Always validate env vars at startup with Zod in `src/lib/env.ts`. Fail fast with clear error messages if missing.
