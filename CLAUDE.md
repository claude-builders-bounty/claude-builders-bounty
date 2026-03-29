# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> This file tells Claude Code how this project works. Every rule exists for a reason.

## Stack & Versions

| Tool | Version | Why |
|------|---------|-----|
| Next.js | 15.x (App Router) | Server components by default, server actions for mutations |
| React | 19.x | Use hooks, no class components |
| SQLite | via `better-sqlite3` | Zero-config, single-file DB, synchronous reads = simple code |
| TypeScript | 5.x strict mode | Catch bugs at compile time, not runtime |
| Tailwind CSS | 4.x | Utility-first, no CSS modules, no styled-components |
| Node.js | 22.x LTS | Native fetch, stable ESM support |

## Project Structure

```
├── app/                      # Next.js App Router pages & layouts
│   ├── (auth)/               # Auth-required route group
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   └── layout.tsx        # Auth check wrapper
│   ├── (public)/             # Public pages
│   │   ├── page.tsx          # Landing page
│   │   └── pricing/
│   ├── api/                  # API routes (only when server actions won't work)
│   │   └── webhooks/
│   └── layout.tsx            # Root layout
├── components/               # Shared React components
│   ├── ui/                   # Primitive UI (Button, Input, Card)
│   └── features/             # Feature-specific (DashboardChart, PricingTable)
├── lib/                      # Core business logic
│   ├── db.ts                 # Database singleton + query helpers
│   ├── db/
│   │   ├── schema.sql        # Full schema (source of truth)
│   │   └── migrations/       # Ordered SQL migration files
│   │       ├── 001_init.sql
│   │       └── 002_add_teams.sql
│   ├── auth.ts               # Auth helpers (session, middleware)
│   └── utils.ts              # Shared utilities
├── actions/                  # Server Actions (all mutations go here)
│   ├── user.ts
│   └── billing.ts
├── types/                    # Shared TypeScript types
│   └── index.ts
├── public/                   # Static assets
├── data/                     # SQLite database file (gitignored)
│   └── app.db
├── CLAUDE.md                 # This file
├── .env.local                # Environment variables (gitignored)
└── package.json
```

### Rules:
- **One component per file.** Named export matching filename.
- **`app/` is for routing only.** No business logic in page files — they compose components.
- **`lib/` is framework-agnostic.** No React imports. Pure functions + DB queries.
- **`actions/` is for server actions.** Every data mutation uses `"use server"`.
- **Feature folders in `components/features/`.** Don't nest deeper than 2 levels.

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files | `kebab-case.ts` | `user-profile.tsx` |
| Components | `PascalCase` | `export function UserProfile()` |
| Database tables | `snake_case`, plural | `user_sessions` |
| Database columns | `snake_case` | `created_at` |
| Server actions | `camelCase`, verb-first | `createUser()`, `updateBilling()` |
| Environment vars | `SCREAMING_SNAKE` | `DATABASE_URL` |
| URL paths | `kebab-case` | `/user-settings` |
| Types/interfaces | `PascalCase`, no `I` prefix | `type User = {...}` |

## SQL / Migration Conventions

### Schema Rules
- **`schema.sql` is the source of truth.** It must always reflect the current state of the database.
- **Every table has:** `id INTEGER PRIMARY KEY AUTOINCREMENT`, `created_at TEXT DEFAULT (datetime('now'))`, `updated_at TEXT DEFAULT (datetime('now'))`.
- **Use `TEXT` for dates.** SQLite has no native datetime; store ISO 8601 strings.
- **Use `INTEGER` for booleans.** 0 = false, 1 = true.
- **Foreign keys always have `ON DELETE CASCADE` or `ON DELETE SET NULL`.** Decide per relationship.
- **Add indexes for any column used in WHERE or JOIN.** Name them `idx_tablename_columnname`.

### Migration Rules
- **Migrations are numbered SQL files:** `001_init.sql`, `002_add_teams.sql`.
- **Never edit a deployed migration.** Create a new one instead.
- **Each migration has UP only.** We don't support rollback — fix forward.
- **Run migrations on app startup** via `lib/db.ts` init function.

### Database Access Pattern
```typescript
// lib/db.ts — THE singleton. Import this everywhere.
import Database from "better-sqlite3";
import path from "node:path";

const db = new Database(path.join(process.cwd(), "data", "app.db"));
db.pragma("journal_mode = WAL");  // Always WAL mode for concurrent reads
db.pragma("foreign_keys = ON");   // Always enforce foreign keys

export default db;
```

### Query Rules
- **Use prepared statements.** Never concatenate SQL strings.
- **Return plain objects.** No ORM — `db.prepare().all()` and `.get()` are enough.
- **One query file per domain:** `lib/db/queries/users.ts`, `lib/db/queries/teams.ts`.
- **Name query functions descriptively:** `getUserById()`, `listTeamMembers()`, not `getUser()`.

## Component Patterns

### Server Components (Default)
```tsx
// app/(auth)/dashboard/page.tsx
import { DashboardStats } from "@/components/features/dashboard-stats";
import { getStats } from "@/lib/db/queries/stats";

export default async function DashboardPage() {
  const stats = await getStats();  // Direct DB call — no API needed
  return <DashboardStats data={stats} />;
}
```

### Client Components (Only When Needed)
```tsx
"use client";  // ONLY add this when you need: useState, useEffect, onClick, onChange
// If a component only displays data, it's a server component.
```

### Server Actions (All Mutations)
```typescript
// actions/user.ts
"use server";

import { revalidatePath } from "next/cache";
import db from "@/lib/db";

export async function updateUserName(formData: FormData) {
  const name = formData.get("name") as string;
  const userId = /* get from session */;
  
  db.prepare("UPDATE users SET name = ?, updated_at = datetime('now') WHERE id = ?")
    .run(name, userId);
  
  revalidatePath("/dashboard");
}
```

### Form Pattern
```tsx
// Always use server actions with forms. No useState for form state.
<form action={updateUserName}>
  <input name="name" defaultValue={user.name} />
  <button type="submit">Save</button>
</form>
```

## Dev Commands

```bash
npm run dev          # Start Next.js dev server (port 3000)
npm run build        # Production build
npm run start        # Start production server
npm run db:migrate   # Run pending migrations
npm run db:reset     # Drop + recreate database (dev only)
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
```

## What We Don't Do (And Why)

| Don't | Why |
|-------|-----|
| **Don't use an ORM (Prisma, Drizzle)** | SQLite is simple. Raw SQL with prepared statements is faster, debuggable, and has zero abstraction cost. |
| **Don't use `useState` for server data** | Server components fetch data directly. Client state is for UI-only state (modals, tabs). |
| **Don't create API routes for internal data** | Server actions replace `POST /api/...` for mutations. Server components replace `GET /api/...` for reads. |
| **Don't use CSS-in-JS or CSS modules** | Tailwind covers everything. One system, zero runtime cost. |
| **Don't use `useEffect` for data fetching** | This isn't a SPA. Data loads on the server. |
| **Don't use `any` type** | Use `unknown` and narrow, or define proper types. |
| **Don't nest components more than 2 levels** | `components/features/dashboard/chart.tsx` is fine. `components/features/dashboard/widgets/charts/bar/index.tsx` is not. |
| **Don't store secrets in code** | `.env.local` for dev, environment variables for production. |
| **Don't add dependencies without justification** | Every `npm install` adds attack surface and bundle size. Ask: can we do this with what we have? |

## Error Handling

- **Server actions:** Throw errors. Next.js `error.tsx` boundaries catch them.
- **Database queries:** Let SQLite errors propagate. Don't silently swallow.
- **Validation:** Validate inputs at the action level with Zod. Never trust client data.

## Testing

- **No tests unless asked.** Move fast. Add tests when a feature is stable and critical.
- **When testing:** Use Vitest. Test `lib/` functions, not components.

## Git Conventions

- **Commit messages:** `type: description` (e.g., `feat: add team invites`, `fix: billing race condition`)
- **Branch names:** `feature/team-invites`, `fix/billing-race`
- **PR = one feature.** Don't bundle unrelated changes.
