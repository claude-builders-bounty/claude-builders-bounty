# Claude Code Project Guidelines

## Core Identity
This is a high-performance Next.js 15 SaaS built with the App Router, React Server Components (RSC), Server Actions, and a local SQLite (better-sqlite3 / Turso) database via Drizzle ORM. We prioritize strict typing, zero-dependency utility functions, and co-location of resources.

## Stack & Versions
- Next.js 15+ (App Router only, no `pages/` directory)
- React 19+ (Embrace new hooks: `use()`, `useActionState`, `useFormStatus`)
- TypeScript 5.5+ (Strict mode always enabled)
- Database: SQLite (via `better-sqlite3` or libSQL/Turso)
- ORM: Drizzle ORM
- Styling: Tailwind CSS v4

## Commands
- **Dev**: `npm run dev`
- **Build**: `npm run build`
- **Lint**: `npm run lint`
- **DB Generate**: `npm run db:generate`
- **DB Migrate**: `npm run db:migrate`
- **DB Studio**: `npm run db:studio`

## Folder Structure (Strict Co-location)
- `src/app/`: Only routing, layouts, and page entry points.
- `src/components/ui/`: Reusable, dumb, presentation components (shadcn/ui style).
- `src/features/[feature]/`: Feature-based architecture. A feature folder contains its own `components/`, `actions.ts`, `queries.ts`, and `types.ts`.
- `src/db/schema/`: Drizzle schemas split by domain (e.g., `users.ts`, `workspaces.ts`). Do not put everything in one giant `schema.ts`.
- `src/db/migrations/`: Auto-generated SQL migrations.

## Database & Migration Rules
1. **Never edit migrations manually.** Always use `drizzle-kit generate` to create migrations from schema changes.
2. **Schema changes first.** When adding a feature, update `src/db/schema/*.ts` first, generate the migration, and apply it before writing application code.
3. **No client-side DB access.** Never import `src/db` into client components (`"use client"`). Use Server Actions or Server Components to pass data down.
4. **Use Transactions.** For multi-table operations, always use `db.transaction()`. SQLite handles concurrent reads, but writes must be atomic.

## Component Patterns
1. **Server by Default:** Every component is a Server Component unless it absolutely needs interactivity (`useState`, `onClick`, `useEffect`).
2. **Push "use client" down:** Do not put `"use client"` at the top of a page. Isolate interactive logic into small, leaf-node components.
3. **Server Actions for Mutations:** Form submissions and data mutations must use Server Actions (`"use server"`). No traditional API routes (`app/api/`) unless building a public REST API or webhooks.
4. **Suspense boundaries:** Wrap data-fetching components in `<Suspense fallback={<Skeleton />}>` inside `page.tsx` rather than fetching in the page directly to enable streaming.

## Anti-Patterns (What We Don't Do and Why)
- ❌ **No `useEffect` for data fetching.** Why? Causes waterfalls and flickers. Use Server Components or SWR/React Query for client-side polling.
- ❌ **No generic API Routes for UI data.** Why? Server Actions provide type-safety without the fetch boilerplate.
- ❌ **No barrel files (`index.ts`).** Why? They break Next.js tree-shaking and cause circular dependencies. Import directly from the file.
- ❌ **No complex client-side state management (Redux/Zustand) unless strictly necessary.** Why? The server is the single source of truth. Use URLs/Query Params for shareable state.

## Formatting & Naming Conventions
- **Files/Folders:** `kebab-case.ts`
- **Components:** `PascalCase.tsx`
- **DB Tables:** `snake_case` (plural), e.g., `users`, `user_subscriptions`.
- **Zod Schemas:** Suffix with `Schema`, e.g., `insertUserSchema`.
- **Types/Interfaces:** Prefix with nothing, just descriptive PascalCase (e.g., `User`, not `IUser`).
