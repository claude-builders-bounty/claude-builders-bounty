# SaaS Stack Guide

## Stack
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 (Auth.js)
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Language**: TypeScript
- **Runtime**: Node.js 22+

## Project Structure
```
src/
├── app/              # Next.js App Router pages
│   ├── (auth)/       # Auth group (login, signup)
│   ├── (dashboard)/  # Authenticated routes
│   ├── api/          # Route handlers (API)
│   └── layout.tsx    # Root layout
├── components/       # React components
│   ├── ui/          # shadcn/ui primitives
│   └── features/    # Feature-specific components
├── db/               # Database
│   ├── schema/      # Drizzle schema files
│   ├── migrations/  # Auto-generated migrations
│   └── index.ts     # DB client
├── lib/              # Shared utilities
├── hooks/            # React hooks
├── actions/          # Server Actions
└── types/            # TypeScript types
```

## Database Rules

### Schema
- One file per domain: `db/schema/users.ts`, `db/schema/teams.ts`
- Use `sqlite` table creator (not `pg`):
  ```ts
  import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
  ```
- Primary keys: `id: integer().primaryKey({ autoIncrement: true })` or `id: text().primaryKey()` (UUID)
- Timestamps: `createdAt: text('created_at').notNull().default(sql\`(CURRENT_TIMESTAMP)\`)`
- Foreign keys: use `references()` with proper naming
- **NEVER** use enums — SQLite doesn't support them. Use `text()` with `$type<UnionType>()` instead:
  ```ts
  role: text('role').$type<'admin' | 'member'>().notNull().default('member'),
  ```

### Migrations
- Generate: `npm run db:generate` (drizzle-kit push)
- Never edit migration files manually
- Run: `npm run db:migrate` in production
- Rollback: use `drizzle-kit drop && db:generate` (destructive)

### Queries
- Use Drizzle query builder, never raw SQL unless absolutely necessary
- Avoid `select *` — always specify columns
- Use transactions for multi-table operations:
  ```ts
  return db.transaction(async (tx) => {
    const user = await tx.insert(users).values({...}).returning();
    await tx.insert(profiles).values({ userId: user[0].id, ... });
    return user[0];
  });
  ```

## Component Patterns

### Server Components (default)
- Fetch data directly in the component
- Keep them async when reading from DB
- Use `Suspense` boundaries for loading states

### Client Components
- Only add `"use client"` when needed (event handlers, browser APIs, hooks)
- Never put DB queries in client components
- Keep client components as leaf nodes in the tree

### Page Organization
- Pages live in `src/app/[route]/page.tsx`
- Layouts in `src/app/[route]/layout.tsx`
- Loading states in `src/app/[route]/loading.tsx`
- Error boundaries in `src/app/[route]/error.tsx`

## Conventions

### Naming
- **Files**: `kebab-case.ts` for utilities, `PascalCase.tsx` for components
- **Functions**: `camelCase` — `fetchUserData()`, `createTeam()`
- **Components**: `PascalCase` — `UserProfile`, `TeamSettings`
- **Types**: `PascalCase` — `UserWithProfile`, `ApiResponse<T>`
- **DB columns**: `snake_case` in DB, `camelCase` in TypeScript (via Drizzle `casing`)

### Server Actions
- Use `"use server"` at the file top, not inline
- One action file per domain: `src/actions/users.ts`
- Always validate input with Zod
- Return typed responses:
  ```ts
  interface ActionResult<T> {
    success: boolean;
    data?: T;
    error?: string;
  }
  ```

### API Routes
- Prefer Server Actions over API routes for internal mutations
- Use API routes only for: webhooks, external API consumption, public endpoints
- Rate limit public endpoints

## Anti-Patterns (Don't)

1. **❌ `useEffect` for data fetching** — use Server Components or React Query
2. **❌ Direct DB access from client** — always use Server Actions or API routes
3. **❌ Storing sensitive data in SQLite plaintext** — hash passwords, encrypt tokens
4. **❌ Large client bundles** — dynamic import heavy libraries
5. **❌ Prop drilling beyond 3 levels** — use React Context or Server Components
6. **❌ editing drizzle migrations** — always generate fresh ones

## Dev Commands

```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run test         # Run tests
npm run db:generate  # Generate DB migrations
npm run db:studio    # Open Drizzle Studio
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
```
