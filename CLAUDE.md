# CLAUDE.md - Next.js + SQLite SaaS Project

> An opinionated project context file for Claude Code.
> Drop this into the root of any Next.js 15 + SQLite project and Claude will understand the conventions without asking questions.

---

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via `better-sqlite3` or Turso (`@libsql/client`)
- **Language**: TypeScript 5.x (strict mode)
- **Styling**: Tailwind CSS 3.x
- **UI Components**: shadcn/ui
- **Auth**: NextAuth.js v5 (Auth.js) or Lucia
- **Validation**: Zod
- **Testing**: Vitest + Testing Library

---

## Folder Structure

```
app/                    # Next.js App Router
  api/                  # Route handlers (auth, CRUD)
  (marketing)/          # Landing page group (no auth)
  dashboard/            # Authenticated app area
  layout.tsx            # Root layout (providers, fonts)
  globals.css           # Tailwind directives
components/
  ui/                   # shadcn/ui components (auto-generated)
  forms/                # Form-specific components
  layout/               # Nav, sidebar, footer
lib/
  db/                   # Database layer
    schema.ts           # Drizzle ORM schema
    client.ts           # DB connection singleton
    migrations/         # Drizzle migrations
  auth/                 # Auth configuration
  validations/          # Zod schemas
  utils.ts              # cn(), formatters, helpers
types/                  # Shared TypeScript types
public/                 # Static assets
```

---

## SQL / Migration Conventions

We use **Drizzle ORM** with SQLite.

### Schema Rules
- Every table has: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `createdAt INTEGER (timestamp)`, `updatedAt INTEGER (timestamp)`
- Use `text()` for strings, `integer()` for numbers/booleans, `real()` for decimals
- Boolean fields: use `integer({ mode: "boolean" })`
- Timestamps: use `integer({ mode: "timestamp" })`
- Foreign keys: always add `references()` and `onDelete: "cascade"` where appropriate
- Indexes: add on foreign keys and frequently queried fields

### Migration Workflow
```bash
# Generate migration from schema changes
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate

# NEVER edit a generated migration file after applying it
# If a migration is broken, create a new fix migration instead
```

---

## Component Patterns

### Server Components (default)
- Use for data fetching, static content
- Keep async - fetch data directly in the component
- Pass primitives to client components via props

### Client Components
- Mark with `"use client"` only when needed (interactivity, hooks, browser APIs)
- Keep minimal - extract server parts when possible
- Form validation: use `react-hook-form` + Zod resolver

### shadcn/ui
- Install: `npx shadcn add <component>`
- Customize in `components/ui/` - these are YOUR components
- Compose primitives rather than overriding styles

---

## API Conventions

### Route Handlers (`app/api/*/route.ts`)
- Use `NextRequest` / `NextResponse` from `next/server`
- Validate ALL inputs with Zod before processing
- Return consistent error shape: `{ error: string, code?: string }`
- Use HTTP status codes properly (400, 401, 403, 404, 409, 500)

### Data Fetching
- Prefer Server Components + direct DB queries
- For client-side: use SWR or React Query with proper caching
- API routes only for mutations and external integrations

---

## What We Don't Do (And Why)

| Anti-Pattern | Why |
|-------------|-----|
| `any` type | We use `unknown` + type guards; `any` defeats the purpose of TS |
| `console.log` in production | Use a proper logger or remove before committing |
| Raw SQL without parameterized queries | SQL injection risk; always use Drizzle query builder |
| Client-side data fetching for static content | Unnecessary JS bundle; use Server Components |
| `export default` for pages | Named exports are more refactor-friendly |
| Mutating state directly | Always use React patterns (setState, reducers) |
| Storing secrets in `.env` without `.env.example` | Other devs can't set up the project |
| Using `var` or non-strict TS | We enforce `strict: true` in tsconfig |
| Magic numbers/strings | Extract to named constants |
| `any[]` for database results | Use Drizzle's type inference: `typeof table.$inferSelect` |

---

## Dev Commands

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Type check
npx tsc --noEmit

# Lint
npm run lint

# DB: Generate migration
npx drizzle-kit generate

# DB: Apply migration
npx drizzle-kit migrate

# DB: Studio (visual editor)
npx drizzle-kit studio
```

---

## Auth Pattern

We use NextAuth.js v5 with the App Router:

```typescript
// lib/auth.ts
import NextAuth from "next-auth"
import { DrizzleAdapter } from "@auth/drizzle-adapter"
import { db } from "./db/client"
import GitHub from "next-auth/providers/github"

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: DrizzleAdapter(db),
  providers: [GitHub],
  pages: { signIn: "/login" },
})
```

Protected routes check auth server-side:
```typescript
// app/dashboard/page.tsx
import { auth } from "@/lib/auth"
import { redirect } from "next/navigation"

export default async function Dashboard() {
  const session = await auth()
  if (!session) redirect("/login")
  // ...
}
```

---

## Environment Variables

Copy `.env.example` to `.env.local` and fill in:

```env
# Database
DATABASE_URL=file:./local.db

# Auth (GitHub OAuth)
AUTH_GITHUB_ID=your_github_app_id
AUTH_GITHUB_SECRET=your_github_app_secret
AUTH_SECRET=random_secret_for_jwt_signing

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

*Generated for Claude Code compatibility. Place at project root.*
