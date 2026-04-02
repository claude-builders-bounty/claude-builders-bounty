# CLAUDE.md — Next.js + SQLite SaaS Template

> Drop this file in your repo root. Claude Code reads it automatically.
> Delete every comment block (<!-- ... -->) after you fill in your specifics.

## Project Overview

<!-- Replace with a 2-3 sentence description of what your SaaS does, who it's for, and the core value prop. Be specific — "invoicing app for freelancers" beats "business tool". -->

This is a Next.js 15 SaaS application using SQLite as the primary database via Drizzle ORM. It runs on a single server (or Vercel + Turso for serverless SQLite). The codebase uses the App Router exclusively — there is no `pages/` directory.

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | Next.js 15 (App Router) | React 19, Server Components by default |
| Database | SQLite via Drizzle ORM | File-based dev, Turso/LibSQL in prod |
| Auth | Auth.js v5 (NextAuth) | Drizzle adapter, email + OAuth providers |
| Styling | Tailwind CSS v4 + shadcn/ui | No CSS modules, no styled-components |
| Validation | Zod | Shared schemas between client and server |
| Payments | Stripe | Checkout Sessions + webhook-driven state |
| Email | React Email + Resend | Transactional only |
| Testing | Vitest + Playwright | Unit/integration + E2E |
| Deployment | Vercel | Edge runtime for middleware only |

## Project Structure

```
├── src/
│   ├── app/                    # App Router — every route is here
│   │   ├── (auth)/             # Route group: login, register, forgot-password
│   │   ├── (dashboard)/        # Route group: authenticated app pages
│   │   │   ├── layout.tsx      # Dashboard shell with sidebar + auth gate
│   │   │   ├── page.tsx        # Dashboard home / overview
│   │   │   ├── settings/       # Account settings, billing, team
│   │   │   └── [resource]/     # Dynamic routes for core domain entities
│   │   ├── (marketing)/        # Route group: landing, pricing, blog
│   │   ├── api/
│   │   │   ├── webhooks/       # Stripe, email, third-party webhooks
│   │   │   └── trpc/           # tRPC handler (if using tRPC) or REST routes
│   │   ├── layout.tsx          # Root layout — providers, fonts, metadata
│   │   └── not-found.tsx       # Global 404
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives (Button, Dialog, etc.)
│   │   └── [feature]/          # Feature-specific components (invoice-table, etc.)
│   ├── db/
│   │   ├── index.ts            # DB client singleton (drizzle + better-sqlite3)
│   │   ├── schema.ts           # All Drizzle table definitions
│   │   ├── migrations/         # Generated SQL migrations (drizzle-kit)
│   │   └── seed.ts             # Development seed data
│   ├── lib/
│   │   ├── auth.ts             # Auth.js config (providers, callbacks, adapter)
│   │   ├── auth-client.ts      # useSession hook re-export + helpers
│   │   ├── stripe.ts           # Stripe client + price/product constants
│   │   ├── email.ts            # Email sending utility (Resend wrapper)
│   │   ├── constants.ts        # App-wide constants (plan limits, feature flags)
│   │   └── utils.ts            # Pure utility functions (cn, formatCurrency, etc.)
│   ├── actions/                # Server Actions organized by domain
│   │   ├── auth.ts             # signIn, signOut, register
│   │   └── [resource].ts       # CRUD actions for each domain entity
│   └── types/                  # Shared TypeScript types and Zod schemas
│       ├── index.ts            # Re-exports
│       └── [resource].ts       # Per-entity types + validation schemas
├── public/                     # Static assets
├── drizzle.config.ts           # Drizzle Kit configuration
├── .env.local                  # Local env vars (never committed)
└── .env.example                # Template for required env vars
```

<!-- Adjust the structure above to match your actual project. Remove sections that don't exist yet. -->

## Commands

```bash
# Development
pnpm dev                        # Start dev server (localhost:3000)
pnpm build                      # Production build
pnpm start                      # Run production build locally

# Database
pnpm db:generate                # Generate migration from schema changes
pnpm db:migrate                 # Apply pending migrations
pnpm db:push                    # Push schema directly (dev only, skip migrations)
pnpm db:studio                  # Open Drizzle Studio (visual DB browser)
pnpm db:seed                    # Seed development data

# Testing
pnpm test                       # Run Vitest (unit + integration)
pnpm test:watch                 # Vitest in watch mode
pnpm test:e2e                   # Run Playwright E2E tests
pnpm test:e2e --ui              # Playwright with interactive UI

# Code Quality
pnpm lint                       # ESLint
pnpm typecheck                  # tsc --noEmit
pnpm format                     # Prettier (write)
pnpm format:check               # Prettier (check only)
```

<!-- Update these commands to match your package.json scripts exactly. -->

## Environment Variables

```bash
# .env.local (required for development)
DATABASE_URL="file:./local.db"              # SQLite file path
# DATABASE_URL="libsql://your-db.turso.io"  # Turso in production

AUTH_SECRET="generate-with-openssl-rand-base64-32"
AUTH_URL="http://localhost:3000"

# OAuth Providers (at least one required)
AUTH_GITHUB_ID=""
AUTH_GITHUB_SECRET=""
AUTH_GOOGLE_ID=""
AUTH_GOOGLE_SECRET=""

# Stripe
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_..."

# Email (Resend)
RESEND_API_KEY="re_..."
EMAIL_FROM="YourApp <noreply@yourapp.com>"
```

<!-- List every env var your app actually uses. Flag which ones are required vs optional. -->

## Database Patterns

### Schema Convention

All tables live in `src/db/schema.ts`. Use Drizzle's SQLite column types:

```typescript
// Table naming: plural, snake_case
// Column naming: snake_case
// Always include: id, created_at, updated_at
// Foreign keys: [singular_entity]_id

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(() => createId()), // cuid2
  email: text("email").notNull().unique(),
  name: text("name"),
  plan: text("plan", { enum: ["free", "pro", "team"] }).default("free").notNull(),
  stripeCustomerId: text("stripe_customer_id"),
  createdAt: integer("created_at", { mode: "timestamp" }).$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" }).$onUpdateFn(() => new Date()),
});
```

### Query Patterns

```typescript
// Always import db from the singleton
import { db } from "@/db";
import { eq, and, desc } from "drizzle-orm";

// Simple queries — use Drizzle's query builder
const user = await db.query.users.findFirst({
  where: eq(users.id, userId),
  with: { invoices: true }, // relations
});

// Complex queries — use the select API
const results = await db
  .select({ id: invoices.id, total: invoices.total })
  .from(invoices)
  .where(and(eq(invoices.userId, userId), eq(invoices.status, "paid")))
  .orderBy(desc(invoices.createdAt))
  .limit(20);
```

### Migration Workflow

1. Edit `src/db/schema.ts`
2. Run `pnpm db:generate` — creates migration SQL in `src/db/migrations/`
3. Run `pnpm db:migrate` — applies to your local DB
4. Commit both the schema change and the migration file
5. Migrations run automatically on deploy (via build script or startup)

**Never** edit generated migration files. If a migration is wrong, revert it and regenerate.

## Auth Patterns

Auth.js v5 is configured in `src/lib/auth.ts`. Key patterns:

```typescript
// Getting the session in Server Components (no hook needed)
import { auth } from "@/lib/auth";

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.user) redirect("/login");
  // session.user.id is always available (configured in callbacks)
}

// Getting the session in Client Components
"use client";
import { useSession } from "next-auth/react";

// Getting the session in Server Actions
import { auth } from "@/lib/auth";

export async function createInvoice(formData: FormData) {
  "use server";
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");
  // ...
}

// Getting the session in API Routes
import { auth } from "@/lib/auth";

export async function GET(req: Request) {
  const session = await auth();
  if (!session?.user) return Response.json({ error: "Unauthorized" }, { status: 401 });
  // ...
}
```

**Rule**: Never trust client-provided user IDs. Always derive the user from the session server-side.

## Server Actions

Server Actions are the primary mutation mechanism. They live in `src/actions/`:

```typescript
// src/actions/invoices.ts
"use server";

import { auth } from "@/lib/auth";
import { db } from "@/db";
import { invoices } from "@/db/schema";
import { createInvoiceSchema } from "@/types/invoice";
import { revalidatePath } from "next/cache";

export async function createInvoice(rawInput: unknown) {
  // 1. Authenticate
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");

  // 2. Validate input with Zod
  const input = createInvoiceSchema.parse(rawInput);

  // 3. Authorize (user owns the resource / has the right plan)
  // ...

  // 4. Mutate
  const [invoice] = await db.insert(invoices).values({
    ...input,
    userId: session.user.id,
  }).returning();

  // 5. Revalidate
  revalidatePath("/dashboard/invoices");

  return { success: true, id: invoice.id };
}
```

**Pattern**: Every server action follows the 5-step flow: Authenticate → Validate → Authorize → Mutate → Revalidate.

**Error handling in actions**: Return `{ error: string }` for expected errors (validation, permissions). Throw for unexpected errors (let the error boundary catch them).

```typescript
// Returning expected errors (not throwing)
export async function updateInvoice(rawInput: unknown) {
  const session = await auth();
  if (!session?.user) return { error: "You must be signed in." };

  const parsed = updateInvoiceSchema.safeParse(rawInput);
  if (!parsed.success) return { error: "Invalid input.", details: parsed.error.flatten() };

  const existing = await db.query.invoices.findFirst({
    where: and(eq(invoices.id, parsed.data.id), eq(invoices.userId, session.user.id)),
  });
  if (!existing) return { error: "Invoice not found." };

  await db.update(invoices).set(parsed.data).where(eq(invoices.id, parsed.data.id));
  revalidatePath("/dashboard/invoices");
  return { success: true };
}
```

## Component Conventions

### Server vs. Client Components

- **Default to Server Components**. Only add `"use client"` when you need interactivity (state, effects, event handlers, browser APIs).
- Server Components can `async/await` directly — use this for data fetching.
- Client Components cannot be async. Fetch data in a parent Server Component and pass via props, or use Server Actions with `useTransition`.

### File Naming

- Components: `PascalCase.tsx` (e.g., `InvoiceTable.tsx`)
- Utilities / libs: `kebab-case.ts` (e.g., `format-currency.ts`)
- Route files: Next.js conventions (`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`)
- Server Actions: `kebab-case.ts` in `src/actions/`
- Test files: `*.test.ts` / `*.test.tsx` co-located next to source

### UI Component Pattern

```tsx
// Composable, prop-driven, no internal data fetching
interface InvoiceRowProps {
  invoice: Invoice;
  onDelete?: (id: string) => void;
}

export function InvoiceRow({ invoice, onDelete }: InvoiceRowProps) {
  return (/* ... */);
}
```

### Data Fetching Pattern

```tsx
// src/app/(dashboard)/invoices/page.tsx — Server Component
import { auth } from "@/lib/auth";
import { db } from "@/db";
import { InvoiceTable } from "@/components/invoices/InvoiceTable";

export default async function InvoicesPage() {
  const session = await auth();
  if (!session?.user) redirect("/login");

  const invoices = await db.query.invoices.findMany({
    where: eq(invoicesTable.userId, session.user.id),
    orderBy: desc(invoicesTable.createdAt),
  });

  return <InvoiceTable invoices={invoices} />;
}
```

## Styling Rules

- **Tailwind only** — no inline `style={}` except for truly dynamic values (e.g., chart widths).
- Use `cn()` utility (from `src/lib/utils.ts`) to merge conditional classes:
  ```tsx
  <div className={cn("rounded-lg border p-4", isActive && "border-primary bg-primary/5")} />
  ```
- **shadcn/ui** components are copied into `src/components/ui/` — they're your code, customize freely.
- Responsive: mobile-first (`sm:`, `md:`, `lg:` breakpoints). Dashboard assumes `md:` minimum.
- Dark mode: use `dark:` variant. All colors must work in both modes.

## Stripe / Billing Patterns

### Subscription Lifecycle (webhook-driven)

```
Checkout Session → customer.subscription.created → update user plan in DB
                → invoice.payment_succeeded     → record payment
                → customer.subscription.updated  → handle plan changes
                → customer.subscription.deleted  → downgrade to free
```

**Critical rule**: Never trust the client for billing state. The webhook handler in `src/app/api/webhooks/stripe/route.ts` is the single source of truth for subscription changes.

### Checking Plan Access

```typescript
// src/lib/auth.ts — extend session with plan info
callbacks: {
  session({ session, user }) {
    session.user.id = user.id;
    session.user.plan = user.plan; // "free" | "pro" | "team"
    return session;
  },
},

// In Server Components / Actions:
const session = await auth();
if (session.user.plan === "free" && invoiceCount >= 5) {
  return { error: "Upgrade to Pro for unlimited invoices." };
}
```

## Error Handling

### Route-Level Error Boundaries

Every route group should have an `error.tsx`:

```tsx
// src/app/(dashboard)/error.tsx
"use client";

export default function DashboardError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 py-20">
      <h2 className="text-lg font-semibold">Something went wrong</h2>
      <p className="text-muted-foreground">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

### API Route Error Pattern

```typescript
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const input = schema.parse(body);
    // ... business logic
    return Response.json({ data: result });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return Response.json({ error: "Validation failed", details: error.flatten() }, { status: 400 });
    }
    console.error("Unexpected error:", error);
    return Response.json({ error: "Internal server error" }, { status: 500 });
  }
}
```

## Testing Strategy

### Unit Tests (Vitest)

- Test utilities, validation schemas, and pure business logic.
- Mock the DB for action tests: `vi.mock("@/db")`.
- Co-locate test files: `utils.ts` → `utils.test.ts`.

### E2E Tests (Playwright)

- Test critical user flows: sign up → create resource → manage → delete.
- Use a test SQLite database (set via `DATABASE_URL` in Playwright config).
- Seed data in `globalSetup` and clean up in `globalTeardown`.

```typescript
// e2e/invoices.spec.ts
test("user can create and send an invoice", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[name="email"]', "test@example.com");
  // ...
  await expect(page.getByText("Invoice sent")).toBeVisible();
});
```

## Code Style Rules

1. **Imports**: Use `@/` path alias for all project imports. No relative imports that go up more than one level (`../` is fine, `../../` means restructure).
2. **Types**: Prefer `interface` for object shapes, `type` for unions/intersections. Export from `src/types/`.
3. **Async**: Use `async/await` everywhere. No raw `.then()` chains.
4. **Nullability**: Use `null` (not `undefined`) for intentionally absent database values. Use optional (`?`) for optional function parameters.
5. **Enums**: Use string literal unions with Zod, not TypeScript enums:
   ```typescript
   const planSchema = z.enum(["free", "pro", "team"]);
   type Plan = z.infer<typeof planSchema>;
   ```
6. **No barrel exports** in `components/` — import directly from the component file.
7. **Server-only imports**: Use `import "server-only"` at the top of any file that must never be bundled client-side (DB queries, auth config, etc.).

## Performance Checklist

- [ ] Images use `next/image` with explicit `width`/`height` or `fill`
- [ ] Dynamic routes that rarely change use `generateStaticParams` + ISR
- [ ] Heavy client components are wrapped in `dynamic(() => import(...), { ssr: false })`
- [ ] Database queries use appropriate indexes (check with `EXPLAIN QUERY PLAN`)
- [ ] Metadata exports on every page (`generateMetadata` for dynamic, static for fixed)

## Common Gotchas

1. **SQLite concurrent writes**: SQLite uses file-level locking. Use WAL mode (`PRAGMA journal_mode=WAL`) for concurrent readers. For high-write workloads, consider Turso or a write queue.
2. **Auth.js edge compatibility**: The Drizzle SQLite adapter does NOT run on the Edge Runtime. Use `export const runtime = "nodejs"` on any route that calls `auth()`. Middleware can check the session cookie but must not call the DB.
3. **Server Action size limits**: Next.js limits request bodies to 1MB by default. For file uploads, use a presigned URL pattern (upload to S3/R2, store the URL).
4. **Revalidation**: `revalidatePath` only works in Server Actions and Route Handlers. If you mutate data outside Next.js (webhook, cron), use `revalidateTag` with fetch cache tags or on-demand ISR.
5. **Drizzle relations**: Drizzle's `relations()` are separate from the schema. They define query API relations but don't create foreign keys — you must add `references()` in the schema too.

## Deployment Notes

- **Vercel**: Set `DATABASE_URL` to your Turso connection string. Local development uses a file-based SQLite.
- **Migrations**: Add `pnpm db:migrate` to the build command: `pnpm db:migrate && pnpm build`.
- **Secrets**: All `AUTH_*`, `STRIPE_*`, and `RESEND_*` env vars must be set in Vercel project settings.
- **Regions**: Deploy to a region near your Turso database (e.g., `iad1` for US East).

---

<!-- 
CUSTOMIZATION CHECKLIST — delete this block when done:
- [ ] Filled in "Project Overview" with your actual app description
- [ ] Updated project structure to match your actual directories
- [ ] Updated commands to match your actual package.json scripts
- [ ] Listed all your actual environment variables
- [ ] Updated DB schema example with your actual tables
- [ ] Added domain-specific patterns (e.g., multi-tenancy, file uploads, real-time)
- [ ] Removed sections that don't apply (e.g., Stripe if no billing)
- [ ] Added any custom conventions your team follows
-->
