# Next.js + SQLite SaaS — Project Context

> Opinionated guide for building production-ready SaaS with Next.js 15 App Router + SQLite.

## Stack & Versions

- **Next.js**: 15.x (App Router only — no Pages Router)
- **Runtime**: Node.js 20+ / Edge Runtime where applicable
- **Database**: SQLite via `better-sqlite3` (local) / `Turso` (production)
- **ORM**: Drizzle ORM (type-safe, lightweight)
- **Auth**: NextAuth.js v5 with credentials or OAuth
- **Styling**: Tailwind CSS 4.x (utility-first, no Tailwind UI)
- **Deployment**: Vercel (serverless) or Railway (persistent)

**No SSR via Express. No TypeORM. No Prisma.**  

Prisma is forbidden in this repo due to slow migrations. Use Drizzle.

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth group: /login, /register
│   ├── (dashboard)/       # Protected dashboard routes
│   ├── api/               # API routes (server actions preferred)
│   └── layout.tsx         # Root layout
├── components/
│   ├── ui/               # Shadcn/ui primitives — do not invent your own buttons
│   └── features/          # Feature-specific components
├── lib/
│   ├── db/               # Drizzle schema + migrations
│   │   ├── schema.ts     # One file per domain (users, orgs, etc.)
│   │   └── index.ts     # DB client export
│   ├── auth/             # Auth utilities
│   └── utils/            # Shared helpers (no lodash)
└── types/                # Shared TypeScript types
```

**Rules:**
- No `pages/` directory — App Router only
- No `getServerSideProps` / `getStaticProps` — use Server Components
- API routes: only for webhooks/external calls; prefer Server Actions

---

## Database Conventions

### Schema Design
```typescript
// One schema file per domain
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),        // CUID v2
  email: text('email').notNull().unique(),
  hashedPassword: text('hashed_password').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
})

// Never use .text() for IDs that are queried — use CUID strings
```

### Migrations
```bash
# Create migration
drizzle-kit generate

# Apply
drizzle-kit push

# Production migration
drizzle-kit migrate
```

**Rules:**
- Never modify existing columns in migrations — add new columns only
- Always add `.notNull()` with a default for new columns
- No raw SQL in application code — use the Drizzle query builder

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | kebab-case | `user-profile.tsx` |
| Components | PascalCase | `UserProfile.tsx` |
| Database tables | snake_case | `user_profiles` |
| Variables | camelCase | `userId` |
| React Components | PascalCase | `UserProfile` |
| CSS classes | kebab-case | `user-profile` |

**Never do this:**
- `userProfile.tsx` (PascalCase file) — use `UserProfile.tsx`
- `get_user_by_id` (raw SQL function) — use Drizzle ORM
- `let userId = req.params["userId"]` — use typed params

---

## Component Patterns

### Server Components First
```tsx
// Default — Server Component
export default async function UsersPage() {
  const users = await db.select().from(usersTable)
  return <UserList users={users} />
}
```

### Client Components — Only When Needed
```tsx
'use client'
import { useState } from 'react'
// Use only for: forms, modals, interactive state
```

### Data Fetching
- Use `cache()` from React for per-request caching
- Never fetch in render — use Server Components
- Optimistic updates via Server Actions + `useOptimistic`

---

## What We DON'T Do (And Why)

| Anti-pattern | Why |替代方案 |
|-------------|-----|---------|
| `useEffect` for data fetching | Causes race conditions | Server Components |
| `.env.local` for secrets | Committed to git accidentally | `env.ts` + `.env` |
| `any` type | Type safety lost | `unknown` + type guard |
| `console.log` in prod | Pollutes logs | Logger utility |
| `try/catch` swallowing errors | Hides bugs | Let errors propagate |
| Importing components in Server Components | Bundle bloat | Dynamic import with `ssr: false` |

---

## Dev Commands

```bash
npm run dev          # Local development
npm run build        # Production build
npm run lint         # ESLint
npm run db:generate  # Drizzle migration
npm run db:push      # Push schema to local DB
npm run test         # Vitest unit tests
```

---

## Anti-Patterns Checklist

Before shipping, verify:
- [ ] No `use client` unless necessary (forms, modals, state)
- [ ] No raw SQL strings — all via Drizzle
- [ ] No `any` types
- [ ] All API routes use rate limiting
- [ ] All mutations use Server Actions
- [ ] Auth checks on every protected route (middleware.ts)

---

*Last updated: 2026-04-07*
