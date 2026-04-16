# CLAUDE.md — Next.js 15 + SQLite SaaS

This document is your context for working on this codebase. Read it fully before making any changes.

---

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js | 15.x (App Router) |
| Language | TypeScript | 5.x (strict mode) |
| Database | SQLite via better-sqlite3 | Latest |
| ORM | Drizzle ORM | Latest |
| Styling | Tailwind CSS + shadcn/ui | Latest |
| Auth | Lucia Auth | v3 |
| Runtime | Node.js | 20+ |
| Package manager | pnpm | 9+ |

---

## Project Structure

```
src/
├── app/                    # Next.js App Router pages and layouts
│   ├── (auth)/             # Route group: login, signup, reset-password
│   ├── (dashboard)/        # Route group: authenticated pages
│   ├── api/                # API route handlers (route.ts)
│   └── layout.tsx          # Root layout
├── components/
│   ├── ui/                 # shadcn/ui primitives (DO NOT modify directly)
│   └── [feature]/          # Feature-scoped components
├── lib/
│   ├── db/
│   │   ├── index.ts        # Database connection singleton
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   └── migrations/     # SQL migration files (numbered: 0001_, 0002_…)
│   ├── auth.ts             # Lucia Auth setup and helpers
│   └── utils.ts            # Shared utilities (cn(), formatDate(), etc.)
├── server/
│   └── [feature].ts        # Server-only actions and data fetching
└── types/
    └── index.ts            # Shared TypeScript types
```

---

## Database Rules

### Schema (Drizzle ORM)

All tables are defined in `src/lib/db/schema.ts`. Use Drizzle's type-safe query builder.

```typescript
// ✅ Good — type-safe, uses Drizzle
const user = await db.select().from(users).where(eq(users.id, id)).get();

// ❌ Bad — raw SQL string, bypasses type safety
const user = db.prepare("SELECT * FROM users WHERE id = ?").get(id);
```

### Migrations

- Migrations live in `src/lib/db/migrations/` and are numbered: `0001_create_users.sql`
- **Never edit an existing migration file.** Create a new one.
- Generate migrations: `pnpm drizzle-kit generate`
- Apply migrations: `pnpm drizzle-kit migrate`
- Never drop columns in production migrations — add nullable columns instead

### Connection

Use the singleton from `src/lib/db/index.ts`. Never create a new `Database()` instance elsewhere.

```typescript
// ✅ Always import from the singleton
import { db } from "@/lib/db";
```

---

## Component Patterns

### Server vs. Client Components

Default to **Server Components**. Only add `"use client"` when you need:
- `useState` / `useEffect`
- Browser-only APIs (localStorage, window)
- Event listeners

```typescript
// ✅ Server Component (default) — no directive needed
export default async function UserProfile({ id }: { id: string }) {
  const user = await getUser(id); // Direct DB call, no API round-trip
  return <div>{user.name}</div>;
}

// ✅ Client Component — explicit directive
"use client";
export function ToggleSwitch({ onToggle }: { onToggle: () => void }) { ... }
```

### Data Fetching

- Fetch data in Server Components. Never use `useEffect` for initial data.
- Keep data fetching functions in `src/server/[feature].ts`
- Use `cache()` from React for request deduplication on repeated queries

### Forms

Use Server Actions for form mutations. Client-side fetch is only for dynamic, real-time features.

```typescript
// ✅ Server Action
"use server";
export async function updateProfile(formData: FormData) {
  const name = formData.get("name") as string;
  await db.update(users).set({ name }).where(eq(users.id, session.userId));
  revalidatePath("/dashboard/profile");
}
```

### File Naming

- Components: `PascalCase.tsx`
- Utilities/helpers: `camelCase.ts`
- Pages: `page.tsx` (Next.js convention)
- Every component in its own file — no barrel exports unless forced

---

## Auth Rules

Auth is handled by Lucia in `src/lib/auth.ts`.

- Session is read in Server Components via `validateRequest()` — never in client code
- Protected routes go inside `(dashboard)/` — middleware validates auth at the route-group level
- Passwords are hashed with Argon2id via the `oslo` package — never bcrypt

```typescript
// ✅ Correct — server-side session check
const { user, session } = await validateRequest();
if (!user) redirect("/login");

// ❌ Wrong — never expose session tokens to client
const session = useSession(); // Do not create this hook
```

---

## Dev Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm lint             # ESLint
pnpm typecheck        # tsc --noEmit
pnpm drizzle-kit generate   # Generate migration from schema changes
pnpm drizzle-kit migrate    # Apply pending migrations
pnpm drizzle-kit studio     # Open Drizzle Studio (DB browser)
```

---

## What We Don't Do (and Why)

| Pattern | Why We Avoid It |
|---------|----------------|
| `useEffect` for data fetching | Server Components fetch directly — no waterfalls |
| `pages/` directory | We're on App Router — `pages/` is legacy |
| Multiple DB connections | SQLite is single-writer; use the singleton |
| `any` in TypeScript | Use `unknown` + type narrowing instead |
| `fetch` in Server Components for own API | Call server functions directly, skip the HTTP layer |
| Prisma | Drizzle is lighter, has better SQLite support, and generates real SQL |
| Raw SQL strings | Drizzle's query builder is type-safe and prevents injection |
| Modifying shadcn components | Extend via wrapper components, not in-place edits |
| Client-side session state | Auth state lives on the server — use `validateRequest()` |

---

## Environment Variables

Required in `.env.local`:

```
DATABASE_URL=./dev.db          # SQLite file path
AUTH_SECRET=<32-char random>   # Lucia session secret
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## Code Review Checklist

Before every PR:
- [ ] `pnpm typecheck` passes with zero errors
- [ ] `pnpm lint` passes
- [ ] No new `any` types introduced
- [ ] New DB columns are nullable (migration safety)
- [ ] No raw SQL strings
- [ ] Server Actions used for mutations (not API routes)
- [ ] No unused imports
