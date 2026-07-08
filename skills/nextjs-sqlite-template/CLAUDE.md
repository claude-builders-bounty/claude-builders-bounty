# CLAUDE.md

> **Project**: Next.js 15 (App Router) + SQLite SaaS
> **Last updated**: 2026-07-08
> **Purpose**: Complete context for Claude Code so it can work on this codebase without asking clarifying questions. Follow it strictly.

---

## Stack & Versions

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Framework | Next.js (App Router) | 15.x | RSC, streaming, server actions — the modern React way |
| Language | TypeScript | 5.x | strict mode on; `noUncheckedIndexedAccess: true` |
| Database | better-sqlite3 | 11.x | Synchronous, zero-dependency SQLite — perfect for single-server SaaS |
| ORM | Drizzle ORM | 0.38+ | Type-safe, lightweight, SQL-first — no magic |
| Migrations | Drizzle Kit | Latest | Declarative SQL migrations, no ORM lock-in |
| Styling | Tailwind CSS | 3.4+ | Utility-first, tree-shaken, consistent design tokens |
| Auth | next-auth (Auth.js) | 5.x (beta) | App Router native, edge-ready, multi-provider |
| Validation | Zod | 3.x | Parse, don't validate — type-safe runtime checks |
| Testing | Vitest + Playwright | Latest | Vitest for unit/integration, Playwright for E2E |
| Payments | Stripe | Latest | Hosted Checkout + webhooks — never handle raw card data |
| Linting | ESLint 9 | Latest | Flat config, strict TypeScript rules |

---

## Folder Structure

```
.
├── CLAUDE.md                          # This file — AI context
├── next.config.ts                     # Next.js configuration
├── tailwind.config.ts                 # Tailwind design tokens
├── tsconfig.json                      # TypeScript configuration
├── drizzle.config.ts                  # Drizzle Kit migration config
├── package.json
├── .env                               # Local secrets (never commit)
├── .env.example                       # Template for required env vars
├── .eslintrc.json                     # ESLint config (strict)
│
├── public/                            # Static assets
│   ├── favicon.ico
│   └── images/
│
├── src/
│   ├── app/                           # Next.js App Router (file-system routing)
│   │   ├── layout.tsx                 # Root layout — providers, metadata
│   │   ├── page.tsx                   # Home / landing page
│   │   ├── globals.css                # Tailwind imports + base styles
│   │   ├── (marketing)/               # Route group — public pages
│   │   │   ├── pricing/
│   │   │   │   └── page.tsx
│   │   │   └── blog/
│   │   │       └── [slug]/
│   │   │           └── page.tsx
│   │   ├── (auth)/                    # Route group — auth pages
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   ├── (dashboard)/               # Route group — authenticated pages (shared layout)
│   │   │   ├── layout.tsx             # Dashboard layout with nav + auth guard
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   └── api/                       # API route handlers
│   │       ├── auth/[...nextauth]/route.ts
│   │       └── webhooks/stripe/route.ts
│   │
│   ├── components/                    # Shared UI components
│   │   ├── ui/                        # shadcn/ui primitives (Button, Input, etc.)
│   │   ├── forms/                     # Form components with Zod validation
│   │   ├── landing/                   # Landing page specific components
│   │   └── dashboard/                 # Dashboard specific components
│   │
│   ├── lib/                           # Shared utilities (NO React code)
│   │   ├── db/                        # Database layer
│   │   │   ├── index.ts              # Database connection singleton
│   │   │   ├── schema.ts            # All Drizzle table definitions
│   │   │   └── migrations/          # Auto-generated SQL migrations
│   │   ├── auth.ts                   # Auth.js configuration
│   │   ├── stripe.ts                 # Stripe client init
│   │   ├── utils.ts                  # General utility functions
│   │   └── constants.ts              # App-wide constants
│   │
│   ├── services/                      # Business logic layer (can import db)
│   │   ├── users.ts                  # User CRUD + business rules
│   │   ├── subscriptions.ts          # Plan management, quota checks
│   │   └── billing.ts               # Stripe integration logic
│   │
│   ├── hooks/                         # Client-side React hooks
│   │   ├── use-user.ts
│   │   └── use-subscription.ts
│   │
│   ├── emails/                        # React Email templates
│   │   ├── welcome.tsx
│   │   └── reset-password.tsx
│   │
│   └── types/                         # Shared TypeScript types
│       └── index.ts
│
├── tests/
│   ├── unit/                          # Fast, no database
│   ├── integration/                   # With test database
│   └── e2e/                           # Playwright browser tests
│
├── scripts/
│   ├── seed.ts                        # Development seed data
│   └── migrate.ts                     # Migration runner
│
└── content/                           # MDX blog content (if blog exists)
    └── posts/
```

---

## Database Conventions

### Schema Design

- **Table names**: `snake_case`, plural (`users`, `subscriptions`, `api_keys`)
- **Column names**: `snake_case` — always. `created_at`, `updated_at`, `deleted_at`
- **Primary keys**: Always `id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID())` — use UUIDs, never auto-increment integers for SaaS
- **Timestamps**: Every table MUST have `created_at` and `updated_at`. Use `$defaultFn(() => new Date())` and `$onUpdateFn(() => new Date())`
- **Soft deletes**: Use `deleted_at: integer("deleted_at", { mode: "timestamp" })` — nullable, set to `Date.now()` on "delete". Never hard-delete user data.
- **JSON columns**: Use `text("metadata", { mode: "json" })` for flexible metadata — but prefer explicit columns for queryable fields

### Schema File Organization

All tables in a SINGLE `src/lib/db/schema.ts` until you hit 15+ tables. Then split:

```
src/lib/db/schema/
├── index.ts          # Re-exports all tables + relations
├── users.ts
├── subscriptions.ts
├── organizations.ts
└── relations.ts      # Drizzle relations only (no circular deps this way)
```

### Migration Rules

1. **Never edit existing migration files** — only add new ones
2. **Always generate, never hand-write**: `npx drizzle-kit generate`
3. **Always review generated SQL** before running: `npx drizzle-kit migrate`
4. **No destructive operations without explicit confirmation**: `DROP TABLE`, `DROP COLUMN`, `ALTER COLUMN ... TYPE` with potential data loss
5. **Add indexes for foreign keys**: Drizzle doesn't auto-index FKs — add `.references()` columns must have `CREATE INDEX` in a follow-up migration
6. **Backward compatibility**: New columns must have a default value or be nullable

### Query Patterns

```typescript
// ✅ CORRECT — dependency injection pattern for testability
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export async function getUserById(id: string) {
  return db.query.users.findFirst({ where: eq(users.id, id) });
}

// ✅ CORRECT — transactional writes always
export async function createUserWithOrg(data: NewUser & { orgName: string }) {
  return db.transaction(async (tx) => {
    const org = await tx.insert(organizations).values({ name: data.orgName }).returning();
    const user = await tx.insert(users).values({ ...data, orgId: org[0]!.id }).returning();
    return { user: user[0], org: org[0] };
  });
}
```

- **Always use Drizzle query methods**: `db.query.users`, not raw SQL (unless performance-critical)
- **Import db from `@/lib/db`** — never create new Database instances
- **`, { mode: "json" }` on all JSON/text columns that hold structured data
- **Use `returning()`** on inserts/updates when you need the result

### SQLite-Specific Rules

- `better-sqlite3` is **synchronous** — no `await` on db calls (but server components/functions still need `async`)
- WAL mode is on by default (enabled in `src/lib/db/index.ts`) — good for concurrent reads
- `PRAGMA foreign_keys = ON` — enabled at connection time
- No concurrent write problem: single-server SQLite handles writes sequentially
- For multi-process (serverless), use **Turso/libsql** instead — same Drizzle syntax

---

## Component Patterns

### Server Components (Default)

```typescript
// ✅ CORRECT — Server Component (default in App Router, no 'use client')
import { getUserById } from "@/services/users";

interface Props { userId: string }

export default async function UserProfile({ userId }: Props) {
  const user = await getUserById(userId);  // Direct DB call, no API layer needed
  if (!user) return <NotFound />;

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}
```

**Rules for Server Components:**
- Direct DB access is fine — no need for a REST middleware
- Call `services/` functions, not `lib/db` directly from components
- Use `async` components for data fetching
- Never import Client Components that use hooks without `'use client'`

### Client Components (When Needed)

Only add `'use client'` when you need:
- `useState`, `useEffect`, `useReducer`
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`localStorage`, `window`)
- Context consumers

```typescript
// ✅ CORRECT — Client Component boundary with server-data passed as props
'use client';

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  initialName: string;  // Passed from server component parent
  onSave: (name: string) => Promise<void>;  // Server action or fetch
}

export function EditableName({ initialName, onSave }: Props) {
  const [name, setName] = useState(initialName);
  return (
    <div>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <Button onClick={() => onSave(name)}>Save</Button>
    </div>
  );
}
```

### Data Fetching Patterns

```typescript
// ✅ PATTERN — Co-locate data fetching with the component that needs it
// src/app/(dashboard)/dashboard/page.tsx
export default async function DashboardPage() {
  const stats = await getDashboardStats();  // From src/services/

  return <DashboardContent stats={stats} />;
}

// ✅ PATTERN — Parallel data fetching for independent queries
export default async function DashboardPage() {
  const [stats, recentActivity, notifications] = await Promise.all([
    getDashboardStats(),
    getRecentActivity(),
    getNotifications(),
  ]);
  // ...
}
```

**Avoid:**
- `useEffect` for data fetching in Client Components — lift to Server Component parent
- API routes that just proxy DB calls — Server Components can call DB directly
- `fetch()` to your own API routes from Server Components

### Form Handling

```typescript
// ✅ CORRECT — Server Actions with Zod validation
// src/app/(dashboard)/settings/actions.ts
'use server';

import { z } from "zod";
import { updateUser } from "@/services/users";
import { auth } from "@/lib/auth";

const schema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
});

export async function updateProfile(formData: FormData) {
  const session = await auth();
  if (!session?.user?.id) throw new Error("Unauthorized");

  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };

  await updateUser(session.user.id, parsed.data);
  return { success: true };
}
```

**Rules:**
- Always validate with Zod BEFORE touching the database
- Server Actions go in `actions.ts` files co-located with their route
- Use `useActionState` for progressive enhancement (works without JS)
- Return typed results: `{ success: true } | { error: ZodFlattenedError }`

---

## What We Don't Do (And Why)

1. **No ORMs with heavy abstractions (Prisma, TypeORM)**
   - SQLite is simple — Drizzle gives us type-safe SQL without the runtime cost
   - Prisma adds 12MB+ to bundle size and requires a binary engine

2. **No REST/GraphQL API layer between components and database**
   - Next.js Server Components are the API layer
   - Adding REST between server code and the DB is unnecessary indirection
   - Exception: public API endpoints for external consumers go in `/api/`

3. **No `useEffect` for data fetching**
   - Causes waterfalls, hurts performance, breaks SSR
   - Must use Server Components or React Query (SWR) for client-side fetching

4. **No CSS-in-JS runtime solutions (styled-components, Emotion)**
   - Adds runtime cost, breaks streaming SSR
   - Tailwind CSS is compile-time, zero-runtime, and tree-shaken

5. **No environment variables accessed client-side without `NEXT_PUBLIC_` prefix**
   - Server-only secrets stay server-only
   - Never pass `DATABASE_URL` or `STRIPE_SECRET_KEY` to the client

6. **No `any` type**
   - Every function parameter and return type must be explicit
   - Use `unknown` if genuinely unknown — forces a type guard

7. **No default exports in `lib/`, `services/`, `hooks/`**
   - Named exports only for better tree-shaking and IDE autocompletion
   - Default exports are OK for Next.js page/layout components (framework convention)

8. **No hard-delete on user data**
   - Always soft-delete with `deleted_at` timestamp
   - GDPR compliance, undo capability, audit trail

9. **No raw SQL string interpolation**
   - Always use Drizzle's query builder or parameterized queries
   - Even with SQLite, injection is possible on user-facing queries

10. **No mixing concerns in `components/`**
    - UI components (`components/ui/`) never import `lib/db` or `services/`
    - Business logic lives in `services/`, not in components

---

## Commands

```bash
# Development
npm run dev              # Next.js dev server (with Turbopack)
npm run build            # Production build
npm run start            # Production server

# Database
npm run db:generate      # Generate migrations from schema changes
npm run db:migrate       # Apply pending migrations
npm run db:studio        # Open Drizzle Studio (local DB browser, port 4983)
npm run db:seed          # Seed development database with test data
npm run db:reset         # Wipe DB, re-run all migrations, re-seed (dev only)

# Testing
npm run test             # Vitest — unit + integration
npm run test:watch       # Vitest in watch mode
npm run test:e2e         # Playwright E2E tests
npm run test:coverage    # Coverage report

# Code Quality
npm run lint             # ESLint (strict)
npm run typecheck        # tsc --noEmit
npm run format           # Prettier
npm run check            # lint + typecheck + test (CI pipeline)

# Stripe
npm run stripe:webhook   # Stripe CLI — forward events to localhost
npm run stripe:trigger   # Trigger test webhook events
```

---

## Testing Conventions

### Vitest (Unit + Integration)

```typescript
// Integration test pattern — real SQLite, in-memory or temp file
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import * as schema from "@/lib/db/schema";
import { createUserWithOrg } from "@/services/users";

describe("users service", () => {
  let db: ReturnType<typeof drizzle>;

  beforeAll(async () => {
    const sqlite = new Database(":memory:");  // In-memory for speed
    sqlite.pragma("foreign_keys = ON");
    db = drizzle(sqlite, { schema });
    // Run migrations programmatically
    // Note: drizzle-kit migrations need a filesystem path — use a test helper
  });

  it("creates user with organization in a transaction", async () => {
    const result = await createUserWithOrg({ email: "test@test.com", orgName: "Acme" });
    expect(result.user.email).toBe("test@test.com");
    expect(result.org.name).toBe("Acme");
  });
});
```

**Rules:**
- Unit tests: `tests/unit/` — mock DB, fast, no I/O
- Integration tests: `tests/integration/` — real SQLite, :memory: or temp file
- Test file naming: `*.test.ts` for Vitest, `*.spec.ts` for Playwright
- Test DB is always :memory: or temp file — never touch dev/prod DB

### Playwright (E2E)

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from "@playwright/test";

test("user can sign up and access dashboard", async ({ page }) => {
  await page.goto("/signup");
  await page.fill('[name="email"]', `test-${Date.now()}@example.com`);
  await page.fill('[name="password"]', "securePassword123!");
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL("/dashboard");
});
```

---

## Common Patterns

### Auth Guard for Protected Routes

```typescript
// src/app/(dashboard)/layout.tsx
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session?.user) redirect("/login");
  return <>{children}</>;
}
```

### Subscription/Metering Check

```typescript
// src/services/subscriptions.ts
export async function checkQuota(userId: string, action: "create_project" | "invite_member") {
  const sub = await db.query.subscriptions.findFirst({
    where: eq(subscriptions.userId, userId),
    with: { plan: true },
  });
  if (!sub) throw new Error("No subscription");

  const limits = PLAN_LIMITS[sub.plan.key];
  if (sub.usage[action] >= limits[action]) {
    throw new QuotaExceededError(action, limits[action]);
  }
}
```

### Soft-Delete Pattern

```typescript
// NEVER do this:
await db.delete(projects).where(eq(projects.id, id));

// ALWAYS do this:
await db.update(projects)
  .set({ deletedAt: new Date() })
  .where(eq(projects.id, id));

// And filter queries:
.where(and(eq(projects.orgId, orgId), isNull(projects.deletedAt)));
```

---

## Environment Variables

```
# .env.example — template, safe to commit
DATABASE_URL=file:./data/local.db    # better-sqlite3 local file
AUTH_SECRET=                          # `openssl rand -base64 32`
AUTH_GOOGLE_ID=                       # Google OAuth client ID
AUTH_GOOGLE_SECRET=                   # Google OAuth client secret
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_APP_URL=http://localhost:3000  # Only NEXT_PUBLIC_ vars go to client
```

---

## Git Conventions

- Branch naming: `feat/description`, `fix/description`, `chore/description`
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/) — `feat: add team invitations`
- PR title matches commit convention
- Never commit `.env`, `*.db`, `data/`, `node_modules/`

---

## Onboarding New Developers

1. Clone repo, run `npm install`
2. Copy `.env.example` → `.env`, fill in values
3. Run `npm run db:migrate` to create local SQLite DB
4. Run `npm run db:seed` for test data
5. Run `npm run dev` — the app is live at `http://localhost:3000`
6. Run `npm run check` to verify everything passes

---

## Key Architectural Decisions

1. **SQLite over Postgres**: Single-file, zero-config, fast enough for 99% of SaaS apps. If you outgrow it (100+ concurrent writes), migrate to Turso.
2. **Drizzle over Prisma**: SQL-first, smaller, TypeScript-native. Migrations are just SQL files.
3. **Server Components first**: Database queries run on the server, no API latency, smaller client bundles.
4. **Server Actions for mutations**: No need for REST endpoints for form submissions. Progressive enhancement built-in.
5. **Tailwind over CSS Modules**: Faster iteration, consistent design system, smaller CSS bundle.
6. **Zod for all boundaries**: API inputs, form data, webhook payloads — validate everything at the edge.
7. **Soft deletes everywhere**: User data is never truly deleted. GDPR compliance, undo, audit trails.
