# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project rules for Claude Code. Every rule exists for a reason.

---

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server Components, streaming, layouts |
| Database | SQLite via better-sqlite3 | Zero-config, single-file, fast reads |
| ORM | Drizzle ORM | Type-safe, SQLite-first, no codegen |
| Auth | NextAuth v5 + Drizzle adapter | Built-in OAuth, session management |
| Styling | Tailwind CSS 4 | Utility-first, no CSS-in-JS runtime |
| Validation | Zod | Runtime + static types from one schema |
| Testing | Vitest + Testing Library | Fast, ESM-native, React support |
| Package Manager | pnpm | Strict, fast, monorepo-ready |

---

## Folder Structure

```
.
├── app/                    # Next.js App Router (pages + layouts)
│   ├── (auth)/             # Auth group (login, register, etc.)
│   ├── (dashboard)/        # Protected dashboard group
│   ├── api/                # API routes
│   └── layout.tsx          # Root layout
├── components/             # Shared React components
│   ├── ui/                 # Primitive UI (Button, Input, Card)
│   └── features/           # Feature-specific components
├── db/                     # Database layer
│   ├── schema.ts           # Drizzle schema definitions
│   ├── migrations/         # SQL migration files
│   └── index.ts            # DB client singleton
├── lib/                    # Utilities, helpers, shared logic
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript type definitions
├── public/                 # Static assets
├── .env.local              # Local environment variables
├── drizzle.config.ts       # Drizzle Kit config
└── CLAUDE.md               # This file
```

---

## Database Rules

### Schema Conventions
- **Table names**: `snake_case`, plural (`users`, `blog_posts`)
- **Column names**: `snake_case` (`created_at`, `user_id`)
- **Primary keys**: Always `id` as `integer` with `autoincrement`
- **Timestamps**: Always include `created_at` and `updated_at`
- **Foreign keys**: Use `.references(() => table.id)` in Drizzle

### Migration Workflow
```bash
# Generate migration from schema changes
pnpm drizzle-kit generate

# Apply migrations
pnpm drizzle-kit migrate

# NEVER edit existing migration files
# ALWAYS create new migrations for schema changes
```

### Query Patterns
```typescript
// ✅ DO: Use prepared statements for repeated queries
const getUserById = db.query.users.prepare(
  "SELECT * FROM users WHERE id = ?"
);
const user = getUserById.get(userId);

// ❌ DON'T: Build raw SQL strings
const user = db.get(`SELECT * FROM users WHERE id = ${userId}`);
```

---

## Component Patterns

### File Naming
- Components: `PascalCase.tsx` (`UserCard.tsx`)
- Hooks: `camelCase.ts` with `use` prefix (`useUser.ts`)
- Utilities: `camelCase.ts` (`formatDate.ts`)
- API routes: `route.ts` (Next.js convention)

### Component Structure
```typescript
// ✅ DO: Props interface above component, named exports
interface UserCardProps {
  user: User;
  onSelect?: (userId: string) => void;
}

export function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <div className="rounded-lg border p-4">
      {/* ... */}
    </div>
  );
}

// ❌ DON'T: Default exports for components
export default function UserCard({ user, onSelect }) { ... }
```

### Server vs Client Components
```typescript
// ✅ Server Component (default) — data fetching, no interactivity
// app/(dashboard)/page.tsx
export default async function DashboardPage() {
  const stats = await getDashboardStats();
  return <DashboardView stats={stats} />;
}

// ✅ Client Component — interactivity, browser APIs
// components/features/dashboard-view.tsx
"use client";
export function DashboardView({ stats }: { stats: DashboardStats }) {
  const [filter, setFilter] = useState("all");
  // ...
}
```

---

## API Route Patterns

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "@/db";

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

export async function POST(request: NextRequest) {
  const body = await request.json();
  const parsed = CreateUserSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const user = await db.insert(users).values(parsed.data).returning();
  return NextResponse.json(user, { status: 201 });
}
```

---

## What We Don't Do (And Why)

| Anti-Pattern | Why Not |
|-------------|---------|
| `any` type | Loses all type safety. Use `unknown` + type guards |
| `useEffect` for data fetching | Use Server Components or React Query |
| CSS-in-JS (styled-components, emotion) | Runtime overhead, SSR complexity |
| Prisma | Heavy codegen, slower SQLite support than Drizzle |
| Redux | Too heavy for SaaS. Use URL state + React context |
| ORM raw queries | Use Drizzle query builder for type safety |
| Client-side auth checks | Always verify auth server-side |
| Storing secrets in code | Use `.env.local`, never commit secrets |
| Editing migrations | Always create new migrations |
| Default exports | Named exports are searchable, refactorable |

---

## Environment Variables

```bash
# .env.local — NEVER commit this file
DATABASE_URL=file:./db.sqlite
NEXTAUTH_SECRET=...       # Generate: openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000
```

---

## Dev Commands

```bash
pnpm dev                  # Start dev server (port 3000)
pnpm build                # Production build
pnpm test                 # Run tests
pnpm test:watch           # Run tests in watch mode
pnpm lint                 # ESLint check
pnpm drizzle-kit generate # Generate migration
pnpm drizzle-kit studio   # Open Drizzle Studio (DB viewer)
```

---

## Testing Rules

- Every API route gets an integration test
- Every utility function gets a unit test
- Components get tests only for complex logic (not simple renders)
- Use `describe` blocks to group related tests
- Test file lives next to the file it tests: `user.ts` → `user.test.ts`

---

## Git Conventions

- Branch: `feat/`, `fix/`, `chore/`, `docs/`
- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`)
- PRs: Must pass CI (lint + test + build) before merge
- No force pushes on `main`
