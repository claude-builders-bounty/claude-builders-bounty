# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

| Technology | Version | Why |
|---|---|---|
| **Next.js** | 15.x (App Router) | React Server Components by default, streaming, server actions |
| **React** | 19.x | Concurrent features, `use()` hook for async components |
| **TypeScript** | 5.x | Strict mode enabled — no `any` unless absolutely unavoidable |
| **Database** | SQLite via `better-sqlite3` | Zero ops, single-file, perfect for SaaS up to ~10M rows |
| **ORM** | Drizzle ORM | Type-safe, lightweight, SQL-like syntax, no magic |
| **Auth** | Lucia v3 | Framework-agnostic, session-based, no vendor lock-in |
| **UI** | shadcn/ui + Tailwind CSS 4 | Accessible, composable, tree-shakeable components |
| **Forms** | React Hook Form + Zod | Performant, type-safe validation, minimal re-renders |
| **Email** | Resend | Transactional emails via API, React Email templates |
| **Payments** | Stripe | Webhook-first, idempotent, test mode by default |
| **Runtime** | Node.js 22 LTS | Long-term support, native fetch, glob support |

> **Reason:** Every choice is the boring, proven, well-documented option. Avoid bleeding-edge or unmaintained libraries.

## Project Structure

```
├── src/
│   ├── app/                    # App Router pages & API routes
│   │   ├── (auth)/             # Auth group — login, signup, reset
│   │   ├── (dashboard)/        # Dashboard — requires auth
│   │   ├── api/                # Route handlers, webhooks
│   │   └── layout.tsx          # Root layout with providers
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── forms/              # Form components
│   │   └── layout/             # Navbar, Sidebar, Footer
│   ├── db/
│   │   ├── schema/             # Drizzle schema (one per domain)
│   │   ├── migrations/         # Auto-generated SQL (DO NOT EDIT)
│   │   ├── seed.ts             # Development seed data
│   │   └── index.ts            # DB client singleton
│   ├── lib/                    # Auth, Stripe, Email, Utils
│   ├── actions/                # Server Actions (one file per domain)
│   └── styles/globals.css      # Tailwind imports
├── drizzle.config.ts
└── tsconfig.json
```

> **Rule:** Keep files under 200 lines. Extract into `lib/` or `actions/` modules when exceeded.

## SQL & Migration Rules

- Every table must have `id` (text/CUID2), `createdAt`, `updatedAt` timestamps
- Use `text()` for IDs and ISO 8601 timestamps
- Use `integer({ mode: "boolean" })` for booleans
- Store currency in cents as `integer`
- Always use prepared statements (Drizzle) — never raw SQL with user input
- Never edit migration files manually — use `drizzle-kit generate`

```bash
pnpm db:generate   # Generate migration
pnpm db:migrate    # Apply migration
pnpm db:seed       # Seed dev data
```

## Component Patterns

- **Default to Server Components** — only add `"use client"` for browser APIs, state, or event handlers
- Fetch data in Server Components, pass down as props
- Use React.cache() for deduplication
- Never use useEffect for data fetching — use RSC or Server Actions

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Component files | kebab-case | `organization-list.tsx` |
| Server actions | kebab-case + `.actions` | `auth.actions.ts` |
| Functions | camelCase | `createOrganization()` |
| Types/Interfaces | PascalCase | `CreateOrgInput` |
| DB columns | snake_case | `created_at` |
| DB tables | snake_case, plural | `organizations` |
| Env vars | UPPER_SNAKE_CASE | `DATABASE_URL` |

## Security Must-Haves

1. All forms must use Server Actions — never expose raw API endpoints for mutations
2. Rate limit auth endpoints — 5 attempts per 15 min
3. Every Server Action must validate inputs with Zod
4. Rotate session ID on privilege escalation
5. Prevent SQL injection via Drizzle parameterized queries
6. Verify Stripe webhook signatures with idempotency keys

## What We Don't Do (And Why)

| Don't | Why |
|---|---|
| **Use Prisma** | Drizzle is lighter, faster, no binary deps |
| **Use Redux/Zustand** | RSC + URL state covers 95%; React Context for rest |
| **Write custom CSS** | Tailwind + shadcn/ui covers all needs |
| **Use getServerSideProps** | App Router — use RSC or Server Actions |
| **Store files in SQLite** | Use S3/R2 for file storage |
| **Add `"use client"` unnecessarily** | Increases bundle, disables RSC streaming |
