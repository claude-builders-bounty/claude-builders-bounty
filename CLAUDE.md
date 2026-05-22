# CLAUDE.md for Next.js 15 App Router + SQLite SaaS Projects

This guide serves as the source of truth for coding patterns, project structure, and conventions for our Next.js + SQLite application.

## Tech Stack & Core Libraries

- **Framework**: Next.js 15 (App Router only, React Server Components by default)
- **Database**: SQLite (via `better-sqlite3` or Turso/libSQL for edge compatibility)
- **Styling**: Tailwind CSS + shadcn/ui components
- **Authentication**: NextAuth.js (v5 / Auth.js) or Lucia Auth
- **Validation**: Zod for all form schemas and API validations
- **State Management**: Zustand (for global client state only, keep state in URL where possible)

## Commands

- `npm run dev` - Start the development server (runs Next.js and DB watchers)
- `npm run build` - Build the production app
- `npm run db:push` - Push schema changes directly to the database
- `npm run db:generate` - Generate migrations from schema changes
- `npm run db:studio` - Open the visual database studio
- `npm run lint` - Run ESLint and TypeScript checks

## Project Structure

```
├── app/                  # Next.js App Router (Pages, Layouts, APIs)
│   ├── (auth)/           # Route groups (auth flows)
│   ├── (dashboard)/      # Protected routes
│   ├── api/              # Route Handlers
│   └── globals.css       # Global CSS and Tailwind directives
├── components/           # Reusable UI components
│   ├── ui/               # shadcn/ui generic components (buttons, inputs)
│   └── features/         # Domain-specific components (e.g., UserProfile, BillingCard)
├── lib/                  # Utilities, helpers, and configurations
│   ├── db/               # Database connection and schema
│   │   ├── index.ts      # Connection instance
│   │   ├── schema.ts     # Drizzle/Prisma schema definitions
│   │   └── queries.ts    # Reusable complex SQL queries
│   ├── auth.ts           # Authentication configuration
│   └── utils.ts          # Shared utility functions (e.g., cn for tailwind)
├── actions/              # Server Actions (form submissions, mutations)
├── types/                # Shared TypeScript types and Zod schemas
└── public/               # Static assets
```

## Component & Routing Patterns

1. **Server First**: Default to React Server Components (RSC). Only add `'use client'` when you absolutely need interactivity (hooks, event listeners).
2. **Server Actions for Mutations**: All database mutations (create/update/delete) MUST use Server Actions placed in the `actions/` directory. Do not use Route Handlers (`app/api/*`) for standard CRUD unless exposing a public API.
3. **Data Fetching**: Fetch data directly in Server Components using async/await. Do not use `useEffect` or client-side fetchers like SWR/React Query unless fetching highly dynamic data that changes every second.
4. **Colocation**: Keep components, actions, and types close to where they are used if they are only used in one specific feature.

## Database & SQL Conventions

1. **Schema Definition**: Define schema in a single `lib/db/schema.ts` file or split by domain if it grows large.
2. **SQLite Types**: Remember SQLite's dynamic typing. Use integers for booleans (`0` and `1`), and integers or ISO strings for dates.
3. **Primary Keys**: Use CUIDs or UUIDs v7 for IDs, NOT auto-incrementing integers (avoids sequence issues and guessable IDs).
4. **Soft Deletes**: Use `deleted_at` timestamps instead of hard deleting records, especially for critical SaaS entities (Users, Workspaces, Subscriptions).

## What We DON'T Do (Anti-patterns)

- **NO Pages Router**: Do not use the `pages/` directory. Everything goes in `app/`.
- **NO Client-side Auth Checks**: Always verify user session on the server via middleware or inside the Server Component / Server Action. Never rely solely on client-side context to protect data.
- **NO Direct DB Calls in Client Components**: This will leak secrets or throw errors. All DB logic must live in Server Components or Actions.
- **NO Inline Tailwind Clutter**: Extract complex Tailwind classes using `cva` (class variance authority) or the `cn` utility to keep components readable.
- **NO Over-fetching**: Only select the columns you need from the database, especially when passing data from Server Components to Client Components, to avoid leaking sensitive data or inflating payload sizes.
