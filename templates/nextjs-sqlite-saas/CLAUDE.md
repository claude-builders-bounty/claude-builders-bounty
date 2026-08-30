# CLAUDE.md — Next.js 15 + SQLite SaaS Engineering Standard

This document is the single source of truth for AI agents (Claude Code, Antigravity) and human contributors developing within this Next.js 15 + SQLite SaaS application. Every convention is strictly reasoned and enforced.

---

## 1. Core Stack & Architecture

- **Framework**: Next.js 15 (App Router, Server Components by default, Server Actions for mutations).
- **Runtime**: Node.js 20+ LTS / Bun.
- **Language**: TypeScript 5+ (`strict: true`, zero `any`).
- **Database**: SQLite via `better-sqlite3` (local development/embedded) or Turso (`@libsql/client` for distributed/serverless).
- **ORM & Migrations**: Drizzle ORM (`drizzle-orm`, `drizzle-kit`).
- **Validation**: Zod (all Server Action payloads, API inputs, and environment variables).
- **Styling**: Tailwind CSS + Shadcn UI / Radix UI primitives.
- **Testing**: Vitest + React Testing Library.

---

## 2. Directory & File Structure

```
.
├── src/
│   ├── app/                    # Next.js App Router (pages, layouts, route handlers)
│   │   ├── (auth)/             # Route group: login, register, reset-password
│   │   ├── (dashboard)/        # Route group: protected user & admin portal
│   │   ├── api/                # Webhooks and external public REST endpoints
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Landing page
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Headless / primitive components (button, input, modal)
│   │   └── dashboard/          # Domain-specific feature components
│   ├── db/                     # Database layer
│   │   ├── schema/             # Drizzle table schemas (auth.ts, users.ts, subscriptions.ts)
│   │   ├── migrations/         # Generated SQL migrations (do not edit manually)
│   │   └── client.ts           # Singleton database connection
│   ├── actions/                # Server Actions (colocated by domain: users.ts, billing.ts)
│   ├── lib/                    # Shared utilities, auth helpers, stripe/payment adapters
│   │   ├── auth.ts             # Session & RBAC guards
│   │   ├── env.ts              # Zod-validated environment schema
│   │   └── utils.ts            # Classnames (cn), formatters
│   └── types/                  # Global shared TypeScript definitions
├── drizzle.config.ts           # Drizzle Kit configuration
├── next.config.ts              # Next.js build configuration
└── package.json
```

---

## 3. Database & Migration Conventions

1. **Schema Definition**:
   - Define tables in modular files under `src/db/schema/`.
   - Always use integer timestamps for created/updated: `createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date())`.
   - Use ULID or UUIDv4 strings for primary keys: `id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID())`.

2. **Migration Rules**:
   - **NEVER** run raw DDL queries in application code.
   - Run `npm run db:generate` to generate migration SQL.
   - Run `npm run db:migrate` to apply migrations deterministically.
   - All migrations must be backward-compatible (safe column additions with defaults; never drop live columns without multi-stage deployment).

---

## 4. Server Actions & Mutation Patterns

1. **Input Validation**:
   - Every Server Action must accept input validated via a Zod schema.
   - Return structured status tuples: `{ success: true, data: T } | { success: false, error: string }`.

2. **Authentication & Authorization**:
   - Every mutation must invoke `await requireAuth()` or `await requireAdmin()` at the first line. Never rely on client-side route guards alone.

3. **Example Server Action Pattern**:
```typescript
"use server";

import { z } from "zod";
import { requireAuth } from "@/lib/auth";
import { db } from "@/db/client";
import { projects } from "@/db/schema/projects";

const CreateProjectSchema = z.object({
  name: z.string().min(1).max(64),
  description: z.string().max(256).optional(),
});

export async function createProjectAction(input: z.infer<typeof CreateProjectSchema>) {
  const session = await requireAuth();
  const parsed = CreateProjectSchema.safeParse(input);

  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0].message };
  }

  const [project] = await db.insert(projects).values({
    name: parsed.data.name,
    description: parsed.data.description,
    userId: session.userId,
  }).returning();

  return { success: true, data: project };
}
```

---

## 5. Development Commands

| Command | Description |
|---|---|
| `npm run dev` | Start Next.js local development server |
| `npm run build` | Compile Next.js production build |
| `npm run lint` | Run ESLint and TypeScript type checking |
| `npm run db:generate` | Generate SQL migration from Drizzle schema |
| `npm run db:migrate` | Apply pending migrations to SQLite database |
| `npm run db:studio` | Launch Drizzle visual database browser |
| `npm test` | Run Vitest test suite |

---

## 6. What We Do NOT Do (And Why)

| Anti-Pattern | Why We Avoid It | Permitted Alternative |
|---|---|---|
| `'use client'` at page root | Destroys SSR benefits, balloons client bundle, leaks data fetching | Keep pages as React Server Components; isolate `'use client'` to interactive leaf components |
| Unbounded `any` types | Bypasses type safety, hides runtime bugs | Strict interfaces, Zod schema inference, or `unknown` with narrowing |
| Direct DB queries in client components | Security vulnerability; exposes database credentials | Server Components or Server Actions |
| Raw SQL concatenation | Vulnerable to SQL injection | Drizzle parameterized query builder |
| Storing secret keys in `NEXT_PUBLIC_*` | Exposes API keys/tokens to browser users | Server-only environment variables in `src/lib/env.ts` |
| Client-only auth checks | Attackers can bypass client routing using cURL/Postman | Server-side `requireAuth()` guards on all actions and route handlers |
