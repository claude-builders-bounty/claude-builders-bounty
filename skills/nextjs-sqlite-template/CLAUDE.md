# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

| Tool | Version | Why |
|------|---------|-----|
| Next.js | 15.2+ (App Router) | Stable React 19, server components, PPR |
| SQLite | via better-sqlite3 | Single-file DB, zero infra, perfect for SaaS |
| Drizzle ORM | 0.40+ | Type-safe, SQL-like syntax, no magic |
| NextAuth v5 | 5.0.0-beta.25 | App Router native, SQLite adapter |
| Tailwind CSS | 4.1+ | Utility-first, CSS-first config |
| TypeScript | 5.7+ | Strict mode always |
| Bun | 1.2+ | Drop-in Node replacement, 5x faster installs |

## Project Structure

```
src/
├── app/                    # App Router pages
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Dashboard route group (requires auth)
│   │   ├── _components/    # Dashboard-only components
│   │   └── settings/
│   ├── api/                # Route handlers
│   │   └── trpc/           # tRPC endpoints (if used)
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/             # Shared UI components
│   ├── ui/                 # Primitive UI (button, input, card)
│   └── shared/             # Business-logic shared components
├── lib/                    # Non-React utilities
│   ├── db/                 # Database layer
│   │   ├── schema/         # Drizzle schema files
│   │   ├── migrations/     # Generated SQL migrations
│   │   ├── index.ts        # DB client singleton
│   │   └── seed.ts         # Seed data
│   ├── auth/               # NextAuth config
│   ├── email/              # Email templates + senders
│   └── utils.ts            # Pure helper functions
├── styles/                 # Global CSS
│   └── globals.css
├── middleware.ts           # Next.js middleware
└── env.ts                  # Type-safe env vars (t3-env)
```

## Database Rules

### Schema Conventions
- **One file per domain**: `users.ts`, `projects.ts`, `subscriptions.ts`
- **No SQLite enums**: Use `text()` with `$default` and runtime validation
- **Timestamps**: Always `createdAt` / `updatedAt` as `integer` (Unix ms)
- **Soft deletes**: Use `deletedAt: integer()` — never `DELETE FROM`
- **Foreign keys**: Enable via `PRAGMA foreign_keys = ON` in each connection

```typescript
// ✅ Good: text with runtime constraint
export const planEnum = z.enum(["free", "pro", "enterprise"]);
export const subscriptions = sqliteTable("subscriptions", {
  id: integer().primaryKey({ autoIncrement: true }),
  plan: text().$default(() => "free").notNull(),
  // Validate at insert:
  // .$type<z.infer<typeof planEnum>>()
});

// ❌ Bad: SQLite doesn't support ENUM
export const subscriptions = sqliteTable("subscriptions", {
  plan: text().$type<"free" | "pro">(), // db column is still TEXT
});
```

### Migration Workflow
```bash
# Generate migration from schema changes
bun drizzle-kit generate

# Apply migration
bun drizzle-kit migrate

# Drop + recreate (dev only)
bun run db:reset
```

**IMPORTANT**: Never edit migration files manually. Drizzle owns them.

### Query Patterns
- **SELECT**: Use `.findFirst()` for single rows, `.all()` for arrays
- **INSERT**: Use `.returning()` when you need the created row back
- **Transactions**: Wrap in `db.transaction((tx) => ...)` for multi-table ops
- **Avoid raw SQL** — Drizzle's query builder is portable and type-safe

## Component Patterns

### Default to Server Components
```typescript
// ✅ Good: server component by default
export default async function ProjectPage({ params }: Props) {
  const project = await db.query.projects.findFirst({
    where: eq(projects.id, params.id),
  });
  return <ProjectDetail project={project} />;
}
```

### Only Add "use client" When Necessary
```typescript
"use client";

// You NEED client when:
// 1. useState / useEffect / useReducer
// 2. onClick / onSubmit / onChange handlers
// 3. Browser-only APIs (localStorage, window)
// 4. Third-party React libs that use hooks
```

### Data Flow
- **Server → Client**: Props pass data down. Never fetch inside client components.
- **Client → Server**: Server Actions for mutations. tRPC for complex queries if needed.
- **Form handling**: Use `useActionState()` with Server Actions.

### Suspense Boundaries
- Every data-fetching component gets a `<Suspense>` wrapper with fallback
- Use `loading.tsx` for page-level loading states
- Streaming SSR is your friend — use `await` per component, not per page

## Anti-Patterns (Do Not Do)

| Anti-pattern | Why | Instead |
|---|---|---|
| `"use client"` on entire page | Breaks RSC streaming, increases bundle | Only add directive to leaf components |
| `useEffect` for data fetching | Double-render, race conditions, no caching | Server Components + Server Actions |
| Direct `fetch()` in client components | No caching, no dedup, waterfall requests | Server Functions or tRPC |
| `DELETE FROM users` style queries | Can't recover from mistakes | Soft deletes with `deletedAt` |
| ENUM columns in SQLite | SQLite has no enum type | Runtime validation (zod) + text column |
| Multiple DB connections per request | Connection pooling issues | Singleton pattern in `lib/db/index.ts` |
| `any` or `as` casts | Eats type safety | Proper Drizzle types + Zod validation |
| `npm install` heavyweight deps | Floats the bundle | Prefer `bun` + tree-shakeable libs |
| Unwrapped async renders | Breaks streaming, worse UX | Always wrap in `<Suspense>` |

## Dev Commands

```bash
# Development
bun dev                 # Start dev server (localhost:3000)
bun dev --turbo         # Turbo mode (faster)

# Database
bun drizzle-kit generate    # Generate migration
bun drizzle-kit migrate     # Apply migration
bun drizzle-kit studio      # Open Drizzle Studio
bun run db:seed             # Seed development data
bun run db:reset            # Drop + migrate + seed

# Testing
bun test                # Run all tests (Vitest)
bun test --watch        # Watch mode
bun test --coverage     # Coverage report

# Linting & Type Checking
bun run lint            # ESLint
bun run typecheck       # tsc --noEmit
bun run format          # Prettier

# Build & Deploy
bun run build           # Production build
bun run start           # Start production server
bun run build && bun run start   # Full deploy cycle
```

## Environment Variables

```env
# Required
DATABASE_URL="file:./data/saas.db"
AUTH_SECRET="generate-with-bunx auth secret"
AUTH_GITHUB_ID=""
AUTH_GITHUB_SECRET=""

# Optional
RESEND_API_KEY=""       # Email (Resend)
UPLOADTHING_SECRET=""   # File uploads
NEXT_PUBLIC_URL="http://localhost:3000"
```

## QA Checklist

Before any PR, verify:
1. `bun run typecheck` passes — no `any`, no implicit `any`
2. `bun run lint` passes — no unused imports, no eslint-disable
3. Schema changes have a migration file
4. All new routes handle the unauthenticated state
5. Error boundaries exist for each route group
6. No `console.log` (use `logger` utility instead)
7. New env vars are documented in `.env.example`
