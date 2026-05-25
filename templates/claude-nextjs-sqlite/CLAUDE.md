# Next.js + SQLite SaaS — CLAUDE.md

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via Turso (production) or better-sqlite3 (local dev)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 (Auth.js)
- **UI**: Tailwind CSS 4 + shadcn/ui
- **Language**: TypeScript (strict mode)
- **Runtime**: Node.js 22+

## Project Structure

```
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Auth group (login, register)
│   │   ├── (dashboard)/       # Dashboard group (protected)
│   │   │   ├── settings/      # User/org settings
│   │   │   └── [org]/         # Org-scoped pages
│   │   ├── api/               # Route handlers
│   │   │   ├── auth/          # NextAuth API routes
│   │   │   ├── webhooks/      # Stripe/webhook handlers (no auth)
│   │   │   └── trpc/          # tRPC routes
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   ├── components/            # Shared React components
│   │   ├── ui/                # shadcn/ui primitives
│   │   └── forms/             # Form components
│   ├── db/                    # Database layer
│   │   ├── schema/            # Drizzle schema files
│   │   ├── migrations/        # Auto-generated migrations
│   │   ├── queries/           # Query functions
│   │   └── index.ts           # DB connection
│   ├── lib/                   # Shared utilities
│   │   ├── auth.ts            # NextAuth config
│   │   ├── stripe.ts          # Stripe client
│   │   ├── email.ts           # Email sending
│   │   └── utils.ts           # General utilities
│   ├── styles/                # Global styles
│   └── middleware.ts          # Next.js middleware (auth, i18n)
├── drizzle.config.ts          # Drizzle config
├── next.config.ts             # Next.js config
├── tailwind.config.ts         # Tailwind config
├── tsconfig.json
└── package.json
```

## Development Commands

```bash
# Install
pnpm install

# Dev server (with Turso or local SQLite)
cp .env.example .env.local
pnpm dev                    # → http://localhost:3000

# Database
pnpm db:generate            # Generate Drizzle migrations
pnpm db:migrate             # Apply migrations
pnpm db:push                # Push schema directly (dev only)
pnpm db:studio              # Open Drizzle Studio

# Type checking & linting
pnpm typecheck              # tsc --noEmit
pnpm lint                   # ESLint + Next.js lint
pnpm format                 # Prettier

# Test
pnpm test                   # Vitest
pnpm test:e2e               # Playwright

# Build
pnpm build                  # Production build
```

## Naming Conventions

- **Files**: `kebab-case.ts` — e.g., `user-settings.tsx`, `api-keys.ts`
- **Components**: `PascalCase.tsx` — e.g., `UserAvatar.tsx`, `SettingsForm.tsx`
- **Functions**: `camelCase` — e.g., `fetchUser()`, `formatDate()`
- **Types/Interfaces**: `PascalCase` with `Type`/`Props` suffix — e.g., `UserType`, `SettingsFormProps`
- **DB tables**: `snake_case` — e.g., `user_sessions`, `organization_members`
- **DB columns**: `snake_case` — e.g., `created_at`, `stripe_customer_id`
- **API routes**: `kebab-case` — e.g., `/api/webhooks/stripe`, `/api/trpc/[trpc]`
- **Environment variables**: `UPPER_SNAKE_CASE` — e.g., `DATABASE_URL`, `NEXTAUTH_SECRET`

## SQL / Migration Rules

1. **NEVER edit migration files** directly. Always generate via `pnpm db:generate`.
2. **One migration per schema change** — if you add a column and a table, that's one migration.
3. **Schema changes require a migration** even in development.
4. **Rollbacks**: Write a `down()` function for every migration in production.
5. **Foreign keys**: Always use `references()` in Drizzle schema.
6. **Indexes**: Add indexes for any column used in `WHERE`, `ORDER BY`, or `JOIN`.
7. **Soft deletes**: Use `deleted_at TIMESTAMP` instead of hard deletes for user-facing data.
8. **Timestamps**: Every table gets `created_at` and `updated_at` columns.

```typescript
// ✅ Good: Drizzle schema example
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  stripeCustomerId: text("stripe_customer_id"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .defaultNow(),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .defaultNow(),
  deletedAt: integer("deleted_at", { mode: "timestamp" }),
});
```

## Component Patterns

- **Server components by default** — only add `"use client"` when you absolutely need interactivity (hooks, event handlers, browser APIs).
- **Keep `page.tsx` thin** — pages compose server components, data fetching happens in the page or via server actions.
- **Form components** use `react-hook-form` + `zod` for validation.
- **API calls** go through server actions (form `action`) or tRPC, never direct `fetch()` from client components.
- **Loading states** use `loading.tsx` files per route segment.
- **Error boundaries** use `error.tsx` files per route segment.

## What We Don't Do (and Why)

| ❌ Don't | Why |
|---|---|
| `any` or `as any` | Bypasses TypeScript — we use strict mode for a reason |
| Hardcoded strings | Everything user-facing goes through `@/lib/i18n` |
| Raw SQL strings | Use Drizzle query builder for type safety |
| `useEffect` for data fetching | Use server components or server actions |
| Client-side secrets | Secrets are server-only via env vars |
| `rm -rf` in scripts | Destructive to production data |
| Direct DB access from components | Data flows through server components or tRPC |
| `git push --force` to main | Always use PRs with branch protection |

## Auth & Security

- **Auth**: NextAuth.js with credentials + OAuth providers
- **Session**: JWT strategy (database sessions optional for SQLite)
- **Rate limiting**: Upstash Ratelimit (or middleware-based)
- **API protection**: All `/api/*` routes check session unless explicitly public
- **CSRF**: Built into NextAuth.js
- **SQL injection**: Prevented by Drizzle ORM (parameterized queries)

## Testing

- **Unit tests**: Vitest for utilities and server actions
- **Component tests**: Vitest + Testing Library
- **E2E tests**: Playwright for critical user flows
- **Test files**: Co-located with source: `component.test.tsx`
- **Coverage target**: 80%+ for utilities, 60%+ for components
