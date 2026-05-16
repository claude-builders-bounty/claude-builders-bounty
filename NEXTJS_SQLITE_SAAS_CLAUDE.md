# CLAUDE.md — SaaS Starter (Next.js 15 + SQLite)

> This file tells Claude Code everything it needs to contribute without asking
> clarifying questions. Every rule has a reason. Keep it up to date with reality.

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | RSC, streaming, server actions |
| Language | TypeScript (strict) | Catch bugs at build time |
| Database | SQLite via `better-sqlite3` | Zero-ops, single-file, fast enough for 99% of SaaS |
| ORM | Drizzle ORM | Type-safe, lightweight, generates migrations |
| Auth | Clerk (or NextAuth v5) | Hosted auth is one less thing to maintain |
| UI | Tailwind CSS + shadcn/ui | Copied components — full control, no dependency lock-in |
| Validation | zod | TypeScript-first, composable schemas |
| Payments | Stripe | Mature, handles billing complexity |
| Forms | react-hook-form + @hookform/resolvers | Performant, zod integration |
| Email | Resend + react-email | Preview emails as React components |
| Testing | Vitest + Playwright | Fast unit tests, real browser E2E |
| Linting | Biome | One tool for format + lint, faster than ESLint/Prettier |

**Version pins:**
```json
{
  "next": "^15.1.0",
  "better-sqlite3": "^11.0.0",
  "drizzle-orm": "^0.38.0",
  "drizzle-kit": "^0.30.0",
  "tailwindcss": "^4.0.0"
}
```

## Project Structure

```
src/
├── app/                    # App Router pages & layouts
│   ├── (auth)/             # Auth route group (login, signup, onboarding)
│   ├── (dashboard)/        # Authenticated route group
│   │   ├── layout.tsx      # Dashboard shell (sidebar, header)
│   │   └── (routes)/       # Feature routes
│   ├── api/                # API routes (webhooks, external callbacks)
│   └── layout.tsx          # Root layout (providers, fonts)
├── lib/
│   ├── db/                 # Database
│   │   ├── schema/         # Drizzle table definitions (one file per domain)
│   │   ├── migrations/     # SQL migration files (auto-generated)
│   │   └── index.ts        # Database connection singleton
│   ├── auth/               # Auth helpers, middleware, permissions
│   ├── billing/            # Stripe integration (checkout, portal, webhooks)
│   └── utils/              # Shared utilities (cn(), formatCurrency(), etc.)
├── components/
│   ├── ui/                 # shadcn/ui primitives (automatic)
│   ├── forms/              # Reusable form components
│   └── features/           # Feature-specific components
├── hooks/                  # Shared React hooks
├── emails/                 # react-email templates
├── types/                  # Shared TypeScript types
└── server/                 # Server-only code (actions, queries, mutations)
    ├── actions/            # Server actions (one file per domain)
    └── queries/            # Database query functions
```

## Database Conventions (CRITICAL)

### Schema Design

- **One table per file** in `src/lib/db/schema/`. File name = table name.
- **Plural table names**: `users`, `teams`, `subscriptions` — not `user`, `team`.
- **Always define `createdAt` and `updatedAt`** on every table. Use Drizzle's `$onUpdate` for `updatedAt`.
- **Foreign keys are mandatory** — define them with `references()`.
- **Soft deletes** via `deletedAt` column (nullable timestamp). Never hard-delete user data.
- **Enums as string unions** in TypeScript, stored as TEXT in SQLite (SQLite has no native enum).

### Migration Rules

1. **Never edit existing migration files.** They are append-only history.
2. Generate with `npx drizzle-kit generate`, then review the SQL before applying.
3. **Always make migrations additive.** Adding columns with defaults is safe. Renaming/deleting columns requires a multi-step migration.
4. For destructive changes: add new column → migrate data in application code → mark old column `@deprecated` → remove in next major version.
5. Run migrations on app startup: `import './lib/db/migrate'` in your root layout or instrumentation hook.

### Query Patterns

- **Server components** fetch data directly: `await db.select().from(users)`.
- **Server actions** handle mutations. Never expose raw SQL to the client.
- **Use Drizzle's relational queries** (`db.query.users.findMany({ with: {...} })`) instead of manual JOINs.
- **Never use raw SQL** except in migrations. Drizzle is the single source of truth for your schema.

## Component Patterns

### The "Server Component First" Rule

Start every new page as a **server component**. Only add `'use client'` when you need:
- Event handlers (`onClick`, `onChange`)
- Hooks (`useState`, `useEffect`, custom hooks)
- Browser APIs (`localStorage`, `window`)
- Context providers

### Data Flow

```
Server Component (fetch data)
    ↓ props
Client Component (render UI, handle interactions)
    ↓ server action
Server Action (mutate data, revalidate)
    ↓ revalidatePath()
Server Component (re-render with fresh data)
```

### Form Pattern

```tsx
// Define schema (src/lib/validations/team.ts)
export const createTeamSchema = z.object({
  name: z.string().min(2).max(50),
  slug: z.string().regex(/^[a-z0-9-]+$/),
});

// Server action (src/server/actions/team.ts)
'use server';
export async function createTeam(input: z.infer<typeof createTeamSchema>) {
  const parsed = createTeamSchema.safeParse(input);
  if (!parsed.success) return { error: parsed.error.flatten() };

  const user = await getCurrentUser();
  if (!user) return { error: 'Unauthorized' };

  await db.insert(teams).values({ ...parsed.data, ownerId: user.id });
  revalidatePath('/dashboard');
  return { success: true };
}

// Client form (src/components/forms/create-team-form.tsx)
'use client';
// Uses react-hook-form with zodResolver, calls server action on submit
```

## What We DON'T Do (and Why)

### ❌ Don't use API Routes for internal logic
**Why:** Server actions are simpler, typesafe end-to-end, and automatically handle CSRF. API routes exist only for external callbacks (Stripe webhooks, OAuth).

### ❌ Don't use `any` or `as` type assertions
**Why:** We're in strict TypeScript. If you need `as`, the types are wrong — fix them instead. `any` masks bugs.

### ❌ Don't use `useEffect` for data fetching
**Why:** Server components fetch data without client JavaScript. `useEffect` fetching causes waterfalls, layout shifts, and SEO problems.

### ❌ Don't put secrets in client components
**Why:** `NEXT_PUBLIC_*` is readable by anyone. All secrets stay server-side. No exceptions.

### ❌ Don't use ORM features that generate inefficient SQL
**Why:** SQLite optimization relies on understanding the query plan. If a Drizzle query generates a suboptimal plan, write a raw query in a dedicated query file with an `EXPLAIN QUERY PLAN` comment.

### ❌ Don't use `SELECT *` without listing columns
**Why:** Explicit column selection prevents accidental data exposure and makes unused-column detection possible.

### ❌ Don't version control `.env` or `.env.local`
**Why:** Obvious, but worth stating. Use `.env.example` with dummy values and comments.

## Dev Commands

```bash
# Development
npm run dev              # Next.js dev server (Turbopack)
npm run db:studio        # Drizzle Studio (visual DB browser)
npm run db:generate      # Generate migration from schema changes
npm run db:migrate       # Apply migrations
npm run db:push          # Push schema directly (dev only, no migration)

# Testing
npm run test             # Vitest unit tests
npm run test:e2e         # Playwright E2E tests

# Quality
npm run lint             # Biome lint
npm run format           # Biome format
npm run typecheck        # tsc --noEmit

# Stripe
npm run stripe:listen    # Stripe CLI webhook forwarding
npm run stripe:trigger   # Trigger test webhook events
```

## Environment Variables

```bash
# Required
DATABASE_URL="data/saas.db"           # SQLite file path

# Auth (Clerk)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=

# Auth (NextAuth) — alternative
# AUTH_SECRET=
# AUTH_GOOGLE_ID=
# AUTH_GOOGLE_SECRET=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PRICE_PRO_ID=

# Email (Resend)
RESEND_API_KEY=

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

## When You're Stuck

1. Check `src/lib/db/schema/` — the schema is the source of truth
2. Run `npm run typecheck` — TypeScript will tell you what's wrong
3. Check existing server actions for the mutation pattern
4. Look at shadcn/ui examples for component patterns
5. This CLAUDE.md is the rulebook — if something isn't covered, add it
