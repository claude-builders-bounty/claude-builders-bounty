# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> **Opinionated, production-ready CLAUDE.md** for a typical SaaS project built with Next.js 15, SQLite (better-sqlite3 / Drizzle ORM), and TypeScript.

---

## 🏗 Project Overview

- **Framework:** Next.js 15 (App Router)
- **Database:** SQLite via better-sqlite3 + Drizzle ORM
- **Language:** TypeScript (strict mode)
- **Auth:** NextAuth.js v5 / Lucia Auth
- **Styling:** Tailwind CSS v4
- **Package Manager:** pnpm or npm
- **Testing:** Vitest + Playwright

---

## 📁 Project Structure

```
.
├── src/
│   ├── app/                  # Next.js App Router pages & API routes
│   │   ├── (auth)/           # Auth-related routes (login, signup)
│   │   ├── (dashboard)/      # Authenticated app routes
│   │   ├── api/              # Route handlers (REST endpoints)
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Landing page
│   ├── components/           # Shared React components
│   │   ├── ui/               # Primitive UI components (Button, Input, etc.)
│   │   └── forms/            # Form components
│   ├── db/                   # Database schema & queries
│   │   ├── schema/           # Drizzle schema files
│   │   ├── migrations/       # Auto-generated SQL migrations
│   │   └── index.ts          # DB client & connection
│   ├── lib/                  # Utility functions & shared logic
│   │   ├── auth.ts           # Auth configuration
│   │   └── utils.ts          # Helper functions
│   ├── hooks/                # React hooks
│   └── styles/               # Global styles
├── drizzle.config.ts        # Drizzle configuration
├── next.config.ts           # Next.js configuration
├── tailwind.config.ts       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
└── vitest.config.ts         # Vitest configuration
```

---

## 🚀 Common Commands

```bash
# Development
pnpm dev              # Start dev server (localhost:3000)

# Database
pnpm db:generate      # Generate SQL migration from schema changes
pnpm db:migrate       # Run pending migrations
pnpm db:seed          # Seed the database with test data
pnpm db:studio        # Launch Drizzle Studio (GUI)

# Testing
pnpm test             # Run Vitest (unit)
pnpm test:e2e         # Run Playwright (E2E)
pnpm test:run         # Run all tests once (CI mode)

# Build & Deploy
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint check
pnpm format           # Prettier format
pnpm type-check       # tsc --noEmit

# CLI helpers
pnpm cli:seed-user    # Create a test user
pnpm cli:backup-db    # Backup SQLite database
pnpm cli:anonymize    # Anonymize production data for dev
```

---

## 🗄 Database Conventions

### Connection
- Database file: `./data/app.db` (gitignored)
- Connection via `src/db/index.ts` — single shared instance
- WAL mode enabled for performance

### Schema
- Files in `src/db/schema/` — one file per domain
- Use `drizzle-orm/sqlite-core` imports
- Timestamps via `sqlite` `text` type (ISO 8601)

```typescript
// Example: src/db/schema/users.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: text("created_at").notNull().default(sql`(datetime('now'))`),
  updatedAt: text("updated_at").notNull().default(sql`(datetime('now'))`),
});
```

### Migrations
- Never edit migration files manually
- Run `pnpm db:generate` → review → `pnpm db:migrate`
- Keep migration files in `src/db/migrations/`

### Seed Data
- Located in `src/db/seed.ts`
- Idempotent (safe to re-run)
- Creates default admin user + demo data

---

## 🧪 Testing

### Unit Tests (Vitest)
- Co-locate with source files: `component.test.tsx`
- Mock DB: use `better-sqlite3` with `:memory:` database
- Test DB setup:

```typescript
import { createTestDb } from "@/test-utils/db";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";

const db = createTestDb(":memory:");
migrate(db, { migrationsFolder: "src/db/migrations" });
```

### E2E Tests (Playwright)
- Config in `playwright.config.ts`
- Test files in `e2e/` directory
- Run against dev server (`pnpm dev`)
- Use `@playwright/test` assertions

---

## 🔐 Auth Patterns

### Route Protection
```typescript
// src/app/(dashboard)/layout.tsx
export default async function DashboardLayout({
  children,
}: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/login");
  return <>{children}</>;
}
```

### API Route Protection
```typescript
// src/app/api/protected/route.ts
import { auth } from "@/lib/auth";

export async function GET() {
  const session = await auth();
  if (!session) return new Response("Unauthorized", { status: 401 });
  // ...
}
```

---

## 📡 API Routes

- All API routes in `src/app/api/`
- Route handler pattern: `export async function GET/POST/PUT/DELETE`
- Validate request body with `zod` before processing
- Return `NextResponse.json(data)` or `NextResponse.json({ error }, { status })`
- Rate limiting via `@upstash/ratelimit` for external endpoints
- Error boundary: wrap handlers in `try/catch` with `500` fallback

---

## 🎨 UI & Styling

- **Tailwind CSS v4**: utility-first, use `@apply` only in `components/ui/`
- **shadcn/ui**: copy-paste component model (no dependency)
- **Dark mode**: `next-themes` with class-based toggle
- **Responsive**: mobile-first breakpoints (`sm:`, `md:`, `lg:`, `xl:`)

---

## 🔄 Data Flow

1. **Server Components**: Fetch data directly in the component (async)
   ```typescript
   const users = await db.select().from(usersSchema).all();
   ```
2. **Client Components**: Use server actions or route handlers
3. **Server Actions**: `"use server"` in form actions
4. **Forms**: React Hook Form + Zod validation
5. **State Management**: URL search params > React context > Zustand

---

## 🛡️ Error Handling

- **Server Components**: `error.tsx` boundary per route segment
- **Client Components**: `ErrorBoundary` wrapper
- **API Routes**: try/catch → structured error response
- **Validation**: Zod schema → typed errors
- **Database**: Wrap queries in try/catch, log to `console.error`
- **404**: `not-found.tsx` per segment

---

## 🧰 Code Quality

- **TypeScript**: strict mode, no `any` (use `unknown` + type guards)
- **ESLint**: flat config, extends `next/core-web-vitals`
- **Prettier**: `--tab-width 2 --semi true --single-quote false`
- **Import order**: React/Next → external → internal → relative
- **File naming**: `kebab-case.ts` for utils, `PascalCase.tsx` for components

---

## 📦 Dependencies (Key)

| Package | Purpose |
|---------|---------|
| `next@15` | Framework |
| `drizzle-orm` + `better-sqlite3` | Database ORM |
| `drizzle-kit` | Migration tool |
| `@auth/core` + `next-auth` | Authentication |
| `tailwindcss@4` | Styling |
| `zod` | Validation |
| `react-hook-form` | Forms |
| `@radix-ui/*` | Accessible primitives |
| `vitest` + `@playwright/test` | Testing |

---

## 📄 License

MIT — template for the Claude Builder community.
