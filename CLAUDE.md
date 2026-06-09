# CLAUDE.md — Next.js 15 + Turso SaaS

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js App Router | 15.x | Server Components, streaming, parallel routes |
| Language | TypeScript | 5.x strict | No `any`, no `@ts-ignore`, no `as` casts |
| Database | Turso (libSQL) | latest | Edge-native SQLite, embedded replicas, zero cold start |
| ORM | Drizzle ORM | 0.36+ | SQL-first, type-safe, no magic, tiny bundle |
| Auth | better-auth | latest | Session-based, works with Turso, no JWT |
| Styling | Tailwind CSS | 4.x | Utility-first, no CSS modules, no styled-components |
| Validation | Zod | 3.x | Runtime + static types from same schema |
| Testing | Vitest | latest | Fast, ESM-native, compatible with Next.js |
| Package Manager | pnpm | 9.x | Fast, strict, monorepo-ready |

## Folder Structure

```
src/
├── app/                    # Next.js App Router (pages only)
│   ├── (auth)/             # Route group: login, register, forgot-password
│   ├── (dashboard)/        # Route group: authenticated app pages
│   │   ├── layout.tsx      # Dashboard shell (sidebar, topbar)
│   │   └── page.tsx        # Dashboard home
│   ├── api/                # API routes
│   │   ├── auth/           # better-auth handlers
│   │   └── trpc/           # tRPC handler (optional)
│   ├── layout.tsx          # Root layout (html, body, providers)
│   ├── page.tsx            # Landing / marketing page
│   └── globals.css         # Tailwind directives only
├── components/
│   ├── ui/                 # Primitive components (button, input, card)
│   ├── forms/              # Form components with Zod validation
│   └── features/           # Feature-specific components
├── db/
│   ├── schema.ts           # All Drizzle table definitions
│   ├── migrate.ts          # Migration runner (for CI/scripts)
│   ├── index.ts            # Turso client + Drizzle instance
│   └── seed.ts             # Development seed data
├── lib/
│   ├── auth.ts             # better-auth configuration
│   ├── email.ts            # Email sending (Resend/Postmark)
│   ├── payments.ts         # Stripe/LemonSqueezy helpers
│   └── utils.ts            # Generic utilities
├── hooks/                  # React hooks (prefixed with use)
├── types/                  # Shared TypeScript types
└── config.ts               # App-level constants (env validation)
```

### Rules

- **One export per file** in `components/`. File name = export name.
- **Route groups** `(auth)` and `(dashboard)` exist for layout nesting, not URL segments.
- **No `components/` inside `app/`**. All components live in `src/components/`.
- **No barrel files** (`index.ts` that re-exports everything). Import directly.
- **`lib/` is for server-only code**. Client-safe code goes in `hooks/` or `components/`.

## Database & Migrations

### Schema Definition

All tables in `src/db/schema.ts`. One file, no splitting.

```typescript
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { createId } from "@paralleldrive/cuid2";

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});
```

### Naming Conventions

- Tables: **plural, snake_case** (`users`, `subscription_items`)
- Columns: **snake_case** (`created_at`, `stripe_customer_id`)
- IDs: **CUID2** via `@paralleldrive/cuid2` (sortable, no auto-increment)
- Timestamps: **integer epoch ms**, mode `"timestamp"`, always `created_at` + `updated_at`
- Foreign keys: `{table}_id` referencing `{table}.id`

### Migrations

```bash
# Generate migration from schema changes
pnpm drizzle-kit generate

# Apply migrations (dev)
pnpm drizzle-kit migrate

# Push schema directly (dev only, skips migration files)
pnpm drizzle-kit push
```

**Rules:**
- **Never edit generated migration files**. Fix the schema, regenerate.
- **Never use `push` in production**. Always use `migrate`.
- **Every migration must be backward-compatible**. No dropping columns without a migration plan.
- **Seed data** goes in `src/db/seed.ts`, run manually in dev only.

### Turso Connection

```typescript
// src/db/index.ts
import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import * as schema from "./schema";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN,
});

export const db = drizzle(client, { schema });
```

## Component Patterns

### Server Components (default)

```typescript
// src/app/(dashboard)/page.tsx
import { db } from "@/db";
import { users } from "@/db/schema";

export default async function DashboardPage() {
  const allUsers = await db.select().from(users);
  return <UserList users={allUsers} />;
}
```

- **Server Components do NOT import hooks**. No `useState`, `useEffect`, `useRouter`.
- **Data fetching happens in Server Components**. Pass data down as props.
- **No `async` Client Components**. If you need both async and state, split into server parent + client child.

### Client Components

```typescript
"use client";

import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

- **Mark `"use client"` only when needed**. Default is server.
- **Client components get data via props**, not by fetching themselves.
- **No `useEffect` for data fetching**. Use Server Components or React Query.

### Forms

```typescript
// src/components/forms/login-form.tsx
"use client";

import { useActionState } from "react";
import { loginAction } from "@/app/(auth)/actions";

export function LoginForm() {
  const [state, formAction, pending] = useActionState(loginAction, null);
  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      <input name="password" type="password" required />
      <button disabled={pending}>{pending ? "..." : "Login"}</button>
      {state?.error && <p className="text-red-500">{state.error}</p>}
    </form>
  );
}
```

- **Server Actions for mutations**. No API routes for form submissions.
- **Zod validation in the action**, not the component.
- **`useActionState`** for pending/error state, not manual `useState`.

### API Routes (read-only data)

```typescript
// src/app/api/users/route.ts
import { NextResponse } from "next/server";
import { db } from "@/db";
import { users } from "@/db/schema";

export async function GET() {
  const all = await db.select().from(users);
  return NextResponse.json(all);
}
```

- **API routes for external integrations** (webhooks, mobile apps).
- **Server Actions for internal mutations** (forms, buttons).
- **No REST nesting**. One file per resource, use query params for filtering.

## Configuration

### Environment Variables

```typescript
// src/config.ts
import { z } from "zod";

const envSchema = z.object({
  TURSO_DATABASE_URL: z.string().url(),
  TURSO_AUTH_TOKEN: z.string().min(1),
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith("whsec_"),
  RESEND_API_KEY: z.string().startsWith("re_"),
});

export const env = envSchema.parse(process.env);
```

- **Validate env at startup**. App crashes immediately if misconfigured.
- **No `process.env.X`** scattered in code. Import from `config.ts`.
- **`.env.local`** for secrets, **`.env`** for defaults (committed).

### Path Aliases

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

All imports use `@/` prefix. No relative imports beyond one level (`../`).

## Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint check
pnpm lint:fix         # ESLint auto-fix
pnpm typecheck        # TypeScript strict check (tsc --noEmit)
pnpm test             # Run Vitest
pnpm test:watch       # Vitest watch mode
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply migrations
pnpm db:push          # Push schema (dev only)
pnpm db:seed          # Seed dev data
pnpm db:studio        # Drizzle Studio (web GUI)
```

## Anti-Patterns (and Why)

| Don't | Why | Do Instead |
|-------|-----|------------|
| `useState` for server data | Breaks SSR, causes waterfalls | Server Components + props |
| `useEffect` for initial data | Double render, loading flicker | Fetch in Server Component |
| CSS modules / styled-components | Inconsistent, slow HMR | Tailwind utility classes |
| `any` / `@ts-ignore` / `as` casts | Defeats TypeScript | Proper types, Zod inference |
| ORM `find*` methods | Hides SQL, hard to optimize | `db.select().from(table).where()` |
| Auto-increment IDs | Leaks info, hard to shard | CUID2 / nanoid |
| JWT for auth | Complex, insecure if wrong | Session cookies (better-auth) |
| Barrel files (`index.ts`) | Slow builds, circular deps | Direct imports |
| `console.log` for debugging | Ships to production | Structured logging or remove |
| Catching errors silently | Hides bugs | Let errors propagate, use error boundaries |
| Prisma | Heavy, slow, opinionated | Drizzle (SQL-first) |
| tRPC for everything | Overhead for simple CRUD | Server Actions for mutations |

## Testing

```typescript
// src/db/schema.test.ts
import { describe, it, expect } from "vitest";
import { users } from "./schema";

describe("users table", () => {
  it("has correct columns", () => {
    expect(users.id).toBeDefined();
    expect(users.email).toBeDefined();
  });
});
```

- **Unit tests** for lib utilities, schema validation, pure functions.
- **Integration tests** for API routes (mock db or use test db).
- **No E2E tests** until you have paying users. Vitest is enough.
- **Test files** live next to source: `schema.test.ts` next to `schema.ts`.

## Deployment

- **Vercel** for hosting (edge runtime where possible).
- **Turso** for database (multi-region, embedded replicas).
- **No Docker** until you need it. Vercel + Turso handles most SaaS scale.

## What We Don't Do

1. **No monorepo** until you have 2+ apps. Single `src/` is enough.
2. **No GraphQL** until REST + Server Actions can't do it.
3. **No microservices** until you have a team.
4. **No Redux/Zustand** until Server Components + `useActionState` aren't enough.
5. **No custom CSS** until Tailwind can't do it (it almost always can).
6. **No `getServerSideProps`** — this is App Router, not Pages Router.
7. **No `import React from 'react'`** — not needed since React 17 JSX transform.
