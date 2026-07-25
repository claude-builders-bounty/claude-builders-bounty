# CLAUDE.md — Next.js 15 + SQLite SaaS Project

Opinionated project context for Claude Code. Designed for greenfield Next.js 15 App Router + SQLite (better-sqlite3/Turso) SaaS projects.

---

## Stack & Versions

| Layer | Version | Notes |
|-------|---------|-------|
| Next.js | 15.x | App Router (NOT Pages Router) |
| React | 19.x | Server Components by default |
| SQLite | better-sqlite3 11.x | Synchronous, fast, no ORM overhead |
| Drizzle ORM | 0.36+ | Thin SQL-first ORM, perfect for SQLite |
| Auth | Better Auth 1.x | Email/password + OAuth, no vendor lock-in |
| Validation | Zod 3.x | Runtime + TypeScript type inference |
| Styling | Tailwind CSS 4.x | Utility-first, no CSS modules |
| Deployment | Vercel / Fly.io | Edge-ready, SQLite on Fly volume |

---

## Folder Structure

```
src/
├── app/
│   ├── (auth)/          # Auth routes (login, signup, forgot-password)
│   ├── (dashboard)/     # Protected dashboard routes
│   ├── api/             # API route handlers
│   │   ├── auth/[...route]/
│   │   └── webhooks/
│   ├── layout.tsx       # Root layout (providers, metadata)
│   ├── page.tsx         # Landing page
│   └── not-found.tsx
├── components/
│   ├── ui/              # Reusable UI primitives (shadcn-style)
│   ├── forms/           # Form components with validation
│   └── layout/          # Nav, footer, sidebar
├── lib/
│   ├── db/              # Database schema, migrations, client
│   │   ├── schema.ts    # Drizzle table definitions
│   │   ├── migrations/  # Generated SQL migrations
│   │   └── index.ts     # DB connection singleton
│   ├── auth/            # Auth config, helpers, middleware
│   ├── utils/           # Shared utilities
│   └── hooks/           # React hooks
├── server/
│   ├── services/        # Business logic layer
│   └── actions/         # Server actions (mutations)
├── types/               # Shared TypeScript types
└── middleware.ts         # Next.js middleware (auth, i18n)

drizzle.config.ts        # Drizzle Kit config
next.config.ts           # Next.js config
.env.example             # Required env vars
```

---

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Files (components) | PascalCase | `UserProfile.tsx` |
| Files (utilities) | camelCase | `formatDate.ts` |
| API routes | lowercase, hyphenated | `app/api/user-profile/` |
| DB tables | snake_case, plural | `user_profiles` |
| Environment variables | SCREAMING_SNAKE | `DATABASE_URL` |
| Server actions | verb-noun | `createUser`, `updateProfile` |
| Boolean variables | `is/has/can` prefix | `isAuthenticated`, `hasAccess` |

---

## SQL / Migration Rules

1. **Always use Drizzle for schema** — no raw SQL in application code
2. **Migrations are generated** — never edit `drizzle/` folder manually
3. **Naming**: `YYYYMMDDHHMMSS_descriptive_name.ts`
4. **Constraints at schema level**: `notNull()`, `unique()`, `default()`
5. **Soft deletes**: Use `deletedAt Timestamp` column, never hard delete
6. **Timestamps**: Every table has `createdAt` and `updatedAt`
7. **Foreign keys**: Always with `onDelete: 'cascade'` or `'set null'`
8. **Index strategy**: Index all foreign keys, frequently queried columns
9. **No `SELECT *`** — always select specific columns
10. **Transactions**: Use `db.transaction()` for multi-step operations

---

## Component Patterns

### Server Component (default)
```tsx
// app/dashboard/page.tsx
import { getSession } from '@/lib/auth';

export default async function DashboardPage() {
  const session = await getSession();
  // Fetch data directly — no useEffect needed
  return <div>Welcome {session.user.name}</div>;
}
```

### Client Component (when needed)
```tsx
'use client';
// Only when: onClick, useState, useEffect, browser APIs
import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Server Action (mutations)
```tsx
// server/actions.ts
'use server';
import { z } from 'zod';
import { db } from '@/lib/db';

const CreateProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
});

export async function createProject(input: z.infer<typeof CreateProjectSchema>) {
  const data = CreateProjectSchema.parse(input);
  const [project] = await db.insert(projects).values(data).returning();
  return project;
}
```

---

## What We Don't Do (and Why)

| Anti-Pattern | Why We Avoid It |
|-------------|-----------------|
| Pages Router | App Router is the RSC-first future |
| Prisma | Too heavy for SQLite, Drizzle is leaner |
| TypeORM | Decorator-heavy, poor TS inference |
| Redux/Zustand for server state | React Query/SWR for client, server components for server |
| CSS Modules / styled-components | Tailwind is faster to write and maintain |
| Custom auth from scratch | Better Auth handles edge cases we'd miss |
| `any` type | Zod gives us runtime + compile-time safety |
| `useEffect` for data fetching | Server components fetch directly |
| Monolithic files | Single responsibility: one export per file |
| `console.log` in production | Use `pino` or `winston` for logging |

---

## Dev Commands

```bash
# Development
pnpm dev              # Start dev server on :3000

# Database
pnpm db:generate      # Generate migration from schema
pnpm db:migrate       # Apply migrations
pnpm db:push          # Push schema (dev only, skip for prod)
pnpm db:studio        # Open Drizzle Studio GUI

# Quality
pnpm lint             # ESLint + @biomejs
pnpm test             # Vitest
pnpm test:e2e         # Playwright
pnpm typecheck        # tsc --noEmit

# Build & Deploy
pnpm build            # Production build
pnpm start            # Start production server
```

---

## Environment Variables

```bash
# Required
DATABASE_URL=file:./local.db
AUTH_SECRET=generate-with-openssl-rand-base64-32
AUTH_URL=http://localhost:3000

# Optional (for OAuth)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_APP_NAME=MySaaS
```

---

## Testing Strategy

- **Unit tests**: Vitest + React Testing Library (components, utils, actions)
- **Integration tests**: Test API routes with `next-test-api-route-handler`
- **E2E tests**: Playwright (critical flows: auth, billing, core features)
- **DB tests**: Use separate test database, reset between tests

---

## Code Review Checklist

- [ ] No `any` types (use `unknown` + Zod parsing)
- [ ] Server components preferred over client
- [ ] No `useEffect` for data fetching
- [ ] All mutations use server actions
- [ ] DB queries use Drizzle (no raw SQL)
- [ ] Auth checks in server actions/middleware
- [ ] Error boundaries for client components
- [ ] Proper loading/error/empty states
- [ ] Responsive design (mobile-first)
- [ ] Accessibility (a11y) basics met
