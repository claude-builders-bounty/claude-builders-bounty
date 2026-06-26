# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework:** Next.js 15 (App Router), React 19
- **Language:** TypeScript 5.x, strict mode
- **Database:** SQLite via better-sqlite3 (dev) / Turso (prod)
- **ORM:** Drizzle ORM (not Prisma — see "What We Don't Do")
- **Auth:** NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **UI:** Tailwind CSS 4 + shadcn/ui
- **Validation:** Zod (server + client shared schemas)
- **Payments:** Stripe (webhook-first pattern)
- **Email:** Resend / React Email
- **Package manager:** pnpm (not npm)
- **Node:** >=20 LTS

## Folder Structure

```
src/
├── app/                   # Next.js App Router pages
│   ├── (auth)/            # Login, register, password reset
│   ├── (dashboard)/       # Authenticated pages (layout groups)
│   ├── api/               # Route handlers
│   └── layout.tsx         # Root layout with providers
├── components/
│   ├── ui/                # shadcn/ui primitives
│   ├── forms/             # react-hook-form + Zod
│   └── layout/            # Navbar, sidebar, footer
├── db/
│   ├── schema/            # Drizzle schema definitions
│   ├── migrations/        # Auto-generated (do not edit)
│   └── index.ts           # DB client singleton
├── lib/
│   ├── auth.ts            # NextAuth config
│   ├── stripe.ts          # Stripe helpers
│   ├── email.ts           # Email sending
│   └── utils.ts           # cn(), formatDate(), etc.
├── validations/           # Zod schemas (shared)
└── types/                 # Global TypeScript types
```

## Dev Commands

```bash
pnpm dev           # Start dev server
pnpm build         # Production build
pnpm lint          # ESLint
pnpm type-check    # tsc --noEmit
pnpm test          # Vitest
pnpm db:generate   # Drizzle migrations
pnpm db:push       # Push to local DB
pnpm db:studio     # Drizzle Studio
pnpm format        # Prettier
```

## SQL / Migration Conventions

1. **Never edit migration files manually.** Always run `pnpm db:generate`.
2. **One migration per feature.** Squash before merge.
3. **Index every foreign key** and column used in WHERE/ORDER BY.
4. **Use `text` over `varchar`** — SQLite treats them identically.
5. **Timestamps are `integer` (Unix ms)** — avoids timezone ambiguity.
6. **Soft deletes:** Add `deletedAt` column; filter with `isNull()`.
7. **Every table** gets `createdAt` and `updatedAt` with defaults.

### Schema Example

```ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  role: text("role", { enum: ["user", "admin"] }).default("user"),
  createdAt: integer("created_at").notNull().$default(() => Date.now()),
  updatedAt: integer("updated_at").$onUpdate(() => Date.now()),
  deletedAt: integer("deleted_at"),
});
```

## Component Patterns

1. **Server components by default.** Only add "use client" when needed.
2. **Server Actions for mutations.** No separate API routes for internal ops.
3. **Search params for filter/sort.** Keeps URLs shareable.
4. **Each page gets its own `page.tsx`** with data fetching at top.
5. **Error boundaries per route segment** — `error.tsx` + `loading.tsx`.

## What We Don't Do (And Why)

| Anti-pattern | Reason |
|---|---|
| **Prisma** | Drizzle gives raw SQL control with better TypeScript for 1/3 the bundle |
| **npm** | pnpm is 2-3x faster on CI, 40% less disk, strict isolation |
| **Separate Express backend** | Next.js Route Handlers + Server Actions replace it entirely |
| **Redux / Zustand** | Server Components + URL state cover 95% of needs |
| **Raw SQL migrations** | Drizzle Kit generates safe, reviewable SQL |
| **CRA / Vite SPA** | Next.js App Router gives better SEO and RSC performance |

## Auth Rules

1. **Session in cookies, token in memory.** Use `auth()` helper.
2. **Middleware** protects `/dashboard/*` routes.
3. **API routes** validate session server-side.
4. **Two roles:** `user` and `admin`.

## Stripe Integration

1. **Webhook is source of truth.** Never trust client-side status.
2. **Idempotency keys** on every Stripe API call.
3. **Store `stripeCustomerId`** on user record at subscription creation.
4. **Webhook handler** in `src/app/api/webhooks/stripe/route.ts`.

## Testing

1. **Vitest** for unit + integration tests.
2. **Playwright** for E2E (critical paths only).
3. **Tests co-located** with module (`*.test.ts`).
4. **Mock Stripe and Resend** — never hit real APIs.
