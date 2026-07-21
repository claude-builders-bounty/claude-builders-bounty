# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- **Framework**: Next.js 15.2+ (App Router), React 19, TypeScript 5.7+ strict mode
- **Database**: SQLite via better-sqlite3 (dev/prod), Drizzle ORM 0.40+
- **Auth**: NextAuth.js v5 with credentials + Google/GitHub OAuth, JWT strategy (no DB sessions)
- **Payments**: Stripe with webhook-driven subscription state stored in SQLite
- **UI**: Tailwind CSS v4 + shadcn/ui + Radix primitives
- **Validation**: Zod 4 — schemas shared via `@repo/validations` workspace package
- **Email**: Resend (transactional) + React Email templates
- **Background**: Inngest for async jobs (webhook processing, email queues)
- **Testing**: Vitest + Playwright (E2E on critical paths)
- **Monorepo**: Turborepo (apps/web, apps/api, packages/*)

## Folder Structure
```
├── apps/
│   └── web/              # Next.js app
│       ├── src/
│       │   ├── app/      # App Router: (auth)/(dashboard)/(public)
│       │   │   ├── (auth)/          # login, register, forgot-password
│       │   │   │   └── login/actions.ts   # Server Action for login
│       │   │   ├── (dashboard)/     # authenticated routes
│       │   │   │   ├── settings/
│       │   │   │   └── org/[id]/
│       │   │   └── api/            # webhooks, external routes
│       │   ├── components/
│       │   │   ├── ui/             # shadcn primitives
│       │   │   ├── forms/          # react-hook-form + Zod wrappers
│       │   │   └── features/       # feature-specific (org/, billing/, team/)
│       │   ├── db/
│       │   │   ├── schema/         # Drizzle schema files (one per domain)
│       │   │   │   ├── users.ts
│       │   │   │   ├── orgs.ts
│       │   │   │   └── subscriptions.ts
│       │   │   ├── queries/        # read-only DB access functions
│       │   │   └── migrations/     # auto-generated, never hand-edit
│       │   ├── lib/
│       │   │   ├── env.ts          # @t3-oss/env-nextjs validated env vars
│       │   │   ├── stripe.ts       # Stripe client singleton
│       │   │   └── auth.ts         # NextAuth config
│       │   └── actions/            # Server Actions, one file per domain
│       │       ├── org.actions.ts
│       │       └── billing.actions.ts
├── packages/
│   └── validations/      # Zod schemas shared across apps
└── tooling/              # ESLint, TSConfig, Prettier configs
```

## SQL / Migration Conventions
- Every schema change = `npm run db:generate` → review → `npm run db:migrate`
- Never hand-write migration files. Drizzle generates them. Hand-editing causes drift.
- Foreign keys always explicit: `foreignKey(() => users.id)` — never rely on naming.
- Soft deletes via `deletedAt TEXT DEFAULT NULL`. Hard delete only for orphaned test data.
- Cursor-based pagination only (offset pagination is O(n) on large tables).
- Index every foreign key column. SQLite needs explicit indices.
- WAL mode enabled in `drizzle.config.ts` for concurrent reads.
- Full-text search via SQLite FTS5 virtual tables, not LIKE '%term%'.

```sql
-- Good
CREATE TABLE subscriptions (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  org_id TEXT NOT NULL REFERENCES orgs(id),
  status TEXT NOT NULL DEFAULT 'trialing' CHECK(status IN ('trialing','active','past_due','canceled')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (org_id) REFERENCES orgs(id)
);
CREATE INDEX idx_subscriptions_org ON subscriptions(org_id);

-- Never
CREATE TABLE subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,  -- No sequential IDs exposed
  orgId INTEGER,                          -- Not camelCase, no FK constraint
  stripe_subscription TEXT                -- No CHECK constraint on status
);
```

## Component Patterns
### Server Components (default)
```tsx
// Good — data fetching in Server Component
export default async function OrgPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const org = await getOrg(id);  // from db/queries/
  if (!org) notFound();
  return <OrgDetail org={org} />;
}
```

### Client Components (only when needed)
```tsx
'use client';
// Only use when: interactivity, browser APIs, context, useEffect
// Keep as thin as possible — pass data from Server Component via props
export function SubscribeButton({ priceId }: { priceId: string }) {
  const [loading, setLoading] = useState(false);
  // ...
}
```

### Server Actions for mutations
```tsx
// actions/org.actions.ts
'use server';
import { z } from 'zod';
import { actionClient } from '@/lib/safe-action';  // next-safe-action wrapper

export const updateOrgName = actionClient
  .schema(z.object({ orgId: z.string(), name: z.string().min(1).max(100) }))
  .action(async ({ parsedInput: { orgId, name } }) => {
    const session = await auth();
    if (!session?.user) throw new Error('Unauthorized');
    await db.update(orgs).set({ name }).where(eq(orgs.id, orgId));
    revalidatePath(`/org/${orgId}`);
  });
```

## What We Don't Do (And Why)
- **No useEffect for data fetching.** Server Components render on the server. Data is available at page load. No spinners, no waterfalls.
- **No barrel exports** (`index.ts`). They break tree-shaking, increase bundle size, and cause circular imports.
- **No raw SQL in components.** Every query lives in `db/queries/` and is tested in isolation.
- **No `any` types.** `strict: true` in tsconfig. If a third-party lib lacks types, write a minimal `.d.ts`.
- **No Prisma.** Drizzle fits SQLite better (smaller bundle, no engine binary, supports Turso natively).
- **No Redux/Zustand.** Server Components + URL search params cover 95% of state. The remaining 5% uses React Context sparingly.
- **No default exports.** Named exports only — better refactoring, explicit imports, grep-friendly.
- **No `process.env` in client code.** All env vars go through `lib/env.ts` with runtime validation.
- **No auto-increment IDs.** Use `crypto.randomUUID()` or `nanoid()` — never expose sequential IDs in URLs.

## Dev Commands
```bash
npm run dev              # Turborepo dev (apps/web + packages)
npm run db:generate      # Generate Drizzle migration
npm run db:migrate       # Apply migration to SQLite
npm run db:seed          # Seed dev data
npm run lint             # Biome check (linter + formatter)
npm run typecheck        # tsc --noEmit across all workspaces
npm run test             # Vitest (unit + integration)
npm run test:e2e         # Playwright (critical paths only)
npm run verify           # lint + typecheck + test
```

## Stripe Integration
- Webhook endpoint: `POST /api/stripe/webhook` — verifies signature via `stripe.webhooks.constructEvent`
- Subscription state stored in local SQLite, derived from Stripe events
- Never trust the client for subscription status — always read from DB
- Idempotency keys on webhook processing to prevent double-charge

## Environment Variables
Validated at build time via `lib/env.ts`. Missing vars = build failure.
No optional secrets — if Stripe isn't configured, the billing feature is gated at the route level, not hidden behind undefined checks.
