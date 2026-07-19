# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

- **Framework:** Next.js 15 (App Router)
- **Database:** SQLite via better-sqlite3 (local) or Turso (production)
- **ORM:** Drizzle ORM
- **Auth:** NextAuth v5 with GitHub + Google providers
- **Styling:** Tailwind CSS v4 + shadcn/ui
- **Language:** TypeScript strict mode
- **Package manager:** pnpm

## Folder Structure

```
src/
  app/          # App Router pages + API routes
    (auth)/     # Auth-protected layouts
    api/        # Route handlers (no Express needed)
  components/   # Shared React components
    ui/         # shadcn/ui primitives
  db/           # Drizzle schema + migrations
    schema/     # Table definitions
    seed.ts     # Development seed data
  lib/          # Utility functions
    email.ts    # Email helpers
    stripe.ts   # Payment helpers
  hooks/        # Shared React hooks
```

## Database Conventions

- **Every migration must be reviewed.** No auto-push to production.
- Use Drizzle Kit for migrations: `pnpm db:generate` then `pnpm db:migrate`
- Foreign keys are defined in Drizzle schema, not in SQLite pragmas
- Soft deletes preferred: add `deletedAt: timestamp` instead of `DELETE FROM`
- Index every column used in `WHERE`, `ORDER BY`, or `JOIN`

### DO

```ts
export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().default(sql`(unixepoch())`),
});
```

### DON'T

```ts
// No raw SQL strings in route handlers
await db.run(sql`DELETE FROM users WHERE id = ${id}`);
// Use Drizzle methods instead
await db.delete(users).where(eq(users.id, id));
```

## Component Patterns

- Server components by default. Client components only when you need `useState`, `useEffect`, or browser APIs.
- Add `"use client"` on a separate line, not mixed with imports.
- Props are typed with `interface`, never `type`.
- Use `cn()` from `clsx + tailwind-merge` for className merging.

## What We DON'T Do

- No `any` types. If you can't type it, restructure the code.
- No raw `<img>` tags. Use `next/image` with explicit `width`/`height`.
- No `useEffect` for data fetching. Use React Server Components or `use` with Suspense.
- No barrel exports (`index.ts` that re-exports everything). Import directly from the module file.
- No `process.env` inline. Use `src/lib/env.ts` with Zod validation.
