# CLAUDE.md

> **Stack:** Next.js 15 App Router · TypeScript (strict) · SQLite (Turso / better-sqlite3) · Prisma ORM · Tailwind CSS · shadcn/ui · React 19
>
> **Target audience:** AI coding assistants (Claude, Copilot, Cursor, etc.) and human developers onboarding onto the project.
>
> **Use:** Copy this file into the root of your Next.js 15 SaaS project. No modification required.

---

## 1. Project Structure

```
src/
├── app/                        # App Router — file-system routes
│   ├── layout.tsx              # Root layout (metadata, providers, shell)
│   ├── page.tsx                # Home page (server component by default)
│   ├── (auth)/                 # Route group — no URL prefix
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/            # Route group — protected pages
│   │   ├── layout.tsx          # Dashboard shell (sidebar, nav)
│   │   ├── dashboard/page.tsx
│   │   └── settings/page.tsx
│   └── api/                    # Route handlers (REST / webhooks)
│       └── webhooks/stripe/route.ts
├── components/                 # Shared UI components
│   ├── ui/                     # shadcn/ui primitives (button, card, input, ...)
│   └── features/               # Feature-specific composed components
│       ├── billing/
│       └── teams/
├── lib/                        # Pure utilities, no React imports
│   ├── auth.ts                 # Auth configuration (NextAuth / Lucia / Clerk)
│   ├── db.ts                   # Prisma client singleton + edge detection
│   ├── email.ts                # Email sending helper (Resend, Postmark, etc.)
│   └── utils.ts                # Generic helpers (cn, formatDate, slugify, ...)
├── server/                     # Server-only code (never imported from "use client")
│   ├── actions/                # Server Actions — one file per domain
│   │   ├── auth.ts
│   │   ├── billing.ts
│   │   └── teams.ts
│   ├── queries/                # Data-fetching functions (cached, composable)
│   │   ├── teams.ts
│   │   └── users.ts
│   └── services/               # Business logic shared by actions & jobs
│       ├── stripe.ts
│       └── email.ts
├── hooks/                      # Client hooks (useFormState, useOptimistic wrappers, ...)
│   └── use-debounce.ts
├── jobs/                       # Background / cron jobs (QStash, Inngest, BullMQ)
│   └── billing-sync.ts
├── emails/                     # React-email templates
│   └── welcome.tsx
└── instrumentation.ts          # OpenTelemetry / observability setup
```

**Reasons:**
- `src/` keeps config files out of the root import namespace and shortens deep `../../` imports.
- Route groups `(auth)`/`(dashboard)` isolate layouts without affecting URLs — avoids layout prop-drilling.
- `server/actions`, `server/queries`, `server/services` form three clear layers (HTTP boundary → data access → business logic). No business logic in components.
- `jobs/` and `emails/` are top-level because they are not request-scoped.

---

## 2. File & Component Naming

### 2.1 Files

| Pattern | Example | Reason |
|---|---|---|
| Pages: `app/<segment>/page.tsx` | `app/settings/billing/page.tsx` | Next.js convention — enforced by framework. |
| Layouts: `layout.tsx` | `app/(dashboard)/layout.tsx` | Next.js convention. |
| Route handlers: `route.ts` | `app/api/webhooks/stripe/route.ts` | Next.js convention. |
| Server components: no suffix | `app/dashboard/page.tsx` | Server is the default; no suffix needed. |
| Client components: no suffix, `"use client"` at top | `components/features/billing/subscribe-button.tsx` | The `"use client"` directive is the marker. |
| Actions: `server/actions/<domain>.ts` | `server/actions/teams.ts` | One file per domain keeps actions discoverable. |
| Queries: `server/queries/<domain>.ts` | `server/queries/teams.ts` | Colocate read and write — different files, same domain. |
| Services: `server/services/<domain>.ts` | `server/services/stripe.ts` | Third-party integrations isolated from app logic. |
| Configs: `config/<thing>.ts` | `config/plans.ts` | Static configuration that rarely changes. |
| Types: colocated, not in a single `types.ts` | `lib/auth.ts` exports its own types | Avoid "junk drawer" type files. |

### 2.2 Components

```tsx
// Default export for pages and layouts
export default function DashboardPage() { ... }

// Named export for everything else
export function SubscribeButton() { ... }
```

- **Component name = file name** (PascalCase). `subscribe-button.tsx` → `<SubscribeButton />`.
- **One component per file** unless a private sub-component is <20 lines and never reused.
- **No `I` prefix for interfaces**, no `T` for types. Use `type` by default, `interface` only when you need declaration merging (rare).

**Reasons:**
- Named exports for shared components make renaming safe (IDE refactoring works).
- Default exports for pages are a Next.js de facto convention.
- Colocating types with their owning module prevents circular imports and keeps types close to usage.

---

## 3. Database Rules

### 3.1 Provider: SQLite (Prisma)

```
prisma/
├── schema.prisma              # Single schema — all models in one file
├── migrations/                 # Auto-generated by `prisma migrate dev`
│   ├── 0001_init/
│   └── 0002_add_teams/
└── seed.ts                    # Idempotent seed script
```

### 3.2 Rules

1. **All migrations MUST be created with `npx prisma migrate dev --name <descriptive_kebab_case>`.**  
   *Reason:* Ensures migrations are repeatable, reversible where possible, and version-controlled.

2. **Never edit a migration that has been committed to `main`.** Create a new migration instead.  
   *Reason:* Editing applied migrations breaks teammate/CI databases. Treat migrations as append-only.

3. **Every model must have `createdAt` and `updatedAt` fields.**  
   *Reason:* Universal audit baseline for debugging, reporting, and soft-deletion logic.

   ```prisma
   model User {
     id        String   @id @default(cuid())
     email     String   @unique
     createdAt DateTime @default(now())
     updatedAt DateTime @updatedAt
   }
   ```

4. **Use `@map` and `@@map` for all tables and columns.** Always snake_case in the database, camelCase in TypeScript.  
   *Reason:* SQLite convention is snake_case; JavaScript convention is camelCase. Explicit mapping prevents Prisma from coupling your JS naming to your DB schema.

   ```prisma
   model UserAccount {
     @@map("user_accounts")
     userId String @map("user_id")
   }
   ```

5. **Soft-delete with `deletedAt DATETIME NULL`, never hard-delete user data.**  
   *Reason:* Data recovery, audit compliance, and avoiding cascading delete surprises. Hard-delete is acceptable for ephemeral data (sessions, tokens, rate-limit counters).

6. **Foreign keys: always define `ON DELETE` / `ON UPDATE` explicitly.**  
   *Reason:* SQLite defaults to `NO ACTION` which can cause confusing errors. Be intentional.

7. **No raw SQL in application code.** Use Prisma Client for everything. If you need a raw query, use `prisma.$queryRaw` inside a `server/queries/` or `server/services/` file with a `// SAFETY:` comment explaining why Prisma Client is insufficient.  
   *Reason:* Prisma Client provides type safety, migration-aware query building, and protection against SQL injection. Raw SQL bypasses all three.

8. **Seed data must be idempotent.** Use `upsert` or a unique seed key, never `create` directly.  
   *Reason:* `npx prisma db seed` should be safe to run multiple times.

9. **Use `cuid()` for primary keys, not autoincrement integers.**  
   *Reason:* CUIDs can be generated client-side (optimistic inserts), are globally unique (no collision risk in multi-writer setups), and do not leak row counts. For Turso/LibSQL, UUID v4 is also acceptable.

10. **Keep the Prisma schema as the single source of truth.** Do not maintain a separate SQL schema file.  
    *Reason:* Prisma's `prisma migrate` is the migration engine; a parallel SQL file inevitably drifts.

### 3.3 Dev Commands (Database)

| Command | Purpose |
|---|---|
| `npx prisma generate` | Regenerate client after schema changes. Run after `git pull` if schema changed. |
| `npx prisma migrate dev --name <name>` | Create + apply a migration. Always use in dev. |
| `npx prisma migrate deploy` | Apply pending migrations in CI/production. Never creates new migrations. |
| `npx prisma db seed` | Seed the database. Idempotent. |
| `npx prisma studio` | GUI database browser on `localhost:5555`. |
| `npx prisma migrate reset` | **Nukes the DB** and re-runs all migrations + seed. Dev only. |

---

## 4. Dev Commands

```bash
# Development
npm run dev                   # Start Next.js dev server (Turbopack)
npm run dev -- --port 3001    # On a different port

# Database
npx prisma generate           # Rebuild client after schema changes
npx prisma migrate dev        # Create + apply migration
npx prisma db seed            # Seed the database
npx prisma studio             # GUI at localhost:5555

# Quality
npm run lint                  # ESLint (flat config)
npm run format                # Prettier
npm run type-check            # tsc --noEmit
npm run test                  # Vitest (unit + integration)
npm run test:e2e              # Playwright (end-to-end)

# Build & Production
npm run build                 # Next.js production build
npm start                     # Start production server (must build first)
```

**Reasons:**
- `npm run type-check` is separate from `build` because `next build` skips some type checking for speed. Run `type-check` in CI.
- `format` is separate from `lint` — Prettier for formatting, ESLint for logic/style rules.
- `test` and `test:e2e` are separate suites: Vitest for fast unit/integration, Playwright for browser tests.

### 4.1 CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
- npm ci
- npx prisma generate
- npm run lint
- npm run format -- --check
- npm run type-check
- npm run test -- --coverage
- npm run build
- npm run test:e2e
```

---

## 5. Patterns to Follow

### 5.1 Server Components First

**Rule:** Every component is a Server Component unless it needs interactivity (event handlers, state, effects, browser APIs, or custom hooks).

```tsx
// ✅ Good: Server Component — fetches data directly, no client JS
// app/dashboard/page.tsx
import { getTeams } from "@/server/queries/teams";

export default async function DashboardPage() {
  const teams = await getTeams();
  return <TeamList teams={teams} />;
}
```

**Reason:** Server Components reduce client JS, eliminate API boilerplate, and can call databases/microservices directly without exposing endpoints. They are the default in Next.js 15 App Router.

### 5.2 Server Actions for Mutations

**Rule:** All data mutations (create, update, delete) go through Server Actions. Never expose a `POST` route handler for a form submit when a Server Action will do.

```tsx
// ✅ Good
// server/actions/teams.ts
"use server";
import { db } from "@/lib/db";
import { revalidatePath } from "next/cache";
import { z } from "zod";

const schema = z.object({ name: z.string().min(3).max(50) });

export async function createTeam(formData: FormData) {
  const { name } = schema.parse(Object.fromEntries(formData));
  await db.team.create({ data: { name } });
  revalidatePath("/dashboard");
}
```

```tsx
// ✅ Good: Client form using the Server Action
// components/features/teams/create-team-form.tsx
"use client";
import { createTeam } from "@/server/actions/teams";

export function CreateTeamForm() {
  return (
    <form action={createTeam}>
      <input name="name" required />
      <button type="submit">Create</button>
    </form>
  );
}
```

**Reasons:**
- Server Actions are progressively enhanced — forms work without JavaScript.
- They are type-safe end-to-end (no fetch/body/headers boilerplate).
- They integrate with `revalidatePath`/`revalidateTag` for automatic cache invalidation.

### 5.3 Optimistic Updates with `useOptimistic`

**Rule:** For instant-feel UIs, use `useOptimistic` to update the UI before the server responds. Always provide a fallback (the server state is the source of truth).

```tsx
// ✅ Good: Optimistic UI for adding an item
"use client";
import { useOptimistic, startTransition } from "react";
import { createTeam } from "@/server/actions/teams";

export function TeamList({ teams: initialTeams }: { teams: Team[] }) {
  const [optimisticTeams, addOptimisticTeam] = useOptimistic(
    initialTeams,
    (state, newTeam: Team) => [...state, newTeam]
  );

  async function handleCreate(formData: FormData) {
    startTransition(async () => {
      addOptimisticTeam({ id: "temp", name: formData.get("name") as string });
      await createTeam(formData);
    });
  }

  return (/* render optimisticTeams */);
}
```

**Reason:** Optimistic UI eliminates perceived latency. Wrapping in `startTransition` marks the update as interruptible so React can prioritize user input over rendering.

### 5.4 Data Fetching — Server Queries

**Rule:** Fetch data in Server Components using dedicated query functions. Use React `cache()` for deduplication within a request, and `unstable_cache` (Next.js cache) for cross-request caching.

```tsx
// ✅ Good: Dedicated query function
// server/queries/teams.ts
import { cache } from "react";
import { db } from "@/lib/db";

export const getTeams = cache(async () => {
  return db.team.findMany({ orderBy: { createdAt: "desc" } });
});

export const getTeam = cache(async (id: string) => {
  return db.team.findUnique({ where: { id } });
});
```

**Reason:** `cache()` deduplicates multiple calls to the same query within a single render pass (e.g., a layout AND a page both calling `getTeams()`). Query functions are composable — `getTeam` can call `getTeams` if needed.

### 5.5 Error Handling

**Rule:** Use error boundaries for unexpected errors, return typed results for expected errors.

```tsx
// ✅ Good: Typed result for expected errors (validation, not-found, auth)
type ActionResult<T> = { ok: true; data: T } | { ok: false; error: string };

export async function createTeam(formData: FormData): Promise<ActionResult<Team>> {
  try {
    const parsed = schema.safeParse(Object.fromEntries(formData));
    if (!parsed.success) return { ok: false, error: parsed.error.message };
    const team = await db.team.create({ data: parsed.data });
    return { ok: true, data: team };
  } catch (e) {
    return { ok: false, error: "Failed to create team" };
  }
}
```

```tsx
// ✅ Good: Error boundary for unexpected errors in Server Components
// app/dashboard/error.tsx
"use client";
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return <div>Something went wrong. <button onClick={reset}>Try again</button></div>;
}
```

**Reason:** Typed results let the caller handle known failure modes gracefully without try/catch in every component. Error boundaries catch the rest and provide a user-facing fallback.

### 5.6 Loading States

**Rule:** Every async page that can take >100ms must have a `loading.tsx` sibling. Use `Suspense` for granular loading boundaries within a page.

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return <DashboardSkeleton />;
}

// app/dashboard/page.tsx
import { Suspense } from "react";

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<TeamsSkeleton />}>
        <TeamsList />
      </Suspense>
      <Suspense fallback={<ActivitySkeleton />}>
        <ActivityFeed />
      </Suspense>
    </div>
  );
}
```

**Reason:** `loading.tsx` provides instant navigation feedback (layouts persist). `Suspense` boundaries let fast content render immediately while slow content streams in — users see a partially complete page instead of a blank screen.

### 5.7 Authentication — Middleware Guard

**Rule:** Protect routes in `middleware.ts`, not in layouts or pages. Use a route group `(dashboard)` with a shared middleware check.

```tsx
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const session = request.cookies.get("session");
  if (!session && request.nextUrl.pathname.startsWith("/(dashboard)")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
}

export const config = {
  matcher: ["/(dashboard)/:path*"],
};
```

**Reason:** Middleware runs on the edge before any component renders — no layout flash, no client-side redirect, no loading skeleton for a page you can't access. Route groups make the matcher trivial.

### 5.8 Environment Variables

**Rule:** All env vars are validated at startup with a single `env.ts` file. Use `T3_ENV` validation pattern.

```ts
// config/env.ts
import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    DATABASE_URL: z.string().url(),
    STRIPE_SECRET_KEY: z.string().min(1),
  },
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
  },
  runtimeEnv: {
    DATABASE_URL: process.env.DATABASE_URL,
    STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
});
```

**Reason:** Validating env vars at startup surfaces misconfiguration immediately (fail-fast) instead of discovering it deep in a request. `NEXT_PUBLIC_*` prefix is required for client exposure — the validator enforces this boundary.

---

## 6. Anti-Patterns — Do NOT Do These

### ❌ Client-Side Data Fetching

```tsx
// ❌ WRONG: useEffect + fetch in a Client Component
"use client";
import { useEffect, useState } from "react";

export function TeamList() {
  const [teams, setTeams] = useState([]);
  useEffect(() => {
    fetch("/api/teams").then(r => r.json()).then(setTeams);
  }, []);
  return <ul>{teams.map(t => <li key={t.id}>{t.name}</li>)}</ul>;
}
```

**Why it's wrong:** Doubles the network waterfall (HTML → JS → fetch → render), leaks API endpoints, breaks SEO, adds unnecessary client-side state management, and disables streaming. Every one of these problems vanishes with a Server Component that calls `getTeams()` directly.

### ❌ Route Handlers for Internal Data Operations

```tsx
// ❌ WRONG: Creating an API route for internal use
// app/api/teams/route.ts
export async function POST(req: Request) {
  const body = await req.json();
  const team = await db.team.create({ data: body });
  return Response.json(team);
}
```

**Why it's wrong:** Introduces an unnecessary HTTP layer between your UI and database. You must manually handle serialization, authentication, validation, error formatting, and CORS. Server Actions do all of this automatically via the framework.

### ❌ `useEffect` for Data or Derived State

```tsx
// ❌ WRONG: useEffect for derived state
const [fullName, setFullName] = useState("");
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// ❌ WRONG: useEffect to sync server data
useEffect(() => {
  setLocalItems(serverItems);
}, [serverItems]);
```

**Why it's wrong:** Causes an extra render pass (render → effect → re-render), can lead to stale UI flashes, and is a common source of infinite loops. Derived state should be computed inline (`const fullName = \`${firstName} ${lastName}\``). Server data should be passed as props from a parent Server Component.

### ❌ Prop Drilling for Global State

```tsx
// ❌ WRONG: Threading `user` and `team` through 5 levels of components
<Sidebar user={user} team={team}>
  <Nav user={user} team={team}>
    <NavItem user={user} team={team} />
  </Nav>
</Sidebar>
```

**Why it's wrong:** Makes refactoring painful and components tightly coupled. Use a Server Component to fetch the data and pass it to the specific leaf component that needs it, or use React Context for truly global client state (theme, locale). Next.js App Router lets you colocate data fetching with the consuming component — use it.

### ❌ Business Logic in Components

```tsx
// ❌ WRONG: Formatting prices, calling APIs, validating data inside a component
export function PricingCard({ price }: { price: number }) {
  const formatted = (price / 100).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
  });
  const isAffordable = price < 5000;
  // ...
}
```

**Why it's wrong:** Not testable in isolation, not reusable, and mixes presentation with logic. Extract to `lib/formatting.ts` or `server/services/billing.ts`.

### ❌ Ignoring Caching Semantics

```tsx
// ❌ WRONG: Always fetching fresh data, never caching
export async function getTeams() {
  return db.team.findMany(); // Called fresh on every render
}
```

**Why it's wrong:** Unnecessary database load. Wrap in `cache()` for request deduplication and consider `unstable_cache` with `revalidateTag` for cross-request caching. Every query should have a deliberate caching strategy.

### ❌ Single `types.ts` or `utils.ts` Dump

**Why it's wrong:** Grows unbounded, creates import cycles, makes it impossible to tree-shake or reason about dependencies. Colocate types with their owning module.

### ❌ Skipping `loading.tsx` for Slow Pages

**Why it's wrong:** Users stare at a blank white screen during page transitions. Always provide a skeleton/loading state.

### ❌ Hard-Deleting User Data

**Why it's wrong:** Impossible to recover from accidental deletion, breaks audit trails, violates GDPR "right to access" if you can't reproduce what was deleted. Always soft-delete with `deletedAt`.

---

## 7. Package Versions (Baseline)

| Package | Version | Purpose |
|---|---|---|
| `next` | `^15.x` | Framework |
| `react` / `react-dom` | `^19.x` | UI library |
| `typescript` | `^5.x` | Type checking |
| `prisma` / `@prisma/client` | `^6.x` | ORM + type-safe client |
| `tailwindcss` | `^4.x` | Utility CSS |
| `@t3-oss/env-nextjs` | `^0.12.x` | Env var validation |
| `zod` | `^3.x` | Schema validation |
| `vitest` | `^3.x` | Unit/integration testing |
| `playwright` | `^1.x` | E2E testing |
| `prettier` | `^3.x` | Code formatting |
| `eslint` | `^9.x` | Linting (flat config) |
| `lucide-react` | `latest` | Icons |
| `next-auth` (or `@clerk/nextjs`) | `^5.x` | Authentication |

---

## 8. Quick-Start Checklist

When starting a new greenfield feature, run through these steps:

1. **Define the Prisma model** → `prisma migrate dev --name add_<feature>`
2. **Write the query** → `server/queries/<domain>.ts` (cached)
3. **Write the server action(s)** → `server/actions/<domain>.ts` (validated, revalidated)
4. **Build the page** → `app/<route>/page.tsx` (Server Component, calls query)
5. **Add loading.tsx** → `app/<route>/loading.tsx` (skeleton)
6. **Add error.tsx** → `app/<route>/error.tsx` (error boundary)
7. **Build interactive parts** → `"use client"` components with `useOptimistic` where needed
8. **Run type-check** → `npm run type-check`

---

## 9. File Template Snippets

### Server Component Page

```tsx
// app/(dashboard)/teams/page.tsx
import { Suspense } from "react";
import { getTeams } from "@/server/queries/teams";
import { CreateTeamForm } from "@/components/features/teams/create-team-form";
import { TeamsList } from "@/components/features/teams/team-list";

export const metadata = { title: "Teams" };

export default async function TeamsPage() {
  const teams = await getTeams();

  return (
    <div className="space-y-8 p-8">
      <h1 className="text-2xl font-bold">Teams</h1>
      <CreateTeamForm />
      <Suspense fallback={<p>Loading teams...</p>}>
        <TeamsList teams={teams} />
      </Suspense>
    </div>
  );
}
```

### Server Action

```tsx
// server/actions/teams.ts
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import { db } from "@/lib/db";
import { getSession } from "@/lib/auth";

const createTeamSchema = z.object({
  name: z.string().min(3).max(50),
});

export async function createTeam(formData: FormData) {
  const session = await getSession();
  if (!session) redirect("/login");

  const { name } = createTeamSchema.parse(Object.fromEntries(formData));

  await db.team.create({
    data: { name, ownerId: session.userId },
  });

  revalidatePath("/dashboard/teams");
}
```

### Database Query

```tsx
// server/queries/teams.ts
import { cache } from "react";
import { db } from "@/lib/db";

export const getTeams = cache(async (userId: string) => {
  return db.team.findMany({
    where: { ownerId: userId },
    orderBy: { createdAt: "desc" },
  });
});

export const getTeam = cache(async (id: string) => {
  return db.team.findUnique({ where: { id } });
});
```

### Prisma Client Singleton

```tsx
// lib/db.ts
import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const db = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = db;
```

### Client Component with Optimistic Update

```tsx
// components/features/teams/create-team-form.tsx
"use client";

import { useOptimistic, startTransition, useRef } from "react";
import { createTeam } from "@/server/actions/teams";

export function CreateTeamForm() {
  const formRef = useRef<HTMLFormElement>(null);

  async function handleSubmit(formData: FormData) {
    startTransition(async () => {
      await createTeam(formData);
      formRef.current?.reset();
    });
  }

  return (
    <form ref={formRef} action={handleSubmit}>
      <input name="name" required className="border px-3 py-2" />
      <button type="submit">Create Team</button>
    </form>
  );
}
```
