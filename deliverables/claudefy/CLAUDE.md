# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> Production-ready development guide for a typical SaaS project built with Next.js 15 (App Router) and SQLite (better-sqlite3 or Turso).

---

## Stack Overview

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| Runtime | Node.js 22+ (Edge or Node runtime) |
| Database | SQLite via `better-sqlite3` (self-hosted) or `@libsql/client` (Turso) |
| ORM | Drizzle ORM (recommended) or Prisma |
| Auth | NextAuth.js v5 (Auth.js) or Clerk |
| Styling | Tailwind CSS + shadcn/ui |
| Validation | Zod |
| State | React Server Components (default), Zustand (client) |
| Testing | Vitest + @testing-library/react |
| Linting | ESLint + Prettier |

---

## Project Structure

```
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/              # Protected dashboard routes
│   │   ├── layout.tsx            # Auth wrapper + sidebar
│   │   ├── page.tsx
│   │   └── settings/
│   ├── api/                      # API routes (if needed)
│   │   └── webhooks/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                       # shadcn/ui components
│   ├── forms/                    # Form components with Zod
│   └── dashboard/                # Dashboard-specific components
├── lib/
│   ├── db.ts                     # Database connection
│   ├── auth.ts                   # Auth configuration
│   ├── utils.ts                  # cn(), formatters, helpers
│   └── validations/              # Zod schemas
├── hooks/                        # Custom React hooks
├── types/                        # TypeScript definitions
├── drizzle/                      # Drizzle migrations (if using Drizzle)
├── public/
├── scripts/                      # DB seed, migration scripts
├── drizzle.config.ts             # Drizzle configuration
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

---

## Database

### Connection (better-sqlite3, self-hosted)

```typescript
// lib/db.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(process.env.DATABASE_URL ?? 'sqlite.db');
export const db = drizzle(sqlite, { schema });
```

### Connection (Turso, managed)

```typescript
// lib/db.ts
import { createClient } from '@libsql/client';
import { drizzle } from 'drizzle-orm/libsql';
import * as schema from './schema';

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN,
});
export const db = drizzle(client, { schema });
```

### Schema conventions

- Use **snake_case** for column names, **camelCase** for TypeScript
- Every table must have `id` (UUID or auto-increment), `createdAt`, `updatedAt`
- Soft deletes via `deletedAt` (never hard-delete user data)
- Foreign keys must be explicitly defined with `onDelete: 'cascade'` or `'set null'`

---

## Authentication

### NextAuth.js v5 (Auth.js)

```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { db } from './db';
import { users } from './schema';
import { compare } from 'bcryptjs';

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      async authorize(credentials) {
        const user = db.query.users.findFirst({
          where: (u, { eq }) => eq(u.email, credentials.email),
        });
        if (!user) return null;
        const valid = await compare(credentials.password, user.passwordHash);
        if (!valid) return null;
        return { id: user.id, email: user.email, name: user.name };
      },
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      if (token.sub) session.user.id = token.sub;
      return session;
    },
  },
});
```

### Protected routes

```typescript
// app/(dashboard)/layout.tsx
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function DashboardLayout({ children }) {
  const session = await auth();
  if (!session) redirect('/login');
  return <>{children}</>;
}
```

---

## API & Data Fetching

### Server Actions (preferred)

```typescript
// app/actions/create-project.ts
'use server';

import { auth } from '@/lib/auth';
import { db } from '@/lib/db';
import { projects } from '@/lib/schema';
import { createProjectSchema } from '@/lib/validations/project';

export async function createProject(data: unknown) {
  const session = await auth();
  if (!session) throw new Error('Unauthorized');

  const validated = createProjectSchema.parse(data);
  const project = await db.insert(projects).values({
    ...validated,
    userId: session.user.id,
  }).returning();

  return project[0];
}
```

### Client-side usage

```typescript
'use client';

import { createProject } from '@/app/actions/create-project';
import { useForm } from 'react-hook-form';

export function ProjectForm() {
  const onSubmit = async (data) => {
    const result = await createProject(data);
    // handle result
  };
}
```

---

## Styling & UI

### shadcn/ui conventions

- Install components individually: `npx shadcn@latest add button`
- Never modify core `components/ui/*` directly — extend via composition
- Use `className` prop for overrides, not CSS overrides
- Dark mode via `next-themes`, default to system preference

### Tailwind utility patterns

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

## Validation

### Zod schema structure

```typescript
// lib/validations/project.ts
import { z } from 'zod';

export const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  visibility: z.enum(['public', 'private']).default('private'),
});

export const updateProjectSchema = createProjectSchema.partial();
```

### Form integration

```typescript
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';

const form = useForm({
  resolver: zodResolver(createProjectSchema),
  defaultValues: { name: '', visibility: 'private' },
});
```

---

## Environment Variables

```env
# Database
DATABASE_URL=sqlite.db                    # better-sqlite3
# or
TURSO_DATABASE_URL=libsql://...
TURSO_AUTH_TOKEN=...

# Auth
NEXTAUTH_SECRET=...                       # openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000

# Optional
NODE_ENV=development
```

---

## Development Commands

```bash
# Install
npm install

# Dev server
npm run dev

# Database
npm run db:generate   # Generate migrations
npm run db:migrate    # Run migrations
npm run db:seed       # Seed test data

# Code quality
npm run lint
npm run format
npm run typecheck

# Testing
npm run test
npm run test:watch
```

---

## Deployment

### Self-hosted (VPS / Docker)

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/sqlite.db ./
RUN npm prune --production
EXPOSE 3000
CMD ["npm", "start"]
```

### Vercel (with Turso)

```bash
vercel --prod
```

- Set `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` in Vercel project settings
- `NEXTAUTH_SECRET` must be set in production

---

## Security Checklist

- [ ] `NEXTAUTH_SECRET` is a strong random value in production
- [ ] SQL injection prevented via parameterized queries (Drizzle handles this)
- [ ] Row-level security: every query filters by `userId` for user-owned data
- [ ] Rate limiting on auth endpoints (use `@upstash/ratelimit` or similar)
- [ ] CSP headers configured in `next.config.ts`
- [ ] Sensitive env vars never exposed to client (`NEXT_PUBLIC_*` prefix required)
- [ ] Password hashing with bcrypt (cost ≥ 12)
- [ ] Session timeout configured (default: 30 days)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `better-sqlite3` compilation fails | Install build tools: `npm install --include=dev`, ensure Python 3 |
| Drizzle migrations out of sync | Delete `drizzle/` folder and re-run `db:generate` |
| NextAuth session not persisting | Check `NEXTAUTH_SECRET` matches across all instances |
| Tailwind styles not applying | Clear `.next` cache: `rm -rf .next && npm run dev` |
| TypeScript errors in `app/` | Run `npm run typecheck`, check `paths` in `tsconfig.json` |

---

## Code Style

```typescript
// ✅ Good: typed, explicit, server component by default
export async function UserProfile({ userId }: { userId: string }) {
  const user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  if (!user) return <NotFound />;
  return <div>{user.name}</div>;
}

// ❌ Avoid: any, implicit returns, client components without "use client"
export function UserProfile({ userId }) {
  const user = await getUser(userId);
  return <div>{user.name}</div>;
}
```

---

*This guide is opinionated but adaptable. Adjust based on project requirements.*
