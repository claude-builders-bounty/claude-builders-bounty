# CLAUDE.md – Next.js 15 SaaS Boilerplate (SQLite + Turso)

## Project Overview
This is a production-grade SaaS application built with Next.js 15 (App Router + React 19). 
We prioritize **Server Components first**, minimal client JavaScript, type safety, and seamless local-to-production database workflow using SQLite.

- Local development → `better-sqlite3` (fast, synchronous, zero network)
- Production / Edge → **Turso** (libSQL) with embedded replicas for low-latency reads
- Goal: Fast iteration, strong tenant isolation (via `tenant_id` or per-tenant DBs later), excellent DX, and security by default.

Core philosophy: **Keep the server heavy, the client light**. Do as much as possible in Server Components and Server Actions. Only mark `'use client'` when interactivity (state, browser APIs, event handlers) is truly required.

## Tech Stack & Versions (Strict – Do Not Deviate Without Strong Reason)
- **Next.js**: 15.x (App Router only)
- **React**: 19.x
- **TypeScript**: ^5.5+ with `"strict": true`
- **Styling**: Tailwind CSS + shadcn/ui (or equivalent headless + Tailwind components)
- **Database**: 
 - ORM: **Drizzle ORM** (best type safety + SQLite performance; Prisma avoided due to heavier runtime and migration DX on SQLite)
 - Local: `better-sqlite3`
 - Production: `@libsql/client` + Turso
- **Validation**: Zod (server and form validation)
- **Forms**: React Hook Form + Zod resolver (when client forms needed)
- **Auth**: NextAuth.js / Auth.js or Clerk/Lucia (implement in middleware + Server Actions double-check)
- **Other**: Server Actions (preferred over Route Handlers for mutations), TanStack Query (only for complex client-side caching)

## Recommended Project Structure (Opinionated – Follow Exactly)

```
/
├── src/
│ ├── app/ # App Router – keep lean
│ │ ├── (auth)/ # Route group for auth pages (no URL impact)
│ │ ├── (dashboard)/ # Protected SaaS area
│ │ ├── api/ # Only for webhooks, external integrations (avoid for internal logic)
│ │ ├── layout.tsx
│ │ ├── globals.css
│ │ └── page.tsx
│ ├── components/
│ │ ├── ui/ # shadcn/ui primitives (unchanged)
│ │ └── features/ # Business components by domain
│ ├── features/ # Feature-sliced architecture (preferred for SaaS)
│ │ └── billing/ # Example: subscriptions, invoices, etc.
│ │ ├── actions.ts # Server Actions
│ │ ├── queries.ts # Data fetching logic
│ │ └── components/
│ ├── lib/
│ │ ├── db/
│ │ │ ├── schema.ts # All Drizzle table definitions
│ │ │ ├── client.ts # Environment-aware DB client (better-sqlite3 vs Turso)
│ │ │ ├── migrations/ # Generated migration files
│ │ │ └── index.ts # db instance export
│ │ ├── utils.ts
│ │ └── auth.ts # Auth helpers
│ ├── hooks/ # Client-only custom hooks
│ └── types/ # Global TS types
├── drizzle.config.ts
├── next.config.mjs
├── tailwind.config.ts
├── package.json
└── .env.example
```

**Why this structure?** 
Feature slicing + domain folders make it easy to scale SaaS features (billing, teams, analytics) without polluting the `app/` folder. Database logic is isolated to prevent accidental client bundling of credentials or connections.

## Naming Conventions (Strict)
- Files & folders: `kebab-case` (e.g. `create-subscription-action.ts`)
- React Components: `PascalCase`
- Functions, variables, hooks: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Database tables & columns: `snake_case`
- Drizzle tables: `xxxTable` (e.g. `usersTable`)
- Server Actions: end with `Action` (e.g. `createWorkspaceAction`)

This consistency reduces cognitive load and makes AI-generated code instantly recognizable.

## Database & Migration Rules (Critical for Reliability)
We use **Drizzle Kit** for versioned migrations — never `db push` in production.

**Development Commands** (add to `package.json` scripts):
```json
"scripts": {
 "dev": "next dev",
 "build": "next build",
 "db:generate": "drizzle-kit generate",
 "db:migrate": "drizzle-kit migrate",
 "db:studio": "drizzle-kit studio"
}
```

**Workflow:**
1. Update src/lib/db/schema.ts
2. Run pnpm db:generate (or npm equivalent)
3. Review the generated migration SQL in src/lib/db/migrations/
4. Run pnpm db:migrate locally
5. Commit the migration files

**Local vs Production:**
- Local: better-sqlite3 with file-based DB (fast feedback loop)
- Production: Turso URL + auth token via env vars (TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
- Never ship a file-based SQLite to Vercel/Edge — the filesystem is ephemeral.

**Anti-patterns to avoid:**
- Running raw SQL strings outside of Drizzle (except rare complex cases using `` sql`` template)
- Modifying schema directly in production
- Importing DB client in any Client Component ('use client') → leaks secrets or breaks Edge runtime
- Using better-sqlite3 in production code paths

## Component & Architecture Patterns (Server-First)
- **Default**: Server Components (no 'use client')
- **Fetch data** directly in Server Components close to where it's used
- **Mutations** → Server Actions (with 'use server'). Prefer over Route Handlers for most internal operations
- **Client Components**: Keep small and focused — only for forms, state, animations, or browser APIs
- Use useActionState (React 19) for progressive enhancement on forms when possible
- **Revalidation**: Use revalidatePath / revalidateTag after mutations

**Why?** This minimizes client bundle size, improves SEO/performance, and keeps sensitive logic (DB, auth, payments) server-only.

## What We Don't Do (and Why)

- **Don't put business logic in Client Components or Route Handlers** when a Server Action suffices → extra network roundtrips and larger bundles.
- **Don't use Prisma with SQLite** in this project → Drizzle offers superior type safety, lighter runtime, and better migration experience for SQLite/Turso.
- **Don't skip migration review** → un-reviewed migrations have caused data loss in past SaaS projects.
- **Don't expose any database credentials or connection logic** to the client.
- **Don't rely solely on middleware for auth** → always double-check permissions in Server Actions/Components (defense in depth).
- **Don't mix local SQLite and Turso clients** in the same code path without clear environment abstraction in client.ts.
- **Don't commit sensitive .env files** or hard-code secrets.

## Security & Production Mindset
- All user input validated with Zod on the server
- Rate limiting and security headers enabled for SaaS exposure
- Tenant isolation enforced at query level (WHERE tenant_id = ?)
- Server Actions protected with auth checks

## How to Work With This Project (For Claude / AI Assistant)

1. Read relevant schema, queries, and actions first.
2. Plan changes: schema → migration → queries/actions → UI.
3. Generate migration if schema changes.
4. Implement with Server Components/Actions by default.
5. Add proper error handling and user-friendly messages.
6. Ensure the change works in both local (better-sqlite3) and Turso environments.
7. Keep code clean, typed, and consistent with existing patterns.

**Strictly follow this CLAUDE.md.** It exists to eliminate ambiguity and keep the codebase maintainable as the SaaS grows.

**Questions?** Ask only if the requirement truly conflicts with these rules.