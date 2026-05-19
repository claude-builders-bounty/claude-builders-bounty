# CLAUDE.md

## Stack & Versions
- **Next.js 15** (App Router, React 19, Server Components by default)
- **TypeScript 5.7+** (strict mode, no `any` without explicit justification)
- **SQLite** via **better-sqlite3** (synchronous API for migrations and queries)
- **Tailwind CSS 4** with `@tailwindcss/vite` plugin
- **Zod** for validation (API routes, form actions, env parsing)
- **Drizzle ORM** for type-safe SQL (schema → migrations → queries)
- **Lucide React** for icons (single import per icon, no icon libraries)

## Folder Structure
```
src/
  app/                    # App Router pages & API routes
    (auth)/               # Route group: auth layouts (login, register)
    (dashboard)/          # Route group: authenticated dashboard
    api/                  # API route handlers
  components/
    ui/                   # Generic UI primitives (Button, Input, Modal)
    features/             # Feature-specific composed components
    layout/               # Shell, Sidebar, Header, Footer
  lib/
    db/                   # Database connection, schema, migrations
    auth/                 # Auth logic (sessions, passwords, OAuth)
    utils/                # Pure utility functions (no side effects)
  hooks/                  # Shared React hooks
  types/                  # Shared TypeScript types
db/
  migrations/             # SQL migration files (Drizzle-generated)
  schema.ts               # Drizzle schema definitions
  index.ts                # Database singleton
```

### Why this structure?
- **Route groups** keep auth-aware layouts separate without URL prefix pollution
- **`components/ui` vs `components/features`** prevents `Button` imports from pulling in business logic
- **`lib/` is side-effect-free imports** — no default exports that initialize on import
- **`db/` at root** because it's infrastructure, not application code

## Database & Migration Conventions
- **Always use Drizzle migrations** — never modify SQLite directly
- Migration workflow: `db/schema.ts` → `drizzle-kit generate` → `drizzle-kit migrate`
- **Never ship a migration without a corresponding schema change in the same PR**
- Column naming: `snake_case` in SQL, `camelCase` in TypeScript (Drizzle maps automatically)
- Timestamps: always `created_at` and `updated_at`, defaults to `CURRENT_TIMESTAMP`
- Enable WAL mode in production: `PRAGMA journal_mode=WAL;`
- `better-sqlite3` is synchronous — use it directly in Server Components and API routes, never need `async` wrappers

## Dev Commands
```bash
pnpm dev              # Next.js dev server
pnpm build            # Production build
pnpm start            # Production server
pnpm lint             # ESLint
pnpm format           # Prettier
pnpm typecheck        # tsc --noEmit
pnpm db:generate      # Generate Drizzle migrations from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Drizzle Studio (UI for browsing data)
pnpm test             # Vitest (unit)
pnpm test:e2e         # Playwright (E2E)
```

## Component Patterns
- **Server Components by default** — only add `'use client'` when you need interactivity
- **No barrel exports** — import directly from file path to avoid circular deps and bundler confusion
- **Props destructuring** in function signature, not in body
- **One component per file** — no exceptions
- Forms use **Server Actions** with Zod validation, not client-side state libraries
- Error boundaries wrap feature sections, not individual components

```tsx
// ✅ Good: Server Component with typed props
interface UserProfileProps {
  userId: string;
  showEmail?: boolean;
}

export async function UserProfile({ userId, showEmail = false }: UserProfileProps) {
  const user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  return <div>{showEmail ? user.email : user.name}</div>;
}

// ❌ Bad: Barrel exports
export { Button } from './Button'; // Don't do this
```

## What We Don't Do (and Why)
- **No ORMs other than Drizzle** — Prisma adds 50MB+ to node_modules, Knex is too low-level for type safety
- **No `any` types** — if typing is genuinely impossible, use `unknown` and narrow with Zod
- **No `useEffect` for data fetching** — Server Components or React Query (for client-side mutations)
- **No API route wrappers (tRPC, GraphQL)** until the app has 20+ endpoints — premature abstraction
- **No CSS-in-JS** — Tailwind is the single source of truth for styling
- **No `.env` committed** — `.env.example` documents required vars, values stay local
- **No `// eslint-disable` without a comment explaining why** — every suppression is a debt marker
- **No giant PRs** — PRs touching more than 15 files need a description explaining why
