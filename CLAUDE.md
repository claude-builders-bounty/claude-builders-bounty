# CLAUDE.md - Next.js 15 + SQLite SaaS Template

> This file tells Claude Code how to work in this codebase. Read it first.

## Stack & Versions (Pinned)

| Technology | Version | Reason |
|------------|---------|--------|
| Next.js | 15.2+ | App Router stable, React 19 |
| React | 19.0+ | RSC streaming, Actions |
| TypeScript | 5.4+ | Satisfies operator, improved inference |
| SQLite | native | Local dev speed |
| Turso | latest | Edge sync, backup, production |
| Drizzle | 0.32+ | Type-safe queries, no abstraction |
| Tailwind | 3.4+ | CSS utilities, no runtime |

## Folder Structure (Domain-Driven)

```
/src
  /app                    # Next.js App Router
    /api                  # Only for webhooks, imports
    /auth                 # (login, signup, callback)
    /[feature]            # Each feature gets its own route folder
    /actions              # Server Actions (NOT /api)
    /layout.tsx           # Root layout
  /lib                    # Shared utilities
    /db                   # Database client
    /auth.ts              # Auth helpers
    /utils.ts             # Pure functions
  /db                     # Database
    schema.ts             # Drizzle schema (single source of truth)
    migrations/           # Drizzle migrations
    seed.ts               # Seed script
  /features               # Colocated by domain (NOT /components)
    /[feature]/
      component.tsx       # Lazy loaded
      action.ts           # Server Action
      schema.ts           # Form validation
  /types                  # Shared TypeScript
/public
.env.local
```

## SQL & Migration Conventions

### Naming Rules
- **Tables:** Singular (`user`, not `users`)
- **Primary keys:** Always `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- **Timestamps:** `created_at`, `updated_at` (auto in schema)
- **Foreign keys:** `{table}_id` (`user_id`, not `userId`)
- **Indexes:** Explicitly named `{table}_{column}_idx`

### Schema Pattern
```typescript
// /db/schema.ts
export const user = sqliteTable('user', {
  id: integer('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at').notNull().default(sql`CURRENT_TIMESTAMP`),
}, (t) => [
  index('user_email_idx').on(t.email),
]);
```

### Migration Commands
```bash
pnpm db:generate   # Create migration from schema changes
pnpm db:migrate    # Apply migrations
pnpm db:studio     # Drizzle Studio UI
pnpm db:reset      # Reset local DB
```

## Component Patterns

### Server Actions > API Routes
```typescript
// Good - Server Action
'use server';
export async function createProfile(formData: FormData) {
  const { name } = schema.parse(Object.fromEntries(formData));
  return db.insert(user).values({ name });
}
```

```typescript
// Bad - API Route (unnecessary boilerplate)
export async function POST(request: Request) { /* ... */ }
```

### Component Structure
```typescript
// /features/profile/profile-form.tsx
'use client';  // Only if hooks needed
import { useActionState } from 'react';
import { createProfile } from './actions';

export function ProfileForm() {
  const [state, formAction] = useActionState(createProfile, {});
  return <form action={formAction}>...</form>;
}
```

### File Naming
- Routes: `page.tsx`, `layout.tsx`, `loading.tsx`
- Components: `kebab-case.tsx`
- Actions: `action.ts`
- Types: `schema.ts` (Zod)

## Anti-Patterns (And Why)

### ❌ No API Routes for CRUD
**Reason:** Server Actions handle form submissions without client fetch code. Reduces 2 files (route + client hook) to 1.

### ❌ No Prisma
**Reason:** Drizzle generates types from SQLite schema. Prisma's query engine adds 50MB overhead for SQLite scale.

### ❌ No separate `/components/` folder
**Reason:** Colocating by feature reduces cognitive load. `features/user/` contains everything user-related.

### ❌ No SWR/TanStack Query for mutations
**Reason:** Server Actions + `useActionState` handle optimistic updates without client cache management.

### ❌ No Zustand/Jotai for server state
**Reason:** Server state lives in the database. Client state fits in URL/search params.

### ❌ No inline styles
**Reason:** Tailwind utilities keep styling consistent and purgeable.

## Development Commands

```bash
pnpm dev          # Start dev server (Tigris for iOS if on Mac)
pnpm build        # Production build
pnpm start        # Start production server
pnpm lint         # ESLint + Prettier
pnpm type-check   # TypeScript check

pnpm db:generate  # Generate migration
pnpm db:migrate   # Run migrations
pnpm db:seed      # Seed development data
pnpm db:studio    # Visual DB editor

pnpm test         # Vitest unit tests
pnpm test:e2e     # Playwright
```

## Environment Variables

```bash
# Local development
DATABASE_URL="file:./local.db"

# Production (Turso)
TURSO_DATABASE_URL="..."
TURSO_AUTH_TOKEN="..."

# Secrets
NEXTAUTH_SECRET="..."
RESEND_API_KEY="..."
```

## TypeScript Rules

- Strict mode enabled
- No `any` type (use `unknown` + type guard)
- Zod for runtime validation
- Infer types from Zod: `type Input = z.infer<typeof schema>`
- Use `satisfies` for literal types: `'active' satisfies Status`

## Deployment

- **Vercel** for Next.js
- **Turso** for SQLite edge storage
- Migrations run via `pnpm db:migrate` in build script

---

*This CLAUDE.md enables context-aware contributions. When in doubt, follow the patterns here.*