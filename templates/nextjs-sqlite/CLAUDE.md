# Claude AI Context: Next.js 15 + SQLite SaaS

This is an opinionated reference for writing code in this repository. Follow these constraints strictly.

## 🏗 Stack & Versions
- **Framework:** Next.js 15 (App Router only, React 19)
- **Database:** SQLite (via `better-sqlite3` locally, or Turso in prod)
- **ORM:** Drizzle ORM
- **Styling:** Tailwind CSS v3 + shadcn/ui

## 📂 Folder Structure
We use a domain-driven structure inside `src/`.
- `src/app/`: ONLY routing, layouts, and page entry points. No business logic.
- `src/db/`: `schema.ts`, `index.ts`, and `migrations/`.
- `src/features/<domain>/`: Self-contained modules (e.g., `features/auth/`, `features/billing/`).
  - Contains its own `components/`, `actions.ts`, `queries.ts`, and `types.ts`.
- `src/components/ui/`: Global reusable UI components (shadcn).

## 🗄 SQL & Migration Conventions
- **Schema Definitions:** All tables must be defined in `src/db/schema.ts`. Use singular names for tables (e.g., `user`, not `users`).
- **Timestamps:** Every table must have `createdAt` and `updatedAt` (defaulting to `sql\`CURRENT_TIMESTAMP\``).
- **Primary Keys:** Use `text('id').primaryKey()` with generated CUIDs/UUIDs, NOT auto-incrementing integers.
- **Migrations:** Never modify the database directly. Always run `npm run db:generate` followed by `npm run db:push` to apply changes.
- **Queries:** Separate read operations into `queries.ts` and write operations into server actions `actions.ts`.

## 🧩 Component Patterns
- **Default to Server Components (RSC):** Every component is a Server Component unless it uses state, effects, or DOM events.
- **Client Boundary:** Use the `"use client"` directive as deep in the tree as possible. Do not put `"use client"` on a page layout.
- **Data Fetching:** Fetch data directly in the Server Component using async/await. Do NOT use `useEffect` for data fetching.
- **Mutations:** Use Next.js Server Actions for all database mutations. Always revalidate the path (`revalidatePath`) after a successful mutation.

## 🚫 What We Don't Do (Anti-Patterns)
1. **NO `getServerSideProps` or `getStaticProps`:** We are strictly App Router. Use standard `async/await` in Server Components.
2. **NO API Routes (`/api/*`) for UI mutations:** Use Server Actions instead. API routes are reserved exclusively for external webhooks (e.g., Stripe).
3. **NO raw SQL strings:** Always use Drizzle ORM's query builder to prevent SQL injection and maintain type safety.
4. **NO inline Tailwind classes longer than 80 chars:** Extract complex logic into `cva` (class-variance-authority) or a separate constant.

## 💻 Developer Commands
- `npm run dev`: Start Next.js development server
- `npm run db:generate`: Generate migration files based on schema changes
- `npm run db:push`: Push schema changes directly to the local SQLite database
- `npm run db:studio`: Open Drizzle Studio to inspect the database
