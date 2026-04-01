# AI Engineering Context (Next.js 15 + SQLite SaaS)

We follow strict, opinionated architectural patterns for this Next.js 15 + SQLite/Turso SaaS project. **Never deviate** from these conventions without explicit authorization from the lead developer.

## Core Stack & Tooling

*   **Framework:** Next.js 15 (App Router strictly)
*   **Database:** SQLite via `libSQL` / Turso (`@libsql/client`)
*   **ORM / Query Builder:** Drizzle ORM
*   **Styling:** Tailwind CSS v3 + `shadcn/ui` components
*   **Auth:** NextAuth (Auth.js) v5 beta (configured with Drizzle)
*   **Package Manager:** `pnpm` (Do not use `npm` or `yarn`)

## Commands

*   `pnpm dev` - Start the local dev server (Turbopack)
*   `pnpm build` - Build the production application
*   `pnpm db:generate` - Generate Drizzle SQLite SQL migration files
*   `pnpm db:push` - Push schema directly to the local development database
*   `pnpm db:studio` - Open Drizzle Studio to inspect the database

## Folder Structure (Strictly Enforced)

```text
src/
├── app/                  # App Router: file-based routing ONLY. No business logic.
│   ├── (auth)/           # Route groups for specific layouts
│   ├── api/              # Route handlers (NextResponse)
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Server Component page maps
├── components/
│   ├── ui/               # Generic shadcn/ui and primitive components ONLY.
│   └── app/              # Domain-specific and feature-specific business components.
├── lib/
│   ├── db/               # Database config, schemas, and Drizzle instances
│   │   ├── schema/       # Exported database tables representing the schema
│   │   └── index.ts      # Turso DB connection
│   ├── server/           # Pure server-side business logic and Server Actions
│   └── utils.ts          # Generic stateless utilities (e.g. cn() tailwind merger)
```

## SQL / Migration Conventions

1.  **Drizzle ORM dictates the schema.** Never write manual `ALTER TABLE` statements or modify the `.db` file directly. Always update definitions in `src/lib/db/schema/` and run `pnpm db:generate`.
2.  **Transactions.** Always wrap multi-statement writes in a `db.transaction(async (tx) => { ... })` to prevent partial updates.
3.  **Client-side SQLite.** Always use `libSQL` and its compatible queries for deployment on serverless edges (Turso capability). Do not use `better-sqlite3` as it relies on node-gyp bindings that crash on Vercel/Cloudflare.
4.  **No complex Joins without Relations.** Rely on Drizzle Relational Queries (`db.query.tableName.findMany`) for joined data. Keep raw SQL `sql` templating strictly to a minimum, and only for unsupported aggregations.

## Component Patterns

1.  **Server Actions are the ONLY way to mutate data.** Define them in `src/lib/server/actions/`. Never use traditional API routes (`src/app/api/...`) for form submissions or internal application state mutations.
2.  **Default to Server Components (RSC).** All pages and components must be standard async server-components unless interactivity (`useState`, `onClick`, `useEffect`) is strictly necessary. If so, add `"use client"` at the very top of the file, but push the boundary as far down the tree as possible.
3.  **Data Fetching.** Fetch data directly in the Server Component using `await db.query...`. 
4.  **Colocate Definitions.** Keep small interfaces/types inside the component file if they are used nowhere else.

## What we DON'T do (Anti-patterns)

1.  **Do NOT use generic API Routes for UI data.** `src/app/api/...` is strictly reserved for exposing public webhooks, cron jobs, or 3rd-party integrations. Internal SaaS UI data must be fetched directly via RSC (Server Components) or mutated via Server Actions.
     *Why: API routes introduce unnecessary HTTP overhead, type-safety loss, and serialization boundaries within the Next.js app.*
2.  **Do NOT use local filesystem SQLite in production.** For `development`, we use a local `.db` file. For `production`, we connect to Turso. Thus, you must never write code that interacts directly with `fs` for database backups, as Vercel ephemeral storage will delete it on cold starts.
    *Why: Edge-compatible architectures require separated network-accessed databases.*
3.  **Do NOT use `useEffect` for data fetching.** Never use SWR or React Query on the client unless polling live data or infinite scrolling. Use RSC.
    *Why: Server components execute closer to the database and eliminate client waterfalls.*
4.  **Do NOT put `"use client"` at the root of a page layout.**
    *Why: It nukes the entire server-side rendering capability for the child tree.*
