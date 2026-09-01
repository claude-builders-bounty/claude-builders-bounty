# CLAUDE.md - Next.js 15 + SQLite (Better-SQLite3/Turso) Production Template

## 🚀 Tech Stack & Versions
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5+ (Strict Mode)
- **Styling**: Tailwind CSS
- **Database**: SQLite via `better-sqlite3` (Local) or `libsql` (Turso)
- **Runtime**: Node.js 20+

## 📁 Project Structure
```text
├── app/                # App Router (Pages, Layouts, API Routes)
│   ├── (auth)/         # Auth group routes
│   ├── (dashboard)/    # Main application routes
│   └── api/            # Serverless API endpoints
├── components/         # React Components
│   ├── ui/             # Atomic UI components (Shadcn style)
│   ├── forms/          # Complex form logic
│   └── layout/         # Page wrappers, Nav, Footer
├── hooks/              # Custom React hooks (client-side)
├── lib/                # Core utilities & Shared logic
│   ├── db/             # Database connection, schema, and migrations
│   │   ├── client.ts   # SQLite client initialization
│   │   └── migrations/ # .sql migration files
│   └── utils.ts        # Helper functions (cn, formatters)
├── services/           # Business logic / Data Access Layer (DAL)
│   └── users.ts        # Domain-specific DB queries
├── types/              # Global TypeScript definitions
└── public/             # Static assets
```

## 🛠 Development Commands
- `npm run dev` - Start development server
- `npm run build` - Production build
- `npm run typecheck` - Run TypeScript type check
- `npm run lint` - Run ESLint
- `npm run migrate` - Execute pending SQL migrations (custom script)

## 📐 Coding Conventions

### 1. Naming Conventions
- **Components**: `PascalCase.tsx` (e.g., `UserDashboard.tsx`)
- **Hooks**: `camelCase.ts` starting with `use` (e.g., `useAuth.ts`)
- **Services/Utils**: `camelCase.ts` (e.g., `userSvc.ts`)
- **Folders/Files**: `kebab-case` (e.g., `user-profile/`)
- **Database Tables**: `snake_case` (e.g., `user_profiles`)

### 2. Database Access Layer (DAL)
- **No Raw SQL in Components**: All DB access must be encapsulated in `/services`.
- **Connection**: Use a singleton pattern in `lib/db/client.ts` to prevent too many SQLite connections.
- **Migrations**: Never alter the DB schema manually. Add a new `.sql` file to `lib/db/migrations/` and run the migrate script.
- **Type Safety**: Use Zod or a lightweight wrapper to validate DB rows before returning them to the UI.

### 3. Next.js 15 Patterns
- **Server Components by Default**: Use `async` components for data fetching.
- **Client Components**: Use `'use client'` only for interactivity or browser-specific APIs.
- **Data Fetching**: Prefer Server Actions over API routes for mutations.
- **Suspense**: Wrap slow-loading components in ` <Suspense> ` with a dedicated `loading.tsx` or skeleton.

## 🚫 Anti-Patterns (Do NOT do this)
- **❌ Direct DB calls in `page.tsx`**: Move them to a service file.
- **❌ `any` type**: Use `unknown` or define a proper interface.
- **❌ In-line styles**: Always use Tailwind classes.
- **❌ Blocking the main thread**: Use `await` for DB calls; avoid synchronous loops for large datasets.
- **❌ Hardcoded Secrets**: Use `.env.local` and access via `process.env`.

## 📝 Migration Example
When adding a column:
1. Create `lib/db/migrations/20260901_add_phone_to_users.sql`.
2. Write `ALTER TABLE users ADD COLUMN phone TEXT;`.
3. Run `npm run migrate`.
