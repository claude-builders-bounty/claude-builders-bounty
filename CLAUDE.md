# CLAUDE.md — Next.js 15 + SQLite SaaS

> **This file is the source of truth for Claude Code when working in this repo.**
> Treat every rule as a hard constraint. Every rule has a reason.

## Stack & Versions

| Component | Version / Choice | Why |
|-----------|-----------------|-----|
| Framework | Next.js 15 (App Router) | Server Components by default, streaming, partial prerendering |
| Database | better-sqlite3 (dev/staging), Turso/libsql (prod) | Sync API in dev, HTTP-edge in prod — same SQL dialect |
| ORM | Drizzle ORM | Type-safe SQL, no code generation, lightweight |
| Auth | NextAuth.js v5 (Auth.js) | OAuth + credentials, edge-compatible |
| Styling | Tailwind CSS v4 | Utility-first, no runtime CSS-in-JS |
| Forms | React Hook Form + Zod | Performant validation with type inference |
| UI Primitives | shadcn/ui (Radix) | Accessible, copy-paste, no dependency package |
| Package Manager | npm | Default, no lockfile migration risk |
| Runtime | Node.js 20+ | Required by Next.js 15 |
| Deployment | Vercel or Railway | Both support edge functions + SQLite edge |
| TypeScript | Strict mode | `strict: true` in tsconfig.json |

## Folder Structure

```
/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Route group: auth pages
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx            # Auth-specific layout (no nav)
│   ├── (dashboard)/              # Route group: authenticated pages
│   │   ├── layout.tsx            # Sidebar + auth guard
│   │   ├── page.tsx              # Dashboard home
│   │   └── settings/page.tsx
│   ├── api/                      # API route handlers
│   │   └── [resource]/route.ts   # RESTful: GET/POST/PATCH/DELETE
│   ├── layout.tsx                # Root layout (providers, fonts)
│   ├── page.tsx                  # Landing page
│   └── globals.css
├── components/
│   ├── ui/                       # shadcn/ui primitives only
│   ├── forms/                    # Form components (React Hook Form + Zod)
│   └── features/                 # Business-logic components
│       └── users/
│           ├── user-list.tsx     # Server Component (data fetch)
│           ├── user-list-client.tsx  # Client wrapper (interactivity)
│           └── user-card.tsx
├── lib/
│   ├── db/
│   │   ├── index.ts             # DB client singleton
│   │   ├── schema.ts            # Drizzle schema definitions
│   │   └── migrations/          # SQL migration files
│   ├── auth/
│   │   ├── config.ts            # NextAuth configuration
│   │   └── middleware.ts        # Edge middleware for route protection
│   ├── actions/                 # Server Actions (use server)
│   │   └── users.ts             # createUser, updateUser, deleteUser
│   └── utils.ts                 # Shared helpers (formatting, dates, etc.)
├── scripts/
│   ├── migrate.ts               # Run pending migrations
│   └── seed.ts                  # Seed development database
├── env.ts                       # Typed environment variables (t3-env)
├── CLAUDE.md                    # ← You are here
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

**Key constraints:**
- **Never** put business logic in `app/api/` route files. Route files call into `lib/` modules.
- **Never** fetch data in Client Components. Fetch in Server Components and pass down as props.
- `lib/` is the single source of truth for all shared logic.

## Naming Conventions

| What | Convention | Example | Why |
|------|-----------|---------|-----|
| Pages / Routes | kebab-case | `app/user-profile/page.tsx` | URL consistency |
| Components | PascalCase | `UserProfileCard.tsx` | React convention |
| Server Actions | camelCase | `createOrganization()` | Function convention |
| Database tables | snake_case | `user_organizations` | SQL convention |
| Database columns | snake_case | `created_at` | Drizzle maps to camelCase in TS |
| API routes | kebab-case | `app/api/billing-events/route.ts` | REST convention |
| CSS classes | Tailwind only | `className="flex gap-2"` | No custom CSS, no inline styles |
| Types / Interfaces | PascalCase | `CreateUserInput` | TypeScript convention |
| Zod schemas | PascalCase + Schema | `CreateUserSchema` | Explicit intent |
| Env variables | UPPER_SNAKE | `DATABASE_URL` | Standard convention |

## Database & Migration Rules

### Migrations

1. **All schema changes via Drizzle migrations** in `lib/db/migrations/`.
2. **Never run DROP or ALTER in production migrations.** Additive only. Deprecate columns over multiple releases.
3. **Never use `db.exec(rawSql)` in application code.** Always use Drizzle's typed query builder.
4. **Always wrap multi-step mutations in transactions.**

### Query Patterns

```typescript
// DO: Drizzle query builder — type-safe, composable
const user = await db.query.users.findFirst({
  where: eq(users.id, userId),
  with: { organization: true },
});

// DO: Parameterized queries when using raw SQL
const rows = db.all('SELECT * FROM users WHERE org_id = ?', [orgId]);

// DON'T: String interpolation (SQL injection risk)
// db.all(`SELECT * FROM users WHERE org_id = ${orgId}`); // NEVER

// DO: Batch inserts for bulk operations
await db.insert(users).values(batch);

// DON'T: Loop-and-insert one row at a time
```

### Transaction Pattern

```typescript
// Always use db.transaction() for multi-step mutations
const result = await db.transaction(async (tx) => {
  const [user] = await tx.insert(users).values(input).returning();
  await tx.insert(orgMembers).values({ userId: user.id, orgId });
  return user;
});
```

### Database Connection

```typescript
// lib/db/index.ts — singleton pattern
import { drizzle } from 'drizzle-orm/better-sqlite3';
import Database from 'better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(env.DATABASE_URL);
export const db = drizzle(sqlite, { schema });

// For Turso (production), swap the driver:
// import { drizzle } from 'drizzle-orm/libsql';
// import { createClient } from '@libsql/client';
```

## Auth Configuration

```typescript
// lib/auth/config.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { db } from '@/lib/db';

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        // Validate with Zod first, then query DB
        const parsed = LoginSchema.safeParse(credentials);
        if (!parsed.success) return null;
        
        const user = await db.query.users.findFirst({
          where: eq(users.email, parsed.data.email),
        });
        if (!user) return null;
        
        const valid = await bcrypt.compare(parsed.data.password, user.passwordHash);
        return valid ? { id: user.id, email: user.email } : null;
      },
    }),
  ],
  pages: { signIn: '/login' },
});
```

**Auth rules:**
- Route protection via `middleware.ts` (edge), not per-page.
- **Never** expose password hashes or auth tokens in API responses.
- Use `auth()` in Server Components, `useSession()` in Client Components.

## Component Patterns

### Server vs Client Components

```typescript
// Server Component (default — no "use client" directive)
// Can be async, can access DB directly
export default async function UserList() {
  const users = await db.query.users.findMany();
  return <UserListView users={users} />;
}

// Client Component — ONLY for interactivity
'use client';
export function UserListView({ users }: { users: User[] }) {
  const [filter, setFilter] = useState('');
  return /* interactive UI */;
}
```

Rule: if a component needs `useState`, `useEffect`, `onClick`, or browser APIs, it's a Client Component. Everything else stays Server Component.

### Form Pattern (React Hook Form + Zod)

```typescript
// lib/actions/users.ts
'use server';
import { db } from '@/lib/db';
import { CreateUserSchema } from '@/lib/validations';

export async function createUser(formData: FormData) {
  const parsed = CreateUserSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { ok: false, errors: parsed.error.flatten().fieldErrors };
  }
  const user = await db.insert(users).values(parsed.data).returning();
  revalidatePath('/users');  // Revalidate the list page
  return { ok: true, user };
}
```

```typescript
// components/forms/create-user-form.tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

export function CreateUserForm() {
  const form = useForm<CreateUserInput>({
    resolver: zodResolver(CreateUserSchema),
  });
  
  async function onSubmit(values: CreateUserInput) {
    const result = await createUser(values);
    if (!result.ok) { /* show field errors */ }
  }
  // ... form JSX
}
```

### Feature Component Organization

Each feature gets its own folder:
```
components/features/<feature>/
├── <feature>-list.tsx       # Server Component (data fetch)
├── <feature>-list-client.tsx # Client wrapper (search, filter, sort)
├── <feature>-card.tsx       # Display card
├── <feature>-form.tsx       # Create/Edit form
└── index.ts                 # Re-export public API
```

## Server Actions (Data Mutations)

**Rules:**
1. **All mutations go through Server Actions** in `lib/actions/`. Never mutate in Client Components.
2. **Always validate with Zod before touching the database.**
3. **Always return `{ ok: boolean, data?, errors? }`** — use a discriminated union.
4. **Always call `revalidatePath()` or `revalidateTag()` after mutations.**

```typescript
// Standard action return type
type ActionResult<T = void> =
  | { ok: true; data: T }
  | { ok: false; errors: Record<string, string[]> };
```

## API Route Pattern

```typescript
// app/api/users/route.ts
import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const page = parseInt(searchParams.get('page') ?? '1');
  
  const users = await db.query.users.findMany({
    limit: 20,
    offset: (page - 1) * 20,
  });
  
  return Response.json({ ok: true, data: users, page });
}
```

**Rules:**
- Use `nextUrl.searchParams` for query params — don't parse `request.url` manually.
- Use `request.json()` for POST/PATCH bodies — always validate before processing.
- **Never** return raw database rows. Transform into a typed DTO.

## What We Don't Do (and Why)

| Pattern | Reason to Avoid |
|---------|----------------|
| Class components | Next.js 15 + React 19 favor hooks and Server Components |
| `useEffect` for data fetching | Server Components fetch data; `useEffect` causes client-side waterfalls |
| `useEffect` for derived state | Use derived values directly in render; `useMemo` only when profiling proves it needed |
| Inline styles or CSS modules | Tailwind is the single source of truth for all styling |
| Direct DOM manipulation | React manages the DOM; use refs only for focus/scroll/measurement |
| `any` type | Use `unknown` + type guards, or proper generics |
| `// @ts-ignore` or `// @ts-expect-error` without comment | Suppress only with a dated comment explaining why |
| Returning DB rows from API routes | Transform into typed DTOs; never leak internal structure |
| Storing secrets in code | Environment variables via `env.ts` (t3-env pattern) |
| `console.log` in production | Use structured logging; no `console.log` in lib/ or app/ code |
| ORM migrations in production CI | Run migrations as a separate deploy step, never on-request |

## Anti-Patterns Claude Code Must Flag

If you try any of these, stop and reconsider:

- **`'use server'` in component files** — Server Actions belong in `lib/actions/`, not in `components/`.
- **String interpolation in SQL** — Use Drizzle query builder or parameterized queries.
- **Plain-text password storage** — Always hash with bcrypt (cost factor 12+).
- **`JSON.parse()` on untrusted input** — Use Zod for all parsing and validation.
- **Fetching in Client Components** — Lift data fetching to the nearest Server Component parent.
- **Multiple `use client` boundaries** — One Client Component wrapper per interactive island; keep the boundary thin.
- **Importing `server-only` packages into Client Components** — Will break at build time.

## Dev Commands

```bash
npm run dev           # Start dev server (http://localhost:3000)
npm run build         # Production build
npm run start         # Start production server
npm run db:migrate    # Run pending Drizzle migrations
npm run db:generate   # Generate migration from schema changes
npm run db:seed       # Seed development database
npm run db:studio     # Open Drizzle Studio (visual DB browser)
npm run lint          # ESLint check
npm run type-check    # tsc --noEmit
npm run format        # Prettier format
npm run test          # Vitest unit tests
npm run test:e2e      # Playwright E2E tests
```

## Testing Conventions

```typescript
// Unit test pattern (Vitest)
import { describe, it, expect } from 'vitest';

describe('createUser', () => {
  it('rejects short passwords', async () => {
    const result = await createUser({ email: 'a@b.com', password: '123' });
    expect(result.ok).toBe(false);
    expect(result.errors?.password).toBeDefined();
  });
});
```

- **Unit tests**: `vitest` — test pure functions, validation, and Server Actions (with mocked DB).
- **E2E tests**: `playwright` — test critical user flows (signup, login, CRUD).
- Mock the DB using `better-sqlite3` in-memory for unit tests.
- No snapshot tests — they break on every intentional change and get blindly updated.

## Environment Variables

```typescript
// env.ts — single source of truth for all env vars
import { createEnv } from '@t3-oss/env-nextjs';
import { z } from 'zod';

export const env = createEnv({
  server: {
    DATABASE_URL: z.string().url(),
    AUTH_SECRET: z.string().min(32),
    AUTH_GOOGLE_ID: z.string().optional(),
    AUTH_GOOGLE_SECRET: z.string().optional(),
  },
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url(),
  },
  runtimeEnv: process.env,
});
```

**Never** access `process.env` directly. Always use the typed `env` object. This catches missing variables at startup, not at runtime.

## Git Conventions

- Branch naming: `<type>/<description>` — e.g., `feat/user-invites`, `fix/login-redirect`
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- PR title matches the primary commit message
- Keep PRs under 500 lines and 10 files — split large changes logically
