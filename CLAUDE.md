# CLAUDE.md — Next.js 15 + SQLite SaaS

This file provides context and instructions for Claude Code when working on this project.

## Project Overview

This is a SaaS application built with:
- **Next.js 15** (App Router, React 19, Server Actions)
- **SQLite** via `better-sqlite3` (local dev) / **Turso** (production)
- **Drizzle ORM** for type-safe database queries
- **TypeScript** strict mode
- **Tailwind CSS** for styling
- **NextAuth.js v5** for authentication

## Development Commands

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:3000)
npm run dev

# Run database migrations
npm run db:migrate

# Reset database (dev only — destroys data)
npm run db:reset

# Run tests
npm run test

# Type check
npm run type-check

# Build for production
npm run build
```

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth routes (login, register)
│   ├── (dashboard)/        # Protected dashboard routes
│   ├── api/                # API routes (webhooks, external)
│   └── layout.tsx          # Root layout
├── components/
│   ├── ui/                 # Reusable UI primitives (shadcn)
│   └── features/           # Feature-specific components
├── lib/
│   ├── db/                 # Database: schema, migrations, client
│   ├── auth/               # Auth configuration
│   └── utils.ts            # Shared utilities
├── hooks/                  # Custom React hooks
└── types/                  # Global TypeScript types
```

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase, prefix `use` | `useSubscription.ts` |
| API routes | kebab-case folders | `src/app/api/stripe-webhook/` |
| DB tables | snake_case, plural | `user_sessions` |
| DB columns | snake_case | `created_at`, `user_id` |
| TypeScript types | PascalCase, suffix `Type` | `UserType` |
| CSS variables | kebab-case, prefix `--` | `--color-primary` |
| Environment vars | SCREAMING_SNAKE_CASE, prefix `NEXT_PUBLIC_` if client | `NEXT_PUBLIC_APP_URL` |

## Database Rules

### Schema (Drizzle ORM)

- All tables MUST have `id` (uuid, primary key), `created_at`, `updated_at`
- Use `references()` with `onDelete('cascade')` for foreign keys
- Add indexes on frequently queried columns (email, foreign keys)
- Use enum types for status fields, never strings

### Migrations

- **Never edit existing migrations** — create a new one
- Run `npm run db:generate` after schema changes
- Run `npm run db:migrate` to apply
- Test migrations on a copy of production data before deploying
- Migrations MUST be reversible (include `down` function)

### Query Patterns

```typescript
// ✅ GOOD: Type-safe, parameterized
const user = await db.query.users.findFirst({
  where: eq(users.email, email),
  with: { subscriptions: true },
});

// ❌ BAD: Raw SQL without parameters
const user = await db.execute(`SELECT * FROM users WHERE email = '${email}'`);
```

## Patterns to Follow

### 1. Server Components by Default

- Default to Server Components (`async` components)
- Only add `"use client"` when you need: `useState`, `useEffect`, event handlers, browser APIs
- Keep client components at the leaves of the component tree

### 2. Server Actions for Mutations

```typescript
// ✅ GOOD: Server Action in app/actions/
export async function updateProfile(formData: FormData) {
  const session = await auth();
  if (!session) throw new Error("Unauthorized");

  const data = profileSchema.parse(Object.fromEntries(formData));
  await db.update(users).set(data).where(eq(users.id, session.user.id));
  revalidatePath("/dashboard");
}
```

### 3. Error Handling

- Use Next.js `error.tsx` and `global-error.tsx` files
- Always wrap Server Actions in try/catch with user-friendly messages
- Log errors to your monitoring service (Sentry)
- Never expose stack traces to users in production

### 4. Authentication

- Check auth at the route level (middleware) AND in Server Actions
- Use `auth()` from NextAuth, not `getSession()`
- Store minimal session data (user ID, role), fetch rest from DB

### 5. Environment Variables

- Client-side vars MUST be prefixed `NEXT_PUBLIC_`
- Never put secrets in client components
- Use `zod` to validate env vars at startup:
```typescript
const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  NEXTAUTH_SECRET: z.string().min(32),
});
export const env = envSchema.parse(process.env);
```

## Anti-Patterns to Avoid

### ❌ Don't do this:

```typescript
// ❌ Fetching in client components
useEffect(() => {
  fetch('/api/users').then(...)
}, [])

// ❌ N+1 queries in loops
for (const user of users) {
  const posts = await db.query.posts.findMany({ where: eq(posts.userId, user.id) });
}

// ❌ Storing sensitive data in localStorage
localStorage.setItem('token', token);

// ❌ Ignoring TypeScript errors with @ts-ignore
// @ts-ignore
const result = someUnsafeOperation();

// ❌ Direct DB access in client components
const db = useDB(); // NEVER
```

### ✅ Do this instead:

```typescript
// ✅ Server Component with async data fetch
export default async function UsersPage() {
  const users = await db.query.users.findMany();
  return <UserList users={users} />;
}

// ✅ Batch queries with IN clause
const userIds = users.map(u => u.id);
const posts = await db.query.posts.findMany({
  where: inArray(posts.userId, userIds),
});

// ✅ HttpOnly cookies for tokens
cookies().set('session', token, { httpOnly: true, secure: true });

// ✅ Fix the type error properly
const result = someUnsafeOperation() as ExpectedType;
```

## Deployment Checklist

- [ ] All migrations applied
- [ ] Environment variables set (DATABASE_URL, NEXTAUTH_SECRET, etc.)
- [ ] Sentry/error monitoring configured
- [ ] Rate limiting on API routes
- [ ] CORS configured if needed
- [ ] Database backups scheduled
- [ ] SSL/TLS enabled
- [ ] `NEXT_PUBLIC_APP_URL` matches production domain

## Testing

- Unit tests: `src/**/*.test.ts`
- Integration tests: `tests/integration/**/*.test.ts`
- E2E tests: `tests/e2e/**/*.spec.ts` (Playwright)
- Run `npm run test` before pushing
- Aim for 80%+ coverage on `lib/` and `app/api/`

---

**Last updated:** 2026-06-30
**Maintainer:** Klacb
