# Project: Next.js 15 + SQLite SaaS

> Opinionated guide for building a production SaaS with Next.js 15 App Router, SQLite, and Drizzle ORM.
> Every rule here exists because its alternative caused real pain.

## Stack & Versions

| Layer | Choice | Why not X |
|-------|--------|-----------|
| Runtime | Node.js 20+ / Bun 1.2+ | Bun for speed, Node for stability |
| Framework | Next.js 15 (App Router) | Pages Router is legacy |
| Language | TypeScript 5.x strict | `strict: true`, `noUncheckedIndexedAccess` |
| Database | SQLite via better-sqlite3 or Turso | No Postgres overhead for single-server SaaS |
| ORM | Drizzle ORM | Prisma slo col starts heavy binary poor App Router edge support |
| Auth | NextAuth.js v5 / Lucia | Clerk/Supabase locks you into their pricing |
| Forms | React Server Actions + Zod | API routes for forms is overkill |
| Styling | Tailwind CSS 4 + shadcn/ui | CSS modules incosistent styled-components runtime cost |
| Validation | Zod (server + shared) | No runtime validation type-only means production crashes |
| Testing | Vitest + Playwright | Jest slow no ESM-first |

## Folder Structure (Opinionated)

```
src/
 app/
   (marketing)/       # Public pages (landing pricing blog)
   (dashboard)/       # Protected route group
   api/               # ONLY for webhooks non-form endpoints
 components/
   ui/                # shadcn/ui primitives
   features/          # Feature-specific
 lib/
   auth.ts            # NextAuth or Lucia config
   db.ts              # Drizzle client singleton
   utils.ts           # cn() formatDate()
   validators/        # One file per domain
 db/
   schema/            # Split by domain
   migrations/        # NEVER TOUCH
   seed.ts
 actions/               # Server Actions grouped by domain
 hooks/                 # Client-side hooks ONLY
 emails/                # React Email templates
 middleware.ts
 instrumentation.ts
```

**Rule**: if a file doesnt fit one of these buckets the structure is wrong not the file

## Database Migration Rules (Hard Rules)

1. NEVER edit migration files. Change schema/ regenerate.
2. Every table MUST have id TEXT PK created_at INTEGER updated_at INTEGER. Use Unix epoch ints.
3. Foreign keys use ON DELETE CASCADE for owned records. ON DELETE SET NULL for optional refs.
4. Always use Drizzle sql template tag for raw queries. Never concatenate SQL strings.
5. Index EVERY column in a WHERE clause. Missing index = full table scan in SQLite.
6. Migrations are reversible. Each file has up and down.
7. Seed data must be idempotent. Running db:seed twice should be safe.

## Data Fetching Rules

- Default: Server Components. Only add use client for interactivity.
- Colocate data fetching. Fetch in the Server Component that needs it.
- No useEffect for data. Ever. Zero use cases in App Router.
- API routes are for webhooks and mobile clients only. Everything else Server Actions or direct db.select().
- Cache aggressive invalidate precise. Use next/cache unstable_cache().

## Auth Pattern

middleware.ts: Check session redirect to /login if unauthenticated
layout.tsx: Call getServerSession() once pass user as prop
Server Action: Re-verify session inside the action never trust client

- Session in SQLite via adapter. No Redis needed.
- Never expose stripe_customer_id hashed_password or email_verified to client.
- Rate limit auth endpoints 5 attempts/min per IP via middleware.
- OAuth (Google GitHub) + Magic Link preferred over password.

## Error Handling

| Layer | Mechanism |
| Route segments | error.tsx + not-found.tsx + loading.tsx |
| Server Actions | Return success error never throw |
| API routes | Try catch NextResponse.json error status |
| Unhandled | global-error.tsx production only resets tree |

## Anti-Patterns

| Anti-pattern | Why |
| useEffect fetching | Waterfalls race conditions double-renders in StrictMode |
| Redux/Zustand for server data | DB is source of truth not client store |
| Prisma | Heavy binary slow cold starts poor edge support |
| Barrel exports index.ts | Breaks tree-shaking increases bundle size |
| any type | Use unknown + Zod narrowing any = no TypeScript |
| inline fetch() in Client Components | Couples UI to network Server Component props |
| Business logic in page.tsx | Pages are routing not logic Use actions/ or lib/ |
| Generic catch-all error pages | Each domain needs its own error UX |
| || for defaults | Use ?? = 0 and empty string are valid values |
| pages/ router for new routes | App Router is standard Two routers is tech debt |

## Dev Commands

npm run dev              # Local dev port 3000
npm run build            # Production build type-check lint bundle
npm run lint             # ESLint + tsc --noEmit
npm run test             # Vitest unit
npm run test:e2e         # Playwright
npm run db:generate      # Generate migration
npm run db:migrate       # Apply pending migrations
npm run db:seed          # Idempotent seed
npm run db:studio        # Drizzle Studio
npm run email:dev        # React Email preview server

## Billing Subscription Pattern

- Stripe Checkout for new subs Customer Portal for management
- Store stripe_customer_id + stripe_subscription_id + status in DB
- Webhook handles checkout.session.completed invoice.paid customer.subscription.updated
- Feature flags driven by DB subscription status not Stripe API calls zero latency
- Grace period 3 days after failed payment before downgrading

## Performance Checklist

- [ ] Dynamic imports for heavy components next/dynamic
- [ ] Image with explicit width/height no layout shift
- [ ] generateStaticParams() for marketing pages
- [ ] Streaming with loading.tsx and Suspense boundaries
- [ ] DB queries use limit + offset never unconstrained select *
- [ ] Bundle analyzer in CI catch regressions per PR
