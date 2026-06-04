# CLAUDE.md — Next.js + SQLite SaaS Project

## Project Overview

A modern Software-as-a-Service application built with Next.js 15 (App Router) and SQLite, featuring user authentication, subscription billing, and real-time data processing.

**Architecture:** Monorepo with Next.js frontend + API routes, SQLite database, background job processor.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5.x (strict mode) |
| UI | React 19 + Tailwind CSS 4 + shadcn/ui |
| Database | SQLite via Turso/LibSQL |
| ORM | Drizzle ORM |
| Auth | NextAuth.js v5 (Auth.js) |
| Payments | Stripe |
| Background Jobs | Inngest / BullMQ |
| Email | Resend / SendGrid |
| Hosting | Vercel (recommended) / Docker |

---

## Development Commands

```bash
# Development
npm run dev              # Start dev server (localhost:3000)
npm run dev:db           # Start local SQLite with Turso

# Database
npm run db:push          # Push schema changes to SQLite
npm run db:generate      # Generate Drizzle migrations
npm run db:migrate       # Run pending migrations
npm run db:seed          # Seed development data
npm run db:studio        # Open Drizzle Studio (GUI)

# Build & Test
npm run build            # Production build
npm run start            # Start production server
npm run lint             # Run ESLint
npm run format           # Run Prettier
npm run type-check       # Run tsc --noEmit
npm test                 # Run vitest
npm run test:e2e         # Run Playwright E2E tests
npm run test:db          # Run database integration tests

# Code Quality
npm run check            # lint + type-check + test (pre-commit)
```

---

## Project Structure

```
├── src/
│   ├── app/                 # Next.js App Router pages & API routes
│   │   ├── (auth)/          # Authentication routes (login, register)
│   │   ├── (dashboard)/     # Authenticated dashboard routes
│   │   ├── api/             # API route handlers
│   │   └── layout.tsx       # Root layout with providers
│   ├── components/          # Shared React components
│   │   ├── ui/              # shadcn/ui primitives
│   │   └── forms/           # Form components (react-hook-form)
│   ├── db/                  # Database layer
│   │   ├── schema/          # Drizzle schema definitions
│   │   ├── queries/         # Reusable database queries
│   │   └── migrations/      # Generated migrations
│   ├── lib/                 # Utility functions & shared logic
│   │   ├── auth.ts          # Auth.js configuration
│   │   ├── stripe.ts        # Stripe client & webhooks
│   │   ├── email.ts         # Email service
│   │   └── utils.ts         # General utilities
│   ├── hooks/               # React hooks
│   ├── actions/             # Server Actions
│   └── styles/              # Global styles
├── public/                  # Static assets
├── drizzle.config.ts        # Drizzle ORM configuration
├── next.config.ts           # Next.js configuration
├── tailwind.config.ts       # Tailwind CSS configuration
└── tsconfig.json            # TypeScript configuration
```

---

## Coding Conventions

### TypeScript
- **Strict mode** enabled — no `any` (use `unknown` and narrow)
- Prefer `interface` over `type` for public APIs
- Use `type` for unions, intersections, and mapped types
- Named exports only (no default exports except pages/layouts)
- Use `satisfies` keyword for type validation

### React / Next.js
- Server Components by default — add `"use client"` only when needed
- Server Actions for form submissions (`"use server"`)
- Use `loading.tsx` and `error.tsx` for each route segment
- Route handlers return `NextResponse` with proper status codes
- Use `generateMetadata` for all pages

### Database (Drizzle + SQLite)
- Always use prepared statements (never raw string interpolation)
- Use transactions for multi-step operations
- Index foreign keys and frequently queried columns
- Use `datetime('now')` for timestamps
- Soft deletes with `deletedAt` column when applicable

### API Routes
- RESTful conventions: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
- All routes validate input with Zod schemas
- Return consistent error shape: `{ error: string, code: string }`
- Authenticated routes check session at the top

### CSS / Styling
- Tailwind utility classes preferred over custom CSS
- Custom CSS only in `styles/` directory for complex animations
- Use CSS Modules for component-scoped styles when needed
- Follow shadcn/ui theming conventions

---

## Database Patterns

### Schema Example
```typescript
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  subscriptionId: text("subscription_id"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$onUpdateFn(() => new Date()),
});
```

### Query Example
```typescript
import { eq } from "drizzle-orm";
import { db } from "@/db";
import { users } from "@/db/schema";

export async function getUserByEmail(email: string) {
  return db.query.users.findFirst({
    where: eq(users.email, email),
    with: { subscriptions: true },
  });
}
```

---

## Authentication Flow

1. **Login:** NextAuth.js credentials/provider → JWT session
2. **Session check:** `auth()` helper in server components / `useSession()` in client
3. **Protected routes:** Middleware checks `/dashboard/*` routes
4. **Webhooks:** Stripe webhook updates subscription status
5. **Rate limiting:** Upstash Redis for API rate limiting

### Auth Helper
```typescript
// src/lib/auth.ts
import NextAuth from "next-auth";
import { DrizzleAdapter } from "@auth/drizzle-adapter";
import { db } from "@/db";

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: DrizzleAdapter(db),
  providers: [/* ... */],
  callbacks: {
    session: ({ session, user }) => ({
      ...session,
      user: { ...session.user, id: user.id },
    }),
  },
});
```

---

## Testing Strategy

| Type | Tool | Location | Coverage |
|------|------|----------|----------|
| Unit | Vitest | `__tests__/unit/` | Utilities, hooks, helpers |
| Integration | Vitest | `__tests__/integration/` | API routes, DB queries |
| E2E | Playwright | `e2e/` | Critical user flows |
| Component | Storybook | `*.stories.tsx` | UI component library |

### Testing Conventions
- Mock external services (Stripe, Resend, OAuth providers)
- Use test SQLite database (separate from dev/prod)
- Factory functions for test data generation
- Run full test suite before commits

---

## Deployment & Environment

### Environment Variables Required
```
DATABASE_URL=libsql://...
AUTH_SECRET=...
AUTH_GITHUB_ID=...
AUTH_GITHUB_SECRET=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
RESEND_API_KEY=...
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Deployment Checklist
1. [ ] Run `npm run build` — verify zero errors
2. [ ] Run `npm run check` — lint + types + tests pass
3. [ ] Run `npm run db:migrate` — migrations applied
4. [ ] Verify Stripe webhook endpoint is configured
5. [ ] Set all environment variables in production
6. [ ] Enable PostgreSQL-compatible mode if using Turso

---

## Common Tasks Reference

| Task | Command/Approach |
|------|-----------------|
| Add a new DB table | Create schema in `src/db/schema/`, run `db:generate` then `db:migrate` |
| Add a new API route | Create `src/app/api/route.ts` with Zod validation |
| Add a new page | Create `src/app/page.tsx` with metadata |
| Add a new form | Use `react-hook-form` + Zod + Server Action |
| Add background job | Define Inngest function in `src/inngest/` |
| Send email | Use Resend template in `src/lib/email.ts` |
| Query data | Use Drizzle ORM query builder in `src/db/queries/` |
| Add subscription tier | Update Stripe dashboard + DB schema + webhook handler |

---

## Security Checklist

- [ ] All API routes use input validation (Zod)
- [ ] SQL queries use prepared statements only
- [ ] Authentication required for all `/dashboard/*` routes
- [ ] CORS configured for API routes
- [ ] Rate limiting on auth endpoints
- [ ] Stripe webhook signature verification
- [ ] Content Security Policy headers set
- [ ] No secrets in client-side code (use environment variables)
- [ ] Regular dependency updates with Dependabot
- [ ] SQLite WAL mode enabled for concurrent access
