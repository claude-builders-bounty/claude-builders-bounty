# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

> **Opinionated project context for Claude Code. Every rule has a reason.**
> Copy this file into any greenfield Next.js 15 App Router + SQLite project.

---

## Project Identity

- **Stack**: Next.js 15 (App Router), TypeScript (strict), SQLite via `better-sqlite3`, Tailwind CSS v4
- **Auth**: next-auth v5 (Auth.js) with credential + OAuth providers
- **ORM**: Drizzle ORM (SQLite dialect) — lightweight, type-safe, no codegen
- **Runtime**: Node.js 22 LTS, pnpm as package manager
- **Hosting**: Vercel (app) + Turso or Litestream (DB replication)

---

## Project Structure

```
src/
├── app/                    # App Router pages & API routes
│   ├── (auth)/             # Auth-grouped routes (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Authenticated dashboard group
│   │   ├── layout.tsx      # Dashboard shell (sidebar, header)
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/page.tsx
│   ├── api/                # Route handlers
│   │   └── auth/[...nextauth]/route.ts
│   ├── layout.tsx          # Root layout (providers, fonts)
│   ├── page.tsx            # Landing page
│   └── globals.css
├── components/             # Shared UI components (shadcn/ui pattern)
│   ├── ui/                 # Primitive components (button, input, card)
│   └── features/           # Feature-specific composed components
├── lib/                    # Pure utilities, no React
│   ├── db/                 # Database layer
│   │   ├── schema.ts       # Drizzle table definitions
│   │   ├── index.ts        # DB connection singleton
│   │   └── migrations/     # SQL migration files (Drizzle Kit)
│   ├── auth.ts             # next-auth config
│   └── utils.ts            # General helpers
├── server/                 # Server-only code (never imported in 'use client')
│   ├── actions/            # Server Actions (form handlers, mutations)
│   └── queries/            # Database query functions
├── hooks/                  # Client-side React hooks
├── types/                  # Shared TypeScript types
│   └── db.ts               # Drizzle-inferred types
└── middleware.ts           # Next.js middleware (auth guards, redirects)
```

**Why this structure**: Server Actions and DB queries are separated from components to prevent accidental client-side imports of server code. Feature components live near their consuming pages, not in a flat list. The `lib/db` directory isolates all database concerns.

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | `kebab-case.tsx` | `user-profile.tsx` |
| Components | `PascalCase` | `UserProfile` |
| Functions | `camelCase` | `getUserByEmail()` |
| DB tables | `snake_case` plural | `user_accounts` |
| DB columns | `snake_case` | `created_at` |
| Server Actions | `action` prefix | `actionCreateTeam` |
| API routes | HTTP method export | `export async function GET()` |
| Types | `PascalCase` with `T` prefix for generics | `TUser`, `UserInsert` |
| Zod schemas | `camelCase` + `Schema` suffix | `loginSchema` |
| Hooks | `use` prefix | `useCurrentUser()` |
| Route groups | `(groupName)` | `(dashboard)` |

**Why kebab-case files**: Next.js uses file-system routing; kebab-case is URL-friendly and avoids case sensitivity issues across OSes.

---

## Database Rules

### Schema Design
- **Always define `created_at` and `updated_at`** on every table
- **Use ULID or cuid2 for primary keys**, not auto-increment integers (prevents enumeration)
- **Foreign keys**: use Drizzle `references()` with `onDelete` explicitly stated
- **Indexes**: add indexes on every column used in WHERE clauses, especially foreign keys
- **Soft deletes**: use `deleted_at TIMESTAMP` column, never hard-delete user data

### Migration Workflow
```bash
# 1. Edit schema.ts
# 2. Generate migration:
npx drizzle-kit generate
# 3. Review generated SQL in lib/db/migrations/
# 4. Apply:
npx drizzle-kit migrate
```

### Critical Rules
- **NEVER edit a migration file after it's been applied** — always create a new migration
- **No raw SQL in application code** — use Drizzle query builder exclusively
- **Transactions**: wrap multi-table writes in `db.transaction()`
- **Connection**: single `db` instance per app, created in `lib/db/index.ts`

**Why Drizzle over Prisma**: Drizzle is 5-10x lighter, has zero-codegen TypeScript inference, works natively in edge runtimes, and doesn't require a generation step before every query.

---

## Dev Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint + TypeScript check
pnpm format           # Prettier format all files
pnpm db:generate      # Generate Drizzle migrations
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Launch Drizzle Studio (DB GUI on port 4983)
pnpm test             # Run Vitest test suite
pnpm test:watch       # Watch mode tests
pnpm typecheck        # tsc --noEmit
```

---

## Patterns to Follow

### 1. Server Components by Default
Everything is a Server Component unless you need interactivity. Add `'use client'` only when using hooks, event handlers, or browser APIs.

```tsx
// Good: Server Component with async data fetch
export default async function DashboardPage() {
  const user = await getCurrentUser();
  const teams = await getUserTeams(user.id);
  return <DashboardShell user={user} teams={teams} />;
}
```

### 2. Server Actions for Mutations
All form submissions and data mutations go through Server Actions. This keeps the mutation logic on the server and enables progressive enhancement.

```tsx
// lib/server/actions/team.ts
'use server';
export async function actionCreateTeam(formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');
  const name = formData.get('name') as string;
  const validated = teamSchema.parse({ name, ownerId: session.user.id });
  return db.insert(teams).values(validated).returning();
}
```

### 3. Optimistic Updates with `useOptimistic`
For instant UI feedback on mutations, use React's `useOptimistic` hook in client components that call Server Actions.

### 4. Zod Validation on Every Boundary
Validate at every trust boundary: form inputs, API payloads, and DB inserts. Define schemas alongside the code that uses them, not in a separate validation file.

### 5. Loading and Error States
Every async page must have a `loading.tsx` and `error.tsx` sibling file. Every data-dependent component should handle the empty state.

### 6. Auth Pattern
```tsx
// Protect a page
import { redirect } from 'next/navigation';
import { auth } from '@/lib/auth';

export default async function ProtectedPage() {
  const session = await auth();
  if (!session) redirect('/login');
  // ... page content
}
```

### 7. Component Composition
Compose complex pages from smaller feature components. Never put all logic in `page.tsx`. The page file should orchestrate, not implement.

---

## Anti-Patterns to Avoid

| ❌ Anti-Pattern | ✅ Do This Instead |
|----------------|-------------------|
| `SELECT *` in queries | Explicit column selection with Drizzle |
| Importing `'server-only'` code in client components | Use Server Actions as the bridge |
| Catching errors silently with empty `catch {}` | Log the error, return a typed error result |
| Storing secrets in `.env` without validation | Use `@t3-oss/env-nextjs` with Zod schemas |
| Passing entire DB rows to client components | Map to a DTO with only needed fields |
| `useEffect` for data fetching | Server Components or SWR/React Query |
| Nested ternary operators in JSX | Extract to named variables or components |
| Inline styles | Tailwind utility classes |
| `any` type | Proper TypeScript types, use `unknown` if truly unsure |
| Multiple `return` statements in render | Single return with conditional rendering inside |
| API routes for simple data reads | Server Components with direct DB access |

---

## Testing Strategy

- **Unit**: Vitest for pure functions and utilities
- **Integration**: Vitest with in-memory SQLite (`:memory:`) for DB queries
- **E2E**: Playwright for critical user flows
- **Test file location**: co-located with source `(user-profile.test.ts)` or in `__tests__/`

---

## Environment Variables

```env
# Required
DATABASE_URL="file:./data.db"
AUTH_SECRET="openssl rand -base64 32"

# Optional (OAuth)
GITHUB_CLIENT_ID=""
GITHUB_CLIENT_SECRET=""
GOOGLE_CLIENT_ID=""
GOOGLE_CLIENT_SECRET=""

# Email (Resend or similar)
RESEND_API_KEY=""
EMAIL_FROM="noreply@example.com"
```

**Never commit `.env` files.** Use `.env.example` with placeholder values.

---

## Deployment Checklist

- [ ] `pnpm build` passes without errors
- [ ] All env vars set in Vercel/Railway dashboard
- [ ] Database migration run against production DB
- [ ] `middleware.ts` auth guards tested
- [ ] Error page (`error.tsx`) renders correctly
- [ ] `robots.txt` and `sitemap.ts` present
- [ ] Rate limiting configured on auth routes
