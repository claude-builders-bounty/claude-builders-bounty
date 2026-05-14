# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Architecture

```
src/
├── app/                    # Next.js 15 App Router (RSC-first)
│   ├── (marketing)/        # Public pages (no auth)
│   ├── (dashboard)/        # Authenticated pages
│   │   └── layout.tsx      # Auth guard layout
│   └── api/                # Route handlers
├── components/             # Shared UI (RSC-safe when possible)
│   ├── ui/                 # shadcn/ui primitives
│   └── forms/              # React Hook Form + Zod validated
├── lib/
│   ├── db/                 # SQLite access layer
│   │   ├── schema.ts       # Drizzle ORM schema (single source of truth)
│   │   ├── migrate.ts      # Migration runner
│   │   └── queries/        # Named query functions, one file per domain
│   ├── auth/               # Auth.js v5 (next-auth) configuration
│   ├── billing/            # Stripe integration
│   └── utils/              # Pure functions, no side effects
├── actions/                # Server Actions (form submissions, mutations)
├── emails/                 # React Email templates
└── env.ts                  # t3-env validated environment variables
```

## Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| DB tables | `snake_case`, plural | `user_orders` |
| DB columns | `snake_case` | `created_at`, `stripe_customer_id` |
| TypeScript types | `PascalCase` | `UserOrder`, `CreateOrderInput` |
| Server actions | `camelCase`, verb-first | `createCheckoutSession` |
| Route handlers | HTTP method + resource | `GET /api/stripe/webhook` |
| Components | `PascalCase`, domain-prefixed | `BillingPricingTable` |
| Files | `kebab-case` | `user-orders.ts`, `billing-portal.tsx` |

## Database Rules

1. **Migrations are append-only.** Never edit an existing migration file. Create a new one.
2. **Every migration must be reversible.** Include `DROP` in the `.down` variant.
3. **Always use transactions** for multi-table writes:
   ```ts
   await db.transaction(async (tx) => { ... })
   ```
4. **Foreign keys enforced** via `onDelete: 'cascade'` or explicit `.references()`
5. **Index every column used in WHERE/JOIN/ORDER BY** of hot-path queries
6. **Never query in a loop.** Use `WHERE id IN (...)` or batch queries.
7. **Seed data is idempotent.** `INSERT OR IGNORE` or check-before-insert.

## Dev Commands

```bash
pnpm dev              # Next.js dev server
pnpm db:generate      # Generate Drizzle migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Drizzle Studio (localhost:4983)
pnpm lint             # ESLint + Prettier
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest (unit)
pnpm test:e2e         # Playwright (integration)
pnpm stripe:webhook   # Stripe CLI webhook forwarding
```

## Patterns to Follow

**Data Fetching:** Prefer RSC `async` components for reads. Use Server Actions for mutations. Client components only for interactivity (forms, modals, real-time).

```tsx
// ✅ Good: RSC data fetch
export default async function DashboardPage() {
  const projects = await getProjectsForUser(currentUserId());
  return <ProjectList projects={projects} />;
}
```

**Error Handling:** Use error boundaries for unexpected failures. Use `notFound()` for missing resources. Return typed errors from Server Actions.

```tsx
// ✅ Good: Typed action result
type ActionResult = { ok: true; id: string } | { ok: false; error: string };
```

**Auth Checks:** Every dashboard layout and action must call `auth()` or `currentUserId()`. Never trust `params.userId` — always verify against session.

**Rate Limiting:** Apply `@upstash/ratelimit` on all public API routes and auth endpoints.

## Anti-Patterns to Avoid

| ❌ Don't | ✅ Do Instead |
|----------|--------------|
| `use client` on layout or page files | Keep layout/page as RSC, push client logic to leaf components |
| Raw SQL string concatenation | Use Drizzle query builder or parameterized queries |
| `any` type in DB queries | Define Zod schema → infer TypeScript type |
| Import server code into client components | Server-only code uses `import 'server-only'` guard |
| `fetch` in loops or client components | Use `React.cache()` deduplication or batch queries |
| `.env` for runtime config | t3-env with validation + `env.ts` |
| Skipping `Suspense` boundaries | Wrap every async component in its own Suspense |
| Direct Stripe API in actions | Route through `lib/billing/` abstraction |

## State Management

- **Server state:** RSC + `React.cache()` + revalidatePath
- **URL state:** `useSearchParams` + `nuqs` for shareable filters
- **Client state:** `useState` for ephemeral UI, React Context for theme/auth
- **Global state is a code smell.** If you think you need Zustand, reconsider the architecture.

## Deployment Checklist

- [ ] `pnpm typecheck` passes
- [ ] `pnpm test` passes
- [ ] DB migrations applied to preview/staging first
- [ ] Environment variables validated (t3-env won't build without them)
- [ ] Stripe webhook endpoint registered in Stripe Dashboard
- [ ] Auth callback URLs updated for production domain
- [ ] Rate limits tested under load
