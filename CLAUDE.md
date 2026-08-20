# Next.js 15 + SQLite SaaS Guidelines

This project is a modern, high-performance SaaS application built with **Next.js 15 (App Router)**, **React 19**, **TypeScript**, and **SQLite** (using `better-sqlite3` and `@libsql/client` / Turso).

---

## 🏛️ Architecture & Project Structure

```
├── src/
│   ├── app/                 # Next.js 15 App Router (Pages, Layouts, API Route Handlers)
│   │   ├── (auth)/          # Authentication routes group (login, register)
│   │   ├── (dashboard)/     # Authenticated SaaS dashboard routes
│   │   ├── api/             # REST & Webhook endpoints
│   │   ├── layout.tsx       # Root layout (Theme provider, fonts)
│   │   └── page.tsx         # Landing page
│   ├── components/          # Reusable UI components (shadcn/ui + Tailwind CSS)
│   │   ├── ui/              # Primitive design system components
│   │   └── dashboard/       # Feature-specific dashboard widgets
│   ├── db/                  # Database schema, connections, and migrations
│   │   ├── index.ts         # Singleton SQLite connection & client
│   │   ├── schema.ts        # Database schema definitions (Drizzle ORM / Kysely)
│   │   └── migrations/      # SQL migration scripts
│   ├── lib/                 # Core utilities, auth helpers, Stripe billing, API clients
│   │   ├── auth.ts          # Session management & user context
│   │   ├── stripe.ts        # Stripe billing & webhook listeners
│   │   └── utils.ts         # General formatting and class utilities
│   └── types/               # Global TypeScript definitions
├── public/                  # Static assets (images, icons, fonts)
├── .env.example             # Documented environment variables
├── next.config.ts           # Next.js configuration
├── package.json
└── tsconfig.json
```

---

## 🛠️ Development Conventions & Coding Standards

### 1. Server Components vs. Client Components
- **Default to React Server Components (RSC):** Fetch data directly on the server in `page.tsx` or `layout.tsx` without client-side `useEffect`.
- **Client Components (`'use client'`):** Reserve strictly for interactive elements (forms, modals, stateful toggles, real-time filters).

### 2. SQLite Database Best Practices
- **Singleton Database Instance:** Always import the shared database client from `@/db` to prevent connection leaks during Next.js hot-reloads.
- **WAL Mode Enabled:** Ensure Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) is enabled on SQLite initialization for concurrent read performance.
- **Prepared Statements:** Always use parameterized queries or type-safe query builders (Drizzle/Kysely) to prevent SQL injection vulnerabilities.
- **Safe Migrations:** Never execute raw destructive DDL (`DROP TABLE`, `ALTER TABLE ... DROP COLUMN`) without backward-compatible migrations.

### 3. Server Actions & Mutations
- Place data mutations in `src/actions/` or alongside route handlers using `'use server'`.
- Always validate inputs using **Zod** schemas before executing database mutations:
  ```typescript
  import { z } from "zod";

  export const updateUserSchema = z.object({
    name: z.string().min(2).max(50),
    email: z.string().email(),
  });
  ```
- Use `revalidatePath()` or `revalidateTag()` after successful mutations to purge stale Next.js cache.

### 4. Authentication & Protected Routes
- Authenticate requests in Next.js `middleware.ts` for protected dashboard routes (`/(dashboard)/*`).
- Check user permissions server-side on every Server Action and API Route handler.

### 5. Error Handling & UI Feedback
- Use Next.js error boundaries (`error.tsx`, `not-found.tsx`, `loading.tsx`) at appropriate route segments.
- Return structured error responses `{ success: false, error: string }` from Server Actions.

---

## ⚡ Common CLI Commands

```bash
# Development server
npm run dev

# Production build & lint
npm run build
npm run lint

# Database migrations
npm run db:generate
npm run db:migrate
npm run db:studio
```
