# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project context for Claude Code. Every rule has a reason.

## Project Stack
- **Framework**: Next.js 15 App Router (React 19, Server Components by default)
- **Database**: SQLite via Turso (libsql) — single file, zero-dependency in dev; Turso for production
- **ORM**: Drizzle ORM — type-safe, lightweight, no codegen DSL
- **Auth**: Better Auth v1 — framework-native, session-based, OAuth providers
- **Styling**: Tailwind CSS v4 + shadcn/ui — utility-first, component library
- **Validation**: Zod — parse at boundaries, trust inside
- **Payments**: Stripe — webhook-driven, idempotent
- **Email**: Resend — React email templates, webhook events

## Project Structure
```
src/
├── app/           # Next.js App Router — routes, layouts, loading, error
│   ├── (auth)/    # Route group: login, signup, verify
│   ├── (dashboard)/ # Route group: authenticated pages
│   └── api/       # Route handlers — public & authenticated
├── db/
│   ├── schema.ts  # Drizzle schema definitions
│   ├── index.ts   # Database client singleton
│   └── migrate.ts # Migration runner
├── lib/
│   ├── auth.ts    # Better Auth config & client
│   ├── stripe.ts  # Stripe client & webhook handler
│   └── email.ts   # Resend client & email sending
├── components/    # Shared UI components (shadcn/ui based)
└── types/         # Shared TypeScript types
```

**Rule**: Keep it flat. Max 2 levels deep under src/. New modules earn a directory only when ≥3 files.

## Naming Conventions

| Thing | Convention | Example | Reason |
|-------|-----------|---------|--------|
| Files | kebab-case | `user-profile.tsx` | Avoids case-sensitivity bugs across OS |
| Components | PascalCase | `UserProfile` | React convention |
| Functions | camelCase | `getUserById` | JS convention |
| DB tables | snake_case plural | `user_profiles` | SQL convention, Drizzle maps to camelCase |
| Route handlers | `route.ts` | `route.ts` | Next.js convention |
| API routes | kebab-case dirs | `/api/user-settings/` | URL-friendly |

## Database Rules

1. **Migrations are additive.** Never edit an existing migration. Create a new one.
2. **Always use transactions.** Wrap multi-statement operations in `db.transaction()`.
3. **Foreign keys ON.** Drizzle config: `foreignKeys: true`. Turso enforces at SQLite level.
4. **Index what you query.** Every WHERE/JOIN column gets an index. Measure with `.explain()`.
5. **Seed data is for dev only.** `db/seed.ts` runs via `pnpm db:seed`. Never referenced in app code.
6. **No raw SQL in app code.** Use Drizzle query builder. Raw SQL only in migrations.

**Migration workflow:**
```bash
pnpm db:generate   # Generate migration from schema changes
pnpm db:migrate    # Apply to local Turso dev
pnpm db:push       # Push schema to Turso production (non-destructive)
```

## Dev Commands

```bash
pnpm dev           # Next.js dev server (TurboPack)
pnpm build         # Production build
pnpm start         # Production server
pnpm lint          # ESLint + next lint
pnpm typecheck     # tsc --noEmit
pnpm db:studio     # Drizzle Studio (localhost:4983)
pnpm db:generate   # Generate migration
pnpm db:migrate    # Run migrations locally
pnpm db:seed       # Seed dev database
pnpm test          # vitest
pnpm test:e2e      # playwright
pnpm stripe:listen # Stripe webhook forwarding
```

## Patterns to Follow

### Server Components First
- Default to Server Components. Add `'use client'` only when you need interactivity.
- Fetch data in Server Components. Pass to client components as props.
- **Reason**: Smaller JS bundle. No client-side waterfalls.

### Data Fetching
```tsx
// ✅ Good: Server Component fetching
import { db } from '@/db';
export default async function UsersPage() {
  const users = await db.query.users.findMany();
  return <UserList users={users} />;
}

// ❌ Bad: Client-side fetch for server-owned data
'use client';
useEffect(() => { fetch('/api/users').then(...) }, []);
```

### Actions over API Routes
- Use Server Actions for mutations. API routes only for webhooks (Stripe, Resend).
- **Reason**: Server Actions are type-safe end-to-end. No separate validation layer needed.

### Zod at Boundaries
```tsx
// Every action validates input
'use server';
import { z } from 'zod';
const schema = z.object({ email: z.string().email() });
export async function subscribe(formData: FormData) {
  const { email } = schema.parse(Object.fromEntries(formData));
  // ... now email is typed and valid
}
```

### Error Handling
- Throw `new Error('User-friendly message')` in Server Actions.
- Use `error.tsx` boundaries in route segments.
- Never expose stack traces or SQL errors to the client.

## Anti-Patterns to Avoid

| Don't | Do Instead | Why |
|-------|-----------|-----|
| `useEffect` for data fetching | Server Components + Server Actions | Avoids waterfalls, loading states |
| `useState` for URL state | `useSearchParams`, `useRouter` | Shareable URLs, browser back works |
| API routes for CRUD | Server Actions | Type-safe, no fetch boilerplate |
| `as any` type assertions | Zod parse + proper types | TypeScript exists for a reason |
| Inline Tailwind >10 classes | Extract to `@apply` or component | Readability |
| `console.log` in production | Structured logging (pino) | Searchable, level-filterable |
| `setTimeout` for polling | SWR or Server Actions revalidation | Race conditions, memory leaks |
| Hardcoded secrets | `process.env` + `.env.local` | Security, environment parity |

## Testing

- Unit: `vitest` for pure functions, utilities, Zod schemas
- Integration: `vitest` + test database for Drizzle queries
- E2E: Playwright for critical user flows (signup, pay, cancel)

```bash
pnpm test          # Unit + integration
pnpm test:e2e      # End-to-end
```

## Environment Variables

```env
# Database
DATABASE_URL=libsql://local.db
TURSO_DATABASE_URL=libsql://[org]-[db].turso.io
TURSO_AUTH_TOKEN=

# Auth
BETTER_AUTH_SECRET=
BETTER_AUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Payments
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=

# Email
RESEND_API_KEY=
```

## Deployment

- **Platform**: Vercel (Edge Functions for middleware, Node.js for API)
- **Database**: Turso (libsql) — multi-region, HTTP-based
- **Env vars**: Set in Vercel dashboard. Never commit `.env` files.
- **CI**: GitHub Actions — lint → typecheck → test → build → deploy preview
