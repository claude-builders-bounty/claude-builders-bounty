# CLAUDE.md — Next.js 15 + SQLite SaaS

This is an opinionated CLAUDE.md for greenfield SaaS projects using Next.js 15 App Router with SQLite (better-sqlite3 for local, Turso for production).

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server Components, streaming, middleware |
| Language | TypeScript 5.x strict | Catch bugs at build time |
| Database | better-sqlite3 (local) / Turso (prod) | SQLite is fast, simple, edge-ready |
| ORM | Drizzle ORM | Type-safe, no codegen, SQL-first |
| Auth | better-auth | Self-hosted, SQLite-native, no vendor lock-in |
| Styling | Tailwind CSS 4 | Utility-first, no CSS-in-JS runtime cost |
| Validation | Zod | Runtime + static types from one schema |
| Testing | Vitest + Playwright | Fast unit tests, real browser E2E |
| Package Manager | pnpm | Fast, strict, disk-efficient |

## Folder Structure

```
src/
├── app/                    # Next.js App Router (routes only)
│   ├── (auth)/             # Auth group (login, register, forgot)
│   ├── (dashboard)/        # Authenticated group
│   │   ├── layout.tsx      # Dashboard shell (sidebar, nav)
│   │   └── page.tsx        # Dashboard home
│   ├── api/                # API routes
│   │   └── trpc/[trpc]/    # tRPC catch-all (if using tRPC)
│   ├── layout.tsx          # Root layout (fonts, providers)
│   └── page.tsx            # Landing / marketing page
├── components/
│   ├── ui/                 # Primitives (button, input, card)
│   ├── forms/              # Form components with validation
│   └── features/           # Feature-specific composites
├── db/
│   ├── schema.ts           # Drizzle schema (all tables)
│   ├── migrations/         # Generated SQL migrations
│   ├── index.ts            # DB client singleton
│   └── seed.ts             # Seed script
├── lib/
│   ├── auth.ts             # better-auth config
│   ├── utils.ts            # Generic helpers (cn, formatDate, etc.)
│   └── constants.ts        # App-wide constants
├── server/
│   ├── queries.ts          # Read-only DB queries (server components)
│   └── mutations.ts        # Write DB actions (server actions)
├── hooks/                  # Client-side React hooks
├── types/                  # Shared TypeScript types
└── env.ts                  # Typed env validation (t3-env or zod)
```

### Rules

- **Routes go in `app/`**, logic stays out. No business logic in route handlers.
- **`components/ui/`** has zero business knowledge. Reusable across any project.
- **`server/queries.ts`** for reads, **`server/mutations.ts`** for writes. Don't mix.
- **One schema file** (`db/schema.ts`). Split only when it exceeds 500 lines.
- **No `lib/` dumping ground.** If it touches the DB, it goes in `server/`. If it's a React hook, it goes in `hooks/`.

## Database & Migrations

### Schema Conventions

```typescript
// db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),          // nanoid or cuid2
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull(),
});
```

Rules:
- **IDs**: Use `nanoid()` or `cuid2()`. Never auto-increment integers as primary keys (leaks row count, breaks distributed).
- **Timestamps**: Always `integer` with `{ mode: "timestamp" }`. Store UTC.
- **Booleans**: `integer("flag", { mode: "boolean" }).default(false)`.
- **No `@@map`** unless the table name genuinely conflicts with a SQL keyword.
- **Foreign keys**: Use `.references(() => table.id)` with explicit `onDelete: "cascade"` where appropriate.

### Migrations

```bash
pnpm drizzle-kit generate    # Create migration from schema diff
pnpm drizzle-kit migrate     # Apply pending migrations
pnpm drizzle-kit push        # Push schema directly (dev only, no migration file)
```

- **Never use `push` in production.** Always generate and commit migration files.
- **Review generated SQL** before committing. Drizzle sometimes drops and recreates indexes.
- **One migration per feature.** Don't bundle unrelated schema changes.

### Seed Data

```bash
pnpm db:seed
```

Seed script lives at `db/seed.ts`. It must be **idempotent** (safe to run twice) — use `onConflictDoNothing()` or check existence before insert.

## Component Patterns

### Server Components (default)

```tsx
// app/(dashboard)/page.tsx
import { getUser } from "@/server/queries";

export default async function DashboardPage() {
  const user = await getUser();  // Direct DB call, no API layer
  return <DashboardShell user={user} />;
}
```

- Server Components call `server/queries.ts` directly. No fetch, no API routes.
- Pass data down as props. Don't create client components just to fetch.

### Client Components

```tsx
"use client";

import { useState } from "react";
import { createUser } from "@/server/mutations";

export function CreateUserForm() {
  const [pending, setPending] = useState(false);

  async function handleSubmit(formData: FormData) {
    setPending(true);
    try {
      await createUser(formData);
    } finally {
      setPending(false);
    }
  }

  return (
    <form action={handleSubmit}>
      {/* ... */}
      <button disabled={pending}>{pending ? "Creating..." : "Create"}</button>
    </form>
  );
}
```

- Add `"use client"` only when the component needs interactivity (state, effects, event handlers).
- Server Actions go in `server/mutations.ts`, not inline in components.
- Use `useTransition` or manual pending state for loading indicators. Don't use external state managers for form state.

### UI Components

- **Shadcn/ui pattern**: Copy components into `components/ui/`, own them, modify freely.
- **No prop drilling more than 2 levels.** Use composition or context.
- **No `children` prop on leaf components.** If it takes children, it's a layout.

## Auth

Using better-auth (self-hosted, SQLite-native):

```typescript
// lib/auth.ts
import { betterAuth } from "better-auth";

export const auth = betterAuth({
  database: db,
  emailAndPassword: { enabled: true },
  // Add OAuth providers as needed
});
```

- **Middleware** (`middleware.ts`) protects routes by checking session cookie.
- **Server Components** get user via `auth.api.getSession()` — never pass user ID from client.
- **Server Actions** validate auth at the top. Throw or redirect if no session.

```typescript
// server/mutations.ts
"use server";

export async function createProject(formData: FormData) {
  const session = await auth.api.getSession();
  if (!session) throw new Error("Unauthorized");
  // ... proceed
}
```

## Environment Variables

```typescript
// env.ts
import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    DATABASE_URL: z.string().url(),
    BETTER_AUTH_SECRET: z.string().min(32),
  },
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
  },
  runtimeEnv: {
    DATABASE_URL: process.env.DATABASE_URL,
    BETTER_AUTH_SECRET: process.env.BETTER_AUTH_SECRET,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
});
```

- **All env vars validated at build time.** Fail fast, not at runtime in production.
- **Never access `process.env` directly.** Always go through `env.ts`.
- **`.env.local`** for secrets, **`.env`** for non-secret defaults. Both gitignored.

## What We Don't Do (and Why)

| Anti-pattern | Why not |
|-------------|---------|
| Prisma | Codegen step, heavier runtime, worse SQLite support |
| tRPC | Adds complexity for what Server Actions already solve |
| Redux / Zustand | Server Components eliminate most client state needs |
| `any` type | Defeats TypeScript. Use `unknown` and narrow. |
| Barrel exports (`index.ts`) | Tree-shaking is fine; barrels add import confusion |
| CSS modules | Tailwind is faster to write and review |
| `useEffect` for data fetching | Use Server Components or React Query for client-side |
| Auto-increment IDs | Leaks count, breaks distributed, not URL-safe |
| `console.log` in production | Use a logger (pino) or remove before commit |
| Catching errors silently | Always log or re-throw. `catch {}` hides bugs. |

## Dev Commands

```bash
pnpm dev              # Start dev server (turbopack)
pnpm build            # Production build
pnpm start            # Serve production build
pnpm lint             # ESLint + TypeScript check
pnpm test             # Vitest (unit + integration)
pnpm test:e2e         # Playwright (browser tests)
pnpm db:generate      # Generate migration
pnpm db:migrate       # Apply migrations
pnpm db:seed          # Seed database
pnpm db:studio        # Open Drizzle Studio (GUI)
```

## Git Conventions

- **Branch**: `feat/thing`, `fix/thing`, `chore/thing`
- **Commit**: Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR**: Squash merge. Title = conventional commit message.
- **No force push to main.** Ever.
- **CI must pass** before merge: lint, typecheck, test, build.

## Performance Rules

- **Images**: Always use `next/image` with explicit `width`/`height` or `fill`.
- **Fonts**: Use `next/font` (self-hosted, zero layout shift).
- **Dynamic imports**: Use `next/dynamic` for heavy client components (charts, editors).
- **Database**: Add indexes for any column used in WHERE or ORDER BY. Check with `EXPLAIN QUERY PLAN`.
- **Bundle**: Run `pnpm build` and check the bundle analyzer output. No package over 100KB gzipped unless justified.

## Testing

### Unit (Vitest)

```typescript
// db/schema.test.ts
import { describe, it, expect } from "vitest";
import { users } from "./schema";

describe("users schema", () => {
  it("requires email", () => {
    // Test Drizzle schema validation
  });
});
```

### E2E (Playwright)

```typescript
// e2e/auth.spec.ts
import { test, expect } from "@playwright/test";

test("user can register and login", async ({ page }) => {
  await page.goto("/register");
  await page.fill('input[name="email"]', "test@example.com");
  await page.fill('input[name="password"]', "securepassword123");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL("/dashboard");
});
```

- **Unit tests** for: DB queries, utility functions, validation schemas.
- **E2E tests** for: auth flow, core CRUD, payment flow.
- **No snapshot tests.** They break on every UI change and provide false confidence.
- **Test the behavior, not the implementation.** Don't test that a function calls another function.

## Deployment

Recommended: **Vercel** (native Next.js) + **Turso** (edge SQLite).

- Turso for production DB: `turso db create app-db --location iad`
- Set env vars in Vercel dashboard
- `pnpm build` runs migrations automatically via `postbuild` script

Alternative: **Docker** + **Fly.io** for full control.

```dockerfile
FROM node:20-slim AS base
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
EXPOSE 3000
CMD ["pnpm", "start"]
```
