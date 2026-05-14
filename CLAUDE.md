# Next.js + SQLite SaaS Project

## Stack
- Next.js 15 (App Router) — RSC, Server Actions, Middleware
- TypeScript — strict mode
- SQLite via better-sqlite3 (dev) / Turso (production)
- Drizzle ORM — schema-first, code-gen migrations
- Auth: NextAuth.js v5 (credentials + provider pattern)
- UI: shadcn/ui + Tailwind CSS v4
- Validation: zod (shared between client + server)

## Folder Structure
```
src/
  app/                  # App Router pages & API routes
    (auth)/             # Auth-grouped routes (login, register)
    (dashboard)/        # Protected dashboard routes
    api/                # API route handlers
  components/
    ui/                 # shadcn/ui primitives
    forms/              # React Hook Form + zod wrappers
    layout/             # Sidebar, navbar, shell
  db/
    schema/             # Drizzle table definitions
    migrations/         # Auto-generated migration files
    queries/            # Reusable SQL query helpers
  lib/
    utils.ts            # cn() helper, formatDate, etc.
    constants.ts        # App-wide constants, env schema
    email.ts            # Email sending (Resend / React Email)
  actions/              # Server Actions co-located by domain
  hooks/                # Custom React hooks
public/                 # Static assets
```

## Naming Conventions
- **Files**: kebab-case for app routes, camelCase for components: `user-settings.tsx`
- **Components**: PascalCase exports, one component per file
- **Functions**: camelCase — `getUserById()`, `createSubscription()`
- **DB tables**: snake_case — `user_sessions`, `subscription_plans`
- **DB columns**: snake_case — `created_at`, `stripe_customer_id`
- **API routes**: RESTful plurals — `api/users/[id]/subscriptions`
- **Server Actions**: verb-noun — `updateProfile()`, `deleteTeam()`
- **Types/Interfaces**: PascalCase with `Type` suffix — `UserType`, `PlanType`
- **Environment variables**: `NEXT_PUBLIC_` prefix for client-safe vars

## SQL / Migration Rules
- Every schema change = new migration file (never edit existing)
- Always wrap data migrations in transactions
- Soft deletes preferred: use `deleted_at TIMESTAMP` column
- Index every foreign key column
- Use `text` instead of `varchar` (SQLite treats them the same)
- Run `pnpm db:migrate` before `pnpm dev` after pulling
- Rollback migrations locally with `pnpm db:rollback`

## Component Patterns
```tsx
// Server Component (default)
async function UserProfile({ userId }: { userId: string }) {
  const user = await db.query.users.findFirst({
    where: eq(users.id, userId),
  });
  return <div>{user.name}</div>;
}

// Client Component (when interactivity needed)
'use client';
function DeleteAccountButton() {
  const [open, setOpen] = useState(false);
  return <Dialog open={open} onOpenChange={setOpen}>...</Dialog>;
}
```

## Server Action Pattern
```ts
'use server';
import { z } from 'zod';
import { revalidatePath } from 'next/cache';

const schema = z.object({ name: z.string().min(1).max(50) });

export async function updateTeam(formData: FormData) {
  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };
  await db.update(teams).set({ name: parsed.data.name });
  revalidatePath('/dashboard/settings');
}
```

## Dev Commands
| Command | Purpose |
|---------|---------|
| `pnpm dev` | Start dev server with Turbopack |
| `pnpm build` | Production build |
| `pnpm test` | Vitest (unit + integration) |
| `pnpm db:generate` | Generate Drizzle migrations |
| `pnpm db:migrate` | Apply migrations to local DB |
| `pnpm db:studio` | Open Drizzle Studio for data browsing |
| `pnpm lint` | ESLint + Prettier check |
| `pnpm type-check` | tsc --noEmit |

## What We Don't Do (And Why)
- **No `any` types** — defeats TypeScript's purpose; use `unknown` + narrowing
- **No `useEffect` for data fetching** — prefer RSC or Server Actions
- **No inline styles** — use Tailwind classes or CSS modules
- **No barrel exports** (`index.ts` re-exports) — causes circular deps in Next.js
- **No raw SQL strings** — always use Drizzle query builder for type safety
- **No client-side secrets** — env vars with `NEXT_PUBLIC_` are public
- **No `fetch` in Server Components without caching** — use Next.js `fetch` with `next: { revalidate }`

## Auth Pattern
```ts
// Always check session in every protected Server Action / Route Handler
import { auth } from '@/lib/auth';

export async function getSessionOrThrow() {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');
  return session;
}
```