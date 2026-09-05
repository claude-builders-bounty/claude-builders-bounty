# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Runtime**: Node.js 20 LTS
- **Language**: TypeScript 5.x (strict mode)
- **Database**: SQLite via better-sqlite3 (local dev) or Turso (production)
- **ORM**: Drizzle ORM (schema-first, no codegen)
- **Styling**: Tailwind CSS 4.x + shadcn/ui components
- **Auth**: NextAuth.js v5 (Auth.js)
- **Validation**: Zod schemas (shared between client/server)
- **Testing**: Vitest + Playwright

## Folder Structure

```
src/
  app/                    # App Router pages and layouts
    (auth)/               # Auth route group (login, register)
    (dashboard)/          # Dashboard route group
      layout.tsx          # Dashboard layout with sidebar
      page.tsx            # Dashboard home
      [team]/
        page.tsx          # Team-specific dashboard
    api/                  # API routes
      [trpc]/             # tRPC handler (if using tRPC)
  components/
    ui/                   # shadcn/ui primitives (Button, Input, etc.)
      button.tsx
      input.tsx
    features/             # Feature-specific components
      auth/
        login-form.tsx
      dashboard/
        sidebar.tsx
        team-switcher.tsx
  lib/
    db/                   # Database layer
      schema.ts           # Drizzle schema definitions
      migrate.ts          # Migration runner
      index.ts            # Database client singleton
    auth.ts               # Auth configuration
    utils.ts              # Shared utilities (cn, formatDate, etc.)
    validations/          # Zod schemas (shared client/server)
      user.ts
      team.ts
  hooks/                  # Custom React hooks
  types/                  # Shared TypeScript types
drizzle/                  # Drizzle migrations
  0000_initial.sql
public/                   # Static assets
```

## Naming Conventions

- **Files**: `kebab-case.tsx` for components, `kebab-case.ts` for utilities
- **Components**: `PascalCase` function names, default exports
- **Functions**: `camelCase`, prefixed with action verb (`getUser`, `createTeam`, `updatePost`)
- **Database tables**: `snake_case` plural (`users`, `teams`, `posts`)
- **DB columns**: `snake_case` (`created_at`, `user_id`)
- **API routes**: `/api/[resource]` with REST verbs (`GET /api/users`, `POST /api/teams`)
- **CSS classes**: Tailwind utility classes, `cn()` for conditional merging

## SQL / Migration Conventions

- **Schema-first**: Define tables in `src/lib/db/schema.ts` using Drizzle
- **Migrations**: Generate with `npx drizzle-kit generate`, apply with `npx drizzle-kit migrate`
- **Always use parameterized queries** — never interpolate user input into SQL
- **Foreign keys**: Explicitly defined in schema, not just in application code
- **Timestamps**: Always include `created_at` and `updated_at` with defaults
- **Soft deletes**: Use `deleted_at` column instead of `DELETE FROM` for user data
- **Indexes**: Add for any column used in WHERE, JOIN, or ORDER BY

```typescript
// Schema example
export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});
```

## Component Patterns

- **Server Components by default** — only add 'use client' when you need interactivity
- **Colocation**: Keep related files together (component + tests + types in same folder)
- **Composition over configuration**: Prefer composing small components over passing many props
- **Extract data fetching to Server Components** — never fetch in 'use client' components
- **Form handling**: Use React Hook Form + Zod for validation

```typescript
// Good: Server Component with data fetching
async function TeamPage({ params }: { params: { team: string } }) {
  const team = await getTeam(params.team);
  return <TeamDashboard team={team} />;
}

// Good: Client Component only where needed
'use client';
function TeamSwitcher({ teams, current }: TeamSwitcherProps) {
  const [selected, setSelected] = useState(current);
  // ... interactivity
}
```

## What We Don't Do (And Why)

- **No Prisma** — Drizzle is schema-first with zero codegen, smaller bundle, better SQLite support
- **No src/index.ts barrel exports** — tree-shaking works better with direct imports
- **No class components** — React function components + hooks are the standard
- **No CSS modules** — Tailwind + cn() is faster to write and more consistent
- **No custom error boundaries for every route** — Next.js error.tsx handles this
- **No API middleware chains** — Next.js middleware is sufficient for auth/logging
- **No Redux/Zustand for server state** — React Server Components + SWR/React Query
- **No inline styles** — Tailwind classes only, cn() for conditional styling
- **No console.log in production** — Use structured logging (pino)
- **No setTimeout for debouncing** — Use useDebounce hook or lodash.debounce

## Dev Commands

```bash
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint + Prettier check
npm run test         # Run Vitest unit tests
npm run test:e2e     # Run Playwright E2E tests
npx drizzle-kit generate   # Generate migration from schema changes
npx drizzle-kit migrate    # Apply pending migrations
npx drizzle-kit studio     # Open Drizzle Studio (DB browser)
```

## Anti-Patterns to Avoid

1. **Don't fetch data in useEffect for initial render** — Use Server Components or Suspense
2. **Don't pass functions as props to Client Components** — Use callbacks from Server Components
3. **Don't use `any` type** — Use `unknown` and narrow, or define proper types
4. **Don't skip the Zod validation** — Validate on server even if client validates
5. **Don't use `require()`** — Use ES module imports only
6. **Don't mutate state directly** — Always use setState or immutably spread
7. **Don't put business logic in components** — Extract to lib/ or hooks/
8. **Don't hardcode API URLs** — Use environment variables or relative paths
9. **Don't ignore TypeScript errors** — Fix them, don't add @ts-ignore
10. **Don't commit .env files** — Use .env.local for secrets, .env.example for documentation
