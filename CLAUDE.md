# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated project context for Claude Code. Paste this at your project root.
> Every rule exists because it prevented a real production bug.

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 15.x |
| Language | TypeScript (strict) | 5.x |
| Database | SQLite via `better-sqlite3` / Turso (libsql) | latest |
| ORM | Drizzle ORM | latest |
| Styling | Tailwind CSS 4 | latest |
| Auth | NextAuth.js v5 or Auth.js | latest |
| Deployment | Docker + Vercel / self-hosted | — |
| Package manager | pnpm | 9.x |

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Route group: login, register
│   ├── (dashboard)/        # Route group: authenticated views
│   │   ├── billing/        # Subscription pages
│   │   └── settings/       # User settings
│   ├── api/                # API routes
│   │   ├── auth/[...nextauth]/
│   │   ├── webhooks/       # Stripe, etc.
│   │   └── trpc/           # tRPC endpoint (if applicable)
│   ├── layout.tsx          # Root layout (providers, fonts)
│   ├── page.tsx            # Landing/marketing page
│   └── globals.css         # Global styles (Tailwind imports)
├── components/             # React components
│   ├── ui/                 # Primitive, unstyled components (Button, Input)
│   ├── features/           # Feature-specific composed components
│   └── layouts/            # Layout wrappers (Sidebar, Header)
├── lib/                    # Application logic (no UI)
│   ├── db.ts               # Database client singleton
│   ├── auth.ts             # Auth configuration
│   ├── utils/              # Pure utility functions
│   │   ├── currency.ts     # Formatting, parsing
│   │   ├── date.ts         # Timezone-safe date helpers
│   │   └── rate-limit.ts   # Rate limiting utilities
│   └── constants.ts        # App-wide constants (no magic strings)
├── server/                 # Server-only code
│   ├── actions/            # Server Actions ("use server")
│   ├── middleware.ts       *# Next.js middleware (lives here, not src)*
│   └── jobs/              # Background job functions (called by cron)
├── schema/                 # Database schema definitions
│   ├── index.ts            # Drizzle schema exports
│   └── migrations/         # SQL migration files (never edit by hand)
├── hooks/                  # Client-side React hooks
├── stores/                 # State management (Zustand or Jotai)
└── types/                  # Shared TypeScript types
```

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Pages/files | `kebab-case` | `billing-page.tsx` |
| Components | `PascalCase` | `UserAvatar.tsx` |
| Utilities | `camelCase` | `formatCurrency.ts` |
| DB tables | `snake_case` | `subscription_plans` |
| DB columns | `snake_case` | `created_at`, `is_active` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_FREE_TIER` |
| Environment vars | `UPPER__PREFIX` | `APP__SECRET_KEY` |
| Server Actions | `camelCase` + noun | `updateSubscription` |

## Database Rules

### Schema

1. **Every table** gets `id INTEGER PRIMARY KEY AUTOINCREMENT`, `created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))`, `updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))`.
2. **Foreign keys** are always `INTEGER NOT NULL` with explicit `REFERENCES` → `ON DELETE CASCADE`.
3. **Enums** are stored as `TEXT NOT NULL` with CHECK constraints — never use JS enums for DB state.
4. **Indexes**: Add on every `WHERE`, JOIN, or `ORDER BY` column that filters >100 rows.
5. **No JSON columns for queryable data** — use them only for blobs (settings blobs, metadata).

### Migrations

1. **Never edit migrations after they're committed.** Create a new one instead.
2. Name migrations: `<NNNN>_<description>.sql` (e.g., `0001_create_users.sql`).
3. Each migration must be **reversible** (include `-- down` section).
4. Test both `up` and `down` on a fresh database before pushing.

### Query Patterns

```typescript
// ✅ DO: Use parameterized queries always
db.prepare('SELECT * FROM users WHERE id = ?').get(userId)

// ❌ DON'T: String interpolation (SQL injection)
db.prepare(`SELECT * FROM users WHERE id = ${userId}`).get()

// ✅ DO: Use transactions for multi-table writes
db.transaction(() => {
  db.prepare('INSERT INTO ...').run(...)
  db.prepare('UPDATE ...').run(...)
})

// ❌ DON'T: Run multiple writes outside a transaction
```

## Component Patterns

### Server Components (default)

```typescript
// app/(dashboard)/billing/page.tsx — Server Component by default
export default async function BillingPage() {
  const user = await getCurrentUser() // server-side auth check
  const subscription = await getSubscription(user.id)

  return <BillingView subscription={subscription} />
}
```

### Client Components (opt-in)

```typescript
// "use client" is a cost — it increases bundle size and disables SSR
// Only use when you need: browser APIs, event handlers, useState/useEffect

'use client'
export function SubscribeButton({ priceId }: { priceId: string }) {
  // client-only logic here
}
```

### Data Fetching

```typescript
// ✅ In Server Components: fetch directly in the component
const data = db.select().from(users).where(eq(users.id, userId)).get()

// ✅ In Client Components: use Server Actions or API routes
const data = await fetchDataServerAction()

// ❌ DON'T: fetch() in Client Components (causes waterfalls, no caching)
```

## Anti-Patterns (Don't Do These)

| ❌ Anti-pattern | ✅ Instead | Why |
|----------------|-----------|-----|
| `fetch()` in Client Components | Server Component + pass props as children | SSR, caching, streaming |
| `any` types | Explicit interfaces | Catches bugs at compile time |
| `console.log(data)` in routes | Structured logging or return to client | Info leaks, performance |
| Business logic in `page.tsx` | `lib/` or `server/actions/` | Reusability, testability |
| Hardcoded URLs | `constants.ts` + `NEXT_PUBLIC_` prefix | Deployable anywhere |
| `.env` committed | `.env.example` + `.gitignore` | Security |
| `SELECT *` | Explicit column names | Schema changes won't break apps |
| Storing money in `FLOAT` | `INTEGER` (store cents) or `TEXT` (decimal) | Floating-point rounding errors |
| Manual SQL string building | Parameterized queries (`?` placeholders) | SQL injection protection |
| One giant migration file | Small, single-purpose migrations | Reviewable, reversible |

## Dev Commands

```bash
# Install
pnpm install

# Development (with Turbopack for fast refresh)
pnpm dev --turbo

# Generate Drizzle migration (after schema change)
pnpm drizzle-kit generate

# Run migrations
pnpm drizzle-kit migrate

# Type-check
pnpm tsc --noEmit

# Lint
pnpm lint

# Build
pnpm build

# Seed development database
pnpm seed

# Run inside Docker (production parity)
docker compose up -d
```

## Environment Variables

Required (`.env` file, never committed):

```env
DATABASE_URL=./data/app.db              # SQLite file path (or Turso URL)
AUTH_SECRET=<generated-secret>          # nextAuth/jwt secret
NEXT_PUBLIC_APP_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_test_...           # Stripe (optional)
STRIPE_WEBHOOK_SECRET=whsec_...         # Stripe webhook (optional)
```

Generate secrets with: `openssl rand -base64 32`

## Testing Strategy

- **Unit tests**: Pure functions in `lib/utils/` — use Vitest
- **Integration tests**: DB operations against in-memory `:memory:` SQLite
- **E2E tests**: Critical paths (signup, checkout) — use Playwright
- **Server Actions**: Test by importing and calling directly (they're just async functions)

## Performance Rules

1. **Dynamic routes** = `generateStaticParams()` for known slugs, otherwise dynamic rendering.
2. **Images**: Always use `next/image` with `sizes` prop — no raw `<img>`.
3. **Fonts**: Use `next/font/google` — no Google Fonts CDN links.
4. **Bundle size**: Check `next build` output — each route should be <200KB gzipped.
5. **Database**: One query per render where possible; use JOINs over N+1 queries.
6. **Revalidate**: Set `revalidate` on fetch/data calls — don't default to no-cache everywhere.
