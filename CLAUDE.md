# Project Guidelines & Context: Next.js 15 + SQLite SaaS Starter

This repository is an opinionated, production-ready SaaS template built with Next.js 15 App Router, Tailwind CSS, TypeScript, and SQLite (better-sqlite3 / Turso).

---

## 🛠️ Tech Stack & Key Architecture
- **Framework:** Next.js 15 (App Router, Server Actions, React Server Components)
- **Language:** TypeScript (Strict Mode)
- **Styling:** Tailwind CSS + `shadcn/ui` (Radix UI primitives)
- **Database:** SQLite (Local `better-sqlite3` in WAL mode / Remote Turso via `@libsql/client`)
- **ORM / Query Builder:** Drizzle ORM (or Prisma/Kysely with SQLite driver)
- **Auth:** NextAuth.js v5 / Clerk
- **Payments:** Stripe / Lemon Squeezy

---

## 🚀 Common Commands

### Development
```bash
npm run dev              # Start development server on http://localhost:3000
npm run build            # Production build
npm run start            # Start production build server
npm run lint             # Run ESLint check
npm run type-check       # Validate TypeScript types without emitting code
```

### Database Management (Drizzle ORM Example)
```bash
npm run db:generate      # Generate Drizzle migration files based on schema changes
npm run db:push          # Push schema changes directly to SQLite database
npm run db:studio        # Open Drizzle Studio to view database GUI
npm run db:seed          # Seed the database with mock/default data
```

### Testing
```bash
npm run test             # Run unit/integration tests (Vitest / Jest)
npm run test:e2e         # Run end-to-end tests (Playwright / Cypress)
```

---

## 📐 Code Architecture & Conventions

### 1. App Router Structure (`app/`)
- **Server Components by Default:** Keep all components as Server Components (`RSC`). Add `'use client';` only at the top of small interactive leaf components (e.g., buttons, modals, forms).
- **Directory Layout:**
  - `app/(auth)/` - Auth routes (login, register, reset-password)
  - `app/(dashboard)/` - Protected SaaS dashboard routes
  - `app/api/` - REST endpoints / Webhook handlers (Stripe, external integrations)
  - `app/actions/` - Next.js Server Actions for mutations
  - `components/ui/` - Reusable primitives (`shadcn/ui`)
  - `components/` - Feature-specific domain components
  - `lib/db/` - Database client, Drizzle schema, and seed scripts
  - `lib/` - Shared utilities, auth options, stripe client

### 2. Server Actions vs API Routes
- Use **Server Actions** (`app/actions/*`) for all internal UI form submissions and data mutations.
- Use **API Routes** (`app/api/*`) exclusively for third-party webhooks (e.g., Stripe) or public REST APIs.
- Always validate incoming Server Action payload using `zod` schemas before querying the database.

### 3. Database Rules (SQLite Specific)
- **Concurrency & Locking:** SQLite allows single-writer at a time. Ensure connection instances are reused (singleton pattern) and SQLite is configured in **WAL (Write-Ahead Logging)** mode for local dev.
- **Transactions:** Wrap multi-table operations inside `db.transaction()` blocks to enforce ACID safety.
- **Foreign Keys:** Explicitly enable foreign key constraints (`PRAGMA foreign_keys = ON;`) on local SQLite startup.
- **Field Types:** Store dates as ISO strings or Unix timestamps (`integer`). Store IDs as UUIDv4 or `cuid2` strings.

### 4. Error Handling & Response Patterns
- Return standard typed response objects from Server Actions:
  ```ts
  type ActionResponse<T> = 
    | { success: true; data: T } 
    | { success: false; error: string; details?: Record<string, string[]> };
  ```
- Catch global route errors using Next.js error boundary pages (`error.tsx`, `not-found.tsx`).

---

## 🔒 Security & Environment Variables
- Never commit `.env` or `.env.local`. Always update `.env.example` when adding new variables.
- Required environment variables:
  - `DATABASE_URL` (file path `file:local.db` or Turso URL `libsql://...`)
  - `DATABASE_AUTH_TOKEN` (for Turso cloud execution)
  - `NEXTAUTH_SECRET` / `AUTH_SECRET`
  - `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET`

---

## 📝 Git Workflow Instructions for Claude
1. Always run `npm run type-check` and `npm run lint` before suggesting or committing code changes.
2. Keep component files under 150 lines. Split logical sub-sections into modular components.
3. Use precise Tailwind CSS utility classes without arbitrary values where design system tokens exist.
