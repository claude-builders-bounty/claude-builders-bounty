# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

> **Opinionated, production-ready project guide** for AI coding agents (Claude, Cursor, Copilot, etc.)
> 
> Use this file as the single source of truth for project structure, conventions, and anti-patterns.
>
> **Every rule has a reason.** If you don't know why, ask.

---

## 🎯 Project Overview

**Tech Stack:**
- **Framework:** Next.js 15 (App Router)
- **Database:** SQLite (better-sqlite3 for dev, Turso for prod)
- **ORM:** Drizzle ORM
- **Auth:** Better Auth (or Clerk for SaaS)
- **Styling:** Tailwind CSS 4
- **Payments:** Stripe
- **Deployment:** Vercel

**Why this stack?**
- Next.js 15 App Router = modern, performant, great DX
- SQLite = zero-config, fast, serverless-ready (via Turso)
- Drizzle = type-safe, lightweight, no magic
- Better Auth = open-source, self-hosted, customizable
- Tailwind = utility-first, rapid UI development
- Stripe = industry standard for SaaS payments

---

## 📁 Project Structure

```
my-saas/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Auth routes (login, register, forgot-password)
│   │   ├── (dashboard)/       # Protected dashboard routes
│   │   ├── api/               # API routes (Route Handlers)
│   │   │   ├── auth/          # Auth endpoints (Better Auth)
│   │   │   ├── stripe/        # Stripe webhooks
│   │   │   └── trpc/          # tRPC router (optional)
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx          # Landing page
│   ├── components/            # Reusable UI components
│   │   ├── ui/               # Base UI components (Button, Input, Modal)
│   │   ├── forms/            # Form components (LoginForm, RegisterForm)
│   │   └── layout/           # Layout components (Header, Sidebar, Footer)
│   ├── lib/                  # Utility functions, helpers
│   │   ├── auth/             # Auth helpers (Better Auth config)
│   │   ├── db/              # Database connection, schema
│   │   ├── stripe/          # Stripe helpers (checkout, webhooks)
│   │   └── utils/           # General utilities (formatDate, cn, etc.)
│   ├── hooks/                # Custom React hooks
│   ├── types/                # TypeScript type definitions
│   └── middleware.ts         # Middleware (auth, redirects)
├── drizzle/                  # Drizzle ORM
│   ├── schema.ts            # Database schema
│   ├── migrations/          # Migration files
│   └── seed.ts             # Seed data
├── public/                   # Static assets (images, fonts, favicon)
├── tests/                    # Test files (Vitest + Playwright)
├── .env                      # Environment variables (local, gitignored)
├── .env.example              # Example env file (committed)
├── drizzle.config.ts         # Drizzle configuration
├── next.config.ts            # Next.js configuration
├── tailwind.config.ts        # Tailwind configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Dependencies, scripts
```

**Why this structure?**
- `(auth)/` and `(dashboard)/` = route groups (Next.js App Router) → logical separation without affecting URLs
- `src/lib/` = all business logic separated from UI → testable, reusable
- `drizzle/` = separate folder for DB stuff → clean separation of concerns
- `tests/` = co-located with source → easy to find and maintain

---

## 🔧 Development Commands

```bash
# Install dependencies
npm install

# Run dev server (Turbo mode)
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Database commands (Drizzle)
npm run db:generate    # Generate migrations
npm run db:push         # Push schema to DB (no migrations)
npm run db:migrate      # Run migrations
npm run db:studio       # Open Drizzle Studio (GUI)

# Lint & Format
npm run lint
npm run lint:fix
npm run format
npm run format:check

# Tests
npm run test             # Unit tests (Vitest)
npm run test:e2e         # E2E tests (Playwright)
npm run test:coverage    # Coverage report

# Type checking
npm run type-check
```

**Why these commands?**
- `npm run dev` uses Turbo → faster HMR, better caching
- `db:push` for rapid prototyping, `db:migrate` for production → safety
- `test:e2e` uses Playwright → real browser testing
- `type-check` separate from build → catch type errors early

---

## 📝 Coding Conventions

### 1. File Naming
- **Components:** PascalCase (`Button.tsx`, `LoginForm.tsx`)
- **Utilities:** camelCase (`formatDate.ts`, `cn.ts`)
- **Database schema:** snake_case (`users_table.ts`, `posts_table.ts`)
- **Constants:** UPPER_SNAKE_CASE (`MAX_FILE_SIZE`, `API_TIMEOUT`)

**Why?**
- React ecosystem expects PascalCase for components
- Database conventions use snake_case (SQL standard)
- Consistency → readable codebase

### 2. Component Structure
```tsx
// ✅ GOOD: Server Component by default
// src/app/(dashboard)/page.tsx
export default async function DashboardPage() {
  const user = await getCurrentUser();
  
  return (
    <main>
      <h1>Welcome, {user.name}</h1>
    </main>
  );
}

// ✅ GOOD: Client Component only when needed
// src/components/ui/button.tsx
'use client';

import { useState } from 'react';

export function Button({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(false);
  // ...
}
```

**Why?**
- Server Components = zero client JS → faster page load
- Client Components only when you need interactivity (useState, useEffect, event handlers)
- **Anti-pattern:** Adding `'use client'` to every component → defeats the purpose

### 3. Database Schema (Drizzle)
```ts
// ✅ GOOD: Explicit column types, indexes, relations
// drizzle/schema.ts
import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';
import { relations } from 'drizzle-orm';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().defaultNow(),
}, (table) => ({
  emailIdx: index('email_idx').on(table.email),
}));

export const posts = sqliteTable('posts', {
  id: text('id').primaryKey(),
  title: text('title').notNull(),
  content: text('content').notNull(),
  authorId: text('author_id').notNull().references(() => users.id),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().defaultNow(),
});

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
}));
```

**Why?**
- `text('id')` instead of `integer` → UUIDs (avoid sequential IDs, more secure)
- Indexes on foreign keys (`authorId`) → faster joins
- Explicit relations → type-safe queries with Drizzle
- **Anti-pattern:** Using `json` column for relational data → use proper relations

### 4. API Routes (Route Handlers)
```ts
// ✅ GOOD: Explicit HTTP methods, validation, error handling
// src/app/api/posts/route.ts
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { posts } from '@/drizzle/schema';
import { validatePost } from '@/lib/validations';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limit = searchParams.get('limit') || '10';
  
  const allPosts = await db.select().from(posts).limit(Number(limit));
  return NextResponse.json(allPosts);
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const validated = validatePost(body);
    
    const [newPost] = await db.insert(posts).values(validated).returning();
    return NextResponse.json(newPost, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: 'Invalid request body' },
      { status: 400 }
    );
  }
}
```

**Why?**
- Explicit `GET` / `POST` / `PUT` / `DELETE` → clear API contract
- Validation BEFORE DB operation → fail fast, avoid DB errors
- Error handling → return proper HTTP status codes
- **Anti-pattern:** Using `any` type for request body → type unsafe

### 5. Environment Variables
```ts
// ✅ GOOD: Validate env vars at startup
// src/lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  BETTER_AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
});

export const env = envSchema.parse(process.env);

// ❌ BAD: Using process.env directly without validation
// const dbUrl = process.env.DATABASE_URL; // Might be undefined!
```

**Why?**
- Zod validation → fail fast if env vars are missing/invalid
- Type-safe `env` object → no `any` types
- **Anti-pattern:** Hardcoding secrets in code → use env vars

---

## 🚫 Anti-Patterns to Avoid

### 1. **Don't use `any` type**
```ts
// ❌ BAD
function handleData(data: any) {
  // ...
}

// ✅ GOOD
interface UserData {
  id: string;
  email: string;
  name: string;
}

function handleData(data: UserData) {
  // ...
}
```

**Why?** `any` defeats TypeScript's purpose → use `unknown` if you really don't know.

### 2. **Don't fetch data in Client Components unnecessarily**
```tsx
// ❌ BAD: Fetching in Client Component (waterfall, slow)
'use client';
import { useEffect, useState } from 'react';

export function Posts() {
  const [posts, setPosts] = useState([]);
  
  useEffect(() => {
    fetch('/api/posts').then(res => res.json()).then(setPosts);
  }, []);
  
  return // ...
}

// ✅ GOOD: Fetch in Server Component (parallel, fast)
export default async function PostsPage() {
  const posts = await db.select().from(postsTable);
  return // ...
}
```

**Why?** Server Components = fetch data on server → no waterfall, no loading states.

### 3. **Don't use `console.log` in production**
```ts
// ❌ BAD
console.log('User:', user);

// ✅ GOOD: Use structured logging
import { logger } from '@/lib/logger';

logger.info('User logged in', { userId: user.id });
```

**Why?** `console.log` = unstructured, hard to search. Use a logger (Pino, Winston) → structured logs, log levels.

### 4. **Don't commit secrets (.env, API keys)**
```bash
# ✅ GOOD: .gitignore includes .env
echo ".env" >> .gitignore

# ❌ BAD: Committing .env
git add .env  # NEVER DO THIS
```

**Why?** Secrets in git history = security risk. Use `.env.example` for documentation.

### 5. **Don't skip database migrations in production**
```bash
# ❌ BAD: Using `db:push` in production
npm run db:push  # DESTROYS data!

# ✅ GOOD: Using `db:migrate` in production
npm run db:migrate  # Safe, incremental
```

**Why?** `db:push` = force sync schema (drops columns!). `db:migrate` = incremental, safe.

---

## ✅ Best Practices to Follow

### 1. **Use Server Actions for mutations**
```tsx
// ✅ GOOD: Server Action for form submission
// src/app/(dashboard)/posts/new/page.tsx
import { createPost } from '@/lib/actions';

export default function NewPostPage() {
  return (
    <form action={createPost}>
      <input name="title" />
      <textarea name="content" />
      <button type="submit">Create Post</button>
    </form>
  );
}

// src/lib/actions.ts
'use server';

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string;
  const content = formData.get('content') as string;
  
  await db.insert(posts).values({ title, content });
  redirect('/dashboard/posts');
}
```

**Why?** Server Actions = no API route needed, type-safe, handles redirects.

### 2. **Use optimistic updates for better UX**
```tsx
// ✅ GOOD: Optimistic update with useOptimistic
'use client';

import { useOptimistic } from 'react';

export function LikeButton({ postId, initialLikes }: { postId: string; initialLikes: number }) {
  const [optimisticLikes, addOptimisticLike] = useOptimistic(
    initialLikes,
    (state) => state + 1
  );
  
  async function handleLike() {
    addOptimisticLike(); // Immediately update UI
    await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
  }
  
  return <button onClick={handleLike}>Like ({optimisticLikes})</button>;
}
```

**Why?** Optimistic updates = instant feedback, better UX.

### 3. **Use Suspense for streaming**
```tsx
// ✅ GOOD: Streaming with Suspense
// src/app/(dashboard)/page.tsx
import { Suspense } from 'react';
import { PostsList } from '@/components/PostsList';
import { PostsSkeleton } from '@/components/PostsSkeleton';

export default function DashboardPage() {
  return (
    <main>
      <h1>Dashboard</h1>
      <Suspense fallback={<PostsSkeleton />}>
        <PostsList />
      </Suspense>
    </main>
  );
}
```

**Why?** Suspense = stream parts of the page → faster first paint.

### 4. **Use middleware for auth checks**
```ts
// ✅ GOOD: Middleware for protected routes
// src/middleware.ts
import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth';

export async function middleware(request: Request) {
  const session = await auth.getSession();
  
  if (!session && request.url.includes('/(dashboard)')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
}

export const config = {
  matcher: ['/(dashboard)/:path*'],
};
```

**Why?** Middleware = centralized auth checks, no repeated logic.

---

## 🐛 Debugging Tips

1. **Use Next.js DevTools** (Chrome extension) → inspect Server Components, Route Handlers
2. **Enable Drizzle logging** → see generated SQL queries
   ```ts
   // drizzle.config.ts
   export default {
     dbCredentials: {
       log: true, // Enable logging
     },
   };
   ```
3. **Use `console.time` for performance profiling**
   ```ts
   console.time('fetchPosts');
   const posts = await db.select().from(posts);
   console.timeEnd('fetchPosts'); // Prints: fetchPosts: 12ms
   ```
4. **Check Next.js build output** → identify large bundles, slow pages

---

## 📦 Deployment (Vercel)

1. **Connect GitHub repo to Vercel**
2. **Set environment variables** (DATABASE_URL, BETTER_AUTH_SECRET, STRIPE_SECRET_KEY)
3. **Configure build command:** `npm run build`
4. **Configure start command:** `npm run start`
5. **Enable Preview Deployments** → test PRs before merging

**Why Vercel?**
- Zero-config deployment for Next.js
- Preview deployments → test before production
- Edge functions → fast global delivery

---

## 🧪 Testing Strategy

```
tests/
├── unit/                 # Unit tests (Vitest)
│   ├── lib/              # Test utility functions
│   └── components/       # Test React components
├── integration/          # Integration tests (Vitest)
│   ├── api/             # Test API routes
│   └── db/              # Test database queries
└── e2e/                 # E2E tests (Playwright)
    ├── auth.spec.ts      # Test login, register
    └── posts.spec.ts     # Test creating posts
```

**Why this strategy?**
- Unit tests = fast, isolated, test business logic
- Integration tests = test API routes, DB queries
- E2E tests = test full user flows (login, create post)

---

## 📚 References

- [Next.js 15 Docs](https://nextjs.org/docs)
- [Drizzle ORM Docs](https://orm.drizzle.team/)
- [Better Auth Docs](https://www.better-auth.com/)
- [Tailwind CSS 4 Docs](https://tailwindcss.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)

---

## 🎯 Quick Start (Greenfield Project)

```bash
# 1. Create Next.js app
npx create-next-app@latest my-saas --app --typescript --tailwind --eslint

# 2. Install dependencies
cd my-saas
npm install better-sqlite3 drizzle-orm drizzle-kit zod better-auth stripe

# 3. Initialize Drizzle
npx drizzle-kit init

# 4. Set up database
npm run db:push

# 5. Start dev server
npm run dev

# 6. Open http://localhost:3000
```

---

**Every rule in this file has a reason. If you don't know why, ASK.**

**Happy coding! 🚀**
