# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

| Layer        | Choice                         | Version |
|--------------|--------------------------------|---------|
| Framework    | Next.js App Router             | 15.x    |
| Language     | TypeScript (strict)            | 5.x     |
| Database     | SQLite via better-sqlite3      | 11.x    |
| ORM          | Drizzle ORM                    | 0.38+   |
| Auth         | next-auth v5 (Auth.js)         | 5.x     |
| Styling      | Tailwind CSS                   | 4.x     |
| Runtime      | Node.js                        | 20 LTS  |

Use `pnpm` — never npm or yarn.

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Protected route group
│   ├── api/                # API routes
│   │   └── v1/             # Versioned API
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Primitive components (Button, Input, Dialog)
│   └── features/           # Feature-scoped composites
├── lib/
│   ├── db/
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   ├── migrations/     # SQL migration files
│   │   ├── index.ts        # DB connection singleton
│   │   └── seed.ts         # Dev seed script
│   ├── auth.ts             # Auth config
│   └── utils.ts            # Shared utilities
├── server/
│   ├── queries/            # Typed DB query functions
│   └── actions.ts          # Server actions
└── types/                  # Shared TypeScript types
```

## Dev Commands

```bash
pnpm dev            # Start dev server (port 3000)
pnpm build          # Production build
pnpm lint           # ESLint
pnpm db:generate    # Generate Drizzle migration from schema changes
pnpm db:migrate     # Apply pending migrations
pnpm db:seed        # Seed dev data
pnpm db:studio      # Open Drizzle Studio (DB GUI)
```

## SQL / Migration Conventions

- **Always use Drizzle schema** (`src/lib/db/schema.ts`) as the source of truth. Never hand-write SQL for DDL.
- **Generate migrations** with `pnpm db:generate` after every schema change. Commit the generated SQL file.
- **Migrations are forward-only**. No down migrations. If you need to revert, write a new migration.
- **Column naming**: `snake_case` in DB, `camelCase` in TypeScript. Drizzle handles the mapping via `casing: "snake_case"`.
- **Never use `sqlite_master` or raw DDL in app code.** Go through Drizzle.
- **Foreign keys**: always include `onDelete: "cascade"` or `"set null"` explicitly. No silent defaults.
- **Timestamps**: use `integer('created_at', { mode: 'timestamp' }).default(sql`(unixepoch())`)`. Never use string dates.

## Component Patterns

- Server Components by default. Add `"use client"` only when you need interactivity (useState, useEffect, event handlers).
- Co-locate server actions in `src/server/actions.ts`. Never fetch in client components when a server action suffices.
- Use `src/components/ui/` for primitives. These are thin wrappers around Radix UI + Tailwind. Do not add business logic here.
- Feature components go in `src/components/features/<feature>/`. A feature folder may contain its own server actions.
- Props: define an explicit `type Props` above every component. Never use `React.FC`.
- Error boundaries: wrap every route segment in `error.tsx`. Never let an unhandled promise crash the page.

## What We Don't Do (and Why)

| Don't                                   | Why                                                      |
|-----------------------------------------|----------------------------------------------------------|
| No Prisma                               | Drizzle is lighter, generates simpler SQL, no Rust build step for SQLite |
| No `getServerSideProps` / Pages Router  | App Router is the standard. Mixing creates confusion     |
| No client-side DB access                | SQLite is server-only. Never import `db` in client files |
| No raw SQL in components                | Use server actions or query functions from `src/server/` |
| No `any` type                           | Use `unknown` + type guard, or a specific type           |
| No environment variables without zod validation | Parse `process.env` in `src/lib/env.ts` with zod at startup |
| No CSS modules alongside Tailwind       | One styling system. Pick Tailwind.                       |
| No `next/link` with `passHref`          | In App Router, `next/link` handles this automatically    |
| No seeding in production                | `db:seed` exits early if `NODE_ENV=production`          |

## Database Connection

Single connection singleton pattern for better-sqlite3:

```typescript
import Database from 'better-sqlite3'
import { drizzle } from 'drizzle-orm/better-sqlite3'

const sqlite = new Database('data/app.db')
sqlite.pragma('journal_mode = WAL')        // Always WAL mode
sqlite.pragma('foreign_keys = ON')         // Enforce FK constraints
export const db = drizzle(sqlite, { schema })
```

Never create multiple database instances. Import from `src/lib/db/index.ts`.

## Auth Rules

- All `(dashboard)` routes require session. Check with `auth()` in server components or `useSession()` in client.
- API routes under `app/api/` must validate the session cookie manually.
- Never store passwords — use OAuth providers or magic links only.
- Session strategy: JWT (no database sessions — SQLite is single-writer).
