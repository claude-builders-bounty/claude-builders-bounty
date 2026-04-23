# SaaS Project - Next.js 15 + SQLite

> Production-ready template for Claude Code. Paste this into your project root and Claude will understand your conventions without asking clarifying questions.

---

## Stack & Versions

- **Next.js 15.1+** - App Router only (no Pages Router)
- **React 19** - Server Components by default, Client Components explicit
- **SQLite** - via `better-sqlite3` (local dev) or Turso (production)
- **TypeScript 5.7+** - Strict mode enabled
- **Tailwind CSS 4.0+** - For styling
- **Zod** - Runtime validation and type inference
- **Auth** - Clerk or NextAuth v5 (Auth.js)
- **Deployment** - Vercel (recommended) or Railway

---

## Folder Structure

```
app/
├── (auth)/              # Auth-protected routes group
│   ├── dashboard/
│   ├── settings/
│   └── layout.tsx       # Shared auth layout
├── (marketing)/         # Public routes group
│   ├── page.tsx         # Homepage
│   ├── pricing/
│   └── layout.tsx       # Marketing layout
├── api/                 # API routes
│   ├── webhooks/        # External webhooks (Stripe, Clerk)
│   └── trpc/            # tRPC routes (if using tRPC)
├── layout.tsx           # Root layout
└── globals.css          # Global styles

lib/
├── db/
│   ├── client.ts        # Database client initialization
│   ├── schema.ts        # Drizzle schema (if using Drizzle)
│   └── migrations/      # SQL migration files
├── actions/             # Server Actions (form submissions, mutations)
├── queries/             # Database queries (SELECT only)
├── validations/         # Zod schemas for validation
└── utils.ts             # Utility functions (cn, formatters, etc.)

components/
├── ui/                  # Shadcn/ui components (Button, Input, etc.)
├── forms/               # Form components (LoginForm, SettingsForm)
└── shared/              # Reusable components (Header, Footer)

public/
└── assets/              # Static assets (images, fonts)

migrations/              # SQL migration files (if not using ORM)
├── 001_init.sql
├── 002_add_users.sql
└── ...
```

### Why This Structure?

- **Route groups** `(auth)` and `(marketing)` keep URLs clean while organizing code
- **Separation of concerns**: queries (read) vs actions (write) prevents accidental mutations
- **Colocation**: components near their routes when single-use, shared when reused
- **Migrations at root**: visible, version-controlled, run before deploy

---

## Database: SQLite with better-sqlite3 / Turso

### Schema Conventions

1. **Table names**: `snake_case`, plural (`users`, `billing_subscriptions`)
2. **Primary keys**: Always `id INTEGER PRIMARY KEY` (SQLite auto-increment)
3. **Timestamps**: Every table has `created_at` and `updated_at` (ISO 8601 strings)
4. **Foreign keys**: `{table}_id` format (`user_id`, `organization_id`)
5. **Soft deletes**: Add `deleted_at TEXT` for recoverable records

Example:

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE posts (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  published_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_published_at ON posts(published_at) WHERE published_at IS NOT NULL;
```

### Migration Rules

1. **Never edit existing migrations** - Create a new migration to fix mistakes
2. **Numbering**: `001_description.sql`, `002_description.sql` (zero-padded, sequential)
3. **Idempotent**: Always use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
4. **Test rollback**: Every migration should have a corresponding `down.sql` (optional but recommended)
5. **Run before deploy**: Migrations run automatically in CI/CD before Next.js build

### Why SQLite?

- **Zero latency**: Database is local (better-sqlite3) or edge-replicated (Turso)
- **No connection pooling**: Eliminates Serverless cold-start issues
- **Cost-effective**: Turso free tier = 9GB, perfect for SaaS MVPs
- **Backup-friendly**: Single file, easy to snapshot

---

## Next.js 15 App Router Patterns

### Server Components (Default)

**Use for**: Data fetching, static content, layouts

```tsx
// app/dashboard/page.tsx
import { db } from '@/lib/db/client';
import { getUserProjects } from '@/lib/queries/projects';
import { auth } from '@clerk/nextjs/server';

export default async function DashboardPage() {
  const { userId } = await auth();
  if (!userId) redirect('/login');

  const projects = await getUserProjects(userId);

  return (
    <div>
      <h1>Your Projects</h1>
      {projects.map((p) => (
        <ProjectCard key={p.id} project={p} />
      ))}
    </div>
  );
}
```

**Why**: Zero JavaScript to client, faster page loads, better SEO

---

### Client Components (Explicit)

**Use for**: Interactivity (onClick, useState, useEffect, forms with real-time validation)

```tsx
// components/forms/create-project-form.tsx
'use client';

import { createProject } from '@/lib/actions/projects';
import { useActionState } from 'react';
import { Button } from '@/components/ui/button';

export function CreateProjectForm() {
  const [state, formAction, isPending] = useActionState(createProject, null);

  return (
    <form action={formAction}>
      <input name="name" required />
      {state?.error && <p className="text-red-500">{state.error}</p>}
      <Button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create Project'}
      </Button>
    </form>
  );
}
```

**Why**: `useActionState` handles pending states, optimistic updates, and progressive enhancement

---

### Server Actions (Mutations Only)

**Location**: `lib/actions/`

**Rules**:
- Always start with `'use server'` directive
- Validate input with Zod
- Return `{ success: boolean, error?: string, data?: T }`
- Handle auth in the action, not the caller

```tsx
// lib/actions/projects.ts
'use server';

import { db } from '@/lib/db/client';
import { auth } from '@clerk/nextjs/server';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
});

export async function createProject(prevState: unknown, formData: FormData) {
  const { userId } = await auth();
  if (!userId) {
    return { success: false, error: 'Unauthorized' };
  }

  const parsed = createProjectSchema.safeParse({
    name: formData.get('name'),
  });

  if (!parsed.success) {
    return { success: false, error: parsed.error.errors[0].message };
  }

  const stmt = db.prepare(
    'INSERT INTO projects (user_id, name) VALUES (?, ?)'
  );
  const result = stmt.run(userId, parsed.data.name);

  revalidatePath('/dashboard');
  return { success: true, data: { id: result.lastInsertRowid } };
}
```

**Why**: Type-safe, validates input, handles auth, revalidates cache automatically

---

### Database Queries (Read-Only)

**Location**: `lib/queries/`

**Rules**:
- Only `SELECT` statements
- Return typed objects (infer from Zod or manually type)
- Cache with `unstable_cache` for frequently-read data
- Never expose raw SQL to components

```tsx
// lib/queries/projects.ts
import { db } from '@/lib/db/client';
import { unstable_cache } from 'next/cache';

export const getUserProjects = unstable_cache(
  async (userId: string) => {
    const stmt = db.prepare(
      'SELECT id, name, created_at FROM projects WHERE user_id = ? ORDER BY created_at DESC'
    );
    return stmt.all(userId) as Array<{
      id: number;
      name: string;
      created_at: string;
    }>;
  },
  ['user-projects'],
  { revalidate: 60, tags: ['projects'] }
);
```

**Why**: Caching reduces database load, tags allow granular revalidation

---

## Component Patterns

### UI Components (Shadcn Style)

**Location**: `components/ui/`

**Rules**:
- Compound components for flexibility: `<Dialog><DialogTrigger /></Dialog>`
- Forward refs for composability
- Merge `className` with `cn()` utility for style overrides
- Export both component and prop types

```tsx
// components/ui/button.tsx
import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, forwardRef } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-md px-4 py-2',
          {
            'bg-primary text-white': variant === 'default',
            'bg-red-500 text-white': variant === 'destructive',
            'border border-input bg-background': variant === 'outline',
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';
```

**Why**: Flexible, composable, overridable

---

### Form Components

**Location**: `components/forms/`

**Rules**:
- One form = one file
- Use Server Actions for submission
- Show loading states with `isPending`
- Display validation errors inline

---

## Dev Commands

```bash
# Install dependencies
npm install

# Run dev server (http://localhost:3000)
npm run dev

# Run database migrations
npm run db:migrate

# Generate new migration
npm run db:migrate:new

# Open Drizzle Studio (if using Drizzle)
npm run db:studio

# Type check (no emit)
npm run type-check

# Lint
npm run lint

# Build for production
npm run build

# Start production server
npm start
```

---

## What We DON'T Do (And Why)

### ❌ No tRPC (unless API-heavy)

**Why**: Server Actions cover 90% of mutation use cases with less boilerplate. Use tRPC only if building a mobile app or external API.

---

### ❌ No Prisma (use Drizzle or raw SQL)

**Why**: Prisma generates 5MB+ of dependencies and doesn't support edge runtimes well. Drizzle is edge-native and 100x smaller. Raw SQL is even lighter.

---

### ❌ No Global State (Zustand, Redux)

**Why**: Server Components + URL state (searchParams) + React Context (when necessary) cover all use cases. Global client state causes hydration mismatches and cache invalidation headaches.

---

### ❌ No `useEffect` for Data Fetching

**Why**: Fetch in Server Components. `useEffect` causes waterfalls, flash of loading state, and hydration mismatches.

```tsx
// ❌ DON'T
'use client';
import { useEffect, useState } from 'react';

export function Projects() {
  const [projects, setProjects] = useState([]);
  useEffect(() => {
    fetch('/api/projects').then(r => r.json()).then(setProjects);
  }, []);
  return <div>{projects.map(...)}</div>;
}

// ✅ DO
import { getUserProjects } from '@/lib/queries/projects';

export async function Projects({ userId }: { userId: string }) {
  const projects = await getUserProjects(userId);
  return <div>{projects.map(...)}</div>;
}
```

---

### ❌ No API Routes for Internal Mutations

**Why**: Server Actions are simpler, type-safe, and avoid serialization overhead.

**Exception**: Use API routes for webhooks (Stripe, Clerk) and external integrations only.

---

### ❌ No Barrel Exports (`index.ts` re-exporting everything)

**Why**: Slows down bundler, makes tree-shaking harder, creates circular dependency risks. Import directly:

```tsx
// ❌ DON'T
import { Button, Input, Dialog } from '@/components/ui';

// ✅ DO
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';
```

---

## Testing Strategy

**Not included in this template** - Add when project matures:

- **Vitest** for unit tests (`lib/` functions)
- **Playwright** for E2E tests (critical user flows)
- Skip testing UI components (diminishing returns, high maintenance)

---

## Deployment Checklist

- [ ] Migrations run automatically in CI/CD (`npm run db:migrate` before `npm run build`)
- [ ] Environment variables set in Vercel/Railway
- [ ] Turso database created (if production)
- [ ] Webhook endpoints configured (Stripe, Clerk)
- [ ] Sentry or PostHog integrated for error tracking
- [ ] `robots.txt` and `sitemap.xml` configured
- [ ] OG images generated for key pages

---

**This template is opinionated by design.** If your project needs something different, fork this and adapt. The goal is zero back-and-forth with Claude — paste this in, start building.

✨ Built for the Claude Code community
