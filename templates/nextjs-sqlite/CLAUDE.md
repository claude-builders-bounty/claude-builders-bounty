# Claude Context: Next.js + SQLite SaaS

This project is a modern, opinionated SaaS built on Next.js App Router and SQLite. Read these rules before writing any code.

## Tech Stack & Versions
- **Framework**: Next.js 15 (App Router only, React 19)
- **Database**: SQLite (via `better-sqlite3` locally, or Turso in production)
- **ORM/Query Builder**: Drizzle ORM
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Auth**: Better-Auth (or NextAuth.js)

## Project Structure
```
├── app/                  # Next.js App Router (pages, layouts, api routes)
│   ├── (auth)/           # Route groups for logical separation
│   ├── (dashboard)/
│   └── api/              # Route handlers
├── components/
│   ├── ui/               # Generic UI components (shadcn)
│   └── shared/           # Domain-specific reusable components
├── db/                   # Database logic
│   ├── schema.ts         # Drizzle schema definitions
│   ├── index.ts          # Database connection instantiation
│   └── migrations/       # Auto-generated SQL migrations
├── lib/                  # Shared utilities
│   ├── actions.ts        # Next.js Server Actions
│   └── utils.ts          # Helper functions (cn, formatters)
└── public/               # Static assets
```

## Database & Migration Rules
- **Schema**: All tables must be defined in `db/schema.ts`. Use snake_case for table and column names in the DB, but camelCase for the Drizzle model definitions.
- **Migrations**: Never write raw SQL migrations by hand. Always run `npm run db:generate` to let Drizzle create the migration, then `npm run db:push` to apply it.
- **Relations**: Define relations explicitly using Drizzle's `relations()` API to ensure type-safe joins.
- **SQLite constraints**: SQLite does not support native Enums or Arrays. Use `text({ enum: ["a", "b"] })` for enums, and `text({ mode: "json" })` to store simple arrays.

## Component & Rendering Patterns
- **Server Components by default**: Every component in `app/` is a React Server Component (RSC) unless explicitly marked with `"use client"`.
- **"use client" usage**: Push `"use client"` as far down the component tree as possible. Only use it on leaf nodes that require interactivity (onClick, useState, hooks).
- **Data Fetching**: Fetch data directly in Server Components using async/await. Do not use `useEffect` or `react-query` for initial data loads.
- **Mutations**: Use Next.js Server Actions (defined in `lib/actions.ts` with `"use server"`) for all form submissions and data mutations. Never use API routes (`/api`) just to submit a form.

## What We Don't Do (And Why)
- ❌ **No Pages Router**: Do not use the `pages/` directory. We are strictly App Router.
- ❌ **No redundant API routes**: Don't build REST API endpoints unless they are being consumed by an external service or a webhook. Use Server Actions for internal client-to-server communication.
- ❌ **No heavy client state**: Avoid Redux or Zustand. The server is the source of truth. Use URL search params (`?query=value`) for shareable UI state (like pagination or tabs).
- ❌ **No raw SQL queries**: Always use the Drizzle query builder or relational query API to prevent SQL injection and maintain type safety.

## Common Dev Commands
- `npm run dev` - Start local dev server
- `npm run db:generate` - Generate Drizzle migration
- `npm run db:push` - Apply migration to local SQLite
- `npm run db:studio` - Open Drizzle studio to view data
- `npm run build` - Build for production
