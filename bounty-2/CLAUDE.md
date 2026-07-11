# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Project Overview
This is a production SaaS application built with Next.js 15 App Router and SQLite (better-sqlite3 or Turso).

## Development Commands
- `npm run dev` — Start dev server on localhost:3000
- `npm run build` — Production build
- `npm run lint` — Run ESLint
- `npm run typecheck` — Run TypeScript compiler in no-emit mode
- `npm run db:migrate` — Run database migrations
- `npm run db:seed` — Seed database with test data
- `npm run db:studio` — Open database GUI (optional)

## Project Structure
```
src/
├── app/                 # Next.js App Router pages and layouts
│   ├── (auth)/         # Auth route group (login, register)
│   ├── (dashboard)/    # Protected dashboard routes
│   ├── api/            # API route handlers
│   └── layout.tsx      # Root layout
├── components/          # Reusable React components
│   ├── ui/             # Primitive UI components (Button, Input, etc.)
│   ├── forms/          # Form components with validation
│   └── layout/         # Layout components (Sidebar, Header)
├── lib/                # Business logic and utilities
│   ├── db/             # Database client, queries, migrations
│   ├── auth/           # Authentication logic
│   ├── stripe/         # Payment integration
│   ├── email/          # Email sending utilities
│   └── utils/          # General utilities
├── server/             # Server-only code (never imported by client)
│   ├── actions/        # Server Actions
│   └── queries/        # Database queries
├── types/              # TypeScript type definitions
└── middleware.ts       # Next.js middleware (auth, i18n)
```

## Naming Conventions
- **Files**: kebab-case (`user-profile.tsx`, `auth-helpers.ts`)
- **Components**: PascalCase exports (`UserProfile`, `AuthProvider`)
- **Functions**: camelCase (`getUserById`, `createStripeCheckoutSession`)
- **Types/Interfaces**: PascalCase with descriptive suffix (`UserDTO`, `SubscriptionInput`)
- **API routes**: kebab-case file names in `app/api/` (`/api/webhooks/stripe/route.ts`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_ATTEMPTS`, `DEFAULT_PAGE_SIZE`)
- **Database tables**: snake_case (`user_subscriptions`, `api_keys`)

## Database Rules
1. **Always use migrations** — Never run raw SQL in application code. All schema changes go through migration files in `src/lib/db/migrations/`.
2. **Parameterized queries only** — Never use string interpolation for SQL. Use `?` placeholders.
3. **Server-only database access** — Database queries live in `src/server/queries/`. Never import `lib/db` in client components.
4. **Transaction for multi-step writes** — Use `db.transaction()` when modifying multiple tables atomically.
5. **Index foreign keys** — Every FK column gets an index. No exceptions.
6. **Soft delete for user data** — Use `deleted_at TIMESTAMP NULL` instead of hard deletes for user-facing records.
7. **Timestamps** — All tables have `created_at` and `updated_at` with `DEFAULT CURRENT_TIMESTAMP`.

## Patterns to Follow

### Server Actions
```typescript
"use server"
import { z } from "zod"
import { auth } from "@/lib/auth"
import { createSubscription } from "@/server/queries/subscriptions"

const input = z.object({
  planId: z.string().uuid(),
  paymentMethodId: z.string().min(1),
})

export async function subscribe(formData: FormData) {
  const session = await auth()
  if (!session?.user) throw new Error("Unauthorized")
  
  const parsed = input.parse({
    planId: formData.get("planId"),
    paymentMethodId: formData.get("paymentMethodId"),
  })
  
  return createSubscription(session.user.id, parsed.planId, parsed.paymentMethodId)
}
```

### Error Handling
- Use `Result<T, E>` pattern for domain logic. Throw only for truly unexpected errors.
- API routes return structured error responses: `{ error: { code: string, message: string } }`
- Client errors use toast notifications. Server errors are logged with context.

### Authentication
- Session-based auth using `iron-session` or `next-auth` with the Credentials provider.
- Middleware protects `(dashboard)` route group. Unauthenticated users redirect to `/login`.
- API routes check `auth()` at the top. No exceptions.
- Role-based access: `admin` and `user` roles. Check `session.user.role` before privileged operations.

## Anti-Patterns to Avoid

1. **Never import server code in client components** — `use client` components must not import `lib/db`, `lib/stripe`, or anything with server-side dependencies.
2. **Never use `useState` for server data** — Use Server Components for data fetching. Only use `useState` for truly client-side state.
3. **Never skip Zod validation** — Every Server Action and API route validates input with Zod before processing.
4. **Never hardcode secrets** — All secrets in `.env.local`. Never commit `.env` files.
5. **Never use `any` type** — Use `unknown` + type narrowing, or define a proper type.
6. **Never mutate database in GET handlers** — GET requests are read-only. Mutations use POST or Server Actions.
7. **Never rely on client-side auth checks alone** — Always verify auth server-side in API routes and Server Actions.
8. **Never use ` dangerouslySetInnerHTML`** — Use a sanitization library if you must render user HTML.

## Testing
- **Unit tests**: `vitest` for pure functions and utilities. Place alongside source: `auth.test.ts` next to `auth.ts`.
- **Integration tests**: `vitest` with a test database. Migrate + seed before each test suite.
- **E2E tests**: `playwright` for critical user flows (signup, payment, dashboard).

## Deployment
- Deploy on Vercel. Set environment variables in the Vercel dashboard.
- Database: Turso for production (libSQL at the edge), better-sqlite3 for local dev.
- Use `next build` for production. The `output: "standalone"` option is set in `next.config.ts`.

## Environment Variables
```
DATABASE_URL=           # SQLite path or Turso connection string
DATABASE_AUTH_TOKEN=    # Turso auth token (production only)
AUTH_SECRET=            # Session encryption key
STRIPE_SECRET_KEY=      # Stripe API key
STRIPE_WEBHOOK_SECRET=  # Stripe webhook signing secret
RESEND_API_KEY=         # Email service API key
```
