# CLAUDE.md - Next.js 15 App Router + SQLite SaaS Template

## 🏗️ Project Architecture & Stack
- **Framework:** Next.js 15 (App Router only)
- **Database:** SQLite (via `better-sqlite3` or Turso/libSQL)
- **ORM:** Drizzle ORM (Type-safe, fast, explicit)
- **Styling:** Tailwind CSS + shadcn/ui
- **Auth:** NextAuth.js (v5) or Lucia (Opinionated session management)
- **State:** React Server Components (RSC) for data fetching, Client Components only when interactivity is needed.

## 📂 Directory Structure & Naming Conventions
- `app/` - Routing only. Pages, layouts, and route handlers.
- `app/api/` - Next.js Route Handlers. Keep logic thin, delegate to `lib/`.
- `components/ui/` - Reusable, dumb UI components (e.g., shadcn/ui).
- `components/features/` - Complex, stateful, or domain-specific components.
- `lib/` - Business logic, utilities, and integrations.
- `db/` - Database schema (`schema.ts`), connection setup, and seed scripts.
- **Naming:**
  - Files/Folders: `kebab-case` (e.g., `user-profile.tsx`, `auth-utils.ts`).
  - Components: `PascalCase` (e.g., `UserProfile`).
  - *Reasoning:* Consistency across OS case-sensitivity limits and recognizable component imports.

## 💾 Database & Migration Rules
- **No Implicit Migrations:** All schema changes must generate a migration file using `drizzle-kit generate:sqlite`.
- **Naming:** Table names should be plural `snake_case` (e.g., `users`, `user_subscriptions`).
- **Timestamps:** Every table must have `created_at` (default `CURRENT_TIMESTAMP`) and `updated_at`.
- **Soft Deletes:** Prefer an `is_deleted` boolean or `deleted_at` timestamp over dropping rows to preserve historical SaaS data.
- **Connections:** Ensure a singleton DB connection in development to prevent "database is locked" errors due to Next.js HMR.

## 🚀 Dev Commands
- `npm run dev` - Start development server
- `npm run db:generate` - Generate Drizzle migration
- `npm run db:push` - Apply schema directly to local SQLite (use only in local dev)
- `npm run db:migrate` - Run migrations against production/staging
- `npm run db:studio` - Open Drizzle Studio to inspect SQLite data

## 🎯 Patterns to Follow
- **Server Actions for Mutations:** Form submissions and data mutations should use Server Actions inside `actions/` directories.
  - *Reasoning:* Reduces client bundle size and automatically integrates with App Router cache invalidation (`revalidatePath`).
- **Colocate Types:** Place interfaces/types in the same file as the feature they belong to, or in `types/` if globally shared.
- **Zod for Validation:** Validate all incoming API payloads and Server Action inputs using Zod.
  - *Reasoning:* Strict runtime type safety before hitting the SQLite database.

## 🚫 Anti-Patterns to Avoid
- **Avoid Client Data Fetching (`useEffect`):** Do not fetch initial data on the client. Use Server Components.
  - *Reasoning:* RSCs are faster, have direct DB access, and prevent layout shifts.
- **Don't abstract SQLite too much:** Avoid complex repository patterns. Use Drizzle's query builder directly in your server actions or data access layer (`lib/queries.ts`).
  - *Reasoning:* SQLite is fast enough that unnecessary abstraction layers just add boilerplate without performance benefits.
- **Never expose DB errors to the client:** Catch SQLite constraint errors (e.g., unique constraints) on the server and return generic, safe error messages to the UI.

## 🛠️ Claude Context Notes
When generating code for this project:
1. Default to Server Components. Add `"use client"` only at the leaf nodes.
2. Use Drizzle ORM syntax, never raw SQL strings unless explicitly requested.
3. Import UI components from `@/components/ui/...`.
