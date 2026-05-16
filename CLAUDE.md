# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Paste this at the root of any greenfield Next.js + SQLite SaaS project.
> Claude Code will understand conventions without asking clarifying questions.

---

## Stack & Versions

- **Node.js:** 20 LTS (no older)
- **Next.js:** 15 App Router (no Pages Router)
- **TypeScript:** strict mode, `noUncheckedIndexedAccess: true`
- **SQLite:** better-sqlite3 (synchronous, no ORM) or Turso (libSQL, remote)
- **Styling:** Tailwind CSS v4 + shadcn/ui components
- **Auth:** NextAuth.js v5 (Auth.js)
- **Validation:** Zod for all external input
- **Email:** Resend (transactional only)

### Why These Choices
- **better-sqlite3 over Prisma:** SQLite is simple enough that an ORM adds overhead, not value. Raw SQL is faster and more transparent for queries under 50 lines.
- **No Pages Router:** App Router is stable in Next.js 15. New projects should not inherit legacy patterns.
- **Zod at boundaries only:** Validate API routes, form submissions, and env vars. Don't validate internal function calls — TypeScript handles that.

---

## Folder Structure

```
my-saas/
├── src/
│   ├── app/                    # App Router pages
│   │   ├── (auth)/             # Auth routes (login, register, forgot)
│   │   ├── (dashboard)/        # Authenticated dashboard routes
│   │   ├── (marketing)/        # Public pages (landing, pricing, blog)
│   │   ├── api/                # API routes (REST only, no GraphQL)
│   │   ├── layout.tsx          # Root layout (providers, fonts)
│   │   └── page.tsx            # Landing page
│   ├── components/             # React components
│   │   ├── ui/                 # shadcn/ui primitives (do not modify directly)
│   │   └── [feature]/          # Feature-specific components
│   ├── lib/                    # Shared utilities
│   │   ├── db.ts               # SQLite connection singleton
│   │   ├── auth.ts             # NextAuth config
│   │   ├── email.ts            # Resend email templates
│   │   └── utils.ts            # cn(), formatDate(), etc.
│   ├── db/                     # Database layer
│   │   ├── migrations/         # SQL migration files (numbered, sequential)
│   │   ├── queries/            # Typed query functions
│   │   └── schema.sql          # Canonical schema (source of truth)
│   ├── hooks/                  # React hooks
│   ├── types/                  # TypeScript type definitions
│   └── middleware.ts           # Auth + rate limiting middleware
├── public/                     # Static assets
├── scripts/                    # Dev/ops scripts
│   ├── migrate.ts              # Run pending migrations
│   └── seed.ts                 # Seed test data
├── .env.example                # Required env vars (committed)
├── .env                        # Local secrets (gitignored)
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

### Naming Rules
- **Files:** kebab-case for routes (`user-profile.tsx`), PascalCase for components (`UserProfile.tsx`)
- **API routes:** plural nouns (`/api/users`, not `/api/user`)
- **DB queries:** verb + noun (`getUserById`, `createInvoice`, `listActiveSubscriptions`)
- **Hooks:** `use` prefix + noun (`useSubscription`, `useCurrentUser`)

---

## Database Conventions

### Schema
- **Single source of truth:** `db/schema.sql` — never edit migrations after they're committed
- **Table names:** plural, snake_case (`users`, `subscription_plans`)
- **Primary keys:** `id INTEGER PRIMARY KEY AUTOINCREMENT`
- **Timestamps:** `created_at` and `updated_at` on every table (INTEGER, unix epoch)
- **Foreign keys:** always declared, always with `ON DELETE` rule
- **Soft deletes:** `deleted_at INTEGER DEFAULT NULL` — never `DROP` or `DELETE` in production

### Migrations
- **Naming:** `001_create_users.sql`, `002_add_subscription_tier.sql` (sequential numbers, descriptive)
- **Never modify** a committed migration — create a new one instead
- **Up-only strategy:** SQLite doesn't support down migrations well. If you need to rollback, write a manual fix script in `scripts/`
- **Run with:** `npx tsx scripts/migrate.ts`

### Query Rules
- **No raw SQL in components** — all DB access goes through `db/queries/`
- **Use prepared statements** — better-sqlite3 `.prepare()` for anything with user input
- **Return types:** always typed. Use Zod to validate query results if schema is uncertain
- **Batch operations:** prefer `db.transaction()` over individual inserts

```typescript
// ✅ Good: typed query with prepared statement
const getUserById = db.prepare(
  "SELECT id, email, name, created_at FROM users WHERE id = ?"
).pluck(false);

// ❌ Bad: raw string concatenation
const user = db.exec(`SELECT * FROM users WHERE id = ${id}`);
```

---

## Component Patterns

### Server Components by Default
- **Default to server components** — only add `"use client"` when you need interactivity (useState, useEffect, event handlers)
- **Data fetching in server components** — query DB directly, no API round-trip
- **Client components at the leaves** — wrap interactive parts in small client components

### Form Handling
- **Server actions** for form submission (Next.js 15 `use server`)
- **Zod validation** in the server action, not the client
- **Optimistic UI** only for low-risk updates (likes, bookmarks). Never for payments or subscriptions.

### Error Boundaries
- **error.tsx** in every route group that has user-facing data
- **not-found.tsx** for 404s (use `not()` from `next/navigation`)
- **Global error handler** in root `layout.tsx` — log to console + email alert in production

---

## API Routes

- **REST only** — no GraphQL unless there's a proven need
- **Zod validation** at the route entry point
- **Error responses:** consistent format `{ error: string, code: string }`
- **Rate limiting:** 100 req/min per IP (use `@upstash/ratelimit` or simple in-memory for dev)
- **Auth:** check session in middleware, not in every route

```typescript
// API route template
import { NextResponse } from "next/server";
import { z } from "zod";

const schema = z.object({ email: z.string().email() });

export async function POST(req: Request) {
  const body = await req.json();
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid email", code: "VALIDATION_ERROR" }, { status: 400 });
  }
  // ... handle request
}
```

---

## Auth & Sessions

- **NextAuth.js v5** with database adapter (stores sessions in SQLite)
- **Session strategy:** JWT + database (JWT for speed, DB for revocation)
- **Password hashing:** bcrypt with cost factor 12
- **Email verification:** required before dashboard access
- **Rate limit login:** 5 attempts per 15 minutes per IP

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | Path to SQLite file (`file:./data/app.db`) |
| `NEXTAUTH_SECRET` | ✅ | Session signing key (`openssl rand -base64 32`) |
| `NEXTAUTH_URL` | ✅ | Base URL (`http://localhost:3000` for dev) |
| `RESEND_API_KEY` | Prod | Email service key |
| `STRIPE_SECRET_KEY` | Prod | Payment processing |
| `STRIPE_WEBHOOK_SECRET` | Prod | Stripe webhook verification |

**Never hardcode** env vars. Always use `process.env.X ?? throw new Error("Missing X")`.

---

## What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It |
|-------------|----------------|
| **ORM (Prisma, Drizzle)** | SQLite is simple enough. ORMs add abstraction layers that hide slow queries and make migrations harder to reason about. |
| **GraphQL** | Adds complexity for SaaS apps that rarely need flexible querying. REST + typed responses is simpler and cacheable. |
| **Client-side data fetching** | Server components eliminate the need for `useEffect` + `fetch`. Data is available at render time. |
| **Global state (Redux, Zustand)** | Server state belongs on the server. Client state belongs in URL params or component state. Global stores create unnecessary coupling. |
| **E2E testing for everything** | E2E tests are slow and flaky. Test critical paths only (auth flow, checkout). Unit test business logic. |
| **Docker for local dev** | SQLite is a file. Docker adds complexity for no benefit locally. Use Docker only for production deployment. |
| **Microservices** | A monolith is the right choice until you have 50+ developers. Split when the team outgrows a single codebase. |
| **`any` type** | TypeScript's value is in catching errors at compile time. `any` defeats the entire purpose. Use `unknown` + type guards if necessary. |
| **Inline styles** | Tailwind's utility classes are consistent, composable, and don't require context switching. Inline styles break design system guarantees. |
| **`console.log` in production** | Use structured logging (`winston` or `pino`) with levels. `console.log` has no metadata, no filtering, no rotation. |

---

## Dev Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint + TypeScript type check
npm run migrate      # Run pending DB migrations
npm run seed         # Seed test data (dev only)
npm run test         # Run unit + integration tests
npm run test:e2e     # Run E2E tests (critical paths only)
```

---

## Commit Conventions

- **feat:** new feature
- **fix:** bug fix
- **db:** database migration or schema change
- **ui:** component or styling change
- **auth:** authentication/authorization change
- **chore:** tooling, deps, config

Example: `db: add subscription_plans table and pricing columns`

---

*Last updated: 2026-05-17 | For Next.js 15 + SQLite SaaS projects*
