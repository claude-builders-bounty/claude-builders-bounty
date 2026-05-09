# CLAUDE.md — Next.js 15 + SQLite SaaS Stack

## Stack & Versions
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **Database:** SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM:** Drizzle ORM
- **Auth:** NextAuth.js v5 (Auth.js)
- **Styling:** Tailwind CSS v4 + shadcn/ui
- **Validation:** Zod
- **Payments:** Stripe
- **Email:** Resend

## Folder Structure
```
src/
├── app/            # Next.js App Router
│   ├── (auth)/     # Auth route group
│   ├── (dashboard)/# Authenticated route group
│   └── api/        # API routes
├── components/
│   ├── ui/         # shadcn/ui primitives
│   └── features/   # Domain components
├── lib/
│   ├── db/         # Database (schema, migrations, queries)
│   ├── auth/       # Auth config
│   └── utils/      # Pure helpers
├── server/
│   └── actions/    # Server Actions
└── types/          # Shared types
```

## Rules

### Database
- All schema changes via Drizzle migrations — never edit SQLite files directly
- `npx drizzle-kit generate` → review → `npx drizzle-kit push`
- Queries in `src/lib/db/queries/`, one file per domain
- Never use raw SQL unless Drizzle cannot express it; if must, wrap in migration

### Components
- Server Components by default — `"use client"` only for interactivity
- Client boundary at the leaf: `PostsList` server, `LikeButton` client
- Forms use Server Actions in `src/server/actions/`
- No `useEffect` for data fetching — use Server Components or React Query

### Types & Validation
- Zod schemas in `src/lib/validations/`
- DB types from Drizzle: `type User = typeof users.$inferSelect`
- Never use `any`
- API routes validate input with Zod

### Naming
- Files: kebab-case | Components: PascalCase | Functions: camelCase
- DB tables: plural snake_case | Branches: `feat/`, `fix/`, `chore/`

## Dev Commands
```bash
pnpm dev           # localhost:3000
pnpm build         # Production build
pnpm db:generate   # Drizzle migrations
pnpm db:push       # Apply migrations
pnpm db:studio     # Drizzle Studio
pnpm lint && pnpm format
pnpm test          # Vitest
```

## What We Don't Do
- ❌ Business logic in components → `lib/` or `server/actions/`
- ❌ Server code in client components
- ❌ Secrets in `.env` → `.env.local` (gitignored)
- ❌ Direct SQLite file manipulation
- ❌ Mix concerns in single file
- ❌ Skip Zod on user input

## What We Do
- ✅ Server-first data fetching
- ✅ Progressive enhancement
- ✅ Edge-compatible Web APIs
- ✅ Tailwind only, no CSS modules
- ✅ Co-locate tests in `__tests__/`
