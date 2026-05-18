# Next.js 15 + SQLite SaaS

## Stack
- **Next.js 15** (App Router, Server Components by default)
- **React 19** (Server Actions, `use` hook)
- **SQLite**: `better-sqlite3` for local / `libsql` + `@libsql/client` for Turso edge
- **TypeScript**: strict, `noUncheckedIndexedAccess: true`
- **Tailwind CSS**: utility-only, no arbitrary values in JSX
- **Auth**: `lucia` + `oslo` (not NextAuth — simpler, works on edge)
- **Validation**: `zod` everywhere, parse at the boundary

## Versions (lock these)
- next: ^15.0.0
- react: ^19.0.0
- better-sqlite3: ^11.0.0
- @libsql/client: ^0.14.0
- lucia: ^3.0.0
- zod: ^3.23.0
- tailwindcss: ^3.4.0

## Folder Structure
```
├── app/                 # Routes, layouts, loading.tsx, error.tsx
│   ├── (auth)/          # Route group: login, register, logout
│   ├── (dashboard)/     # Route group: all authenticated pages
│   ├── api/             # Route handlers ONLY for webhooks / OAuth
│   └── layout.tsx       # Root layout: fonts, providers, metadata
├── components/
│   ├── ui/              # Atomic: Button, Input, Modal
│   └── features/        # Domain-specific: PostList, UserCard
├── lib/
│   ├── db/              # Schema, migrations, connection
│   ├── auth/            # Lucia setup, session validation
│   ├── validation/      # Zod schemas shared client/server
│   └── utils.ts         # cn() only. No business logic here.
├── actions/             # Server Actions ONLY
├── hooks/               # React hooks (client components only)
├── types/               # Shared TypeScript (not generated DB types)
├── public/
└── scripts/
    ├── migrate.ts       # One-shot migration runner
    └── seed.ts          # Dev seed data
```

## Naming Conventions
- **Files**: PascalCase for components (`UserCard.tsx`), kebab-case for everything else
- **Functions**: camelCase. Async functions end in `Async` only if there's a sync variant.
- **Server Actions**: `async function createPost(formData: FormData)` — no "Action" suffix
- **Database tables**: snake_case, plural. `users`, `posts`, `session`
- **Columns**: snake_case. `created_at`, `updated_at` on every table (triggers, not app code)

## Database Conventions
- **One schema file**: `lib/db/schema.sql`. No ORM. Raw SQL + `better-sqlite3`.
- **Migrations**: numbered, immutable, never edited after merge. `001_init.sql`, `002_add_posts.sql`
- **Runner**: `npx tsx scripts/migrate.ts` reads `lib/db/migrations/` in order, tracks in `_migrations` table
- **No `SELECT *`**. Always name columns.
- **No `delete` without `where`**. The app never calls `DELETE FROM`. Soft-delete with `deleted_at`.
- **No joins in components**. Fetch in Server Action or route handler, pass flattened data to component.

## Component Patterns
- **Server Components default**. Mark `use client` only when you need: event handlers, `useState`, `useEffect`, browser APIs.
- **Data fetching in Server Components**: call `lib/db/queries.ts` directly (not from client).
- **Forms**: Server Action bound via `<form action={createPost}>`. No `onSubmit` + `fetch` unless file upload > 2MB.
- **Loading state**: use `loading.tsx` at the route segment level. No skeletons scattered in components.
- **Errors**: `error.tsx` at route segment level. Log to console in dev, to monitoring in prod. Never show raw SQL errors to users.

## Authentication
- **Lucia v3** session cookie, HTTP-only, `SameSite=Lax`, `Secure` in prod.
- **Session validation in Server Components**: `const { user } = await validateRequest()` at top of page.
- **Session validation in Server Actions**: same helper, called inside the action.
- **Middleware**: only for `/api/*` that MUST bypass RSC (webhooks). Auth lives in components, not middleware.

## Validation Rules
- **Every user input**: parsed with Zod. No `as string` casts.
- **Reusable schemas in `lib/validation/`**: `userSchema`, `postSchema`. Used by Server Actions AND client `useFormState`.
- **Form state pattern**:
  ```ts
  'use client'
  const [state, action] = useFormState(createPost, { message: '' })
  ```
- **Never trust client**. Re-validate all inputs in Server Action even if client validated.

## Anti-Patterns (We Don't Do This)
1. **No `useEffect` for data fetching**. Server Components or Server Actions only.
2. **No `axios` / `fetch` wrappers in components**. If you need client-side data, create a Server Action.
3. **No CSS-in-JS** (`styled-components`, `emotion`). Tailwind only. Keeps RSC bundle small.
4. **No barrel exports** (`index.ts` re-exporting 20 files). Import directly. Prevents circular deps.
5. **No `any`**. Use `unknown` + parse, or `satisfies` for inline type narrowing.
6. **No database queries in `page.tsx` without `Suspense`**. If query > 50ms, wrap in `Suspense` + `loading.tsx`.

## Dev Commands
```bash
# Install
npm install

# Migrate (creates local dev.db)
npx tsx scripts/migrate.ts

# Seed dev data
npx tsx scripts/seed.ts

# Dev server
npm run dev

# Type check (CI)
npm run typecheck

# Lint + format
npm run lint
npm run format
```

## Environment Variables
```
DATABASE_URL=file:./dev.db          # local better-sqlite3
# DATABASE_URL=libsql://...?auth=... # Turso prod
AUTH_SECRET=                        # 32+ random bytes, openssl rand -base64 32
```

## Testing
- **No unit tests for UI** (React Testing Library) unless complex interaction logic.
- **Test what breaks**: DB migrations (run forward/back), Zod schemas (edge cases), auth flows (cookie/session lifecycle).
- **Integration test**: `scripts/smoke.ts` creates user, logs in, creates post, verifies DB state. Run in CI before deploy.

## Deployment
- **Vercel**: Serverless functions. Use `@libsql/client` (HTTP), not `better-sqlite3` (native module).
- **Non-Vercel**: Docker. `better-sqlite3` compiles natively. Mount volume for `data/`.
- **Migrations run in build step**, not at runtime. `scripts/migrate.ts` called in `package.json` `build` script.
