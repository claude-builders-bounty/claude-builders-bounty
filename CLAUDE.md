# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework:** Next.js 15 (App Router, React 19)
- **Database:** SQLite via `better-sqlite3` (local) / Turso (production)
- **Auth:** `better-auth` with session-based auth
- **Styling:** Tailwind CSS 4 + `shadcn/ui` components
- **Language:** TypeScript 5.x (strict mode)
- **Package Manager:** pnpm
- **Node:** 22 LTS

## Dev Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm lint             # ESLint + TypeScript check
pnpm test             # Vitest (unit + integration)
pnpm test:e2e         # Playwright E2E tests
pnpm db:migrate       # Run pending migrations
pnpm db:seed          # Seed dev database
pnpm db:studio        # Open Drizzle Studio (DB inspector)
```

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth group (login, register, forgot-password)
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx      # Auth layout (centered card)
│   ├── (dashboard)/        # Protected dashboard group
│   │   ├── layout.tsx      # Dashboard layout (sidebar + topbar)
│   │   ├── page.tsx        # Dashboard home
│   │   ├── settings/       # User settings
│   │   └── [team]/         # Team-scoped routes
│   ├── api/                # API routes
│   │   ├── auth/           # Auth endpoints
│   │   └── trpc/           # tRPC handler (single endpoint)
│   ├── layout.tsx          # Root layout (fonts, providers)
│   └── globals.css         # Tailwind imports + CSS variables
├── components/
│   ├── ui/                 # shadcn/ui primitives (Button, Input, etc.)
│   ├── forms/              # Form components (validated with zod)
│   └── layouts/            # Layout components (Sidebar, Topbar)
├── server/
│   ├── db/
│   │   ├── schema.ts       # Drizzle schema (ALL tables defined here)
│   │   ├── migrate.ts      # Migration runner
│   │   └── index.ts        # Database client singleton
│   ├── auth.ts             # better-auth server config
│   └── trpc/
│       ├── router.ts       # Root router
│       ├── context.ts      # tRPC context (db, session)
│       └── routers/        # Sub-routers (user.ts, team.ts, billing.ts)
├── lib/
│   ├── utils.ts            # cn(), formatDate(), etc.
│   ├── errors.ts           # Typed error classes
│   └── constants.ts        # App-wide constants
├── hooks/                  # Custom React hooks
└── types/                  # Shared TypeScript types
```

## Folder Conventions

- **Route groups** `(auth)` and `(dashboard)` — parentheses = no URL segment
- **`[team]`** — dynamic segment for multi-tenant team scoping
- **One file per route** — `page.tsx` for pages, `layout.tsx` for layouts
- **`loading.tsx`** — automatic Suspense boundaries
- **`error.tsx`** — automatic error boundaries per segment
- **No `src/components/ui/` edits** — only add via `npx shadcn@latest add`

## Database / Migration Rules

### Schema Definition

```typescript
// src/server/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),          // nanoid(21)
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull(),
});
```

### Rules

1. **IDs are `text` with `nanoid(21)`** — never auto-increment integers
2. **Timestamps are `integer` with `mode: "timestamp"`** — store as Unix epoch
3. **Always define both `createdAt` and `updatedAt`** on every table
4. **Foreign keys reference `text("id")`** — not integer IDs
5. **One schema file** — `src/server/db/schema.ts` contains ALL tables
6. **Migration naming:** `YYYY_MM_DD_description` (e.g., `2025_01_15_add_teams`)
7. **Never modify existing migrations** — always create a new one
8. **Run `pnpm db:migrate` after schema changes** — never edit the SQLite file directly

### Migration Workflow

```bash
# 1. Edit src/server/db/schema.ts
# 2. Generate migration
npx drizzle-kit generate
# 3. Review generated SQL in drizzle/ folder
# 4. Apply migration
pnpm db:migrate
# 5. Verify with Drizzle Studio
pnpm db:studio
```

## Component Patterns

### Server Components (default)

```tsx
// src/app/(dashboard)/page.tsx
import { db } from "@/server/db";
import { teams } from "@/server/db/schema";

export default async function DashboardPage() {
  const userTeams = await db.select().from(teams);
  return <TeamList teams={userTeams} />;
}
```

### Client Components (when needed)

```tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export function TeamList({ teams }: { teams: Team[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  // ... interactive logic
}
```

### Forms with Zod Validation

```tsx
// Always use zod schemas for form validation
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

const createTeamSchema = z.object({
  name: z.string().min(2).max(50),
  slug: z.string().regex(/^[a-z0-9-]+$/),
});

type CreateTeamInput = z.infer<typeof createTeamSchema>;
```

### tRPC Routers

```typescript
// src/server/trpc/routers/team.ts
import { z } from "zod";
import { router, protectedProcedure } from "../trpc";

export const teamRouter = router({
  create: protectedProcedure
    .input(z.object({ name: z.string().min(2), slug: z.string() }))
    .mutation(async ({ ctx, input }) => {
      // ctx.session.user is guaranteed (protectedProcedure)
      return ctx.db.insert(teams).values({
        id: nanoid(),
        ...input,
        userId: ctx.session.user.id,
        createdAt: new Date(),
        updatedAt: new Date(),
      }).returning();
    }),

  list: protectedProcedure.query(async ({ ctx }) => {
    return ctx.db.select().from(teams)
      .where(eq(teams.userId, ctx.session.user.id));
  }),
});
```

## Anti-Patterns (and Why)

| ❌ Don't | ✅ Do | Why |
|----------|-------|-----|
| `use client` at page level | Keep pages as Server Components | Performance — smaller JS bundle |
| Direct SQL strings | Use Drizzle query builder | Type safety + SQL injection prevention |
| `any` type | `unknown` + type guards | Catches bugs at compile time |
| `console.log` for errors | Use typed error classes | Structured error handling |
| Inline styles | Tailwind classes | Consistency + design system |
| `useState` for server data | Server Components + tRPC | Avoid hydration mismatches |
| Edit `ui/` components | Wrap in custom components | Preserves shadcn/ui upgradability |
| `Date.now()` for IDs | `nanoid()` | Collision-resistant, sortable |
| Mutate schema in place | New migration file | Preserves migration history |
| `try/catch` in every route | tRPC error middleware | Centralized error handling |

## Auth Rules

- **Session-based** — no JWTs, no cookies with secrets
- **Protected routes** — use `protectedProcedure` in tRPC, check `ctx.session` in Server Components
- **Auth pages** — in `(auth)` route group, redirect to dashboard if already logged in
- **API routes** — always validate session, never trust client-side auth state

## Environment Variables

```env
# .env.local (never commit)
DATABASE_URL=file:local.db          # Local SQLite
TURSO_DATABASE_URL=                 # Production Turso
TURSO_AUTH_TOKEN=                   # Production Turso
BETTER_AUTH_SECRET=                 # Random 32-byte hex
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## What We Don't Do

- **No ORM raw SQL** — use Drizzle's query builder (type safety)
- **No client-side data fetching for initial load** — Server Components fetch data
- **No global state libraries** — tRPC cache + React context is enough
- **No CSS modules** — Tailwind only
- **No class components** — function components + hooks
- **No default exports for components** — named exports only (except pages/layouts)
- **No barrel files (`index.ts`)** — import directly from the file
- **No `useEffect` for data fetching** — use Server Components or tRPC's `useQuery`
