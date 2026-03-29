# CLAUDE.md â Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Next.js 15** (App Router only â no Pages Router)
- **React 19** with Server Components by default
- **SQLite** via `better-sqlite3` (local dev) / Turso (production)
- **TypeScript 5.5+** â strict mode, no `any`
- **Tailwind CSS 4** â utility-first, no CSS modules
- **Drizzle ORM** â type-safe SQL, no raw queries outside migrations

## Folder Structure

```
âââ src/
â   âââ app/                    # Next.js App Router
â   â   âââ (auth)/             # Route group: login, signup, forgot-password
â   â   âââ (dashboard)/        # Route group: authenticated pages
â   â   â   âââ layout.tsx      # Dashboard layout with sidebar
â   â   â   âââ page.tsx        # Dashboard home
â   â   â   âââ settings/
â   â   âââ api/                # API routes (POST/PUT/DELETE only â reads use RSC)
â   â   âââ layout.tsx          # Root layout
â   â   âââ page.tsx            # Landing page
â   âââ components/
â   â   âââ ui/                 # Reusable primitives (Button, Input, Card)
â   â   âââ features/           # Feature-specific components (UserAvatar, PricingTable)
â   âââ db/
â   â   âââ schema.ts           # Drizzle schema (single source of truth)
â   â   âââ migrations/         # SQL migration files (sequential, never edited)
â   â   âââ seed.ts             # Dev seed data
â   â   âââ index.ts            # DB connection singleton
â   âââ lib/
â   â   âââ auth.ts             # Auth helpers (session, middleware)
â   â   âââ constants.ts        # App-wide constants
â   â   âââ utils.ts            # Pure utility functions
â   âââ actions/                # Server Actions (one file per domain)
â   â   âââ user.actions.ts
â   â   âââ billing.actions.ts
â   â   âââ project.actions.ts
â   âââ types/                  # Shared TypeScript types
â       âââ index.ts
âââ drizzle.config.ts
âââ next.config.ts
âââ package.json
```

**Rules:**
- One `page.tsx` per route. No logic in `page.tsx` â it composes components.
- Route groups `(name)` for layout sharing. Never nest more than 2 levels deep.
- `components/ui/` is generic. `components/features/` knows about the domain.
- `lib/` is pure functions only â no React, no DB, no side effects.
- `actions/` is the only place Server Actions live. Named `<domain>.actions.ts`.

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files | `kebab-case` | `user-avatar.tsx` |
| Components | `PascalCase` | `UserAvatar` |
| Functions | `camelCase` | `getUserById` |
| Server Actions | `camelCase`, verb-first | `createProject`, `deleteUser` |
| DB tables | `snake_case`, plural | `users`, `project_members` |
| DB columns | `snake_case` | `created_at`, `is_active` |
| API routes | `route.ts` only | `app/api/webhooks/stripe/route.ts` |
| Types | `PascalCase`, no `I` prefix | `User`, `ProjectMember` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_UPLOAD_SIZE` |
| Env vars | `UPPER_SNAKE_CASE` | `DATABASE_URL` |

## SQL & Migration Conventions

### Schema (Drizzle)
```typescript
// src/db/schema.ts â THE source of truth
export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()), // cuid2, never autoincrement
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});
```

**Rules:**
- **IDs are always `text` with cuid2.** Never `integer` autoincrement. Reason: safe for distributed systems, no enumeration attacks.
- **Timestamps are `integer` with `mode: "timestamp"`.** SQLite has no native datetime. Unix timestamps are unambiguous.
- **Every table has `created_at` and `updated_at`.** No exceptions.
- **Soft delete with `deleted_at` column.** Never hard delete user data.

### Migrations
```bash
# Generate migration from schema changes
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate
```

**Rules:**
- Migrations are **sequential and immutable**. Never edit a committed migration.
- One migration per logical change. Don't batch unrelated changes.
- **Always test migrations on a copy of production data** before deploying.
- Migration files are committed to git. The `migrations/` folder is the migration history.

## Dev Commands

```bash
npm run dev          # Start Next.js dev server (port 3000)
npm run db:generate  # Generate migration from schema changes
npm run db:migrate   # Apply pending migrations
npm run db:seed      # Seed dev database
npm run db:studio    # Open Drizzle Studio (DB browser)
npm run build        # Production build
npm run lint         # ESLint + type-check
npm run test         # Vitest
```

## Component Patterns

### Server Components (default)
```tsx
// src/app/(dashboard)/page.tsx
import { getProjects } from "@/actions/project.actions";

export default async function DashboardPage() {
  const projects = await getProjects(); // Direct DB access, no API call
  return <ProjectList projects={projects} />;
}
```
**Why:** Server Components fetch data without client-side waterfalls. No loading spinners for initial data.

### Client Components (opt-in)
```tsx
"use client"; // Only when you need interactivity

import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```
**Why:** Client Components add JS bundle size. Only use when you need browser APIs, state, or event handlers.

### Server Actions (mutations)
```typescript
// src/actions/project.actions.ts
"use server";

import { db } from "@/db";
import { projects } from "@/db/schema";
import { revalidatePath } from "next/cache";

export async function createProject(formData: FormData) {
  const name = formData.get("name") as string;
  await db.insert(projects).values({ name });
  revalidatePath("/dashboard");
}
```
**Why:** Server Actions colocate mutation logic server-side. No API route boilerplate for form submissions.

### Error Handling
```tsx
// src/app/(dashboard)/error.tsx
"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```
**Every route group gets an `error.tsx`.** Errors bubble up to the nearest error boundary.

## What We Don't Do (and Why)

| Anti-pattern | Why not | Do this instead |
|-------------|---------|-----------------|
| `getServerSideProps` / `getStaticProps` | Pages Router patterns. We use App Router. | Use Server Components + `fetch` or direct DB queries |
| Raw SQL strings | SQL injection risk, no type safety | Use Drizzle ORM query builder |
| `useEffect` for data fetching | Client-side waterfalls, loading spinners | Server Components fetch data at render time |
| API routes for reads | Unnecessary network hop | Server Components read directly from DB |
| `any` type | Defeats TypeScript's purpose | Use proper types, `unknown` if truly unknown |
| CSS modules / styled-components | Bundle bloat, naming conflicts | Tailwind utility classes |
| Prisma | No native SQLite support without adapter, heavier | Drizzle ORM (built for SQLite) |
| UUID v4 for IDs | 36 chars, not sortable, poor index performance | cuid2 (shorter, sortable, collision-resistant) |
| `moment` / `dayjs` | Unnecessary dependency | Native `Date` + `Intl.DateTimeFormat` |
| Barrel exports (`index.ts` re-exporting) | Kills tree-shaking, circular dep risk | Import directly from source file |
| Storing files in SQLite | BLOB performance degrades | Use S3/R2 + store URL in DB |
| JWT for sessions | Can't revoke, complexity | Server-side sessions with SQLite storage |

## Environment Variables

```env
# .env.local (never committed)
DATABASE_URL=file:./dev.db           # Local SQLite path
DATABASE_AUTH_TOKEN=                  # Turso auth token (production only)
NEXTAUTH_SECRET=                     # Random 32+ char string
NEXTAUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Rules:**
- `.env.local` is gitignored. Always.
- `.env.example` is committed with dummy values.
- Access env vars through `process.env` only in `lib/constants.ts`. Never scatter `process.env` calls.
