# Claude.md Template: Next.js + SQLite SaaS

This is an opinionated, production-ready `CLAUDE.md` tailored for a Next.js 15 (App Router) + SQLite (Turso/better-sqlite3) SaaS application.

## Core Stack & Versions
- Next.js 15 (App Router)
- React 19
- TypeScript 5+
- Tailwind CSS 3.4+ / shadcn/ui
- Drizzle ORM (Type-safe SQL)
- SQLite (Turso / libSQL / better-sqlite3)

## Dev Commands
- `npm run dev`: Start local development server
- `npm run db:push`: Push schema changes to the local SQLite database directly
- `npm run db:generate`: Generate migration files for production
- `npm run db:migrate`: Run generated migrations
- `npm run db:studio`: Open Drizzle Studio to inspect data
- `npm run build`: Build for production
- `npm run lint`: Run ESLint and Prettier

## Folder Structure
We follow a domain-driven feature folder approach inside the App Router.
```text
src/
├── app/                  # Next.js App Router (only routing and layouts)
│   ├── (auth)/           # Route groups for layout sharing
│   ├── api/              # API Routes (avoid unless necessary; prefer Server Actions)
│   └── page.tsx          # Page components
├── components/           # Generic, reusable UI components
│   └── ui/               # shadcn/ui components (do not edit unless necessary)
├── lib/                  # Framework configurations (db, auth, utils)
│   ├── db/
│   │   ├── schema.ts     # Drizzle ORM schema definitions
│   │   └── index.ts      # Database connection export
│   └── utils.ts          # Tailwind merge, generic helpers
└── features/             # Domain logic (business rules, specialized components)
    └── [feature-name]/
        ├── actions.ts    # Server Actions for this domain
        ├── queries.ts    # Database read operations (Data Access Layer)
        └── components/   # UI components specific to this feature
```

## SQL / Migration Conventions
We use Drizzle ORM for type-safe interactions with SQLite.
- **Single Source of Truth**: All tables must be defined in `src/lib/db/schema.ts`. Do not use raw SQL `CREATE TABLE` scripts.
- **Primary Keys**: Always use standard text-based UUIDs or CUIDs (`text('id').primaryKey()`). Do not use auto-incrementing integers (`integer('id', { mode: 'number' })`) for user-facing models because they leak scale and create predictable URLs.
- **Timestamps**: Every table must include `createdAt` and `updatedAt` integer columns (SQLite does not have native date types; store as Unix epoch or ISO text. We prefer integer Unix epoch `integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(strftime('%s', 'now'))`)`).
- **Migrations**: 
  - For local dev, run `npm run db:push` to sync schema instantly. 
  - When a feature is complete, run `npm run db:generate` to output `.sql` migration files for deployment.
  - Never manually edit generated `.sql` migration files in the `drizzle/` folder.

## Component Patterns
- **Server-First by Default**: React Server Components (RSC) are the default. Do not add `'use client'` unless the component strictly requires React hooks (`useState`, `useEffect`) or browser APIs.
- **Data Access Layer**: Do not run database queries directly inside `page.tsx` or `layout.tsx`. Extract all data fetching into `features/[name]/queries.ts`. This isolates the DB logic and makes testing easier.
- **Server Actions for Mutations**: All form submissions and data mutations must use Next.js Server Actions defined in `features/[name]/actions.ts`. Return structured `{ data, error }` objects instead of throwing raw exceptions.
- **Colocation**: Put feature-specific components inside the `features/[feature]/` folder, not the global `components/` folder. The global folder is reserved strictly for generic UI blocks (buttons, inputs, modals).

## What We Don't Do (Anti-Patterns)
1. **No Client-Side Fetching for Initial Load**: Do not use `useEffect` or `react-query` to fetch data on mount. Use Server Components to fetch data server-side and pass it down as props.
2. **No Prisma**: We use Drizzle ORM. Prisma's Rust binary engine overhead is too heavy for edge deployments and Turso/SQLite. Do not suggest or install Prisma.
3. **No Default Exports**: Use named exports exclusively (`export const Button = ...`, not `export default Button`). Exception: Next.js specific files like `page.tsx`, `layout.tsx`, and `route.ts` which require default exports by framework design.
4. **No `.env` in Version Control**: Never hardcode API keys or database URLs. All configuration flows through `process.env`. Check `env.mjs` (if using T3 Env) to validate variables at startup.
5. **No Barrel Files**: Avoid `index.ts` files that just re-export other files (e.g., `export * from './button'`). They break tree-shaking and bloat development server memory. Import directly from the file path.
