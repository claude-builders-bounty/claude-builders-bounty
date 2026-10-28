# CLAUDE.md - Next.js 15 + SQLite SaaS Project

This file provides context and conventions for Claude Code to work effectively on this project. Follow these rules strictly.

## Stack & Versions

| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| [Next.js](https://nextjs.org/) | 15.x | Full-stack React framework (App Router) | Use Server Components by default, Client Components only when necessary |
| [TypeScript](https://www.typescriptlang.org/) | 5.x | Type safety | Strict mode enabled, no `any` without justification |
| [React](https://react.dev/) | 19.x | UI library | Compatible with Next.js 15 |
| [SQLite](https://www.sqlite.org/) | Latest | Database | Use `better-sqlite3` for local/dev or [Turso](https://turso.tech/) for production |
| [Tailwind CSS](https://tailwindcss.com/) | v4 | Styling | Use utility classes, follow design system tokens |
| [Zod](https://zod.dev/) | Latest | Schema validation | Validate all inputs (forms, API routes, server actions) |

## Folder Structure

```
src/
├── app/                    # Next.js App Router (routes, layouts, pages)
│   ├── (auth)/            # Auth route group
│   ├── (dashboard)/       # Protected app routes
│   ├── api/               # API routes (Route Handlers)
│   └── layout.tsx         # Root layout
├── components/            # Reusable UI components
│   ├── ui/               # Base components (buttons, inputs, etc.)
│   └── features/         # Feature-specific components
├── lib/                  # Core utilities, configs, helpers
│   ├── db/               # Database setup, queries, migrations
│   │   ├── schema.ts     # Drizzle/SQL schema definitions
│   │   ├── migrations/   # SQL migration files
│   │   └── index.ts      # DB connection
│   ├── auth/             # Authentication logic
│   └── utils.ts          # Shared utilities
├── server/               # Server-only code (actions, services)
│   ├── actions/          # Server Actions
│   └── services/         # Business logic
├── hooks/                # Custom React hooks (client-side)
└── types/                # TypeScript type definitions
```

**Rule:** Keep server logic in `server/` or server components. Never import server-only code into client components.

## Dev Commands

```bash
# Development
npm run dev          # Start dev server on http://localhost:3000

# Database
npm run db:generate  # Generate migrations from schema
npm run db:migrate   # Run migrations
npm run db:studio    # Open Drizzle Studio / DB browser
npm run db:seed      # Seed database with test data

# Build & Production
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run typecheck    # Run TypeScript type checking

# Testing
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
```

## SQL / Migration Conventions

### Schema Rules
- **Use explicit types**: Define all columns with proper SQLite types (`TEXT`, `INTEGER`, `REAL`, `BLOB`)
- **Primary keys**: Use `INTEGER PRIMARY KEY AUTOINCREMENT` for auto-incrementing IDs, or `TEXT PRIMARY KEY` with UUIDs/CUIDs
- **Timestamps**: Always include `created_at` and `updated_at` as `INTEGER` (unix timestamp) or `TEXT` (ISO8601). Set defaults.
- **Foreign keys**: Enable foreign keys in SQLite (`PRAGMA foreign_keys = ON`). Always define `ON DELETE` behavior explicitly.
- **Indexes**: Add indexes for foreign keys and frequently queried columns
- **Soft deletes**: Prefer `deleted_at` over hard deletes for user data (audit trail)

### Migration Rules
1. **Never edit existing migrations** - Create a new migration file for schema changes
2. **Migrations are sequential** - Name as `XXXX_description.sql` where XXXX is zero-padded number
3. **Migrations are idempotent when possible** - Use `IF NOT EXISTS` / `IF EXISTS`
4. **One logical change per migration** - Keep migrations focused and atomic
5. **Always test migrations** - Test up and down (rollback) locally before committing
6. **Store in version control** - All migration files must be committed

### Query Rules
- **Use parameterized queries** - Never interpolate user input into SQL strings
- **Use a query builder/ORM** - Prefer Drizzle ORM or Kysely for type safety
- **Transactions for multi-step operations** - Wrap related writes in transactions
- **Select only needed columns** - Avoid `SELECT *` in production queries
- **Handle errors gracefully** - Catch DB errors and return user-friendly messages

## Component Patterns

### Server vs Client Components
- **Default to Server Components** - Fetch data, access DB, read env vars in server components
- **Use Client Components sparingly** - Only when you need: `useState`, `useEffect`, event handlers, browser APIs
- **Mark client components** - Add `'use client'` at top of file when needed
- **Pass serializable props** - Don't pass functions/classes from server to client components

### Component Structure
```tsx
// Server Component example
export default async function Page() {
  const data = await fetchData();
  return <Component data={data} />;
}

// Client Component example
'use client'
export function InteractiveComponent() {
  const [state, setState] = useState();
  return <button onClick={() => setState(...) }>Click</button>;
}
```

### Best Practices
- **Colocate related code** - Keep component, types, and styles together when tightly coupled
- **Use composition** - Prefer `children` and slots over prop drilling
- **Type all props** - Define explicit interfaces/types for component props
- **Use Server Actions** - For form submissions and mutations, prefer Server Actions over API routes when possible
- **Handle loading/error states** - Use `loading.tsx`, `error.tsx`, and Suspense boundaries

## Patterns to Follow

- **Type safety first** - Infer types from DB schema where possible (Drizzle)
- **Validation at boundaries** - Validate all user input with Zod on server side
- **Authentication/Authorization** - Check auth on every protected route/action
- **Environment variables** - Use `zod` to validate env vars, access via `process.env` only in server code
- **Error handling** - Use try/catch, return typed results or throw appropriate errors
- **Security** - Sanitize inputs, use CSRF protection, set secure headers
- **Performance** - Use React Suspense, streaming, and proper caching strategies
- **Accessibility** - Use semantic HTML, ARIA labels where needed

## Anti-Patterns to Avoid

| Anti-Pattern | Why | What to do instead |
|--------------|-----|-------------------|
| **`"use client"` everywhere** | Bloats bundle size, loses server benefits | Only use client components when necessary |
| **Raw SQL string concatenation** | SQL injection vulnerability | Use parameterized queries/ORM |
| **Exposing secrets to client** | Security risk | Keep secrets in server code/env, never in client bundles |
| **Direct DB access in Client Components** | Not possible & insecure | Use Server Actions or API routes |
| **Storing sensitive data in localStorage** | XSS vulnerable | Use httpOnly cookies for auth tokens |
| **Skipping input validation** | Data corruption, security issues | Validate with Zod on server |
| **Editing old migrations** | Breaks migration history | Create new migration files |
| **Using `any` type** | Loses type safety | Use proper types, `unknown`, or type guards |
| **Mixing server/client logic** | Import errors, security issues | Respect the server/client boundary |
| **Ignoring foreign keys** | Data integrity issues | Enable PRAGMA foreign_keys and define relationships |

## Quick Start Checklist

When working on a greenfield Next.js 15 + SQLite project:

1. [ ] Set up Next.js 15 with App Router and TypeScript strict mode
2. [ ] Configure SQLite (better-sqlite3/Turso) with migrations
3. [ ] Enable foreign keys and set up schema
4. [ ] Add authentication (if needed) with secure session management
5. [ ] Set up environment variable validation
6. [ ] Follow the folder structure and conventions above

**Remember:** When in doubt, keep it on the server. Type safety and security are non-negotiable.
