# CLAUDE.md — Next.js 15 + SQLite SaaS

> Copy this file into the root of your greenfield Next.js 15 project.
> Every rule here has a concrete reason — nothing is generic or aspirational.

## Project Structure

```
src/
  app/               # App Router routes (file-based routing)
    (auth)/          # Auth-related routes — login, signup, callback
    (dashboard)/     # Authenticated pages — wrapped in layout guard
    api/             # Route handlers (server-only, never client components)
    layout.tsx       # Root layout (html/body wrappers only)
  components/
    ui/              # Primitive UI kit (Button, Card, Input, etc.)
    forms/           # Form components tied to specific features
    layout/          # Sidebar, header, navigation shell
  db/
    migrations/      # SQL migration files, one per change, timestamped
    schema.ts        # Drizzle ORM schema definitions
    seed.ts          # Seed data for local development
    client.ts        # Database client singleton
  lib/
    auth.ts          # Auth helpers (session read, middleware)
    email.ts         # Transactional email
    payments.ts      # Stripe/Lemon Squeezy helpers
    utils.ts         # Pure utility functions only
  hooks/             # Shared React hooks (useDebounce, useMediaQuery)
  types/             # Shared TypeScript types and interfaces
  middleware.ts      # Next.js middleware (auth guard, i18n)
```

**Reason**: A flat `src/` avoids the `../../` pyramid and keeps every import
reachable in two hops. Colocating route groups with their pages keeps the
router visible while separation by domain (auth, dashboard, api) prevents
leaky imports.

## Naming Conventions

| Category | Convention | Example | Reason |
|----------|-----------|---------|--------|
| Route files | `page.tsx` / `layout.tsx` | `app/(dashboard)/settings/page.tsx` | Next.js requires these exact names |
| Route handlers | `route.ts` | `app/api/stripe/webhook/route.ts` | Convention enforced by Next.js |
| UI components | PascalCase | `Button.tsx`, `DataTable.tsx` | Standard React convention |
| Utility functions | camelCase | `formatCurrency()`, `cn()` | Idiomatic JS/TS |
| DB tables | snake_case | `user_sessions`, `subscription_plans` | SQL convention — case-insensitive |
| DB columns | snake_case | `created_at`, `stripe_customer_id` | Same as tables |
| Files with default export | PascalCase | `UserAvatar.tsx` | Matches component name |
| Files with named exports | camelCase | `useDebounce.ts`, `auth.ts` | Utility/hook pattern |
| Environment variables | UPPER_SNAKE | `DATABASE_URL`, `STRIPE_SECRET_KEY` | Industry standard |

## Database Migration Rules

1. **One file per change.** Each migration is a single `.sql` file named
   `YYYYMMDD_HHMMSS_description.sql`. Never edit an existing migration after
   it has been committed.

2. **Always add, never remove.** A migration may `ALTER TABLE ADD COLUMN` or
   `CREATE TABLE`, but it must never `DROP COLUMN` or `DROP TABLE` without a
   two-phase process: mark as deprecated in one migration, remove in the next
   release cycle.

3. **Every migration must be reversible.** Include a `-- DOWN:` comment block
   at the end of each migration file that reverts the change. Example:
   ```sql
   ALTER TABLE users ADD COLUMN avatar_url TEXT;
   -- DOWN:
   -- ALTER TABLE users DROP COLUMN avatar_url;
   ```

4. **Run migrations through a script, never manually.** Use
   `npm run db:migrate` (not raw SQL in a console). This guarantees the
   `_migrations` tracking table stays in sync.

5. **Seed data is for local dev only.** `seed.ts` must check
   `NODE_ENV !== 'production'` and exit early in production. Never run seed
   on a staging database that mirrors production.

**Reason**: These rules make migrations reviewable in PRs, deployable without
heroics, and reversible without a restore-from-backup incident.

## Dev Commands

| Command | What it does | When to run |
|---------|-------------|-------------|
| `npm run dev` | Start dev server on :3000 | Every session |
| `npm run build` | Production build + type-check | Before pushing |
| `npm run lint` | ESLint + Prettier check | Before committing |
| `npm run type-check` | tsc --noEmit | Before pushing |
| `npm run test` | Vitest unit/integration tests | After changing logic |
| `npm run db:migrate` | Apply pending migrations | After pulling new migrations |
| `npm run db:generate` | Generate new migration from schema changes | After editing schema.ts |
| `npm run db:seed` | Insert seed data | First time setting up local DB |
| `npm run db:studio` | Open Drizzle Studio (GUI browser) | Debugging data |
| `npm run format` | Auto-format with Prettier | Before committing |

## Patterns to Follow

### Server components by default
Every component is a server component unless it needs interactivity (onClick,
onChange, useEffect, useState). When a component needs client interactivity,
add `"use client"` at the top and keep the client boundary as narrow as
possible — wrap only the interactive leaf, not the entire page.

**Reason**: Server components render to static HTML, produce zero JS for the
browser, and can directly query the database without an API layer. This cuts
bundle size by 40-60% on typical pages.

### Route handlers for mutations, server actions for form submissions
- Use **Route Handlers** (`app/api/*/route.ts`) for webhooks, third-party API
  callbacks, and mobile-app endpoints.
- Use **Server Actions** (`"use server"` functions) for form submissions that
  come from your own pages. They preserve the progressive-enhancement path
  and work without JavaScript.

**Reason**: Server Actions eliminate the boilerplate of creating, fetching,
and error-handling a fetch() call for every form. Route Handlers are still
needed for non-browser clients that can't send a POST with a Content-Type
that triggers a Server Action.

### Auth check in middleware, session read in server components
The `middleware.ts` file checks for a valid session cookie and redirects to
`/login` if missing. Individual page components read the session via a
`getSession()` call — they don't repeat the redirect logic.

**Reason**: A single middleware redirect is simpler and more reliable than
eleven different `if (!session) redirect()` calls scattered across pages.

### Database queries go in the server component, not in a lib/ helper
When a page needs data, query it directly in the server component:
```tsx
// ✅ Good — query in the server component
export default async function DashboardPage() {
  const projects = await db.select().from(projectsTable);
  return <ProjectList projects={projects} />;
}
```
```tsx
// ❌ Bad — query in a client component via useEffect
export default function DashboardPage() {
  const [projects, setProjects] = useState([]);
  useEffect(() => { fetch('/api/projects').then(...) }, []);
}
```

**Reason**: Direct queries in server components are typesafe, fast (no HTTP
round-trip), and require zero loading state ceremony. The client-side fetch
pattern doubles latency, adds a flash-of-loading, and needs error state
handling everywhere.

## Anti-Patterns to Avoid

### ❌ `useEffect` for data fetching
**Why it's bad**: Race conditions, double-fires in Strict Mode, no structural
loading state, breaks if the API moves. Use server components or React Query
on the rare client that genuinely needs client-side data.

### ❌ Prop drilling through 4+ levels
**Why it's bad**: Adding a prop means editing 5 files. Use React Context for
truly global state (theme, auth user) or component composition (layout
components that receive children/headers as props).

### ❌ Storing files in `public/` that aren't truly public
**Why it's bad**: Everything in `public/` is served at the root URL with no
auth check. If a file needs authentication to access (user uploads, invoices),
serve it through a Route Handler that checks the session.

### ❌ Raw SQL in migration files that references TypeScript types
**Why it's bad**: SQL migration files are plain text — they don't get
type-checked. If you rename a column in schema.ts but forget to update the
migration, the migration silently breaks in production. Always write
migrations in SQL and test them against a local copy of the database.

### ❌ Calling `db:push` (Drizzle Kit) in production
**Why it's bad**: `db:push` introspects your schema and generates diff SQL on
the fly. It can produce unexpected destructive changes (dropping a column
that was renamed). Use `db:generate` + `db:migrate` instead for production.

### ❌ Using `next/image` for external images without a domain allowlist
**Why it's bad**: Without `remotePatterns` in `next.config.ts`, Next.js
refuses to optimize external images and they render at full resolution,
destroying Lighthouse scores.

### ❌ Importing server-only code into client components
**Why it's bad**: If a client component imports a file that uses `fs`,
`crypto`, or `process.env` (without `NEXT_PUBLIC_`), the build fails with
`Module not found`. Keep `"use client"` files pure UI and pass data as props.

---
*Template version 1.0 — Generated for Claude Builders Bounty #2*
*License: MIT — use freely in any project*
