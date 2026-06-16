# CLAUDE.md — SaaS Project (Next.js 15 + SQLite)

## Stack & Versions

| Layer       | Technology                        | Why                                                             |
|-------------|-----------------------------------|-----------------------------------------------------------------|
| Framework   | Next.js 15 (App Router)           | Server-first, RSC-native, fast refresh                          |
| Language    | TypeScript 5.x (strict)           | `strict: true` — no exceptions                                  |
| Database    | SQLite via better-sqlite3         | Zero-operations, single-file, fast for single-tenant SaaS       |
| ORM         | Drizzle ORM                       | Type-safe, SQL-like, no hidden magic                            |
| Auth        | NextAuth.js v5 (Auth.js)          | Built for App Router, session-based                             |
| UI          | Tailwind CSS 4 + shadcn/ui        | Utility-first, composable, accessible                           |
| Forms       | React Hook Form + Zod             | Type-safe validation, minimal re-renders                        |
| Payments    | Stripe (webhook-first)            | Idempotent events, no polling                                   |

## Project Structure

```
├── src/
│   ├── app/                    # App Router (routes = folders)
│   │   ├── (marketing)/        # Public pages (landing, pricing, about)
│   │   ├── (dashboard)/        # Authenticated routes (layout.tsx checks session)
│   │   │   └── [orgSlug]/      # Multi-tenant org-scoped routes
│   │   ├── api/                # Route handlers (NO business logic here)
│   │   │   └── webhooks/       # Stripe/webhook handlers (raw body, no parsing)
│   │   ├── layout.tsx          # Root layout (fonts, providers, metadata)
│   │   └── page.tsx            # Landing page
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives (do NOT edit directly)
│   │   └── features/           # Feature-specific components (one dir per domain)
│   ├── db/
│   │   ├── schema/             # Drizzle schema files (one file per domain)
│   │   ├── migrations/         # Auto-generated (do NOT hand-edit)
│   │   ├── index.ts            # DB client singleton
│   │   └── seed.ts             # Development seed data
│   ├── lib/
│   │   ├── auth.ts             # NextAuth config (callbacks, adapters, providers)
│   │   ├── stripe.ts           # Stripe client + webhook parser
│   │   ├── email.ts            # Email client (Resend / SendGrid)
│   │   └── utils.ts            # Shared helpers (cn(), formatDate(), etc.)
│   └── middleware.ts           # Auth middleware (matcher = dashboard routes only)
├── drizzle.config.ts           # Drizzle config
├── next.config.ts              # Next.js config
├── tailwind.config.ts          # Tailwind config
├── tsconfig.json               # strict: true, path aliases: @/*
└── CLAUDE.md                   # ← you are here
```

## Rules We Follow

### SQL / Migration Conventions
- Every schema change = a new migration file. **Never edit old migrations.**
- Drizzle Kit generates migrations: `npx drizzle-kit generate`
- Apply: `npx drizzle-kit migrate`
- Rollbacks: write a **down migration** manually — no automated rollback.
- Foreign keys: always name them: `FK_${table}_${refTable}`.
- Indexes on: `foreignKey`, `createdAt`, `orgId` (every query scoped to org).
- **Never use `SELECT *`** — always name the columns.

### Component Patterns
- Server Components by default. Client Components only when you need: `useState`, `useEffect`, `onClick`, browser APIs, or context.
- **File naming**: `page.tsx` (route), `layout.tsx` (layout), `loading.tsx` (suspense boundary), `error.tsx` (error boundary).
- Props: `interface Props { ... }` — always explicit, never `any`.
- Server actions: `"use server"` in a separate `actions.ts` file, never inline in components.
- Forms: React Hook Form + Zod schema. Validate server-side in the action too.

### Data Flow
- **Route Handler** → validates input → calls **Service** → returns `NextResponse`.
- **Server Action** → validates (Zod) → calls **Service** → revalidates path.
- **Service** → reads/writes DB via Drizzle → returns typed result.
- **NEVER** call the DB from a component. Always go through a service or action.

### Authentication & Authorization
- `middleware.ts` protects dashboard routes. Redirects to `/login` if unauthenticated.
- Every org-scoped API route checks: (1) session exists, (2) user belongs to org, (3) user has required role.
- Roles: `owner`, `admin`, `member`. Check via `getUserOrgRole(userId, orgId)`.
- API routes: prefer `POST` for mutations, `GET` for reads. No REST purity dogmatism.

### Error Handling
- Route handlers: try/catch → log → return `{ error: string, code: string }`.
- Server actions: return `{ success: true, data } | { success: false, error: string }`.
- Client: use `useActionState` for form errors. Global `error.tsx` boundary catches unhandled errors.
- **Never swallow errors.** Every catch block must log, return, or rethrow.

## Anti-Patterns (Don't Do These)

| ❌ Don't                                          | ✅ Do Instead                              |
|---------------------------------------------------|--------------------------------------------|
| `useEffect` for data fetching                     | Server Component + `async`                 |
| `any` type                                        | `unknown` + type guard, or proper interface |
| Inline styles (`style={{}}`)                      | Tailwind utility classes                   |
| Hand-edit migration files                         | New migration file                         |
| Business logic in route handlers                  | Extract to `src/lib/services/`             |
| `SELECT *` in production queries                  | Name columns explicitly                    |
| `"use client"` on the root layout                 | Keep layout as Server Component            |
| Direct DB calls from components                   | Server Action or Service layer             |
| Catch-all error messages to client                | Log full error, return sanitized message   |
| `process.env` access outside `src/lib/env.ts`     | Centralized env validation with Zod        |

## Dev Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build (check for type errors)
npm run test         # Run vitest
npm run test:e2e     # Run Playwright E2E
npx drizzle-kit generate   # Generate migration after schema change
npx drizzle-kit migrate    # Apply pending migrations
npx drizzle-kit studio     # Open Drizzle Studio (read-only DB browser)
```

## Architecture Decisions & Rationale

**Why SQLite (not Postgres)?** For single-tenant SaaS, SQLite eliminates Docker, connection pooling, RDS costs, and replication complexity. better-sqlite3 is synchronous = simpler code. Scale up: migrate to Turso (SQLite-compatible, distributed) without changing queries.

**Why Drizzle (not Prisma)?** Drizzle maps 1:1 to SQL. You write `db.select().from(users).where(eq(users.email, email))` — no hidden N+1, no giant generated client. Prisma's abstraction leaks more than it hides for relational queries.

**Why App Router (not Pages)?** App Router is the future — RSC, streaming, nested layouts, and built-in loading/error boundaries. Pages Router is maintenance mode.

**Why `better-sqlite3` (not `sql.js`)?** `better-sqlite3` is 10x faster, supports WAL mode, and is synchronous — meaning simpler code without `await db.query()` everywhere. Native addon required, but that's fine for SaaS deployments.
