# Project Context

## Stack & Versions

| Layer | Choice | Version | Reason |
|-------|--------|---------|--------|
| Framework | Next.js 15 | 15.x | App Router, React Server Components, streaming |
| Runtime | Node.js | >= 20 LTS | Native SQLite support, fetch API caching |
| Language | TypeScript | >= 5.5 | Strict mode, no `any` without comment |
| Database | SQLite | — | Zero-config, single-file, perfect for SaaS < 50K users |
| SQLite Driver | better-sqlite3 | >= 9.4 | Synchronous API (faster for queries), prepared statements |
| ORM/Query Builder | drizzle-orm | >= 0.30 | Type-safe, lightweight, no Rust binary / codegen step |
| Styling | Tailwind CSS | >= 4.x | Utility-first, no CSS-in-JS runtime cost |
| Auth | NextAuth.js v5 | >= 5 | App Router native, Edge compatible |
| Validation | Zod | >= 3.23 | Schema-first, composes with TypeScript |
| UI Components | shadcn/ui | latest | Composable, accessible, copy-paste (not a dependency) |

**Why not Prisma?** Prisma's query engine adds a Rust binary dependency. For SQLite SaaS, drizzle-orm is ~8x smaller and runs in-process.

**Why not tRPC?** Next.js 15 Server Actions eliminate the need for a separate RPC layer. Keep it simple.

**Why not Postgres?** SQLite handles most SaaS workloads under 50K users with zero operational cost. Migrate to Postgres only when you need concurrent writes at scale.

## Dev Commands

```bash
npm run dev          # Start dev server (Turbopack)
npm run build        # Production build
npm run typecheck    # TypeScript type checking
npm run lint         # ESLint
npm run test         # Vitest unit tests
npm run test:e2e     # Playwright E2E tests
npm run db:generate  # Generate Drizzle migrations
npm run db:push      # Push schema to local DB
npm run db:migrate   # Run pending migrations
npm run db:studio    # Open Drizzle Studio (local DB viewer)
```

If a command is missing, inspect `package.json` first. Do not invent new package managers or switch from npm to pnpm/yarn unless the repository already uses them.

## Folder Structure

```
src/
├── app/                    # App Router pages & API routes
│   ├── (auth)/             # Route group — login, register (no layout wrapper)
│   ├── (dashboard)/        # Route group — authenticated pages
│   ├── api/                # API route handlers
│   │   ├── auth/[...nextauth]/  # NextAuth config
│   │   └── webhooks/       # External webhooks (Stripe, etc.)
│   ├── layout.tsx          # Root layout (providers, fonts, meta)
│   └── page.tsx            # Landing page (public)
├── components/
│   ├── ui/                 # shadcn/ui primitives (don't modify source)
│   ├── forms/              # Form components with Zod validation
│   └── shared/             # Reusable non-UI (pagination, empty states, skeletons)
├── lib/
│   ├── db/                 # Database layer
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   ├── migrations/     # Generated migration files (don't edit by hand)
│   │   └── index.ts        # DB connection singleton
│   ├── auth.ts             # NextAuth configuration
│   ├── stripe.ts           # Stripe client initialization
│   ├── env.ts              # Runtime environment validation (Zod)
│   └── utils.ts            # Shared utilities (cn, formatDate, etc.)
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types
└── middleware.ts           # Next.js middleware (auth guards)
```

**Rule:** Every file in `src/` must be under a directory. No flat files in `src/` root.

**Reason:** Routes stay thin, database access stays centralized, business logic is testable without rendering pages.

## Naming Conventions

| Category | Convention | Example |
|----------|------------|---------|
| Files | `kebab-case.tsx/.ts` | `user-profile.tsx` |
| Components | `PascalCase` | `UserProfile` |
| Hooks | `use` prefix | `useAuth`, `usePagination` |
| API routes | RESTful | `GET /api/users`, `POST /api/users` |
| DB tables | `snake_case` plural | `user_profiles`, `subscription_plans` |
| DB columns | `snake_case` | `created_at`, `user_id` |
| Types | `PascalCase`, no `I` prefix | `UserProfile`, `ApiResponse` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Zod schemas | Suffix with `Schema` | `CreateUserSchema` |

## Database Rules

### Schema

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  email: text("email").notNull().unique(),
  name: text("name"),
  role: text("role", { enum: ["user", "admin"] }).default("user").notNull(),
  created_at: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updated_at: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});
```

- Every table gets: `id` (text, cuid via `crypto.randomUUID()`), `created_at`, `updated_at`
- Use `text()` for IDs, not `serial()` — SQLite doesn't do auto-increment well
- Foreign keys: `user_id` references `users.id`, always `onDelete: "cascade"`
- Add indexes for every foreign key and common lookup column

### Migrations

```bash
# Generate a migration after changing schema.ts
npx drizzle-kit generate

# Push to local dev DB
npx drizzle-kit push

# Production (Turso)
npx drizzle-kit migrate
```

- Migration files live in `src/lib/db/migrations/`
- **Never edit a migration file after committing it** — deployed databases need append-only history
- Name migrations with ordered prefix: `0001_create_users.sql`, `0002_add_billing_status.sql`
- Every migration must be reversible — if `UP` is `ALTER TABLE`, `DOWN` must restore the previous state
- Prefer additive migrations. For destructive changes, create a backfill plan first
- Wrap related schema/data changes in a transaction

### Connection

```typescript
// src/lib/db/index.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";

const sqlite = new Database(process.env.DATABASE_URL ?? "data/app.db");
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("foreign_keys = ON");

export const db = drizzle(sqlite);
```

- One shared connection singleton in `lib/db/index.ts`
- Enable WAL mode for production-like performance
- Enable foreign keys on every connection
- Keep transactions explicit for multi-step writes

### Query Patterns

```typescript
// ✅ DO: Prepared statement at module scope
const getUserByEmail = db
  .select()
  .from(users)
  .where(eq(users.email, sql.placeholder("email")))
  .prepare();

// ✅ DO: Transaction for multi-step writes
await db.transaction(async (tx) => {
  const [user] = await tx.insert(users).values(data).returning();
  await tx.insert(profiles).values({ userId: user.id });
});

// ❌ DON'T: Inline raw SQL in route handlers
// ❌ DON'T: String-interpolate user input into SQL
```

- Put query helpers in `lib/db/queries/<domain>.ts`
- Put business workflows in `lib/services/<domain>.ts`
- Validate all user input with Zod before it reaches a query
- Use prepared statements for all dynamic values
- Return typed domain objects, not raw DB rows

## Component Patterns

### Server Components (default)

```tsx
// src/app/(dashboard)/page.tsx
export default async function DashboardPage() {
  const user = await getCurrentUser();
  const projects = await db.query.projects.findMany({
    where: eq(projects.user_id, user.id),
    orderBy: desc(projects.created_at),
  });
  return <ProjectList projects={projects} />;
}
```

- Default to Server Components — fetch data directly in the component
- No `useEffect` for data fetching
- No `useState` for server data
- Keep `page.tsx` and `layout.tsx` thin; move business logic to `lib/services`

### Client Components

```tsx
// src/components/forms/TaskForm.tsx
"use client";
export function TaskForm() {
  const [state, formAction] = useActionState(createTask, null);
  return <form action={formAction}>...</form>;
}
```

- Only when you need: interactivity, browser APIs, React state, effects
- Mark with `"use client"` at the top
- Keep them small and leaf-shaped
- Push data fetching up to Server Components

### Forms

- Define Zod schemas in `lib/validators` or next to the server action
- Reuse the same schema for server validation and client form hints
- Server actions return structured errors: `{ field: "email", message: "Invalid" }[]`
- Show field-level errors when possible
- Re-check authorization inside the action even if the page already checked it

### Loading & Error States

- Every route folder can have `loading.tsx` (auto suspense boundary)
- Every route folder can have `error.tsx` (must be client component)
- For inline loading: `Suspense` wrapper with skeleton component
- For mutations: optimistic updates via `useOptimistic`

## API Routes

Use `app/api` for: webhooks, public API endpoints, OAuth callbacks, integration callbacks.

- Always validate input with Zod before processing
- Return consistent error shape: `{ error: { message, code, status } }`
- Use `NextResponse`, not raw `Response`
- Keep handlers thin; call services for business logic
- Log enough context to debug without logging secrets

## Authentication

- NextAuth v5 with credentials provider
- Session strategy: JWT (not database sessions)
- Centralize session lookup in `lib/auth.ts`
- Centralize permission checks in `lib/auth/permissions.ts`
- Protect routes in `middleware.ts`:

```typescript
export default auth((req) => {
  if (!req.auth && req.nextUrl.pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/login", req.nextUrl));
  }
});
```

- Get server-side user: `const user = await getCurrentUser()` (throws if not auth)
- Get client-side user: `const { data: session } = useSession()`
- Never rely on hidden form fields for ownership or role decisions

## Environment Variables

```typescript
// src/lib/env.ts
import { z } from "zod";

export const env = z.object({
  DATABASE_URL: z.string().url(),
  NEXTAUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
}).parse(process.env);
```

- Validate once in `lib/env.ts` with Zod at startup
- Import from `lib/env.ts`; never read `process.env` throughout the app
- Prefix browser-safe values with `NEXT_PUBLIC_` only when truly public
- Never put secrets in `NEXT_PUBLIC_` variables
- Commit `.env.example` (without real secrets), never commit `.env.local`

## Testing Expectations

- Unit-test services, validators, and query helpers (Vitest)
- Add regression tests for every bug fix
- Use Playwright for critical flows: sign up, sign in, create workspace, billing
- Tests must not require production secrets — use an isolated SQLite test database
- Co-locate unit tests: `Component.test.tsx` next to `Component.tsx`

## Security Rules

- Never expose server secrets to Client Components
- Never build SQL with string interpolation for user input
- Always verify ownership on reads and writes for tenant-scoped data
- Treat webhook payloads as untrusted until signatures are verified
- Do not log passwords, tokens, cookies, or full payment payloads
- Use secure, httpOnly cookies for sessions
- Rate-limit public auth and API endpoints

## Performance Rules

- Avoid loading large datasets in one query — paginate from the beginning
- Add indexes when adding new list/filter screens
- Use `revalidatePath` or targeted cache invalidation after mutations
- Avoid unnecessary Client Components (they increase JS shipped to the browser)
- SQLite performs very well when queries are indexed and pages don't over-fetch

## What We Don't Do (and Why)

| Anti-Pattern | Why |
|--------------|-----|
| No `any` types | Use `unknown` and narrow. `any` defeats TypeScript. |
| No `useEffect` for data fetching | This is Next.js 15. Fetch in Server Components. |
| No inline styles | Use Tailwind classes. Dynamic values via `cn()`. |
| No `console.log` in production | Use a proper logger. `console.error` minimum for dev. |
| No editing shadcn/ui source directly | Copy to `components/shared/` and modify there. |
| No offset-based pagination at scale | Cursor-based handles concurrent inserts better. |
| No raw SQL without parameterized queries | SQL injection is not an option. |
| No client-side auth as the only guard | Always verify server-side too. |
| No committing `.env` files | Ever. Not even `.env.example` with real secrets. |
| No `ts-ignore` | Use `@ts-expect-error` with a comment explaining why. |
| No editing migration files after commit | Append-only history for deployed databases. |
| No global state for server data | URL + server rendering + query invalidation own server state. |
| No generic abstractions before 3 real call sites | Premature abstractions make code harder to change. |

## Working Agreement for Claude Code

When making changes:

1. Inspect `package.json`, existing folders, and current database tooling first
2. Make the smallest change that satisfies the request
3. Keep server-only logic out of Client Components
4. Add or update tests for behavior changes
5. Run typecheck, lint, tests, and build when available
6. Summarize changed files, validation commands, and any follow-up migration steps

When uncertain:

- Prefer explicit SQL over hidden magic
- Prefer Server Components over Client Components
- Prefer Zod validation at boundaries
- Prefer asking for product intent before inventing billing, role, or permission behavior
