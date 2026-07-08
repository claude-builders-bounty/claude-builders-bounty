# CLAUDE.md — Next.js 15 + SQLite SaaS Template

## Stack & Versions

- **Framework:** Next.js 15 (App Router, Turbopack)
- **Language:** TypeScript 5.7+ (strict mode)
- **Database:** SQLite via better-sqlite3 (or Turso for edge)
- **ORM:** Drizzle ORM (NOT Prisma — see below)
- **Auth:** NextAuth.js v5 (Auth.js)
- **UI:** shadcn/ui + Tailwind CSS v4
- **Package Manager:** pnpm (NOT npm or yarn)
- **Node:** 22 LTS

## Why This Stack

| Decision | Reason |
|----------|--------|
| SQLite over Postgres | One file = zero infra. Backup = copy file. Dev/prod parity is absolute. |
| Drizzle over Prisma | Drizzle is a thin SQL layer, not a black box. You can read the SQL it generates. |
| pnpm over npm | Disk space + install speed. Monorepo-ready. |
| Turbopack over Webpack | 10x faster HMR. The default in Next.js 15 anyway. |

## Folder Structure (Must Follow)

```
src/
├── app/                  # Next.js App Router pages
│   ├── (auth)/           # Auth group (login, register)
│   ├── (dashboard)/      # Authenticated routes
│   │   ├── settings/
│   │   └── [org]/
│   └── api/              # Route handlers (no separate /pages/api)
├── components/           # React components
│   ├── ui/               # shadcn/ui primitives
│   └── features/         # Feature-specific components
├── db/                   # Database layer
│   ├── schema/           # Drizzle schema definitions
│   ├── migrations/       # Generated migrations (do NOT hand-edit)
│   └── index.ts          # DB client singleton
├── lib/                  # Utilities & shared logic
│   ├── auth.ts           # NextAuth config
│   └── utils.ts          # Shared helpers
├── actions/              # Server Actions (NOT in route handlers)
└── types/               # Shared TypeScript types
```

## Database Rules

### Schema Conventions
- Every table gets: `id TEXT PRIMARY KEY` (nanoid, not serial), `createdAt`, `updatedAt`
- Use `TEXT` for IDs, not `INTEGER` — URL-safe, shardable, no sequence leaks
- Index every `foreignKey` column
- Soft deletes: add `deletedAt INTEGER | NULL` — never `DELETE FROM`

### Migration Rules
```bash
# Generate migration after schema change
pnpm db:generate

# Apply migration
pnpm db:migrate

# NEVER hand-edit migration files
# NEVER run migration in production without a backup
```

### Query Patterns
```typescript
// ✅ CORRECT: Use prepared statements
const user = db.select().from(users).where(eq(users.id, id)).get();

// ❌ WRONG: Raw SQL interpolation
db.run(`SELECT * FROM users WHERE id = ${id}`);
```

## Server Actions (The Core Pattern)

This project uses Server Actions, NOT API routes, for all mutations:

```typescript
// app/actions/orgs.ts (SERVER FILE)
'use server'

export async function createOrg(formData: FormData) {
  const name = formData.get('name')
  // validate → db insert → revalidate → redirect
  revalidatePath('/dashboard')
  redirect('/dashboard/' + org.id)
}
```

Rules:
- Server Actions go in `src/actions/`, co-located by domain
- Always validate input with Zod before DB writes
- Always wrap in `try/catch` and return structured errors
- No `useActionState` for simple forms — use `formData` directly

## What We DON'T Do

| Anti-pattern | Why |
|-------------|-----|
| Redux / Zustand / Jotai | Server Components + URL state cover 95% of cases. The rest goes in React context. |
| API routes for mutations | Server Actions are type-safe, don't need fetch(), and work without JS. |
| `useEffect` for data fetching | Use Server Components + `async` directly. |
| Client Components by default | Only add `'use client'` when you need hooks or browser APIs. |
| Catch-all `[...slug]` routes | Each page gets its own file. Explicitness beats cleverness. |
| Inline SQL in components | Every query goes through `src/db/`. |

## Naming Conventions

- **Files:** `kebab-case.ts` — `user-settings.tsx`, `db-schema.ts`
- **Components:** PascalCase — `UserAvatar.tsx`, `OrgSwitcher.tsx`
- **Functions:** camelCase — `getUserById()`, `createOrg()`
- **DB Tables:** snake_case — `user_sessions`, `org_members`
- **DB Columns:** snake_case — `first_name`, `last_login_at`
- **Types/Interfaces:** PascalCase prefixed with `T` — `TUser`, `TOrgMember`
- **Server Actions:** verbNoun — `createOrg`, `inviteMember`, `deleteProject`

## Dev Commands

```bash
pnpm dev              # Start dev server (Turbopack)
pnpm build            # Production build
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply migration
pnpm db:studio        # Open Drizzle Studio (GUI DB browser)
pnpm lint             # ESLint + tsc --noEmit
pnpm test             # Vitest
pnpm typecheck        # tsc --noEmit
```

## Testing

- Unit tests: Vitest (co-located as `.test.ts`)
- E2E tests: Playwright (in `e2e/`)
- No mocking of DB in unit tests — use an in-memory SQLite
- Every Server Action needs at least one test

## Deployment

- Platform: Vercel / Docker
- SQLite: Turso (edge-compatible libSQL) for production
- Env vars: All in `.env.local` (never committed). Production vars in deployment dashboard.
