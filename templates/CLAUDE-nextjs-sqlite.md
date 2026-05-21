# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

> Opinionated, production-ready context file for Claude Code.
> Drop this into any greenfield Next.js 15 + SQLite project and Claude Code
> understands the stack, conventions, and constraints immediately.

---

## Stack & Versions

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | ^15.x |
| Language | TypeScript | ^5.6+ |
| Database | SQLite via better-sqlite3 (local dev) or Turso (prod) | ^11.x / @latest |
| ORM | Drizzle ORM | ^0.36+ |
| Auth | NextAuth.js v5 (Auth.js) | ^5.0-beta |
| Styling | Tailwind CSS | ^3.4+ |
| Validation | Zod | ^3.23+ |
| Payments | Stripe | ^latest |
| Email | Resend | ^4.x |
| Hosting | Vercel (primary) / Docker (fallback) | — |

---

## Project Structure

```
src/
├── app/                    # Next.js App Router pages & API routes
│   ├── (auth)/             # Auth route group (login, register, verify)
│   ├── (dashboard)/        # Authenticated dashboard group
│   │   ├── app/            # App-specific pages
│   │   └── settings/       # Account & org settings
│   ├── api/                # API route handlers
│   │   ├── auth/           # NextAuth route
│   │   ├── stripe/         # Stripe webhooks
│   │   └── trpc/           # tRPC or public API
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/             # Shared React components
│   ├── ui/                 # shadcn/ui components (generated)
│   └── features/           # Feature-specific composed components
├── db/                     # Database layer
│   ├── schema.ts           # Drizzle schema definitions
│   ├── migrations/         # Drizzle migration files
│   └── index.ts            # DB client singleton
├── lib/                    # Shared utilities
│   ├── auth.ts             # NextAuth configuration
│   ├── stripe.ts           # Stripe client
│   ├── email.ts            # Resend client
│   └── utils.ts            # General helpers
├── server/                 # Server-only code (data access, actions)
│   ├── actions/            # Server actions (use server)
│   └── queries/            # Database queries
├── stores/                 # Client state (Zustand)
├── types/                  # Shared TypeScript types
└── middleware.ts           # Next.js middleware (auth, rewrites)
```

---

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files (components) | `kebab-case.tsx` or `PascalCase.tsx` | `user-menu.tsx` |
| Files (utilities) | `kebab-case.ts` | `format-currency.ts` |
| React components | `PascalCase` function | `function UserMenu()` |
| Database tables | `snake_case` plural | `user_accounts` |
| Drizzle schemas | `snake_case` plural, exported as camelCase | `export const userAccounts` |
| Server actions | `verbNoun` pattern | `createOrganization`, `updateProfile` |
| API routes | RESTful, `kebab-case` | `/api/orgs/[orgId]/members` |
| TypeScript types | `PascalCase` | `UserProfile`, `SubscriptionTier` |
| Zod schemas | `camelCase` suffixed with `Schema` | `createOrgSchema` |
| Environment vars | `UPPER_SNAKE_CASE` | `DATABASE_URL` |

---

## Database Conventions

### Migrations
- **Always** generate migrations with `drizzle-kit generate` — never edit SQLite files by hand.
- Run `drizzle-kit push` only in local development; use `drizzle-kit migrate` in CI/prod.
- **Never** create a migration that drops a column — SQLite doesn't support it. Use a multi-step approach:
  1. Add new column (nullable)
  2. Backfill data
  3. Stop writing to old column in application code
  4. (Optional) remove old column in a future migration via table rebuild

### Query Patterns
```typescript
// ✅ GOOD: Use Drizzle query builder with proper typing
const user = await db.query.userAccounts.findFirst({
  where: eq(userAccounts.id, userId),
  with: { organization: true },
});

// ✅ GOOD: Use prepared statements for hot-path queries
const getUserByEmail = db.query.userAccounts
  .findFirst({ where: eq(userAccounts.email, sql.placeholder("email")) })
  .prepare();

// ❌ BAD: Raw SQL without parameterization
const user = db.get(`SELECT * FROM user_accounts WHERE id = ${userId}`);
```

### Indexing
- Index every foreign key column.
- Index columns used in `WHERE` clauses on hot paths.
- Use composite indexes for queries that filter on multiple columns.
- Add `EXPLAIN QUERY PLAN` comments above complex queries.

---

## Component Patterns

### Server Components First
- Prefer Server Components by default. Only add `"use client"` when you need:
  - Event handlers (`onClick`, `onChange`)
  - Hooks (`useState`, `useEffect`, `useFormStatus`)
  - Browser APIs (`localStorage`, `window`)
- Fetch data directly in Server Components:
  ```typescript
  // ✅ GOOD: Server Component with direct data access
  export default async function Dashboard() {
    const user = await getCurrentUser();
    const projects = await db.query.projects.findMany({
      where: eq(projects.orgId, user.orgId),
    });
    return <ProjectList projects={projects} />;
  }
  ```

### Client Boundaries
- Keep `"use client"` components as leaves in the tree.
- Pass server-fetched data as props to client components.
- Use server actions for mutations — avoid client-side fetch for form submissions.

### Forms
```typescript
// ✅ GOOD: Server action with Zod validation
"use server";
import { createOrgSchema } from "@/types";

export async function createOrganization(formData: FormData) {
  const parsed = createOrgSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };
  await db.insert(organizations).values(parsed.data);
  revalidatePath("/dashboard");
  return { success: true };
}
```

---

## Dev Commands

```bash
# Development
npm run dev                  # Start Next.js dev server (port 3000)
npm run db:studio            # Open Drizzle Studio (port 4983)
npm run db:generate          # Generate migration from schema changes
npm run db:migrate           # Apply migrations
npm run db:push              # Push schema directly (dev only)
npm run db:seed              # Seed database with sample data

# Quality
npm run lint                 # ESLint
npm run format               # Prettier
npm run type-check           # tsc --noEmit
npm run test                 # Vitest
npm run test:e2e             # Playwright

# Stripe
npm run stripe:listen        # Stripe CLI webhook forwarding
npm run stripe:trigger       # Trigger test webhook events
```

---

## What We Do (and Why)

| Practice | Reason |
|----------|--------|
| Server-first data fetching | Better perf, smaller client bundle, no loading spinners |
| Zod for all input validation | Type-safe runtime validation; shared between client & server |
| Server actions for mutations | Progressive enhancement, works without JavaScript |
| Drizzle over Prisma | Lighter, faster, SQL-like API, better SQLite support |
| SQLite for SaaS | Zero ops for early-stage, easy backup, 1-file database |
| shadcn/ui components | Copy-paste ownership, no dependency lock-in |
| TypeScript strict mode | Catch null/undefined bugs at compile time |
| `revalidatePath` after mutations | Keep UI consistent without full page reloads |

---

## What We Don't Do (and Why)

| Anti-Pattern | Why We Avoid It |
|-------------|-----------------|
| Client-side data fetching (`useEffect` + `fetch`) | Waterfalls, flash of loading, SEO penalty |
| API routes for internal mutations | Adds unnecessary HTTP boundary; server actions are simpler |
| ORM-level migrations (auto-sync in prod) | Risk of data loss; always review generated SQL |
| Raw SQL strings in components | SQL injection risk, no type safety, hard to refactor |
| Barrel exports (`index.ts` re-exporting everything) | Slow HMR, circular dependency risk, tree-shaking issues |
| `any` or `as` casts | Defeats TypeScript; fix the type, don't cast it |
| Inline styles or CSS-in-JS | Tailwind gives us a single mental model |
| Multi-tenant via row-level in app code | Use separate SQLite files per tenant or schema-based isolation |

---

## Auth Patterns

```typescript
// Server Component: get current session
import { auth } from "@/lib/auth";
const session = await auth();
if (!session?.user) redirect("/login");

// Server Action: protect mutation
export async function deleteProject(projectId: string) {
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");
  const project = await db.query.projects.findFirst({
    where: and(eq(projects.id, projectId), eq(projects.userId, session.user.id)),
  });
  if (!project) throw new Error("Not found");
  await db.delete(projects).where(eq(projects.id, projectId));
}

// Middleware: protect routes
export { auth as middleware } from "@/lib/auth";
export const config = { matcher: ["/dashboard/:path*"] };
```

---

## Error Handling

```typescript
// ✅ Return discriminated unions, don't throw in server actions
type ActionResult = { success: true; data: T } | { success: false; error: string };

// ✅ Use Next.js error.tsx for unexpected errors
// ✅ Use not-found.tsx for 404s
// ✅ Log errors server-side with structured logging, never expose stack traces
```

---

## Environment Variables

```env
# Required
DATABASE_URL="file:./data.db"          # SQLite file path (dev) or Turso URL (prod)
AUTH_SECRET="generate-with-npx-auth"    # NextAuth secret
AUTH_GOOGLE_ID="..."                    # OAuth provider
AUTH_GOOGLE_SECRET="..."
STRIPE_SECRET_KEY="sk_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
RESEND_API_KEY="re_..."

# Optional
TURSO_AUTH_TOKEN="..."                  # Only for Turso in production
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

---

## Testing

```typescript
// Unit: Vitest for utilities and server logic
// Integration: Vitest + test SQLite database
// E2E: Playwright for critical user flows (signup, payment, dashboard)
// Run before every PR: npm run type-check && npm run lint && npm run test
```

---

*Generated for [Claude Builders Bounty](https://github.com/claude-builders-bounty) — Bounty #2*
