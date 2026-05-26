# CLAUDE.md — Next.js 15 SaaS Starter

> Stack: Next.js 15 App Router, TypeScript, SQLite (better-sqlite3 via Drizzle ORM), Tailwind CSS, NextAuth.js
> This file gives Claude Code full context to work on this codebase without asking clarifying questions.

## Stack & Versions
- **Framework:** Next.js 15.2+ (App Router only — no `pages/`)
- **Language:** TypeScript 5.5+ strict mode
- **Database:** SQLite via `better-sqlite3` + `drizzle-orm`
- **Styling:** Tailwind CSS v4 (`@tailwindcss/vite` plugin)
- **Auth:** NextAuth.js v5 (Auth.js) with `@auth/drizzle-adapter`
- **Validation:** Zod for API routes + form schemas
- **Package manager:** pnpm (lockfile: `pnpm-lock.yaml`)

## Project Structure
```
src/
├── app/                    # App Router — routes live here
│   ├── (auth)/             # Auth group (login, register, verify)
│   ├── (dashboard)/        # Authenticated dashboard group
│   ├── api/                # Route handlers (no Express — use Next.js Route Handlers)
│   └── layout.tsx          # Root layout
├── components/
│   ├── ui/                 # shadcn/ui primitives (Button, Input, Dialog...)
│   └── features/           # Domain components (BillingForm, TeamSwitcher...)
├── db/
│   ├── schema.ts           # Drizzle schema definitions
│   ├── migrations/         # Auto-generated SQL migrations
│   └── index.ts            # DB connection + client export
├── lib/
│   ├── auth.ts             # NextAuth config
│   ├── email.ts            # Resend or similar
│   └── utils.ts            # cn(), formatCurrency(), etc.
├── actions/                # Server Actions (use 'use server' directive)
└── types/                  # Shared TypeScript types
```

## SQL / Migration Conventions
- **MUST** use Drizzle for all schema changes — never touch raw SQL files by hand
- Run `pnpm db:generate` to create migrations, then `pnpm db:migrate` to apply
- All tables get: `id` (TEXT UUID primary), `createdAt`, `updatedAt` (timestamps)
- **NEVER** drop a column in a migration — use ALTER TABLE ADD COLUMN, deprecate old columns
- Foreign keys enforced at app level (Drizzle relations), not database level (SQLite limitation)
- Migration names: `YYYYMMDDHHMMSS_descriptive_name`

## Dev Commands
```bash
pnpm dev            # Start dev server (Turbopack)
pnpm build          # Production build (checks types + lint first)
pnpm db:generate    # Generate Drizzle migration
pnpm db:migrate     # Apply pending migrations
pnpm db:studio      # Open Drizzle Studio (localhost:4983)
pnpm lint           # ESLint + Prettier
pnpm test           # Vitest (unit + integration)
pnpm typecheck      # tsc --noEmit
```

## Component Patterns
- **Server Components by default** — only add `'use client'` when you need: state, effects, event handlers, browser APIs
- **Data fetching:** fetch in Server Components, pass down as props. Use `React.cache()` to dedupe
- **Forms:** Use Server Actions with `useActionState()` + Zod validation in the action
- **Auth checks:** `import { auth } from '@/lib/auth'` then `const session = await auth()` in server context
- **Loading states:** Use `loading.tsx` (file convention) + `<Suspense>` for granular loading
- **Error boundaries:** `error.tsx` per route segment

## Anti-Patterns — What We DON'T Do
- ❌ No `pages/` directory — everything is App Router
- ❌ No `useEffect` for data fetching — fetch in Server Components
- ❌ No raw SQL strings — use Drizzle query builder
- ❌ No prop drilling beyond 2 levels — extract to context or colocate
- ❌ No `any` type — every function has explicit types
- ❌ No `as` type assertions in production code — fix the types
- ❌ No direct `fetch()` in client components — use Server Components or SWR
- ❌ No `process.env` in client components — prefix with `NEXT_PUBLIC_`

## API Route Pattern
```typescript
// src/app/api/teams/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { db } from '@/db'
import { teams } from '@/db/schema'
import { z } from 'zod'

const createTeamSchema = z.object({
  name: z.string().min(2).max(50),
})

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  try {
    const body = createTeamSchema.parse(await req.json())
    const [team] = await db.insert(teams).values({
      name: body.name,
      ownerId: session.user.id,
    }).returning()
    return NextResponse.json(team, { status: 201 })
  } catch (e) {
    if (e instanceof z.ZodError) {
      return NextResponse.json({ error: e.errors }, { status: 400 })
    }
    throw e // Let error boundary handle unexpected errors
  }
}
```

## Environment Variables
```
DATABASE_URL=file:./data.db
AUTH_SECRET=openssl rand -base64 32
AUTH_GOOGLE_ID=
AUTH_GOOGLE_SECRET=
RESEND_API_KEY=
```
Only `NEXT_PUBLIC_*` vars are available on the client.
