# CLAUDE.md — Next.js 15 + SQLite SaaS
 
## Stack & Versions
 
- **Framework:** Next.js 15.3+ (App Router only — no Pages Router)
- **Database:** SQLite via `better-sqlite3` 11.x
- **ORM:** Drizzle ORM 0.42.x (not Prisma — see "What we don't do")
- **Auth:** Lucia Auth 3.x (session-based, not JWT)
- **UI:** Tailwind CSS 4.x + shadcn/ui (Radix primitives)
- **Forms:** React Hook Form 7.x + Zod 3.x validation
- **Runtime:** Node.js 22 LTS (not Bun, not Deno)
- **Package manager:** pnpm 10.x (not npm, not yarn)
- **TypeScript:** 5.8+ with strict mode — `strict: true` in tsconfig
 
> **Why these choices?** `better-sqlite3` + Drizzle gives us zero-overhead synchronous SQL without a sidecar server. Lucia provides framework-agnostic auth without vendor lock-in. shadcn/ui means we own the components — no hidden dependencies.
 
---
 
## Folder Structure
 
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Dashboard route group (requires auth)
│   ├── api/                # Route handlers (API endpoints)
│   └── layout.tsx          # Root layout
├── components/             # Shared UI components
│   ├── ui/                 # shadcn/ui primitives (button, input, etc.)
│   └── forms/              # Form components (composed from ui/ + RHF)
├── db/                     # Database layer
│   ├── schema/             # Drizzle schema definitions
│   ├── migrations/         # Auto-generated SQL migrations
│   ├── queries/            # Reusable query functions
│   └── index.ts            # DB client singleton
├── lib/                    # Utility functions and shared logic
│   ├── auth.ts             # Lucia auth helpers
│   ├── validation.ts       # Zod schemas
│   └── utils.ts            # General utilities (cn, format, etc.)
├── hooks/                  # Shared React hooks
├── types/                  # Shared TypeScript types (not in schema/)
└── middleware.ts            # Next.js middleware (auth checks, redirects)
 
> **Why this structure?** Feature-grouping by domain (`(auth)`, `(dashboard)`) lets Next.js colocate layouts without nesting URLs. Separating `db/schema` from `db/queries` keeps Drizzle schema files clean — they're the source of truth and should never contain business logic.
 
---
 
## SQL / Migration Conventions
 
### Schema rules
- Every table gets `id TEXT PRIMARY KEY` (nanoid, not auto-increment — UUIDs prevent enumeration attacks and simplify sharding later).
- Every table gets `created_at TEXT NOT NULL DEFAULT (datetime('now'))` and `updated_at TEXT NOT NULL DEFAULT (datetime('now'))`.
- Every foreign key is indexed with `createIndex()`.
- Use `text()` for strings (SQLite has no varchar limit — don't add one).
- Use `integer({ mode: 'boolean' })` for booleans.
- Use `integer()` for currency (store in cents, divide by 100 on display).
 
### Migration rules
- **NEVER edit a committed migration file.** Create a new one.
- Run `pnpm db:generate` after schema changes, then `pnpm db:migrate`.
- Migration files are auto-named by Drizzle — don't rename them.
- Test migrations on a copy of production data before deploying.
- Every migration MUST have a corresponding rollback (Drizzle generates these automatically — never delete the `down` SQL).
 
### Query rules
- All queries go in `src/db/queries/`, organized by domain (`user.queries.ts`, `team.queries.ts`).
- Queries return plain objects, not ORM entities. Transform in the query function.
- Use `db.transaction()` for multi-step operations (e.g., create user + create team).
- No raw SQL strings outside of migration files. If Drizzle can't express it, add it to the schema first.
 
> **Why these rules?** SQLite doesn't enforce types or length — `text()` reminds us of intent. Auto-increment IDs expose user counts. Editing committed migrations breaks reproducibility for other devs.
 
---
 
## Component Patterns
 
### Server components by default
- Every component starts as a server component (`async` function, no `'use client'`).
- Add `'use client'` ONLY when you need: `useState`, `useEffect`, `onClick`, browser APIs, or context.
- Keep client components as leaf nodes — don't let client boundaries creep up the tree.
 
### Data fetching
- Fetch data in server components using `searchParams` or route params.
- Use Next.js `cache()` (not `unstable_cache`) for deduplication.
- Mutations go through Server Actions (files named `actions.ts` in the route directory).
- Server Actions validate input with Zod before touching the database.
 
### Forms
- Every form uses React Hook Form + Zod resolver.
- Schema is defined in `src/lib/validation.ts` and exported.
- Error messages come from Zod — displayed inline under each field.
- Forms are client components (minimal — just the form wrapper, fields are reusable).
 
### Styling
- Tailwind only — no CSS modules, no styled-components, no CSS-in-JS.
- Use `cn()` helper for conditional classes (from `src/lib/utils.ts`).
- Follow shadcn/ui conventions: `variant` prop for visual variations.
- No inline `style` props except for dynamic values that can't be expressed in Tailwind.
 
> **Why these patterns?** Server components reduce the JS bundle by 40-60% on average. Keeping client boundaries narrow prevents unnecessary re-renders. Tailwind + shadcn means zero CSS to maintain and zero design decisions to make per component.
 
---
 
## What We Don't Do (And Why)
 
| ❌ Don't | Why |
|----------|-----|
| **Use Prisma** | Prisma adds a binary engine (~30MB), slows cold starts, and doesn't leverage SQLite's synchronous speed. Drizzle is a thin type-safe layer over raw SQL. |
| **Use Pages Router** | App Router is the future — Pages Router is in maintenance mode. Mixing both doubles the mental model. |
| **Use `any` type** | `any` bypasses TypeScript completely. Use `unknown` + type guards, or define the type. No exceptions. |
| **Use environment variables for non-secrets** | `NEXT_PUBLIC_*` is visible to the client. Use `config.ts` files with typed exports for public config. |
| **Catch-all error boundaries** | Don't wrap the entire app in one error boundary. Each route segment handles its own errors. |
| **Store files in SQLite** | SQLite is not a file server. Use S3/R2 for uploads and store the URL. |
| **Use `useEffect` for data fetching** | Server components and Server Actions cover 99% of data needs. `useEffect` for data is a last resort. |
| **Nest `'use client'` inside `'use client'`** | If a parent is already a client component, children don't need the directive. Unnecessary directives break server rendering. |
| **Run migrations automatically on startup** | Migrations are manual and reviewed. Auto-running in production is how data loss happens. |
 
---
 
## Development Commands
 
```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm lint             # ESLint + type-check
pnpm test             # Vitest (unit + integration)
pnpm db:generate      # Generate migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Drizzle Studio (GUI for SQLite)
pnpm format           # Prettier (all files)
────────────────────────────────────────────────────────────────────────────────
Commit Conventions
Use conventional commits:
-  feat:  — New feature (minor version bump)
-  fix:  — Bug fix (patch version bump)
-  chore:  — Tooling, dependencies, config
-  refactor:  — Code change with no behavior change
-  docs:  — Documentation only
-  db:  — Database schema or migration changes
Always write commits in the present tense ("add login form" not "added login form").
────────────────────────────────────────────────────────────────────────────────
Testing Philosophy
- Unit tests — Pure functions, queries, utilities. Vitest, no DOM.
- Integration tests — Server Actions, API routes. Vitest +  fetch  mock.
- E2E tests — Critical paths only (auth, payment). Playwright.
- We don't test components in isolation — they're tested through integration tests.
- We don't aim for 100% coverage. We aim for 100% confidence in critical paths.
