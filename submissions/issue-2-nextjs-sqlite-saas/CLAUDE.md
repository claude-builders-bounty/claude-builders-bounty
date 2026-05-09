# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude Code everything it needs to know about this codebase.
Do not ask clarifying questions covered here — follow these rules directly.

---

## 1. Stack & Exact Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js App Router | 15.x | RSC-first, no Pages Router |
| Language | TypeScript | 5.x strict | No `any`, no `@ts-ignore` |
| Database | Turso (libSQL) | `@libsql/client ^0.14` | Edge-compatible SQLite; use `better-sqlite3 ^11` for local-only |
| ORM / Query Builder | Drizzle ORM | `^0.41` | SQL-first, no magic, type-safe |
| Auth | better-auth | `^1.2` | Sessions in SQLite, no JWTs by default |
| Styling | Tailwind CSS | v4 | CSS-first config, no `tailwind.config.ts` |
| UI Primitives | shadcn/ui (Radix) | latest | Copy-paste components, not npm dep |
| Validation | Zod | `^3.23` | Single source of truth for schemas |
| Email | Resend | `^4` | Transactional only |
| Payments | Stripe | `^17` | Webhooks + portal |
| Testing | Vitest + Playwright | latest | Unit + E2E |
| Deployment | Vercel | — | Edge runtime for API routes |

---

## 2. Folder Structure

```
.
├── app/                        # Next.js App Router root
│   ├── (auth)/                 # Unauthenticated routes (login, signup, reset)
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   └── layout.tsx          # Minimal layout, no sidebar
│   ├── (dashboard)/            # Authenticated routes
│   │   ├── layout.tsx          # Sidebar + session guard
│   │   ├── dashboard/page.tsx
│   │   └── settings/
│   │       ├── page.tsx
│   │       └── billing/page.tsx
│   ├── api/                    # Route handlers only — no business logic here
│   │   ├── auth/[...all]/route.ts   # better-auth catch-all
│   │   ├── webhooks/
│   │   │   └── stripe/route.ts
│   │   └── trpc/[trpc]/route.ts     # Optional: tRPC adapter
│   ├── layout.tsx              # Root layout: fonts, providers, metadata
│   └── globals.css             # Tailwind v4 entry + CSS variables
│
├── components/
│   ├── ui/                     # shadcn/ui generated components (DO NOT edit directly)
│   └── features/               # Business-logic components (edit freely)
│       ├── billing/
│       ├── dashboard/
│       └── auth/
│
├── lib/
│   ├── db/
│   │   ├── index.ts            # Drizzle client singleton
│   │   ├── schema.ts           # ALL table definitions in one file
│   │   └── migrations/         # Drizzle-generated SQL files (commit these)
│   ├── auth.ts                 # better-auth server instance
│   ├── auth-client.ts          # better-auth browser client
│   ├── stripe.ts               # Stripe singleton
│   ├── resend.ts               # Resend singleton
│   └── utils.ts                # cn() and pure utility functions only
│
├── hooks/                      # Custom React hooks (client-only)
├── types/                      # Shared TypeScript types (no runtime code)
├── actions/                    # Server Actions (one file per domain)
│   ├── billing.ts
│   └── profile.ts
│
├── drizzle.config.ts
├── middleware.ts               # Auth session check + redirects
└── .env.local                  # Never committed
```

**Rule:** If a file does business logic, it lives in `lib/` or `actions/`, not in `app/`.
**Rule:** `components/ui/` is generated — never modify manually. Run `npx shadcn@latest add` instead.

---

## 3. Database: Schema & Migration Rules

### Schema (`lib/db/schema.ts`)

All tables in **one file**. Use snake_case for column names, camelCase for TypeScript properties via Drizzle mapping.

```typescript
import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";
import { createId } from "@paralleldrive/cuid2";

// Always use cuid2 for IDs — never auto-increment in distributed SQLite
export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  email: text("email").notNull().unique(),
  name: text("name"),
  stripeCustomerId: text("stripe_customer_id"),
  plan: text("plan", { enum: ["free", "pro", "enterprise"] }).notNull().default("free"),
  createdAt: integer("created_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
});

export const subscriptions = sqliteTable("subscriptions", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  stripeSubscriptionId: text("stripe_subscription_id").notNull().unique(),
  status: text("status").notNull(), // active | canceled | past_due
  currentPeriodEnd: integer("current_period_end", { mode: "timestamp" }).notNull(),
});
```

### Migrations

```bash
# After editing schema.ts:
npx drizzle-kit generate       # Creates SQL file in lib/db/migrations/
npx drizzle-kit migrate        # Applies to local/Turso DB

# NEVER run drizzle-kit push in production
# ALWAYS commit migration files — they are the source of truth
```

**Rules:**
- Add columns as `.default(value)` or nullable — never add NOT NULL without a default to existing tables
- Rename = new column + backfill migration + drop old column (3 separate migrations)
- Foreign keys always use `onDelete: "cascade"` unless there's an explicit reason not to
- Index every FK column: `index("idx_subscriptions_user_id").on(subscriptions.userId)`

### Query Patterns

```typescript
// ✅ Parameterized via Drizzle (always)
const user = await db.query.users.findFirst({
  where: eq(users.email, email),
  with: { subscriptions: true },
});

// ✅ Transactions for multi-table writes
await db.transaction(async (tx) => {
  await tx.insert(users).values({ id, email });
  await tx.insert(subscriptions).values({ userId: id, ... });
});

// ❌ Never raw SQL strings with interpolation
db.run(`SELECT * FROM users WHERE email = '${email}'`); // SQL injection
```

---

## 4. Auth (`better-auth`)

```typescript
// lib/auth.ts
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "@/lib/db";

export const auth = betterAuth({
  database: drizzleAdapter(db, { provider: "sqlite" }),
  emailAndPassword: { enabled: true },
  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    },
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24,      // Refresh if 1 day old
  },
});
```

```typescript
// middleware.ts — protect (dashboard) routes
import { auth } from "@/lib/auth";
import { NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  const session = await auth.api.getSession({ headers: request.headers });
  const isDashboard = request.nextUrl.pathname.startsWith("/dashboard");

  if (isDashboard && !session) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/dashboard/:path*", "/settings/:path*"] };
```

**Getting the session in Server Components:**
```typescript
import { auth } from "@/lib/auth";
import { headers } from "next/headers";

const session = await auth.api.getSession({ headers: await headers() });
if (!session) redirect("/login");
const user = session.user;
```

---

## 5. Component Patterns

### Server vs Client

```typescript
// ✅ Default: Server Component (no directive needed)
// Fetches data directly — no useEffect, no fetch()
export default async function DashboardPage() {
  const session = await getSession(); // server-side
  const stats = await db.query.subscriptions.findMany({ ... });
  return <StatsGrid data={stats} />;
}

// ✅ Client Component — only when you need interactivity
"use client";
import { useState } from "react";
export function BillingToggle({ plan }: { plan: string }) { ... }
```

**Rule:** Start Server Component. Add `"use client"` only when you hit: `useState`, `useEffect`, event handlers, browser APIs, or third-party client libs.

### Props

```typescript
// ✅ TypeScript interface for every component
interface UserCardProps {
  user: Pick<typeof users.$inferSelect, "id" | "name" | "email" | "plan">;
  onUpgrade?: () => void;
}

// ❌ No inline object types, no `any`, no implicit props
```

**Rule:** Prop-drilling limit is **2 levels**. Beyond that: Server Component composition or Zustand store.

### Server Actions

```typescript
// actions/profile.ts
"use server";
import { auth } from "@/lib/auth";
import { headers } from "next/headers";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { profileSchema } from "@/types/schemas";
import { eq } from "drizzle-orm";

export async function updateProfile(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Unauthorized");

  const parsed = profileSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };

  await db.update(users)
    .set({ name: parsed.data.name, updatedAt: new Date() })
    .where(eq(users.id, session.user.id));

  return { success: true };
}
```

---

## 6. API Response Format

All Route Handlers return this shape — no exceptions:

```typescript
type ApiResponse<T> = {
  data: T | null;
  error: string | null;
  meta?: { page?: number; total?: number; cursor?: string };
};

// Helper
export function ok<T>(data: T, meta?: ApiResponse<T>["meta"]): Response {
  return Response.json({ data, error: null, meta } satisfies ApiResponse<T>);
}
export function err(message: string, status = 400): Response {
  return Response.json({ data: null, error: message }, { status });
}
```

```typescript
// app/api/users/route.ts
export async function GET(request: Request) {
  const session = await getSession(request);
  if (!session) return err("Unauthorized", 401);

  const allUsers = await db.select().from(users);
  return ok(allUsers);
}
```

---

## 7. Dev Commands

```bash
# Setup
cp .env.example .env.local
npm install
npx drizzle-kit migrate          # Apply migrations

# Development
npm run dev                      # Next.js on :3000 with Turbopack

# Database
npx drizzle-kit studio           # Visual DB browser
npx drizzle-kit generate         # Generate migration after schema change
npx drizzle-kit migrate          # Apply migration

# Stripe webhooks (local)
stripe listen --forward-to localhost:3000/api/webhooks/stripe

# Testing
npm run test                     # Vitest unit tests
npm run test:e2e                 # Playwright E2E
npm run lint                     # ESLint + TypeScript check
npm run build                    # Production build check (run before PR)
```

---

## 8. Environment Variables

```bash
# .env.local — ALL required, no optional fallbacks
DATABASE_URL=libsql://your-db.turso.io
DATABASE_AUTH_TOKEN=your-turso-token

BETTER_AUTH_SECRET=32-char-random-string     # openssl rand -base64 32
BETTER_AUTH_URL=http://localhost:3000

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...

RESEND_API_KEY=re_...
FROM_EMAIL=hello@yourdomain.com

NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Rule:** Never access `process.env` directly in components. Create a validated `lib/env.ts` using Zod:

```typescript
// lib/env.ts
import { z } from "zod";
const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  BETTER_AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  // ... all vars
});
export const env = envSchema.parse(process.env);
```

---

## 9. What We Don't Do (and Why)

| Anti-pattern | Why it's banned | What to do instead |
|---|---|---|
| `any` in TypeScript | Defeats the type system — bugs become invisible | Use `unknown` + type narrowing, or Zod inference |
| `useEffect` for data fetching | Race conditions, waterfall, poor DX | Server Components + `use()` or Server Actions |
| API routes for simple reads | Extra round-trip, no benefit in RSC world | Fetch directly in Server Components via Drizzle |
| `prisma` | Runtime overhead, poor edge compatibility | Drizzle ORM — SQL-first, smaller bundle |
| `next-auth` v4 | Complex config, JWT sessions, maintenance mode | `better-auth` — simpler, native SQLite sessions |
| Auto-increment IDs | Breaks distributed SQLite (Turso replicas) | `cuid2` — collision-resistant, sortable |
| Drizzle `push` in production | No migration history, can destroy data | Always `generate` + `migrate` |
| Client Components by default | Larger bundles, lost RSC benefits | Server Components by default, client only when needed |
| Props drilled >2 levels | Maintenance nightmare, tight coupling | Server Component composition or Zustand |
| Raw SQL string interpolation | SQL injection | Always use Drizzle parameterized queries |
| `console.log` in production | Leaks sensitive data, noise | `pino` or `console.error` with structured objects |
| Storing secrets in code | Security breach | `.env.local` + Vercel env vars only |
| Middleware for data fetching | Runs on every request, not cached | Fetch in the page/layout that needs the data |

---

## 10. Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Files/folders | kebab-case | `user-card.tsx`, `billing-portal/` |
| React components | PascalCase | `UserCard`, `BillingPortal` |
| Server Actions | camelCase verb | `updateProfile`, `cancelSubscription` |
| DB tables | snake_case plural | `users`, `subscriptions`, `audit_logs` |
| DB columns | snake_case | `created_at`, `stripe_customer_id` |
| TypeScript types | PascalCase | `UserSession`, `SubscriptionStatus` |
| Zod schemas | camelCase + `Schema` | `profileSchema`, `checkoutSchema` |
| Env vars | SCREAMING_SNAKE | `STRIPE_SECRET_KEY` |
| CSS classes | Tailwind utilities only | No custom class names unless in `globals.css` |

---

## 11. Stripe Integration

```typescript
// lib/stripe.ts
import Stripe from "stripe";
export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2025-02-24.acacia",
  typescript: true,
});

// app/api/webhooks/stripe/route.ts
export async function POST(request: Request) {
  const body = await request.text();
  const sig = request.headers.get("stripe-signature")!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return err("Invalid signature", 400);
  }

  switch (event.type) {
    case "customer.subscription.updated":
    case "customer.subscription.deleted":
      await syncSubscription(event.data.object as Stripe.Subscription);
      break;
  }

  return ok({ received: true });
}
```

---

## 12. Testing Conventions

```typescript
// Unit test (Vitest) — test pure functions and Server Actions
import { describe, it, expect, vi } from "vitest";
import { updateProfile } from "@/actions/profile";

// E2E (Playwright) — test full user flows
// tests/e2e/auth.spec.ts
test("user can sign up and reach dashboard", async ({ page }) => {
  await page.goto("/signup");
  await page.fill('[name="email"]', "test@example.com");
  await page.fill('[name="password"]', "SecurePass123!");
  await page.click('[type="submit"]');
  await expect(page).toHaveURL("/dashboard");
});
```

**Coverage targets:** 80% unit for `lib/`, 100% E2E for critical paths (auth, checkout, cancel).
