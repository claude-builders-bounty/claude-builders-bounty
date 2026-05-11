# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated project context for Claude Code. Paste into your project root.

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components + streaming |
| Language | TypeScript | 5.x | Strict mode always |
| Database | better-sqlite3 | 11.x | Embedded, zero-config, fast |
| ORM | Drizzle | latest | Type-safe, SQL-first, zero runtime |
| Auth | Lucia | 3.x | Session-based, DB-backed, no vendor lock-in |
| Styling | Tailwind CSS | 4.x | Utility-first, JIT |
| Validation | Zod | 3.x | Infer types from schemas |
| Testing | Vitest | 2.x | Fast, ESM-native |

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group (login, register)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/       # Protected route group
│   │   ├── layout.tsx     # Dashboard shell (sidebar + auth check)
│   │   └── settings/
│   ├── api/               # Route handlers
│   │   └── [...slug]/     # REST endpoints
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── lib/
│   ├── db/                # Database layer
│   │   ├── index.ts       # DB connection singleton
│   │   ├── schema.ts      # Drizzle schema (source of truth)
│   │   └── migrations/    # SQL migration files
│   ├── auth/              # Auth logic
│   │   ├── index.ts       # Lucia config
│   │   └── session.ts     # Session helpers
│   ├── validation/        # Zod schemas
│   └── utils.ts           # Shared utilities
├── components/
│   ├── ui/                # Primitive UI (Button, Input, Dialog)
│   └── features/          # Feature-specific components
└── middleware.ts           # Auth middleware
```

## Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run db:generate  # Generate migration from schema changes
npm run db:migrate   # Run pending migrations
npm run db:push      # Push schema directly (dev only!)
npm run db:studio    # Drizzle Studio (DB browser)
npm run test         # Run all tests
npm run test:watch   # Run tests in watch mode
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
```

## Database Rules

### Schema is Source of Truth
- **NEVER** write raw SQL migrations by hand
- Change `src/lib/db/schema.ts` → run `npm run db:generate` → review the generated SQL → run `npm run db:migrate`
- All column types, defaults, and constraints live in the Drizzle schema

### Migration Conventions
- One migration per PR that changes the schema
- Migration files are immutable — never edit a committed migration
- Name convention: `0001_add_users_table.sql`
- Always include both `UP` and `DOWN` (rollback) in the same file

### Query Patterns
```typescript
// ✅ DO: Use Drizzle query builder
const users = await db.select().from(usersTable).where(eq(usersTable.email, email));

// ❌ DON'T: Raw SQL strings
const users = await db.run(sql`SELECT * FROM users WHERE email = ${email}`);
```

### Connection Management
- DB connection is a **singleton** — import from `@/lib/db`
- Never create new connections in route handlers
- better-sqlite3 is synchronous — no connection pooling needed

## Component Patterns

### Server Components by Default
```typescript
// ✅ DO: Server Component (default)
export default async function UserProfile({ params }: Props) {
  const user = await getUser(params.id);
  return <UserCard user={user} />;
}
```

### Client Components Only When Needed
```typescript
// ✅ DO: 'use client' only for interactivity
'use client';
export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### What We Don't Do in Components
- ❌ No `fetch` calls in Client Components — use Server Components or Server Actions
- ❌ No `useEffect` for data fetching — use Server Components
- ❌ No global state management (Redux, Zustand) — use Server Components + URL state
- ❌ No CSS modules — use Tailwind utility classes
- ❌ No `any` types — use Zod inference or explicit types

## Server Actions

```typescript
// ✅ DO: Validate input with Zod, return typed results
'use server';
const schema = z.object({ name: z.string().min(1), email: z.string().email() });
export async function createUser(input: unknown) {
  const data = schema.parse(input);          // throws if invalid
  const [user] = await db.insert(usersTable).values(data).returning();
  revalidatePath('/users');
  return { success: true, user };
}
```

## Auth Patterns

- Session stored in SQLite via Lucia
- Middleware checks session on all `/(dashboard)` routes
- Never store passwords — use OAuth or magic links
- Session ID in httpOnly cookie, not localStorage

## Anti-Patterns (Don't Do This)

| Anti-Pattern | Why | Instead |
|-------------|-----|---------|
| `prisma` | Heavy, slow cold start, bad for edge | Drizzle (lightweight, SQL-first) |
| `next-auth` | Vendor lock-in, complex callbacks | Lucia (simple, DB-backed) |
| `useState` for forms | Unnecessary client state | Server Actions + `useActionState` |
| `getServerSideProps` | Pages Router legacy | App Router `async` components |
| Environment-dependent DB paths in code | Breaks tests | `DATABASE_URL` env var always |
| `JSON.stringify` for API responses | No type safety | Zod schemas + typed returns |
| `setTimeout`/`setInterval` in components | Memory leaks | Server-side scheduling or Web APIs |
| Dynamic imports everywhere | Defeats purpose of RSC | Static imports; dynamic only for heavy client libs |

## Testing

```typescript
// ✅ DO: Test business logic, not framework internals
import { describe, it, expect } from 'vitest';

describe('createUser', () => {
  it('validates email format', async () => {
    await expect(createUser({ name: 'A', email: 'bad' }))
      .rejects.toThrow();
  });
});
```

- Test files: `src/**/*.test.ts`
- Use in-memory SQLite for tests: `:memory:`
- No MSW or API mocking — test against real DB functions

## Environment Variables

```bash
DATABASE_URL=./data.db          # SQLite file path
AUTH_SECRET=<random-32-chars>   # Lucia session secret
NODE_ENV=development            # development | production
```

- Never commit `.env` — only `.env.example`
- All env vars accessed via `process.env.VAR` — no `next/public` prefix
