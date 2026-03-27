# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated project context for Claude Code. Version: 1.0.0
> Last updated: 2026-03-27

---

## 🎯 Project Overview

This is a **production SaaS application** built with:
- **Framework**: Next.js 15 with App Router
- **Database**: SQLite (better-sqlite3 or Turso)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS + shadcn/ui
- **Auth**: Clerk or NextAuth.js

**Architecture**: Monorepo-style with clear separation of concerns.

---

## 📁 Project Structure

```
/
├── app/                      # Next.js App Router
│   ├── (auth)/              # Auth-related pages (login, signup)
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/         # Protected dashboard pages
│   │   ├── layout.tsx       # Dashboard layout with sidebar
│   │   ├── page.tsx         # Dashboard home
│   │   └── settings/
│   ├── api/                 # API routes (REST endpoints)
│   │   ├── webhooks/        # Stripe, Clerk webhooks
│   │   └── trpc/            # tRPC routers (if using)
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Landing page
├── components/
│   ├── ui/                  # shadcn/ui components (auto-generated)
│   ├── features/            # Feature-specific components
│   └── layout/              # Layout components (Header, Sidebar, Footer)
├── lib/
│   ├── db/                  # Database layer
│   │   ├── schema.ts        # Drizzle schema definitions
│   │   ├── migrations/      # SQL migration files
│   │   └── index.ts         # DB connection
│   ├── auth.ts              # Auth configuration
│   ├── utils.ts             # Utility functions (cn, formatters)
│   └── constants.ts         # App constants
├── public/                  # Static assets
├── scripts/                 # Utility scripts (seed, migrate)
└── tests/                   # Test files ( Vitest or Jest)
```

---

## ⚙️ Tech Stack & Versions

| Technology | Version | Why |
|------------|---------|-----|
| Next.js | 15.x | App Router, Server Actions, latest features |
| React | 19.x | Concurrent features, improved performance |
| TypeScript | 5.x | Type safety, better DX |
| SQLite | better-sqlite3 11.x / Turso | Zero-config, serverless-friendly |
| Drizzle ORM | 0.30+ | Type-safe SQL, migrations |
| Tailwind CSS | 3.4+ | Utility-first styling |
| shadcn/ui | latest | Accessible, customizable components |
| Clerk / NextAuth | latest | Production-ready auth |

---

## 🗃️ Database & Migrations

### Schema Rules

1. **Always use Drizzle ORM** for schema definitions
2. **Snake_case for columns**, camelCase in TypeScript
3. **Timestamps**: `created_at`, `updated_at` (use `$timestamp()`)
4. **IDs**: Use `uuid` or `cuid2` (never auto-increment for public IDs)
5. **Soft deletes**: Add `deleted_at` column, never hard delete user data

### Migration Commands

```bash
# Generate migration from schema changes
npm run db:generate

# Apply migrations to database
npm run db:migrate

# Push schema directly (development only!)
npm run db:push

# Open Drizzle Studio (database GUI)
npm run db:studio

# Seed database with test data
npm run db:seed
```

### Migration Rules

- **Never edit existing migrations** after they're committed
- **Always test migrations** with `npm run db:migrate` before committing
- **Use transactions** for data migrations
- **Name migrations descriptively**: `add_user_preferences_table.sql`
- **Rollback scripts** for destructive changes (optional but recommended)

---

## 🎨 Component Patterns

### Server vs Client Components

```tsx
// ✅ Default to Server Components
// app/dashboard/page.tsx
import { getUser } from '@/lib/auth'
import { DashboardContent } from '@/components/features/dashboard-content'

export default async function DashboardPage() {
  const user = await getUser() // Server-side data fetching
  
  return <DashboardContent user={user} />
}

// ✅ Use 'use client' only when necessary
// components/features/dashboard-content.tsx
'use client'

import { useState } from 'react'

export function DashboardContent({ user }) {
  const [isOpen, setIsOpen] = useState(false) // Client-side state
  
  return <div>...</div>
}
```

### When to Use Client Components

- Event listeners (onClick, onChange, etc.)
- useState, useEffect, useRef
- Browser-only APIs (localStorage, window)
- Third-party libraries that need client-side

### Component Naming

- **Page components**: `page.tsx` (Next.js convention)
- **Layout components**: `layout.tsx`
- **Feature components**: PascalCase, descriptive (e.g., `UserProfile.tsx`)
- **UI components**: Follow shadcn/ui naming (e.g., `button.tsx`)

---

## 🔒 Security & Auth

### Authentication Flow

1. **Clerk**: Use middleware for route protection
2. **NextAuth**: Use `getServerSession` in Server Components

### Protected Routes

```typescript
// middleware.ts (Clerk example)
import { authMiddleware } from '@clerk/nextjs'

export default authMiddleware({
  publicRoutes: ['/', '/login', '/signup'],
  ignoredRoutes: ['/api/webhooks/(.*)'],
})

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
}
```

### Security Rules

- **Never expose sensitive data** in client components
- **Validate all inputs** with Zod schemas
- **Use environment variables** for secrets (never hardcode)
- **Rate limit API routes** (use Upstash or similar)
- **Sanitize user content** before rendering (React does this by default)

---

## 🚫 Anti-Patterns to Avoid

### 1. Don't Use `useEffect` for Data Fetching

```tsx
// ❌ Wrong - causes waterfalls, no caching
useEffect(() => {
  fetch('/api/data').then(data => setData(data))
}, [])

// ✅ Right - use Server Components or SWR/TanStack Query
const data = await db.query.posts.findMany() // Server Component
```

### 2. Don't Fetch Data in Layouts

```tsx
// ❌ Wrong - slows down entire layout subtree
export default async function Layout({ children }) {
  const user = await getUser() // Blocks every page!
  return <div>{children}</div>
}

// ✅ Right - fetch in individual pages or use React Cache
export default async function Page() {
  const user = await getUser() // Only blocks this page
  return <Dashboard user={user} />
}
```

### 3. Don't Mix Client and Server State

```tsx
// ❌ Wrong - duplicate state sources
// Server: user from DB
// Client: user from useState

// ✅ Right - single source of truth
// Server: fetch and pass as props
// Client: use for display, mutate via server actions
```

### 4. Don't Use `localStorage` Directly

```tsx
// ❌ Wrong - breaks SSR
const theme = localStorage.getItem('theme')

// ✅ Right - use with caution, check for window
const [theme, setTheme] = useState(() => {
  if (typeof window === 'undefined') return 'light'
  return localStorage.getItem('theme') || 'light'
})
```

### 5. Don't Create Massive Components

```tsx
// ❌ Wrong - 500+ line component
export default function Dashboard() {
  // 100 lines of state
  // 200 lines of effects
  // 200 lines of JSX
}

// ✅ Right - split into smaller components
export default function Dashboard() {
  return (
    <>
      <DashboardHeader />
      <DashboardStats />
      <DashboardChart />
      <DashboardTable />
    </>
  )
}
```

---

## ✅ Development Commands

```bash
# Development
npm run dev              # Start dev server (port 3000)
npm run dev:turbo        # Start with Turbopack (experimental)

# Database
npm run db:generate      # Generate migration from schema
npm run db:migrate       # Apply migrations
npm run db:push          # Push schema directly (dev only!)
npm run db:studio        # Open Drizzle Studio

# Build & Production
npm run build            # Build for production
npm run start            # Start production server
npm run lint             # Run ESLint
npm run type-check       # Run TypeScript check

# Testing
npm run test             # Run tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Run tests with coverage

# Utilities
npm run seed             # Seed database with test data
npm run clean            # Remove .next, node_modules
```

---

## 📝 Code Style & Conventions

### File Naming

- **Pages**: lowercase with dashes (e.g., `user-profile.tsx`)
- **Components**: PascalCase (e.g., `UserProfile.tsx`)
- **Utilities**: camelCase (e.g., `formatDate.ts`)
- **Types**: PascalCase with `.ts` extension (e.g., `types.ts`)

### Import Order

```typescript
// 1. React & Next.js
import { useState } from 'react'
import { useRouter } from 'next/navigation'

// 2. Third-party libraries
import { z } from 'zod'
import { format } from 'date-fns'

// 3. Internal imports (use @ alias)
import { Button } from '@/components/ui/button'
import { getUser } from '@/lib/auth'

// 4. Types
import type { User } from '@/lib/db/schema'
```

### TypeScript Rules

- **Always use strict mode** (enabled in `tsconfig.json`)
- **Prefer interfaces over types** for object shapes
- **Use `type` for unions, intersections, primitives**
- **Never use `any`** - use `unknown` and narrow types
- **Use const assertions** for immutable data

```typescript
// ✅ Good
interface User {
  id: string
  name: string
  email: string
}

type Status = 'active' | 'inactive' | 'pending'

const ROLES = ['admin', 'user', 'guest'] as const
```

---

## 🌍 Environment Variables

### Required Variables

```bash
# Database
DATABASE_URL="file:./dev.db"              # Local SQLite
# or
DATABASE_URL="libsql://your-db.turso.io"  # Turso

# Auth (Clerk)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_..."
CLERK_SECRET_KEY="sk_..."

# or Auth (NextAuth)
NEXTAUTH_SECRET="your-secret-here"
NEXTAUTH_URL="http://localhost:3000"

# Payments (Stripe)
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_..."

# Optional: Analytics
NEXT_PUBLIC_POSTHOG_KEY="..."
```

### Environment Rules

- **Never commit `.env` files** (already in `.gitignore`)
- **Use `.env.example`** as template
- **Prefix client-safe vars** with `NEXT_PUBLIC_`
- **Validate at startup** with Zod or similar

---

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Build Checklist

- [ ] All environment variables set
- [ ] Database migrations applied
- [ ] `npm run build` succeeds
- [ ] `npm run type-check` passes
- [ ] Tests passing

---

## 🧪 Testing Strategy

### Unit Tests

- Test utility functions in `lib/`
- Test data transformations
- Use Vitest or Jest

### Integration Tests

- Test API routes
- Test auth flows
- Use `next/test` for page tests

### E2E Tests

- Use Playwright for critical paths
- Test signup, login, checkout

---

## 📚 Resources

- [Next.js 15 Documentation](https://nextjs.org/docs)
- [Drizzle ORM Docs](https://orm.drizzle.team/docs/overview)
- [shadcn/ui Components](https://ui.shadcn.com)
- [Clerk Auth Docs](https://clerk.com/docs)
- [Turso Database](https://docs.turso.tech)

---

## 🔧 Common Tasks

### Add a New Page

```bash
# Create page file
touch app/(dashboard)/new-page/page.tsx

# Add to navigation (if needed)
# Edit components/layout/sidebar.tsx
```

### Add a New Database Table

```bash
# 1. Edit lib/db/schema.ts
# 2. Generate migration
npm run db:generate

# 3. Review and apply
npm run db:migrate
```

### Add a New API Route

```bash
# Create API route
touch app/api/resource/route.ts

# Follow REST conventions
# GET = read, POST = create, PUT = update, DELETE = delete
```

---

## 🎓 Philosophy

1. **Simplicity over complexity** - Don't over-engineer
2. **Type safety first** - Let TypeScript catch errors
3. **Server Components default** - Client only when needed
4. **Database as source of truth** - Use migrations, not ORMs
5. **Security by default** - Validate, sanitize, protect

---

**This CLAUDE.md is opinionated for a reason. Every rule exists to prevent common mistakes in Next.js + SQLite SaaS projects.**
