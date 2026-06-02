# Next.js 15 + SQLite SaaS Project

## Stack
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via better-sqlite3 (local) / Turso (production)
- **ORM**: Drizzle ORM (not Prisma — Drizzle plays nicer with SQLite)
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **Styling**: Tailwind CSS 4 + shadcn/ui
- **Forms**: React Hook Form + Zod validation
- **Payments**: Stripe (webhook-first, not client-side SDK)

## Folder Structure
```
src/
├── app/                    # App Router pages
│   ├── (auth)/            # Auth pages (login, register)
│   ├── (dashboard)/       # Authenticated routes
│   ├── api/               # API routes (route handlers)
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── ui/               # shadcn/ui primitives
│   └── forms/            # Form components
├── db/                    # Database layer
│   ├── schema/           # Drizzle schema definitions
│   ├── migrations/       # Generated migrations
│   └── index.ts          # DB client instance
├── lib/                   # Utility functions
├── actions/              # Server actions
└── hooks/                # Custom React hooks
```

## DB & Migration Rules
- **Every schema change = a new migration file.** Never edit existing migrations.
- Migration naming: `YYYYMMDD_description.sql`
- Run migrations with: `npm run db:migrate`
- Seed data goes in `src/db/seed.ts`
- Use `drizzle-kit studio` for local inspection
- **No raw SQL in route handlers** — use Drizzle queries only
- Foreign keys: always name them explicitly (`fk_orders_user_id`)

## Component Patterns
- Server components by default. Client components only when you need:
  - `useState` / `useEffect`
  - Event handlers
  - Browser APIs
- Mark client boundary at the lowest possible level
- Page components = server. Interactive pieces = client children.
- Loading states: use `loading.tsx` and `Suspense` boundaries

## What We Don't Do
- ❌ **No `any` types** — ever. Use `unknown` + type narrowing.
- ❌ **No prop drilling** — use compound components or React Server Components
- ❌ **No `useEffect` for data fetching** — use Server Actions or RSC
- ❌ **No Redux / Zustand** — URL state + React Server Actions cover 95%
- ❌ **No raw SQL in API routes** — Drizzle abstracts the dialect

## Dev Commands
| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm run db:generate` | Generate migration from schema changes |
| `npm run db:migrate` | Apply pending migrations |
| `npm run db:seed` | Seed database |
| `npm run lint` | ESLint + Prettier check |
| `npm run typecheck` | `tsc --noEmit` |

## Anti-patterns to Avoid
1. **Catch-all API route for everything** — use Server Actions for form submissions
2. **Over-sharding components** — a file per component only when it has state or exports
3. **Direct DB calls from `layout.tsx`** — use RSC patterns or parallel data fetching
4. **SQLite for high-write tables** — it's great for reads, but writes are file-locked
