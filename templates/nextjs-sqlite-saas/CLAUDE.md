# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project context for Claude Code. Every rule exists for a reason.

## Stack

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js App Router | 15.x | Server Components, streaming, layouts |
| Language | TypeScript | 5.x strict | Type safety, no `any` |
| Database | better-sqlite3 | 11.x | Embedded, zero-config, fast reads |
| ORM | Drizzle ORM | 0.35+ | Type-safe SQL, migrations, SQLite-first |
| Auth | better-auth | 1.x | Session-based, SQLite-native |
| Styling | Tailwind CSS | 4.x | Utility-first, no custom CSS |
| UI | shadcn/ui | latest | Copy-paste components, Radix primitives |
| Validation | Zod | 3.x | Runtime + static types from one schema |
| Testing | Vitest | 2.x | Fast, ESM-native |
| Package | pnpm | 9.x | Strict, fast, monorepo-ready |

## Folder Structure

```
src/
├── app/                    # Next.js App Router (routes only)
│   ├── (auth)/             # Auth group: login, register, forgot
│   ├── (dashboard)/        # Protected group: app pages
│   ├── api/                # API routes (thin — delegate to services)
│   ├── layout.tsx          # Root layout (providers, fonts, metadata)
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # shadcn/ui primitives (Button, Input, etc.)
│   └── features/           # Feature-specific components
├── db/
│   ├── schema.ts           # Drizzle schema (all tables)
│   ├── migrations/         # Generated SQL migrations
│   ├── index.ts            # DB client singleton
│   └── seed.ts             # Dev seed script
├── lib/
│   ├── auth.ts             # better-auth instance
│   ├── utils.ts            # Generic helpers (cn, formatDate, etc.)
│   └── constants.ts        # App-wide constants
├── services/               # Business logic
│   └── user.service.ts
├── types/                  # Shared TypeScript types
└── middleware.ts            # Auth redirect, rate limiting
```

## Commands

```bash
pnpm dev                    # Start dev server (Turbopack)
pnpm build                  # Production build
pnpm db:generate            # Generate migration from schema changes
pnpm db:migrate             # Run pending migrations
pnpm db:seed                # Seed dev database
pnpm test                   # Run tests
pnpm test:watch             # Tests in watch mode
pnpm lint                   # ESLint + TypeScript check
```

## Database Rules

1. **Schema in `src/db/schema.ts`** — All tables defined here, nowhere else
2. **Migrations are generated, not hand-written** — Change schema → `pnpm db:generate`
3. **No raw SQL in routes** — Use services or Drizzle query builder
4. **IDs are text (nanoid)** — Never auto-increment integers for public-facing IDs
5. **Timestamps are ISO strings** — `text` column, default `new Date().toISOString()`
6. **Soft deletes** — Add `deletedAt` text column, filter with `isNull(schema.table.deletedAt)`
7. **Foreign keys are explicit** — Always define `.references()` in schema

## Component Patterns

```tsx
// ✅ Server Component (default) — data fetching, no hooks
export async function UserList() {
  const users = await userService.list();
  return <div>{users.map(u => <UserCard key={u.id} user={u} />)}</div>;
}

// ✅ Client Component — interactivity only
'use client';
export function UserCard({ user }: { user: User }) {
  const [expanded, setExpanded] = useState(false);
  return <div onClick={() => setExpanded(!expanded)}>...</div>;
}

// ❌ Don't fetch in client components
'use client';
export function BadUserList() {
  const [users, setUsers] = useState([]);
  useEffect(() => { fetch('/api/users').then(r => r.json()).then(setUsers); }, []);
}
```

## API Route Pattern

```tsx
// src/app/api/users/route.ts
import { z } from 'zod';
import { userService } from '@/services/user.service';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

export async function POST(req: Request) {
  const body = await req.json();
  const data = CreateUserSchema.parse(data);
  const user = await userService.create(data);
  return Response.json(user, { status: 201 });
}
```

## Anti-Patterns (Don't Do These)

| ❌ Don't | ✅ Do | Why |
|-----------|-------|-----|
| `fetch()` in Server Components | Direct function call | Server Components can call functions directly |
| `useState` for form data | Server Actions + `useFormState` | Progressive enhancement, less JS |
| Custom CSS files | Tailwind classes | Consistency, no specificity wars |
| `any` type | `unknown` + type guard | Type safety |
| Inline SQL strings | Drizzle query builder | Type safety, injection prevention |
| `console.log` for debugging | `console.error` + structured logging | Production readiness |
| Secrets in code | `.env.local` + `z.string()` validation | Security |
| Client-side auth checks | Middleware + server-side only | Auth must be server-verified |

## Auth Flow

1. User registers → `POST /api/auth/register` → creates user + session
2. Session stored in SQLite `sessions` table (not JWT)
3. Cookie: `session_token` (httpOnly, secure, sameSite: lax)
4. Middleware checks session on every `(dashboard)` route
5. API routes call `auth.requireUser(req)` → throws 401 if invalid

## Testing Conventions

- Unit tests: `src/**/*.test.ts` (co-located with source)
- Integration tests: `tests/api/*.test.ts`
- DB tests: Use `:memory:` SQLite, run migrations in `beforeAll`
- Mock at the service boundary, never mock DB directly

## What We Don't Do (And Why)

- **No tRPC** — API routes are simpler, fewer abstractions
- **No Prisma** — Drizzle is lighter, better SQLite support
- **No Redux/Zustand** — React Server Components handle most state
- **No Docker for dev** — SQLite is a file, no container needed
- **No GraphQL** — REST is simpler for SaaS CRUD
- **No monorepo** — Single app, scale when needed
