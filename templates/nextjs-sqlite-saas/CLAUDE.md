# CLAUDE.md — Next.js 15 + SQLite SaaS Template

## Stack & Versions

- **Framework**: Next.js 15 (App Router, Server Components by default)
- **Runtime**: Node.js 20+
- **Database**: SQLite via `better-sqlite3` (local) or `@libsql/client` (Turso edge)
- **Auth**: NextAuth.js v5 (Auth.js) with SQLite adapter
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Validation**: Zod (schemas everywhere)
- **API**: tRPC or Server Actions (prefer Server Actions for mutations)
- **Deployment**: Vercel (frontend) + Turso (DB) or self-hosted

## Project Structure

```
├── app/                    # Next.js App Router
│   ├── (auth)/            # Route groups for auth pages
│   │   ├── login/
│   │   └── register/
   ├── api/                # API routes (minimal, prefer Server Actions)
│   ├── dashboard/         # Protected routes
│   ├── layout.tsx         # Root layout with providers
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/               # shadcn/ui components (never edit directly)
│   └── app/              # App-specific components
├── lib/
│   ├── db/               # Database layer
│   │   ├── index.ts      # Connection + client export
│   │   ├── schema.ts     # Drizzle ORM schema
│   │   └── migrations/   # Generated migrations (never hand-edit)
│   ├── auth.ts           # Auth.js configuration
│   └── utils.ts          # cn() and helpers
├── server/
│   └── actions/          # Server Actions only
│       ├── user.ts
│       └── subscription.ts
├── types/
│   └── index.ts          # Shared TypeScript types
├── public/
├── .env.local            # Never commit
├── drizzle.config.ts
└── next.config.js
```

## Naming Conventions

- **Files**: kebab-case (`user-profile.tsx`)
- **Components**: PascalCase (`UserProfile`)
- **Server Actions**: camelCase (`createSubscription`)
- **Database tables**: snake_case, plural (`users`, `subscriptions`)
- **Database columns**: snake_case (`created_at`, `stripe_customer_id`)
- **Environment variables**: UPPER_SNAKE_CASE (`DATABASE_URL`, `NEXTAUTH_SECRET`)

## Database Conventions

### Schema Rules

1. **Every table has**: `id` (integer primary key), `created_at`, `updated_at`
2. **Soft deletes only**: Never `DELETE FROM`, use `deleted_at` timestamp
3. **Foreign keys**: Always indexed, always `ON DELETE CASCADE` unless business reason not to
4. **JSON columns**: Use `text` with Zod validation, not SQLite JSON extension (portability)
5. **Enums**: Store as `text` with CHECK constraints or Zod validation at app layer

### Migration Rules

1. **Generate**: `npx drizzle-kit generate` (never write raw SQL migrations)
2. **Apply**: `npx drizzle-kit migrate` in CI/CD only
3. **Local dev**: `npx drizzle-kit push` (auto-sync, never for production)
4. **Migration names**: Descriptive, timestamped by Drizzle automatically
5. **Rollback strategy**: Back up DB before prod migrations (Turso has built-in snapshots)

### Query Patterns

```typescript
// ✅ Good: Typed queries with Drizzle
const user = await db.select().from(users).where(eq(users.id, id)).get();

// ❌ Bad: Raw SQL without type safety
const user = await db.run(`SELECT * FROM users WHERE id = ${id}`);

// ✅ Good: Transactions for multi-step operations
await db.transaction(async (tx) => {
  await tx.insert(subscriptions).values({ ... });
  await tx.update(users).set({ plan: 'pro' }).where(eq(users.id, userId));
});
```

## Component Patterns

### Server Components (Default)

```typescript
// ✅ Good: Fetch data directly in Server Component
async function DashboardPage() {
  const session = await auth();
  if (!session) redirect('/login');
  
  const data = await db.select().from(projects).where(eq(projects.userId, session.user.id));
  
  return <ProjectList projects={data} />;
}
```

### Client Components (Only when needed)

```typescript
'use client';

// ✅ Good: Client component for interactivity only
function ProjectForm() {
  const [name, setName] = useState('');
  
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await createProject({ name }); // Server Action
  }
  
  return <form onSubmit={handleSubmit}>...</form>;
}
```

### Server Actions

```typescript
'use server';

// ✅ Good: Validate input, handle errors, revalidate
export async function createProject(input: CreateProjectInput) {
  const session = await auth();
  if (!session) throw new Error('Unauthorized');
  
  const data = createProjectSchema.parse(input);
  
  try {
    const project = await db.insert(projects).values({
      ...data,
      userId: session.user.id,
    }).returning().get();
    
    revalidatePath('/dashboard');
    return { success: true, project };
  } catch (error) {
    // Log to monitoring service
    throw new Error('Failed to create project');
  }
}
```

## What We Do

1. **Server Components by default** — Only add `'use client'` for browser APIs or state
2. **Server Actions for mutations** — No API routes unless external integration needed
3. **Zod everywhere** — Validate at boundaries (forms, API, DB inputs)
4. **Type-safe DB** — Drizzle ORM with strict TypeScript
5. **Soft deletes** — Never hard delete user data
6. **Optimistic UI** — `useOptimistic` for immediate feedback on mutations
7. **Error boundaries** — Each route has `error.tsx`
8. **Loading states** — Each route has `loading.tsx` (Suspense)

## What We Don't Do (And Why)

1. **No raw SQL in components** — Type safety and maintainability
2. **No `any` types** — Use `unknown` + type guards if type is uncertain
3. **No client-side data fetching for initial load** — Server Components handle this
4. **No storing secrets in code** — Environment variables only
5. **No unvalidated user input** — Zod validation on all inputs
6. **No `SELECT *`** — Explicit column selection for performance
7. **No migrations without backups** — Production data is sacred
8. **No mixing auth patterns** — Auth.js only, no custom JWT logic

## Dev Commands

```bash
# Setup
npm install
cp .env.example .env.local
npx drizzle-kit push          # Sync schema to local DB

# Development
npm run dev                   # Start dev server
npx drizzle-kit studio        # Open Drizzle Studio (DB GUI)

# Build & Deploy
npm run build                 # Production build
npx drizzle-kit migrate       # Run pending migrations (production)
```

## Environment Variables

```bash
# Required
DATABASE_URL="file:./local.db"           # or libsql:// for Turso
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="generate-with-openssl-rand-base64-32"

# OAuth Providers (at least one)
GITHUB_CLIENT_ID=""
GITHUB_CLIENT_SECRET=""

# Optional
TURSO_AUTH_TOKEN=""                      # Only for Turso
STRIPE_SECRET_KEY=""                     # For payments
STRIPE_WEBHOOK_SECRET=""
```

## Anti-Patterns Checklist

Before submitting PR, verify:

- [ ] No `'use client'` without reason (add comment why if used)
- [ ] No unvalidated `formData.get()` without Zod schema
- [ ] No database queries in Client Components
- [ ] No hardcoded colors (use Tailwind classes)
- [ ] No `console.log` in production code (use proper logger)
- [ ] No missing `await` on async operations
- [ ] No `any` types in new code

## Testing Strategy

1. **Unit tests**: Vitest for utilities and schemas
2. **Integration tests**: Playwright for critical user flows
3. **DB tests**: Use in-memory SQLite, reset between tests
4. **Auth tests**: Mock session, test both authenticated/unauthenticated states

## Deployment Checklist

- [ ] Environment variables set in Vercel
- [ ] Database migrated (Turso or SQLite file)
- [ ] OAuth callbacks configured (GitHub/Google settings)
- [ ] Stripe webhooks configured (if using payments)
- [ ] `next.config.js` has proper headers/redirects
- [ ] Error monitoring configured (Sentry recommended)

---

**Usage**: Copy this file to your project root as `CLAUDE.md`. Claude Code will automatically read it when working on your codebase.