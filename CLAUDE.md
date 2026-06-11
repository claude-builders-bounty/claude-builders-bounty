# CLAUDE.md — Next.js + SQLite SaaS Template

> Opinionated guide for Claude Code working on a greenfield Next.js 15 App Router SaaS project with SQLite. Every rule here has a reason. If you disagree, the project owner's preference wins.

---

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| **Framework** | Next.js 15 (App Router) | Server Components by default, streaming, Server Actions |
| **React** | 19 (canary) | Required by App Router; includes `use()` hook, Server Components |
| **Language** | TypeScript 5.x strict | No `any`. Use `unknown` + type guards if you must |
| **Database** | better-sqlite3 (local) or Turso (edge) | SQLite is zero-config for dev, Turso for prod edge replication |
| **ORM/Query** | Drizzle ORM | Type-safe SQL, tiny bundle, SQLite-first |
| **Auth** | better-auth or Lucia v3 | Session-based, no JWT in cookies |
| **Styling** | Tailwind CSS 4 | Utility-first, co-located with components |
| **Package Manager** | pnpm | Fast, strict, monorepo-ready |
| **Runtime** | Node.js 20.9+ LTS | Minimum for Next.js 15 |

---

## Project Structure

```
├── app/                          # App Router (routes only)
│   ├── layout.tsx                # Root layout — HTML shell, fonts, providers
│   ├── page.tsx                  # Home / landing
│   ├── (auth)/                   # Route group: login, register, forgot-password
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/              # Route group: protected app pages
│   │   ├── layout.tsx            # Dashboard shell — sidebar, nav
│   │   ├── page.tsx              # Dashboard home
│   │   └── settings/page.tsx
│   └── api/                      # API routes (Webhooks, external integrations only)
│       └── webhooks/stripe/route.ts
├── components/                   # Shared UI components
│   ├── ui/                       # Primitives (Button, Input, Card) — shadcn/ui style
│   └── features/                 # Domain-specific (InvoiceTable, PricingCard)
├── lib/                          # Shared logic, no UI
│   ├── db/
│   │   ├── schema.ts             # Drizzle schema definitions
│   │   ├── migrate.ts            # Migration runner
│   │   └── index.ts              # Database client singleton
│   ├── auth.ts                   # Auth configuration
│   ├── stripe.ts                 # Stripe client
│   └── utils.ts                  # Generic helpers (cn, formatCurrency, etc.)
├── drizzle/                      # Migration files (auto-generated, don't hand-edit)
├── public/                       # Static assets only (images, fonts, favicon)
├── middleware.ts                  # Auth redirects, rate limiting
├── drizzle.config.ts             # Drizzle Kit config
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### What goes where

- **`app/`**: Only route files. No business logic, no DB calls directly in page components — use Server Actions or `lib/` functions.
- **`components/ui/`**: Stateless, reusable primitives. Never import from `lib/` or `app/`.
- **`components/features/`**: Domain components. Can import from `lib/`.
- **`lib/`**: Pure logic. Database, auth, external APIs. Zero React imports.

---

## Database & Migrations (SQLite)

### Schema Conventions

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { createId } from "@paralleldrive/cuid2";

export const users = sqliteTable("users", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => createId()),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});
```

**Rules:**

1. **IDs**: Always `text` with CUID2. Never auto-increment integers for public-facing IDs — they leak count and are guessable.
2. **Timestamps**: Always `integer` with `mode: "timestamp"`. SQLite has no native datetime; integers are portable and sortable.
3. **Booleans**: Use `integer("flag", { mode: "boolean" })`. SQLite stores as 0/1.
4. **Foreign keys**: Define with `.references(() => table.id)` in Drizzle. SQLite enforces them when `PRAGMA foreign_keys = ON`.
5. **No JSON columns**: SQLite JSON support is limited. If you need structured data, use a separate table. Exception: small metadata blobs where querying inside the JSON is never needed.
6. **Table names**: Plural nouns, snake_case (`users`, `invoice_items`). Never pluralize with `es` — keep it boring.

### Migration Workflow

```bash
# Generate migration from schema changes
pnpm drizzle-kit generate

# Apply migrations (dev — automatic via lib/db/migrate.ts)
pnpm drizzle-kit migrate

# Push directly to DB (dev shortcut, skips migration files)
pnpm drizzle-kit push
```

**Critical**: Never hand-edit files in `drizzle/`. They are auto-generated. If a migration is wrong, revert the schema change and regenerate.

### Database Client

```typescript
// lib/db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database("local.db");
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("foreign_keys = ON");

export const db = drizzle(sqlite, { schema });
```

- **Singleton**: One client, reused. Never create `new Database()` per request.
- **WAL mode**: Always enable. Allows concurrent reads during writes.
- **Foreign keys**: Always enable. SQLite defaults to OFF.

### Turso (Production)

```typescript
// lib/db/index.ts (production)
import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

export const db = drizzle(client, { schema });
```

Switch `drizzle.config.ts` driver based on `NODE_ENV`.

---

## Server Actions vs. Route Handlers

### Use Server Actions for:
- Form submissions (`<form action={createInvoice}>`)
- Data mutations from client components
- Anything that reads/writes to your DB from user interaction

```typescript
// app/(dashboard)/invoices/actions.ts
"use server";

import { db } from "@/lib/db";
import { invoices } from "@/lib/db/schema";
import { revalidatePath } from "next/cache";
import { z } from "zod";

const CreateInvoiceSchema = z.object({
  amount: z.coerce.number().positive(),
  description: z.string().min(1).max(500),
});

export async function createInvoice(formData: FormData) {
  const parsed = CreateInvoiceSchema.safeParse({
    amount: formData.get("amount"),
    description: formData.get("description"),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await db.insert(invoices).values(parsed.data);
  revalidatePath("/invoices");
}
```

### Use Route Handlers (`route.ts`) for:
- Webhooks (Stripe, GitHub, etc.)
- External API integrations
- Anything that needs custom headers or streaming

### Never:
- Call `fetch("/api/...")` from a Server Component. Just call the function directly.
- Put DB queries in `route.ts` when a Server Action is cleaner.
- Use Route Handlers for form submissions. Server Actions handle progressive enhancement automatically.

---

## Component Patterns

### Server Components (default)

```tsx
// app/(dashboard)/page.tsx
import { db } from "@/lib/db";
import { invoices } from "@/lib/db/schema";

export default async function DashboardPage() {
  const allInvoices = await db.select().from(invoices);

  return (
    <div>
      <h1>Dashboard</h1>
      <InvoiceTable data={allInvoices} />
    </div>
  );
}
```

- **No `"use client"` needed** — it's the default.
- **Can be async** — fetch data directly, no `useEffect`.
- **Never import `useState`, `useEffect`, event handlers** — those belong in Client Components.

### Client Components

```tsx
// components/features/invoice-form.tsx
"use client";

import { useActionState } from "react";
import { createInvoice } from "@/app/(dashboard)/invoices/actions";

export function InvoiceForm() {
  const [state, action, pending] = useActionState(createInvoice, null);

  return (
    <form action={action}>
      <input name="amount" type="number" required />
      <textarea name="description" required />
      <button disabled={pending}>
        {pending ? "Creating..." : "Create Invoice"}
      </button>
      {state?.error && <p className="text-red-500">{JSON.stringify(state.error)}</p>}
    </form>
  );
}
```

- **Always `"use client"` at top** of file.
- **Minimize client boundary** — push `"use client"` as deep as possible.
- **Never fetch data in `useEffect`** — pass it from a Server Component parent or use Server Actions.

### Pattern: Server Component → Client Component

```tsx
// Server Component fetches data
async function Page() {
  const user = await getUser();
  return <UserMenu user={user} />;  // Client Component receives serializable data
}
```

**The boundary**: Server Components pass **serializable props** (plain objects, arrays, primitives) to Client Components. Never pass functions, Dates, or DB instances across the boundary.

---

## Auth

### Session-Based (not JWT)

```typescript
// lib/auth.ts
import { betterAuth } from "better-auth";

export const auth = betterAuth({
  database: db,
  emailAndPassword: { enabled: true },
  session: {
    expiresIn: 60 * 60 * 24 * 30, // 30 days
    updateAge: 60 * 60 * 24,       // Refresh daily
  },
});
```

### Middleware Protection

```typescript
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { auth } from "@/lib/auth";

export async function middleware(request: NextRequest) {
  const session = await auth.api.getSession({
    headers: request.headers,
  });

  const isAuthRoute = request.nextUrl.pathname.startsWith("/(auth)");
  const isPublicRoute = ["/", "/pricing", "/about"].includes(request.nextUrl.pathname);

  if (!session && !isPublicRoute && !isAuthRoute) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/webhooks).*)"],
};
```

---

## Stripe Integration

```typescript
// lib/stripe.ts
import Stripe from "stripe";

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2024-12-18.acacia",
  typescript: true,
});
```

### Webhook Handler

```typescript
// app/api/webhooks/stripe/route.ts
import { stripe } from "@/lib/stripe";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import Stripe from "stripe";

export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get("stripe-signature")!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return new Response("Invalid signature", { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed":
      // Handle successful payment
      break;
    case "customer.subscription.updated":
      // Handle subscription changes
      break;
  }

  return new Response(null, { status: 200 });
}
```

**Critical**: Always verify webhook signatures. Never trust raw payload.

---

## What We Don't Do (and Why)

| ❌ Don't | Why |
|----------|-----|
| Use `any` type | Defeats TypeScript. Use `unknown` + narrowing. |
| Fetch in `useEffect` | Server Components fetch server-side. `useEffect` fetch = loading spinners + waterfalls. |
| Use `pages/` router | App Router is the future. Pages Router is maintenance mode. |
| Store sessions in JWT | JWTs in cookies are hard to revoke. Database sessions are safer and simpler. |
| Use Prisma with SQLite | Prisma's SQLite adapter is slow and limited. Drizzle is faster, smaller, SQLite-native. |
| Use CSS-in-JS | Runtime cost, SSR complexity. Tailwind is zero-runtime and co-located. |
| Use global state (Redux, Zustand) | Server Components + Server Actions eliminate most client state needs. Use `useActionState` + URL state. |
| Auto-increment IDs | Leaks record count, guessable. CUID2/UUID for all public IDs. |
| Hand-edit migrations | Drizzle generates them. Hand edits break the diff engine. |
| `export default` functions | Named exports only. Default exports make grep/refactor harder. |
| Use `console.log` in production | Use a logger (pino) or remove. `console.log` leaks to client in some contexts. |
| Import from `../..` | Always use `@/` alias. Relative imports break when files move. |
| Put business logic in components | Components render UI. `lib/` handles logic. Keep the boundary clean. |

---

## Dev Commands

```bash
pnpm dev              # Start dev server (Turbopack, http://localhost:3000)
pnpm build            # Production build (catches type errors + lint)
pnpm start            # Run production server
pnpm lint             # ESLint check
pnpm lint:fix         # ESLint auto-fix
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply migrations
pnpm db:push          # Push schema directly (dev shortcut)
pnpm db:studio        # Open Drizzle Studio (DB GUI)
pnpm test             # Run tests (Vitest)
pnpm test:e2e         # Run E2E tests (Playwright)
```

---

## Testing

```typescript
// __tests__/invoice.test.ts
import { describe, it, expect } from "vitest";
import { createInvoice } from "@/app/(dashboard)/invoices/actions";

describe("createInvoice", () => {
  it("rejects negative amounts", async () => {
    const formData = new FormData();
    formData.set("amount", "-100");
    formData.set("description", "Test");

    const result = await createInvoice(formData);
    expect(result?.error).toBeDefined();
  });
});
```

- **Unit tests**: Vitest, co-located in `__tests__/` or `.test.ts` files.
- **E2E tests**: Playwright, in `e2e/` directory.
- **No snapshot tests**: Brittle, hard to debug, incentivize wrong behavior.
- **Test behavior, not implementation**: Test what the function returns, not how it calls DB.

---

## Git Conventions

- **Branch naming**: `feat/short-description`, `fix/issue-number`, `chore/what`
- **Commit format**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR size**: < 300 lines changed. Split large features into stacked PRs.
- **Never commit**: `.env`, `local.db`, `node_modules`, migration files (they're auto-generated, but commit them for team sync)

---

## Environment Variables

```bash
# .env.local (never commit)
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
BETTER_AUTH_SECRET=xxx  # Generate: openssl rand -base64 32
BETTER_AUTH_URL=http://localhost:3000
```

**Validate at startup** with `@t3-oss/env-nextjs` or a simple check:

```typescript
// lib/env.ts
function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value) throw new Error(`Missing env var: ${key}`);
  return value;
}
```

---

## Anti-Patterns to Reject in Code Review

1. **`"use client"` at the top of a page** — You just killed server-side rendering for the entire page tree.
2. **`fetch` in a Server Component to your own API** — Import the function directly. You're on the server.
3. **Storing `Date` objects in state** — Serialize to ISO string. Dates across the server/client boundary are unreliable.
4. **Inline SQL strings** — Use Drizzle's query builder. Raw SQL only for complex queries, and always with parameterized values.
5. **Catching errors with empty catch blocks** — At minimum, log the error. Ideally, return a user-friendly message.
6. **One massive component** — If a component exceeds 150 lines, extract sub-components or a custom hook.

---

*This CLAUDE.md is opinionated by design. Every rule exists because the alternative caused real problems. Modify as needed for your project, but know why you're changing each rule.*
