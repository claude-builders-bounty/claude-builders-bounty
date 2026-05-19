# CLAUDE.md — Next.js 15 + SQLite SaaS Project Template

## Stack & Versions
- **Runtime**: Node.js 20+ (use `nvm use` in this project)
- **Framework**: Next.js 15 App Router (Server Components by default)
- **Database**: SQLite via `better-sqlite3` (synchronous, great for single-server SaaS)
- **ORM**: Prisma (schema-first, migrations, type-safe queries)
- **Styling**: Tailwind CSS v4
- **Auth**: NextAuth.js v5 (credentials + OAuth)
- **Deployment**: Vercel (optimized for Next.js) or Railway

---

## Folder Structure
```
/
├── apps/
│   └── web/              # Next.js frontend (monorepo workspace)
│       ├── app/          # App Router pages (src/app/)
│       │   ├── (auth)/   # Auth group route (login, register)
│       │   ├── (dashboard)/  # Protected dashboard routes
│       │   ├── api/      # API Route Handlers
│       │   └── layout.tsx
│       ├── components/   # React components
│       │   ├── ui/       # Base UI (Button, Input, Card — shadcn/ui)
│       │   └── features/ # Feature-specific components
│       ├── lib/          # Utilities, helpers
│       └── styles/       # Global CSS, Tailwind config
├── packages/
│   └── db/               # Prisma schema + migrations
│       ├── prisma/
│       │   └── schema.prisma
│       └── scripts/      # DB seed scripts
├── prisma/
│   └── schema.prisma     # Single source of truth for DB schema
└── package.json          # Workspace root
```

---

## SQL / Migration Conventions

### Rules
1. **Always use Prisma migrations** — never touch SQLite directly
   ```bash
   # Create migration
   npx prisma migrate dev --name add_user_table
   
   # Apply in production
   npx prisma migrate deploy
   ```
2. **All schema changes go through `schema.prisma`** — no ad-hoc ALTER TABLE
3. **Foreign keys are enforced** — use `relation` fields, not raw JOINs
4. **Indexes on all query filter columns** — add `@index` in schema

### SQLite Specifics
- Use `String` for UUIDs (`cuid()` generator)
- No `enum` type in SQLite — use `String` with Prisma enums
- `DateTime` stored as ISO 8601 strings

---

## Component Patterns

### Server vs Client Components
```typescript
// ✅ Default to Server Component
// app/dashboard/page.tsx
export default async function DashboardPage() {
  const data = await db.query.users.findMany(); // direct DB, no API
  return <UserList users={data} />;
}

// ✅ Only use 'use client' when you need interactivity
// components/counter.tsx
'use client';
import { useState } from 'react';
export function Counter() {
  const [n, setN] = useState(0);
  return <button onClick={() => setN(n+1)}>{n}</button>;
}
```

### Data Fetching
```typescript
// In Server Components — use Prisma directly, no fetch()
const user = await db.query.user.findUnique({ where: { id } });

// In Client Components — use React Query or SWR for API calls
// Never call Prisma from client components
```

### Error Handling
```typescript
// Always use error.tsx and loading.tsx in route segments
// app/(dashboard)/error.tsx
'use client';
export default function Error({ error, reset }) {
  return (
    <div>
      <p>Something went wrong: {error.message}</p>
      <button onClick={reset}>Retry</button>
    </div>
  );
}
```

---

## What We Don't Do (And Why)

| Anti-Pattern | Why Not | Correct Approach |
|---|---|---|
| `any` types | Silent type failures at runtime | Use `unknown` + type narrowing, or Zod |
| Direct SQLite in `.ts` files | No schema enforcement, no migrations | Use Prisma exclusively |
| `useEffect` for initial data | Race conditions, no loading states | Server Components + `await` |
| Global CSS for component styles | Specificity wars | Tailwind utility classes |
| `.env` for secrets in Vercel | Not env-scoped | Vercel project settings |

---

## Dev Commands
```bash
# Install dependencies
npm install

# Database setup
npx prisma migrate dev

# Seed database
npx prisma db seed

# Run dev server
npm run dev

# Type check
npm run typecheck

# Build
npm run build
```

---

## Conventions

### Naming
- **Files**: kebab-case (`user-profile.tsx`, `auth-service.ts`)
- **Components**: PascalCase (`UserProfile.tsx`)
- **Database tables**: snake_case in schema (`user_profile`), PascalCase in Prisma (`UserProfile`)

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add user registration
fix: handle nil email in reset password
docs: update API docs
refactor: extract payment service
```
