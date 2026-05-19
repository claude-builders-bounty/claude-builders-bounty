# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

| Layer | Technology | Version | Reason |
|-------|-----------|---------|--------|
| Framework | Next.js | 15.x (App Router) | SSR/SSG hybrid, API routes in one codebase |
| Runtime | Node.js | 20.x LTS | Native fetch, stable, Vercel compatible |
| Language | TypeScript | 5.5+ | Strict mode, path aliases |
| Database | better-sqlite3 | 11.x | Synchronous, fast, zero-config for single-tenant |
| ORM | Drizzle ORM | 0.30+ | Type-safe SQL, lightweight, SQLite-native |
| Auth | Lucia | 3.x | Session-based, works with SQLite, no OAuth lock-in |
| Styling | Tailwind CSS | 3.4+ | Utility-first, minimal CSS bundle |
| UI | shadcn/ui | 2024 | Radix primitives, copy-paste components |
| Validation | Zod | 3.23+ | Runtime + compile-time type safety |
| Testing | Vitest | 1.6+ | Fast, native TS support |

## Folder Structure

```
my-app/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Route group: auth pages
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/       # Route group: authenticated pages
│   │   ├── layout.tsx     # Auth guard, sidebar
│   │   └── page.tsx       # Dashboard home
│   ├── api/               # API routes
│   │   ├── auth/          # Login, logout, register
│   │   └── [...]/route.ts
│   ├── layout.tsx         # Root layout, providers
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/                # shadcn components (auto-generated)
│   └── app/               # App-specific components
├── lib/
│   ├── db/                # Database layer
│   │   ├── schema.ts      # Drizzle schema (single source of truth)
│   │   ├── index.ts       # DB connection singleton
│   │   └── migrations/    # Drizzle migrations (committed to git)
│   ├── auth/              # Lucia auth setup
│   ├── validations/       # Zod schemas
│   └── utils.ts           # cn(), formatters
├── tests/
│   └── *.test.ts
├── .env.local             # Never commit
├── drizzle.config.ts
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## Naming Conventions

### Files
- **Components**: PascalCase (`UserCard.tsx`)
- **Hooks**: camelCase, prefixed with `use` (`useAuth.ts`)
- **Utils**: camelCase (`formatDate.ts`)
- **API Routes**: kebab-case (`reset-password/route.ts`)
- **Database**: snake_case in schema, camelCase in TS (`created_at` → `createdAt`)

### Database
- Table names: plural, snake_case (`users`, `team_members`)
- Primary key: `id`, auto-increment integer (SQLite native)
- Foreign keys: `{table}_id` (`user_id`)
- Timestamps: `created_at`, `updated_at` (always)
- Soft delete: `deleted_at` (nullable) — never `DELETE` user-facing rows

## SQL / Migration Conventions

### Schema Changes
1. **Never modify existing migrations**. Always create a new one.
2. **Migration naming**: `0000_init.sql`, `0001_add_users_table.sql`
3. **Generate via Drizzle**: `npx drizzle-kit generate`
4. **Apply in dev**: `npx drizzle-kit migrate`
5. **Apply in prod**: Run migrations on deploy, before app starts

### Query Patterns
```typescript
// DO: Use Drizzle query builder
const user = await db.select().from(users).where(eq(users.id, id)).get();

// DON'T: Raw SQL without type safety
const user = await db.run(`SELECT * FROM users WHERE id = ${id}`);
```

### Indexing Rules
- Index all foreign keys automatically
- Index fields used in `WHERE`, `ORDER BY`, `JOIN`
- Composite index for multi-column queries: `(team_id, created_at)`
- Name convention: `idx_{table}_{column(s)}`

## Component Patterns

### Server Component (default)
```typescript
// app/dashboard/page.tsx
import { db } from "@/lib/db";

export default async function DashboardPage() {
  const data = await db.select().from(projects).all();
  return <ProjectList data={data} />;
}
```

### Client Component (explicit)
```typescript
// components/app/ProjectForm.tsx
"use client";

import { useState } from "react";

export function ProjectForm() {
  const [name, setName] = useState("");
  // ...
}
```

### Rule: Start server-side, hoist to client only when needed
- Need event handlers? → `"use client"`
- Need browser API? → `"use client"`
- Just rendering data? → Server component

## API Route Patterns

```typescript
// app/api/projects/route.ts
import { NextResponse } from "next/server";
import { z } from "zod";

const createSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function POST(req: Request) {
  const body = await req.json();
  const parsed = createSchema.safeParse(body);
  
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error }, { status: 400 });
  }
  
  // Auth check
  const session = await auth.validateSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  
  // Insert
  const project = await db.insert(projects).values({
    ...parsed.data,
    ownerId: session.userId,
  }).returning().get();
  
  return NextResponse.json(project, { status: 201 });
}
```

## Auth Pattern (Lucia + SQLite)

```typescript
// lib/auth/index.ts
import { Lucia } from "lucia";
import { BetterSqlite3Adapter } from "@lucia-auth/adapter-sqlite";
import { db } from "@/lib/db";

const adapter = new BetterSqlite3Adapter(db, {
  user: "users",
  session: "sessions",
});

export const lucia = new Lucia(adapter, {
  sessionCookie: {
    attributes: {
      secure: process.env.NODE_ENV === "production",
    },
  },
});
```

## Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL="./data/app.db"
APP_URL="http://localhost:3000"
```

## Dev Commands

```bash
# Install
npm install

# Dev server
npm run dev

# DB: generate migration from schema changes
npm run db:generate

# DB: apply migrations
npm run db:migrate

# DB: open Drizzle Studio
npm run db:studio

# Test
npm run test

# Build (prod)
npm run build
```

## What We Don't Do (And Why)

| Don't | Why |
|-------|-----|
| Use Prisma | Heavy, slow, migration conflicts in team |
| Use NextAuth.js | OAuth-only focus, complex for password auth |
| Commit `.env.local` | Secrets leak risk |
| Use `any` type | Defeats TypeScript purpose |
| Client-side data fetching for initial load | Waterfalls, slower TTFB |
| Raw SQL without Drizzle | Type safety loss, injection risk |
| `DELETE` without `deleted_at` | Accidental data loss, no recovery |
| Store files in SQLite | Bloat, use S3/R2 instead |
| Mix auth logic in components | Centralize in `lib/auth`, reuse |

## Testing Strategy

```typescript
// tests/auth.test.ts
import { describe, it, expect } from "vitest";

describe("Auth", () => {
  it("rejects invalid credentials", async () => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: "bad", password: "short" }),
    });
    expect(res.status).toBe(400);
  });
});
```

## Deployment Checklist

- [ ] `DATABASE_URL` set in prod
- [ ] `NODE_ENV=production`
- [ ] Migrations run before app start
- [ ] `next.config.js`: `output: "standalone"`
- [ ] SQLite file on persistent volume (not ephemeral)
