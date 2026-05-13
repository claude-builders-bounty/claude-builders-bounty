# CLAUDE.md — Next.js 15 + SQLite SaaS Template
> **Bounty $75** · claude-builders-bounty

---

## Project Identity

This is a **Next.js 15 App Router** SaaS application using **SQLite** (via `better-sqlite3` or **Turso**) as the primary database. The codebase prioritizes simplicity, type safety, and fast iteration — no ORM overhead, raw SQL with a thin query helper.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | Next.js 15 (App Router) | RSC, streaming, server actions |
| Language | TypeScript (strict mode) | Type safety, DX |
| Database | SQLite (better-sqlite3 / Turso) | Zero-infra, single-file, fast |
| Auth | NextAuth.js v5 (Auth.js) | Flexible, email + OAuth |
| Payments | Stripe | Standard SaaS billing |
| Email | Resend | Modern email API |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, composable |
| Validation | Zod | Schema-first validation |
| Testing | Vitest + Playwright | Unit + E2E |
| CI/CD | GitHub Actions | Standard |

---

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group (login, register, verify)
│   ├── (dashboard)/       # Protected dashboard routes
│   │   └── app/           # Main app pages
│   ├── api/               # API routes (Stripe webhooks, etc)
│   └── layout.tsx         # Root layout
├── components/            # Shared UI components
│   ├── ui/                # shadcn/ui primitives (Button, Input, etc)
│   └── features/          # Feature-specific components
├── lib/                   # Core utilities
│   ├── db/                # Database layer
│   │   ├── schema.ts      # Table definitions & migrations
│   │   ├── queries/       # Typed query functions per domain
│   │   └── migrate.ts     # Migration runner
│   ├── auth.ts            # NextAuth configuration
│   ├── stripe.ts          # Stripe client & helpers
│   └── utils.ts           # General utilities
├── hooks/                 # React hooks
├── types/                 # Shared TypeScript types
├── server/                # Server-only logic
│   └── actions/           # Server actions (per domain)
├── emails/                # Email templates (React Email)
└── tests/                 # Test files
```

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `kebab-case.ts` | `user-queries.ts` |
| Components | `PascalCase.tsx` | `UserProfile.tsx` |
| Functions | `camelCase` | `getUserById()` |
| DB tables | `snake_case` | `user_subscriptions` |
| DB columns | `snake_case` | `created_at` |
| TypeScript types | `PascalCase` | `UserProfile` |
| Server actions | `camelCase` + `Action` suffix | `createTeamAction` |
| API routes | Next.js convention | `route.ts` |
| env vars | `UPPER_SNAKE_CASE` | `DATABASE_URL` |

---

## Database Rules

### Schema Management
- **No ORM.** Raw SQL with a thin wrapper for parameterized queries.
- All schema changes go through numbered migration files: `lib/db/migrations/001_init.sql`, `002_add_subscriptions.sql`, etc.
- Never modify an existing migration — always add a new one.
- Run migrations via `pnpm db:migrate` on startup (never in request handlers).

### Query Patterns
```typescript
// ✅ CORRECT — typed query function
export function getUserByEmail(email: string): User | null {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email) as User | null;
}

// ❌ WRONG — inline SQL in component
const user = db.prepare(`SELECT * FROM users WHERE email = '${email}'`).get();
```

### Connection Management
- **better-sqlite3**: Single connection, synchronous. Use `db.prepare().get/all/run()`.
- **Turso**: Use `@libsql/client`. All queries are async. Use connection pooling in production.

---

## Auth Rules

- All dashboard routes are protected by `middleware.ts`
- Use `auth()` from `lib/auth.ts` in server components
- Use `getSession()` in API routes
- Never expose user IDs in URLs — use slugs or hashed IDs

---

## Dev Commands

```bash
pnpm dev              # Start dev server (next dev --turbo)
pnpm build            # Production build
pnpm start            # Production start
pnpm db:migrate       # Run pending migrations
pnpm db:studio        # Open Drizzle Studio / SQLite browser
pnpm db:seed          # Seed development data
pnpm lint             # ESLint + Prettier check
pnpm lint:fix         # Auto-fix lint issues
pnpm typecheck        # TypeScript check (no emit)
pnpm test             # Run Vitest tests
pnpm test:e2e         # Run Playwright E2E tests
pnpm stripe:listen    # Stripe webhook forwarding (dev)
```

---

## Patterns to Follow

1. **Server Components by default** — Only add `"use client"` when you need interactivity
2. **Server Actions for mutations** — Form actions, data writes go through `server/actions/`
3. **Optimistic updates** — Use `useOptimistic` for instant UI feedback on mutations
4. **Streaming** — Use `loading.tsx` and `Suspense` boundaries for progressive rendering
5. **Type-safe queries** — Every query function returns a typed interface, never `any`
6. **Environment validation** — On startup, validate all required env vars with Zod

---

## Anti-Patterns to Avoid

1. ❌ **API routes for mutations** — Use Server Actions instead
2. ❌ **Inline SQL** — Always go through `lib/db/queries/`
3. ❌ **`any` types** — Always define interfaces
4. ❌ **Direct DB access from client components** — Use Server Actions or API routes
5. ❌ **Hardcoded secrets** — Everything through env vars
6. ❌ **Monolithic pages** — Split into smaller server components
7. ❌ **Skipping error boundaries** — Every async page should have an `error.tsx`

---

## Security Checklist

- [ ] All user inputs validated with Zod before DB writes
- [ ] CSP headers configured in `next.config.ts`
- [ ] Rate limiting on auth endpoints
- [ ] Stripe webhook signature verified
- [ ] SQL injection prevented via parameterized queries only
- [ ] CSRF protection via NextAuth built-in
- [ ] Sensitive env vars not exposed to client (`NEXT_PUBLIC_` prefix gate)

---

## Deployment

- **Hosting**: Vercel (recommended) or Docker on any VPS
- **Database**: Turso (production, edge) or SQLite file on persistent volume
- **Build**: `pnpm build` includes Prisma/migration step
- **Health check**: `GET /api/health` returns `{ status: "ok", db: "connected" }`

---

_claude-builders-bounty #2 · MIT Licensed_
