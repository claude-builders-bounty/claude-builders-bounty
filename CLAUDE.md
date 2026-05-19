# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated, production-ready. Every rule has a reason. Drop this into any greenfield Next.js 15 App Router + SQLite project and Claude Code understands the context without follow-up questions.

---

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | RSC, streaming, server actions built-in |
| Language | TypeScript 5.x (strict) | Catch bugs at compile time, not runtime |
| Database | SQLite via `better-sqlite3` | Zero-config, single-file, fast. Use Turso (libsql) if you need edge replication |
| ORM | Drizzle ORM | Type-safe, lightweight, SQL-first. Not Prisma — Prisma has worse SQLite support and heavier runtime |
| Auth | `next-auth` (Auth.js v5) | De facto standard. Avoid rolling your own |
| Styling | Tailwind CSS 4 + `clsx` | Utility-first for speed. No CSS-in-JS — it breaks RSC |
| UI | `shadcn/ui` | Accessible, copy-paste components. Not npm install — copy into your project |
| Validation | Zod | Runtime type safety at boundaries (API routes, server actions, forms) |
| Payments | Stripe | Standard. Use `stripe` npm package with webhooks |
| Linting | ESLint (flat config) + Prettier | Enforce conventions. Prettier for formatting, ESLint for logic rules |
| Testing | Vitest + Playwright | Vitest for unit/integration, Playwright for e2e. Not Jest — too slow |

---

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Auth-required routes (route group)
│   │   ├── dashboard/
│   │   └── settings/
│   ├── (marketing)/        # Public routes
│   │   ├── page.tsx        # Landing page
│   │   └── pricing/
│   ├── api/                # Route handlers
│   │   └── webhooks/
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Home
├── components/             # Shared UI components
│   ├── ui/                 # shadcn/ui primitives (button, input, etc.)
│   └── features/           # Feature-specific components
├── db/                     # Database layer
│   ├── schema.ts           # Drizzle schema definitions
│   ├── migrations/         # Drizzle migration files (git-tracked)
│   └── index.ts            # DB connection singleton
├── lib/                    # Business logic
│   ├── auth.ts             # Auth configuration
│   ├── env.ts              # Zod-validated environment variables
│   ├── stripe.ts           # Stripe client
│   └── utils.ts            # Generic helpers (cn, formatDate, etc.)
├── actions/                # Server actions
│   └── ...                 # Grouped by domain (user, billing, etc.)
├── emails/                 # react-email templates
├── hooks/                  # Client-side React hooks
├── types/                  # Shared TypeScript types (if not in db/schema)
└── middleware.ts           # Next.js middleware (auth, redirects)
```

**Rules:**
- Server-only code lives in `db/`, `lib/`, `actions/` — NEVER import these into client components
- Client components get `"use client"` directive at top of file
- Route groups in `app/` use parentheses `()` — they don't affect URL
- Every new domain gets its own folder under `components/features/`

---

## SQL / Migration Conventions

### Schema Design
- **Use UUIDs for primary keys**, not auto-increment integers. Safer for multi-tenant and prevents enumeration attacks.
  ```ts
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID())
  ```
- **All tables must include `createdAt` and `updatedAt` timestamps.**
- **Soft deletes preferred over hard deletes.** Add `deletedAt` column for data-sensitive tables.
- **Use foreign keys** — SQLite supports them with `PRAGMA foreign_keys = ON`.

### Migrations
- **Migration files are generated, never hand-written.**
  ```bash
  npx drizzle-kit generate   # Generate
  npx drizzle-kit migrate    # Apply
  ```
- **Migration files live in `db/migrations/` and MUST be git-tracked.**
- **Before merging a PR that changes schema:** run `drizzle-kit generate` and commit the generated SQL.
- **Never modify a migration after it's been applied to production.** Create a new migration instead.
- **Rollback strategy:** write forward-only migrations. Each migration has an "up" — no "down". If you need to revert, write a new migration.

### Query Patterns
- **Use Drizzle's query builder, never raw SQL in application code.** Raw SQL only in migrations.
- **Server Components can access DB directly** — no need for API routes just to fetch data.
- **Wrap DB writes in `db.transaction()`** when touching multiple tables.
- **Server actions for mutations, not API routes.** Server actions handle CSRF automatically.

---

## Component Patterns

### Server Components (default)
- **Always default to Server Components.** Only add `"use client"` when you need interactivity.
- **Server Components can be async** — fetch data directly:
  ```tsx
  export default async function Dashboard() {
    const user = await getUser();
    const projects = await db.query.projects.findMany({ where: eq(projects.ownerId, user.id) });
    return <ProjectsList projects={projects} />;
  }
  ```

### Client Components
- **Mark with `"use client"` at the absolute top** (before imports).
- **Keep them at the leaf nodes** of the component tree.
- **Pass data from Server → Client as props** (serializable — no functions, no class instances).
- **Use `useActionState` for form state**, not manual useState + onSubmit.

### State Management
- **URL is the primary state manager.** Use `useSearchParams` + `useRouter`.
- **React Context for UI state** (theme, sidebar open, modal visibility).
- **No Redux, no Zustand.** Overkill for SaaS. Context + URL handles 95% of cases.
- **Server state = cached DB queries.** Use `unstable_cache` or React `cache()` for deduplication.

### Naming
- **Files:** kebab-case (`user-profile.tsx`)
- **Components:** PascalCase (`UserProfile`)
- **Functions:** camelCase (`getUserById`)
- **DB tables:** snake_case (`user_profiles`)
- **DB columns:** camelCase (Drizzle default) — `ownerId`, `stripeCustomerId`
- **Server actions:** `verbNoun` pattern — `createProject`, `updateBilling`, `deleteMember`

---

## Auth Conventions

- **Use middleware.ts for route protection**, not per-page checks:
  ```ts
  export { auth as middleware } from "@/lib/auth";
  export const config = { matcher: ["/dashboard/:path*", "/settings/:path*"] };
  ```
- **Get session in Server Components:** `const session = await auth()`
- **Get session in API routes:** same as above
- **Never expose `session.user.id` to the client** unless necessary. Pass it to server actions via closure.
- **Client-side auth status:** use `useSession()` from next-auth/react — but only in client components.

---

## What We DON'T Do (and Why)

| Anti-pattern | Why not |
|-------------|---------|
| `export default` for utilities | Named exports enable better tree-shaking and IDE autocomplete |
| `any` type in TypeScript | Defeats the purpose. If truly unknown, use `unknown` and type-narrow |
| API routes for data fetching | Server Components fetch data directly. API routes are for webhooks and external consumers |
| `useEffect` for data fetching | Use Server Components, server actions, or React Query for client-side fetching |
| Environment variables without Zod validation | Runtime crash on deploy is worse than startup crash. Validate in `lib/env.ts` |
| Large barrel exports (`export * from "./foo"`) | Slows down bundler and makes tree-shaking harder. Export explicitly |
| CSS-in-JS (styled-components, emotion) | Breaks Server Components, adds runtime overhead. Tailwind is sufficient |
| Prisma with SQLite | Prisma's SQLite support is inferior. Better-sqlite3 + Drizzle is faster and more SQL-native |
| Multiple ORMs in one project | Pick one. Mixing leads to inconsistent patterns and migration conflicts |

---

## Dev Commands

```bash
# Setup
npm install
cp .env.example .env    # Fill in required values
npx drizzle-kit generate  # Create initial migration
npx drizzle-kit migrate   # Apply to local SQLite

# Development
npm run dev               # Next.js dev server (localhost:3000)
npm run db:studio         # Drizzle Studio (localhost:4983)

# Testing
npm run test              # Vitest (unit + integration)
npm run test:e2e          # Playwright (requires dev server running)

# Pre-commit
npm run lint              # ESLint
npm run format            # Prettier
npm run typecheck         # tsc --noEmit

# Production
npm run build             # Next.js build
npm run start             # Start production server
npx drizzle-kit migrate   # Apply migrations to production (before deploy)
```

---

## File Template: New Server Action

```typescript
// src/actions/projects/create-project.ts
"use server";

import { revalidatePath } from "next/cache";
import { auth } from "@/lib/auth";
import { db } from "@/db";
import { projects } from "@/db/schema";
import { createProjectSchema } from "./schemas";

export async function createProject(formData: FormData) {
  const session = await auth();
  if (!session?.user?.id) throw new Error("Unauthorized");

  const parsed = createProjectSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };

  const [project] = await db.insert(projects).values({
    ...parsed.data,
    ownerId: session.user.id,
  }).returning();

  revalidatePath("/dashboard");
  return { project };
}
```

---

*Last updated: 2026-05-19 · Drop this file into any greenfield Next.js 15 + SQLite project root.*
