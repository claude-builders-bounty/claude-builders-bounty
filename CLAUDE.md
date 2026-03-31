# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> **Opinionated rules for Claude Code when working on this SaaS project.**
> Every rule exists because we learned the hard way. Follow them.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | RSC, Server Actions, streaming |
| Database | SQLite via `better-sqlite3` (local) / Turso (prod) | Zero-config dev, edge-ready prod |
| ORM | Drizzle ORM | Type-safe, lightweight, SQLite-native |
| Auth | Lucia Auth or NextAuth v5 | Session-based, no JWT overhead |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, composable components |
| Testing | Vitest + Playwright | Fast unit tests, reliable E2E |
| Package Manager | pnpm | Fast, disk-efficient, strict |

---

## Project Structure

```
/
├── app/                    # Next.js App Router (pages + layouts)
│   ├── (auth)/             # Auth group (login, register, etc.)
│   ├── (dashboard)/        # Dashboard group (authenticated)
│   ├── api/                # Route handlers (keep minimal)
│   └── layout.tsx          # Root layout
├── components/             # Shared UI components
│   ├── ui/                 # shadcn/ui primitives (don't edit directly)
│   └── [feature]/          # Feature-specific components
├── db/                     # Database layer
│   ├── schema.ts           # Drizzle schema definitions
│   ├── migrations/         # Generated migration files
│   └── index.ts            # DB connection singleton
├── lib/                    # Utility functions (no UI)
│   ├── auth.ts             # Auth configuration
│   ├── utils.ts            # General helpers
│   └── validations.ts      # Zod schemas
├── drizzle.config.ts       # Drizzle Kit config
├── tailwind.config.ts      # Tailwind config
└── CLAUDE.md               # You are here
```

### Rules
- **One component per file.** No exceptions.
- **Colocate feature code.** If a component is only used in `/dashboard/settings`, put it in `components/settings/`.
- **Never put business logic in components.** Extract to `lib/` or Server Actions.
- **Route groups `(group)/` are for layout boundaries only.** Don't use them for "organizing" pages.

---

## Naming Conventions

| What | Convention | Example |
|------|------------|---------|
| Components | `PascalCase` | `UserProfile.tsx` |
| Hooks | `use` prefix, `camelCase` | `useCurrentUser.ts` |
| Utilities | `camelCase` | `formatCurrency.ts` |
| Database tables | `snake_case`, plural | `user_sessions` |
| Database columns | `snake_case` | `created_at`, `user_id` |
| API routes | `kebab-case` | `app/api/user-profile/route.ts` |
| Zod schemas | `PascalCase` + `Schema` | `LoginSchema` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_LOGIN_ATTEMPTS` |

---

## Database Rules

### Schema Changes
```bash
# 1. Edit db/schema.ts
# 2. Generate migration
pnpm drizzle-kit generate
# 3. Review migration in db/migrations/
# 4. Apply migration
pnpm drizzle-kit migrate
```

**NEVER**:
- Edit migration files manually (regenerate instead)
- Use `db.run()` for schema changes in production
- Drop columns without a migration (data loss)
- Use `CASCADE` in migrations (we track dependencies manually)

**ALWAYS**:
- Add `createdAt` and `updatedAt` to every table
- Use `integer({ mode: 'timestamp' })` for dates (Unix timestamps)
- Index foreign keys and frequently queried columns
- Name migration files descriptively

### Queries
```typescript
// ✅ DO: Use Drizzle query builder
const users = await db.select().from(usersTable).where(eq(usersTable.id, userId));

// ❌ DON'T: Raw SQL unless absolutely necessary
const users = await db.all('SELECT * FROM users WHERE id = ?', [userId]);
```

---

## Dev Commands

```bash
pnpm dev              # Start dev server (turbopack)
pnpm build            # Production build
pnpm lint             # ESLint + Prettier check
pnpm test             # Run Vitest
pnpm test:e2e         # Run Playwright E2E
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Run migrations
pnpm db:studio        # Open Drizzle Studio (DB GUI)
pnpm db:seed          # Seed dev database
pnpm typecheck        # TypeScript strict check
```

---

## Patterns to Follow

### Server Components by Default
```tsx
// ✅ Server Component (no "use client" needed)
export default async function UserPage({ params }: { params: { id: string } }) {
  const user = await getUser(params.id);
  return <UserCard user={user} />;  // Pass data to client component if needed
}
```

### Server Actions for Mutations
```typescript
// app/actions/user.ts
"use server";

export async function updateUser(formData: FormData) {
  const parsed = UpdateUserSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.error) return { error: parsed.error.flatten() };
  
  await db.update(usersTable).set(parsed.data).where(eq(usersTable.id, userId));
  revalidatePath('/settings');
  return { success: true };
}
```

### Zod for All Validation
```typescript
// lib/validations.ts
export const LoginSchema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
```

### Error Boundaries
```tsx
// Always wrap route groups in error boundaries
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary fallback={<DashboardError />}>
      {children}
    </ErrorBoundary>
  );
}
```

---

## Anti-Patterns (Avoid These)

### ❌ Don't Use `any`
```typescript
// ❌ BAD
function process(data: any) { ... }

// ✅ GOOD
function process(data: User | null) { ... }
```

### ❌ Don't Fetch in Client Components
```tsx
// ❌ BAD: Fetching in useEffect
"use client";
useEffect(() => {
  fetch('/api/users').then(r => r.json()).then(setUsers);
}, []);

// ✅ GOOD: Fetch in Server Component, pass to Client
const users = await db.select().from(usersTable);
return <UserList users={users} />;
```

### ❌ Don't Use `useRouter` for Navigation
```tsx
// ❌ BAD
const router = useRouter();
router.push('/dashboard');

// ✅ GOOD: Use Link component
<Link href="/dashboard">Go to Dashboard</Link>
```

### ❌ Don't Store Sensitive Data in URL
```tsx
// ❌ BAD: Token in URL (logged in server access logs)
/api/reset-password?token=abc123

// ✅ GOOD: Token in header or body
fetch('/api/reset-password', { 
  method: 'POST', 
  body: JSON.stringify({ token }) 
});
```

### ❌ Don't Create Abstractions Prematurely
```tsx
// ❌ BAD: Over-engineered abstraction for 2 usages
const GenericDataTable = createTable<User | Order | Product>({ ... });

// ✅ GOOD: Direct implementation until 3+ usages
<UserTable users={users} />
```

---

## Testing Rules

- **Unit tests** for `lib/` utilities (Vitest)
- **Integration tests** for Server Actions (Vitest + test DB)
- **E2E tests** for critical flows only: auth, checkout, data mutation (Playwright)
- **Never test UI styling** (visual regression tools exist for that)
- **Mock external services** (Stripe, email, etc.) in tests

```bash
# Run specific test file
pnpm vitest run lib/utils.test.ts

# Run with coverage
pnpm vitest run --coverage
```

---

## Git & PR Rules

- **Branch naming**: `feat/short-description`, `fix/issue-number`, `chore/what-changed`
- **Commit messages**: Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR size**: Keep under 400 lines changed (split larger work into stacked PRs)
- **Always run** `pnpm typecheck && pnpm lint && pnpm test` before pushing

---

## Environment Variables

```bash
# .env.local (gitignored)
DATABASE_URL=file:./dev.db          # SQLite path (dev)
TURSO_DATABASE_URL=libsql://...     # Turso URL (prod)
TURSO_AUTH_TOKEN=...                # Turso auth token
AUTH_SECRET=...                     # Generate: npx auth secret
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**NEVER** put secrets in `.env` (only in `.env.local` or deployment secrets).

---

## Performance Checklist

- [ ] Use `React.memo()` only on components that re-render frequently with same props
- [ ] Images: Always use `<Image>` from `next/image` (automatic optimization)
- [ ] Fonts: Use `next/font` (automatic self-hosting)
- [ ] Dynamic imports for heavy client components: `const Chart = dynamic(() => import('./Chart'))`
- [ ] Database: Use `select()` with specific columns, never `select().from(table)` for lists

---

*This CLAUDE.md is a living document. Update it when you discover new patterns or anti-patterns.*
*Last updated: 2026-03-31*
