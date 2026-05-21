# Claude Code Guidelines: Next.js 15 + SQLite SaaS Template 🚀

This guide defines the strict architectural patterns, commands, and conventions for this codebase.

## 🛠️ Stack & Versions
- **Framework**: Next.js 15.x (App Router, React 19)
- **Database**: SQLite via `@libsql/client` (Turso) or `better-sqlite3`
- **ORM**: Drizzle ORM
- **Styling**: Tailwind CSS v4 / shadcn/ui
- **Runtime**: Node.js 22.x LTS

---

## 📁 Recommended Folder Structure
Follow this standard directory layout for all modules:
```
src/
├── app/                  # App Router pages and API routes
│   ├── (auth)/           # Route groups for auth layout separation
│   ├── dashboard/        # Dashboard module
│   ├── api/              # Standard Next.js serverless API routes
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Homepage
├── components/           # Reusable UI/Shared components
│   ├── ui/               # Lower-level shadcn primitive elements
│   └── dashboard/        # dashboard specific components
├── lib/                  # Shared utility libraries
│   ├── db/               # Database config & schemas
│   │   ├── migrations/   # Generated SQL migrations
│   │   ├── client.ts     # SQLite connection client
│   │   └── schema.ts     # Drizzle schemas
│   └── utils.ts          # Tailwind CN merging helper
└── hooks/                # Custom React client hooks
```

---

## 💻 Dev Commands
- **Development Server**: `npm run dev`
- **Build Production Bundle**: `npm run build`
- **Lint Codebase**: `npm run lint`
- **Drizzle Schema Generate**: `npm run db:generate` (Generates SQL migration files)
- **Drizzle Schema Migrate**: `npm run db:migrate` (Applies migrations to local SQLite)
- **Drizzle Studio**: `npm run db:studio` (Visual DB interface)

---

## 🗄️ Database & Migration Conventions (SQLite + Drizzle)
SQLite is single-writer. Follow these conventions for transactional safety:
1. **Drizzle Schemas**: All table definitions must be inside `src/lib/db/schema.ts` (or mapped imports) to keep definitions centralized.
2. **Nullable Fields**: Explicitly mark fields as `.notNull()` unless they are optional or user-inputted.
3. **No Direct Schema Updates**: Never mutate the local SQLite file directly. Always generate migrations via Drizzle:
   ```bash
   npm run db:generate
   npm run db:migrate
   ```
4. **Transactions**: Use Drizzle `db.transaction()` block whenever writing to multiple tables simultaneously (e.g. creating a new user and an associated billing profile).

---

## 🧩 Component & Coding Patterns
- **Server Components by Default**: All components under `src/app/` are React Server Components (RSC) by default. Use RSCs to fetch data directly at the component level:
  ```tsx
  // GOOD: RSC fetching data directly
  export default async function DashboardPage() {
    const items = await db.select().from(itemsTable);
    return <ItemList items={items} />;
  }
  ```
- **Interactive Boundaries**: Mark client components explicitly with `"use client"` only when incorporating hooks (`useState`, `useEffect`) or DOM event listeners.
- **Server Actions**: All mutations (form submissions, button clicks triggers) must use React Server Actions placed inside files ending with `.actions.ts` or scoped under a `"use server"` function.
- **Strict TypeScript**: Avoid `any` type casting. Declare types for props and return objects explicitly.

---

## ❌ Anti-Patterns to Avoid
- **No Database Queries in Client Components**: Never fetch SQLite data directly from client components. Doing so exposes database operations or leaks server secrets. Always fetch in RSCs or wrap queries inside Server Actions.
- **No SQLite Connection Spams**: Avoid invoking database connection instances per-query. Always import the single cached client export from `src/lib/db/client.ts`.
- **No SQL String Concat**: Always use Drizzle query builders to avoid SQL Injection vulnerabilities. If raw SQL is needed, use Drizzle's `sql` template literal:
  ```tsx
  // BAD
  db.run(`SELECT * FROM users WHERE id = '${userId}'`);
  // GOOD
  db.execute(sql`SELECT * FROM users WHERE id = ${userId}`);
  ```
- **No client-side state for routing**: Prefer search parameters (`?tab=profile`) over local component state (`useState`) for tabs and filter navigation. This maintains shareable URLs.
