# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated conventions for a production SaaS built with Next.js 15 App Router and SQLite.
> Every rule here exists because we got burned without it.

## Stack (pinned)

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server Components cut client JS by 40%+ |
| Language | TypeScript 5.7+ strict | `any` is a bug, not a type |
| Database | SQLite via Turso (prod) / better-sqlite3 (dev) | Edge-compatible, zero-ops, sub-ms reads |
| ORM | Drizzle ORM 0.41+ | Type-safe SQL without the magic |
| Auth | NextAuth.js v5 (Auth.js) | Session strategy, not JWT — SQLite sessions are cheaper to revoke |
| UI | shadcn/ui + Tailwind v4 | Copy-pasted components you own, not a black box |
| Forms | React Hook Form + Zod | Validate once, share schema client+server |
| Payments | Stripe (webhook-driven) | Never trust client-side payment state |
| Tests | Vitest + Playwright | Unit for logic, E2E for money paths |
| Package manager | pnpm | Faster, stricter, no phantom deps |

**Never use npm or yarn.** If you see a `package-lock.json`, delete it.

## Project Structure

```
app/
├── (auth)/                 # Route group: login, register, forgot-password
│   ├── layout.tsx          # Minimal layout — no sidebar, no nav
│   └── login/page.tsx
├── (dashboard)/            # Route group: authenticated app
│   ├── _components/        # Dashboard-only components
│   ├── _actions.ts         # Server Actions for this group
│   ├── layout.tsx          # Sidebar + auth guard
│   └── settings/page.tsx
├── api/                    # Route handlers (webhooks, external APIs)
│   └── stripe/webhook/     # Stripe webhook — raw body parser
├── layout.tsx              # Root: fonts, metadata, providers
└── page.tsx                # Landing — server-rendered, zero client JS

lib/
├── db/
│   ├── index.ts            # Client: Turso in prod, better-sqlite3 in dev
│   ├── schema/             # One file per domain (user.ts, billing.ts)
│   └── migrations/         # Auto-generated — NEVER hand-edit
├── auth.ts                 # Auth.js config
├── stripe.ts               # Stripe helpers
├── validations/            # Zod schemas (shared client+server)
└── utils.ts                # cn(), formatDate(), etc.

components/
├── ui/                     # shadcn primitives — don't edit, re-generate
├── forms/                  # React Hook Form wrappers
└── layout/                 # Navbar, sidebar, footer
```

**Rule of thumb:** If a file imports React, it goes in `app/` or `components/`. If it doesn't, it goes in `lib/`.

## Naming Conventions

| What | Pattern | Example |
|------|---------|---------|
| Route groups | `(name)` | `(dashboard)` |
| Route handlers | `route.ts` | `app/api/stripe/webhook/route.ts` |
| Server Actions | `_actions.ts` | `app/(dashboard)/_actions.ts` |
| Components | PascalCase `.tsx` | `UserAvatar.tsx` |
| Utilities | camelCase `.ts` | `formatDate.ts` |
| DB schemas | PascalCase `.ts` | `User.ts` |
| Zod schemas | PascalCase `Schema` | `LoginSchema.ts` |
| Tests | `*.test.ts` | `auth.test.ts` |

## Database Rules

### Migrations

```bash
# Generate migration from schema changes
pnpm drizzle-kit generate

# Apply migrations
pnpm drizzle-kit migrate

# Push schema directly (dev only — skip migration files)
pnpm drizzle-kit push
```

**NEVER hand-edit migration files.** If a migration is wrong, create a new one that fixes it.

### Schema patterns

```typescript
// lib/db/schema/user.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});
```

**Always use `text` for IDs** (UUIDs). Auto-increment integers leak row counts.

### Queries

```typescript
// Good: type-safe, composable
const user = await db.query.users.findFirst({
  where: eq(users.email, email),
});

// Bad: raw string interpolation (SQL injection risk)
const user = await db.get(`SELECT * FROM users WHERE email = "${email}"`);
```

## Component Patterns

### Server Components by default

```typescript
// Good: server component, zero client JS
export default async function DashboardPage() {
  const session = await auth();
  if (!session) redirect("/login");

  const data = await db.query.orders.findMany({
    where: eq(orders.userId, session.user.id),
  });

  return <OrderList orders={data} />;
}
```

### Client components only when needed

```typescript
// "use client" ONLY when you need:
// - useState, useEffect, useRef
// - Event handlers (onClick, onChange)
// - Browser APIs (localStorage, window)
// - Third-party client libraries

"use client";

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Server Actions for mutations

```typescript
// app/(dashboard)/_actions.ts
"use server";

import { auth } from "@/lib/auth";
import { db } from "@/lib/db";
import { orders } from "@/lib/db/schema";
import { revalidatePath } from "next/cache";

export async function createOrder(formData: FormData) {
  const session = await auth();
  if (!session) throw new Error("Unauthorized");

  const name = formData.get("name") as string;
  // validate with Zod before writing
  await db.insert(orders).values({ name, userId: session.user.id });
  revalidatePath("/dashboard");
}
```

## Anti-Patterns (and why)

| Don't | Why | Do instead |
|-------|-----|------------|
| `"use client"` at the root | Bundles everything into client JS | Keep pages as Server Components, wrap interactive bits |
| `fetch()` in Server Components | Unnecessary network hop | Query DB directly via Drizzle |
| `any` type | Silences all type errors | Use `unknown` + type guards |
| `localStorage` for auth tokens | XSS can steal them | HttpOnly cookies via Auth.js |
| Edit shadcn components | Upstream updates will conflict | Extend with wrapper components |
| `npm install` | Creates `package-lock.json` | Always `pnpm install` |
| Hand-edit migrations | Drizzle will overwrite | Generate new migration |
| Trust client-side payment state | Stripe webhooks are authoritative | Verify via webhook handler |
| `router.push()` after mutations | Stale data | `revalidatePath()` + `redirect()` |
| `console.log` in production | Leaks to client | Use a logger or `NODE_ENV` guard |

## Testing

```bash
# Unit tests
pnpm test

# E2E tests
pnpm test:e2e

# Type check
pnpm typecheck
```

### What to test

- **Money paths**: checkout, billing, subscription changes
- **Auth flows**: login, register, session refresh, logout
- **Data mutations**: any Server Action that writes to DB
- **Edge cases**: empty states, error states, race conditions

### What NOT to test

- Static pages (just check they render)
- Third-party integrations (mock Stripe, not test it)
- CSS/styling (Playwright visual tests are flaky)

## Dev Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm typecheck        # TypeScript strict check
pnpm lint             # ESLint
pnpm test             # Vitest unit tests
pnpm test:e2e         # Playwright E2E
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply migrations
pnpm db:push          # Push schema (dev only)
pnpm db:seed          # Seed test data
pnpm db:studio        # Drizzle Studio (DB GUI)
```

## PR Checklist

Before submitting a PR, verify:

- [ ] `pnpm typecheck` passes (zero errors)
- [ ] `pnpm lint` passes
- [ ] `pnpm test` passes
- [ ] New DB changes have a generated migration
- [ ] No `"use client"` added to page-level components without justification
- [ ] No `any` types introduced
- [ ] Server Actions validate input with Zod
- [ ] Auth checks present in all protected routes/actions
