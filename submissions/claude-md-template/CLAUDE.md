# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Stable, RSC-native, server-first |
| Database | SQLite via **better-sqlite3** | Zero-infra, fast, sync API |
| ORM | **Drizzle ORM** | Type-safe, SQL-like, lightweight |
| Auth | **NextAuth.js v5** (Auth.js) | Built-in credentials + OAuth providers |
| UI | **Tailwind CSS v4** + **shadcn/ui** | Utility-first, composable, accessible |
| Forms | **React Hook Form** + **Zod** | Performant, validated, type-safe |
| Hosting | **Vercel** or **Docker** | App-appropriate, no vendor lock-in |

## Project Structure

```
src/
├── app/                    # App Router pages & layouts
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Dashboard route group (requires auth)
│   ├── api/                # API routes (Route Handlers)
│   │   └── trpc/          # tRPC HTTP handler (if used)
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page (public)
├── components/
│   ├── ui/                 # shadcn/ui primitives
│   └── features/           # Feature-specific components
├── db/
│   ├── schema/             # Drizzle schema definitions
│   ├── migrations/         # Auto-generated migration files
│   ├── index.ts            # DB connection (singleton)
│   └── seed.ts             # Seed data
├── lib/
│   ├── auth.ts             # NextAuth config
│   ├── utils.ts            # Shared utilities (cn, format, etc.)
│   └── validations.ts      # Zod schemas for forms/API
├── styles/
│   └── globals.css         # Tailwind base + custom theme
└── types/
    └── index.ts            # Shared TypeScript types
```

**Rationale:** Flat is better than nested. `app/` only contains route files. All actual logic lives in `components/`, `db/`, and `lib/`. This keeps routes discoverable and business logic testable without touching routing.

## Naming Conventions

- **Files:** `kebab-case.tsx` — `user-profile.tsx`, `api-keys.ts`
- **Components:** PascalCase — `UserProfile`, `ApiKeyList`
- **Functions:** camelCase — `fetchUser()`, `formatDate()`
- **Database tables:** `snake_case` — `user_sessions`, `api_keys`
- **Database columns:** `snake_case` — `created_at`, `updated_at`
- **TypeScript types:** PascalCase — `User`, `CreateUserInput`
- **CSS classes:** Tailwind utility classes only (no custom CSS unless unavoidable)

## Database & Migrations

### Rules

1. **Every change goes through Drizzle Kit** — never edit SQLite files directly
2. **One migration per feature** — squash related schema changes
3. **Migration naming:** `YYYYMMDD_description` format
4. **Rollbacks:** Keep the down migration when possible
5. **Seed data** belongs in `db/seed.ts`, runnable via `npm run db:seed`

### Commands

```bash
npm run db:generate    # Generate migration from schema changes
npm run db:migrate     # Apply pending migrations
npm run db:push        # Direct push (dev only, skip migration files)
npm run db:seed        # Insert seed data
npm run db:studio      # Open Drizzle Studio (GUI)
```

### Patterns

```typescript
// db/schema/users.ts — Single Responsibility per Schema File
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey().$defaultFn(crypto.randomUUID),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date())
    .$onUpdateFn(() => new Date()),
});
```

**Anti-pattern:** Putting all tables in one giant `schema.ts`. Split by domain.

## Component Patterns

### Server Components First

```typescript
// ✅ DO: Default to server component
export default async function UserList() {
  const users = await db.select().from(usersTable);
  return <UserListClient users={users} />;
}
```

### Client Components Only When Needed

Add `"use client"` only for: `useState`, `useEffect`, event handlers, browser APIs.

### Data Fetching

```typescript
// ✅ DO: Fetch in server component, pass down
// ❌ DON'T: Fetch in client component with useEffect
```

### Form Handling

```typescript
// ✅ DO: Use Server Actions for forms
export async function createUser(formData: FormData) {
  "use server";
  const parsed = createUserSchema.parse(formData);
  await db.insert(usersTable).values(parsed);
  redirect("/users");
}

// ❌ DON'T: Handle forms with client-side fetch + state management
```

## What We Don't Do (And Why)

| Anti-pattern | Reason |
|---|---|
| ❌ **Redux / Zustand / global state** | Next.js App Router + RSC makes global state almost unnecessary. Use URL params or React context for the remaining edge cases. |
| ❌ **`useEffect` for data fetching** | Server Components + Server Actions exist for this. `useEffect` data fetching causes waterfalls and race conditions. |
| ❌ **Raw SQL strings** | Drizzle ORM is type-safe and SQLite-native. Raw SQL bypasses type checking and makes migrations harder. |
| ❌ **MongoDB or Postgres for an MVP** | SQLite handles 99% of SaaS workloads. Migrate later only when you actually need horizontal scaling. |
| ❌ **CSS modules / styled-components** | Tailwind + shadcn/ui covers everything. Custom CSS increases bundle size and maintenance burden. |
| ❌ **`any` types** | If you don't know the type, create a Zod schema. `any` defeats TypeScript's purpose entirely. |
| ❌ **Separate `.env` files per developer** | Use `.env.example` with documented defaults. Actual secrets go in the deployment platform's secret store. |

## Dev Commands

```bash
npm run dev          # Next.js dev server (turbo)
npm run build        # Production build
npm run lint         # ESLint + Prettier
npm run type-check   # tsc --noEmit
npm run test         # Vitest (unit + integration)
npm run db:generate  # Drizzle schema → migration
npm run db:migrate   # Apply migrations
npm run db:seed      # Seed development database
```

## Pull Request Standards

- **Branch naming:** `feat/description`, `fix/description`, `chore/description`
- **Commit messages:** Conventional commits (`feat:`, `fix:`, `refactor:`, `chore:`)
- **PR description:** Include "What", "Why", "Testing" sections
- **Screenshots:** Required for UI changes
- **Migration check:** Does this need a new DB migration? If yes, include it.
