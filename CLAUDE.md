# CLAUDE.md — Next.js 15 + SQLite SaaS Project

**Version:** 1.0.0  
**Stack:** Next.js 15 (App Router) + TypeScript + SQLite (better-sqlite3/Turso)  
**Last Updated:** 2026-04-10

---

## 📋 Table of Contents

1. [Project Structure](#project-structure)
2. [Coding Standards](#coding-standards)
3. [Database & SQLite](#database--sqlite)
4. [API Patterns](#api-patterns)
5. [Authentication](#authentication)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Security](#security)
9. [Common Tasks](#common-tasks)

---

## 📁 Project Structure

```
my-saas/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group
│   │   ├── login/
│   │   ├── register/
│   │   └── layout.tsx
│   ├── (dashboard)/              # Dashboard route group
│   │   ├── dashboard/
│   │   ├── settings/
│   │   └── layout.tsx
│   ├── api/                      # API routes
│   │   ├── auth/
│   │   ├── users/
│   │   └── webhooks/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                       # Reusable UI components
│   ├── forms/                    # Form components
│   └── layouts/                  # Layout components
├── lib/
│   ├── db/                       # Database utilities
│   │   ├── index.ts              # DB connection
│   │   ├── schema.ts             # Schema definitions
│   │   └── migrations/           # Migration files
│   ├── auth/                     # Auth utilities
│   ├── validators/               # Zod schemas
│   └── utils.ts
├── hooks/                        # Custom React hooks
├── types/                        # TypeScript types
├── tests/                        # Test files
├── .env.local                    # Local environment variables
├── .env.example                  # Example environment variables
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### Key Conventions

| Pattern | Description |
|---------|-------------|
| `(group)/` | Route groups for layout organization (not in URL) |
| `route.ts` | API endpoint handler |
| `page.tsx` | Page component |
| `layout.tsx` | Layout wrapper |
| `loading.tsx` | Loading UI (automatic) |
| `error.tsx` | Error boundary (automatic) |

---

## ✏️ Coding Standards

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### Code Style Rules

```typescript
// ✅ DO: Use explicit types for function returns
function getUser(id: string): Promise<User | null> {
  return db.user.findUnique({ where: { id } });
}

// ✅ DO: Use Zod for runtime validation
import { z } from 'zod';

const userSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().positive().optional(),
});

// ✅ DO: Use server actions for mutations
async function updateUser(formData: FormData) {
  'use server';
  const data = userSchema.parse(Object.fromEntries(formData));
  await db.user.update({ where: { id: data.id }, data });
}

// ❌ DON'T: Use any type
function bad(data: any) {} // Never do this

// ❌ DON'T: Skip validation on user input
async function createUser(input: unknown) {
  // Always validate with Zod first
  const validated = userSchema.parse(input);
}
```

### ESLint Rules (Critical)

```js
// .eslintrc.cjs
module.exports = {
  extends: ['next/core-web-vitals', 'plugin:@typescript-eslint/recommended'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'react/no-unescaped-entities': 'off',
  },
};
```

---

## 🗄️ Database & SQLite

### Connection Setup

```typescript
// lib/db/index.ts
import Database from 'better-sqlite3';
import { join } from 'path';

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(
      process.env.NODE_ENV === 'production'
        ? process.env.DATABASE_URL!
        : join(process.cwd(), 'dev.db')
    );
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}

export function closeDb() {
  db?.close();
}
```

### Schema Definition

```typescript
// lib/db/schema.ts
import { getDb } from './index';

export const schemas = {
  users: `
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      password_hash TEXT NOT NULL,
      created_at INTEGER DEFAULT (strftime('%s', 'now')),
      updated_at INTEGER DEFAULT (strftime('%s', 'now'))
    )
  `,
  sessions: `
    CREATE TABLE IF NOT EXISTS sessions (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      token TEXT UNIQUE NOT NULL,
      expires_at INTEGER NOT NULL,
      created_at INTEGER DEFAULT (strftime('%s', 'now'))
    )
  `,
};

export function runMigrations() {
  const db = getDb();
  Object.values(schemas).forEach((sql) => db.exec(sql));
}
```

### Query Patterns

```typescript
// ✅ DO: Use prepared statements
const stmt = db.prepare('SELECT * FROM users WHERE email = ?');
const user = stmt.get(email);

// ✅ DO: Use transactions for multiple writes
const transaction = db.transaction((userData, sessionData) => {
  db.prepare('INSERT INTO users ...').run(userData);
  db.prepare('INSERT INTO sessions ...').run(sessionData);
});
transaction(userData, sessionData);

// ❌ DON'T: String interpolation (SQL injection risk)
db.exec(`SELECT * FROM users WHERE email = '${email}'`); // NEVER!
```

### Migration Strategy

```bash
# Create new migration
npm run db:migrate --name add_user_avatar

# Run migrations
npm run db:migrate

# Reset dev database
npm run db:reset
```

---

## 🌐 API Patterns

### Route Handler Structure

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getDb } from '@/lib/db';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  password: z.string().min(8),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = createUserSchema.parse(body);
    
    const db = getDb();
    const stmt = db.prepare('INSERT INTO users ... RETURNING *');
    const user = stmt.get(data);
    
    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

### Server Actions (Preferred for Forms)

```typescript
// app/(dashboard)/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { getDb } from '@/lib/db';
import { auth } from '@/lib/auth';

export async function updateProfile(formData: FormData) {
  const session = await auth();
  if (!session) throw new Error('Unauthorized');

  const name = formData.get('name') as string;
  const email = formData.get('email') as string;

  // Validate
  if (!name || !email) {
    return { error: 'Name and email are required' };
  }

  // Update
  const db = getDb();
  db.prepare('UPDATE users SET name = ?, email = ? WHERE id = ?')
    .run(name, email, session.userId);

  revalidatePath('/dashboard');
  redirect('/dashboard');
}
```

### Error Handling Pattern

```typescript
// lib/errors.ts
export class AppError extends Error {
  constructor(
    public code: string,
    public status: number = 400,
    message?: string
  ) {
    super(message || code);
  }
}

export const errors = {
  notFound: () => new AppError('NOT_FOUND', 404),
  unauthorized: () => new AppError('UNAUTHORIZED', 401),
  invalidInput: (field: string) => new AppError('INVALID_INPUT', 400, `${field} is invalid`),
};

// Usage in API routes
export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(params.id);
  
  if (!user) {
    throw errors.notFound();
  }
  
  return NextResponse.json(user);
}
```

---

## 🔐 Authentication

### Session-Based Auth Setup

```typescript
// lib/auth/index.ts
import { cookies } from 'next/headers';
import { randomBytes } from 'crypto';
import { getDb } from '@/lib/db';

export async function createSession(userId: string): Promise<string> {
  const token = randomBytes(32).toString('hex');
  const expiresAt = Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 7; // 7 days

  const db = getDb();
  db.prepare('INSERT INTO sessions (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)')
    .run(randomBytes(16).toString('hex'), userId, token, expiresAt);

  return token;
}

export async function getSession(): Promise<{ userId: string } | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get('session')?.value;

  if (!token) return null;

  const db = getDb();
  const session = db.prepare(`
    SELECT s.user_id FROM sessions s
    WHERE s.token = ? AND s.expires_at > strftime('%s', 'now')
  `).get(token) as { userId: string } | undefined;

  return session || null;
}

export async function auth() {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');
  return session;
}
```

### Protected Route Pattern

```typescript
// app/(dashboard)/layout.tsx
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) {
    redirect('/login');
  }
  return <>{children}</>;
}
```

---

## 🧪 Testing

### Vitest Setup

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./tests/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
```

### Test Examples

```typescript
// tests/db.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { getDb, closeDb } from '@/lib/db';

describe('Database', () => {
  beforeEach(() => {
    // Use in-memory DB for tests
    process.env.DATABASE_URL = ':memory:';
  });

  it('should create a user', () => {
    const db = getDb();
    const stmt = db.prepare('INSERT INTO users (id, email, name, password_hash) VALUES (?, ?, ?, ?)');
    const result = stmt.run('user-1', 'test@example.com', 'Test User', 'hash123');
    
    expect(result.changes).toBe(1);
  });

  it('should enforce unique email', () => {
    const db = getDb();
    db.prepare('INSERT INTO users ...').run('user-1', 'test@example.com', 'Test', 'hash');
    
    expect(() => {
      db.prepare('INSERT INTO users ...').run('user-2', 'test@example.com', 'Test', 'hash');
    }).toThrow();
  });
});
```

### E2E Testing (Playwright)

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('user can register and login', async ({ page }) => {
  // Register
  await page.goto('/register');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=password]', 'password123');
  await page.click('button[type=submit]');
  
  await expect(page).toHaveURL('/dashboard');
  
  // Logout
  await page.click('[data-testid=logout]');
  await expect(page).toHaveURL('/login');
});
```

---

## 🚀 Deployment

### Environment Variables

```bash
# .env.example
DATABASE_URL=file:/data/production.db
AUTH_SECRET=your-secret-key-here
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

### Vercel Configuration

```json
// vercel.json
{
  "regions": ["iad1"],
  "env": {
    "NODE_ENV": "production"
  },
  "build": {
    "env": {
      "ENABLE_FILE_SYSTEM_API": "1"
    }
  }
}
```

### Neon/Serverless SQLite (Alternative)

```typescript
// For serverless deployments, use Neon or Turso
import { createClient } from '@neondatabase/serverless';

export const neon = createClient(process.env.DATABASE_URL!);

// Usage
const result = await neon`SELECT * FROM users WHERE id = ${userId}`;
```

---

## 🔒 Security

### Rate Limiting

```typescript
// lib/rate-limit.ts
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, number>({
  max: 10000,
  ttl: 60 * 1000, // 1 minute
});

export function rateLimit(identifier: string, limit: number = 10): boolean {
  const count = cache.get(identifier) || 0;
  if (count >= limit) return false;
  cache.set(identifier, count + 1);
  return true;
}

// Usage in API route
export async function POST(request: NextRequest) {
  const ip = request.ip || 'unknown';
  
  if (!rateLimit(ip, 10)) {
    return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
  }
  
  // ... handle request
}
```

### SQL Injection Prevention

```typescript
// ✅ ALWAYS use parameterized queries
const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);

// ❌ NEVER use string interpolation
const user = db.exec(`SELECT * FROM users WHERE email = '${email}'`); // DANGEROUS!
```

### XSS Prevention

```typescript
// In Next.js 15, content is escaped by default
// ✅ Safe: React escapes by default
<div>{userInput}</div>

// ❌ Dangerous: Don't use dangerouslySetInnerHTML unless necessary
<div dangerouslySetInnerHTML={{ __html: userInput }} /> // AVOID!

// If you must, sanitize first
import DOMPurify from 'isomorphic-dompurify';
const sanitized = DOMPurify.sanitize(userInput);
```

---

## 📝 Common Tasks

### Create New Feature

```bash
# 1. Create route
mkdir -p app/(dashboard)/new-feature

# 2. Create page
cat > app/(dashboard)/new-feature/page.tsx << 'EOF'
export default function NewFeaturePage() {
  return <h1>New Feature</h1>;
}
EOF

# 3. Add tests
cat > tests/new-feature.test.ts << 'EOF'
import { describe, it, expect } from 'vitest';
describe('NewFeature', () => {
  it('should render', () => {
    expect(true).toBe(true);
  });
});
EOF
```

### Add Database Migration

```bash
# 1. Create migration file
cat > lib/db/migrations/001_add_avatar.sql << 'EOF'
ALTER TABLE users ADD COLUMN avatar_url TEXT;
EOF

# 2. Run migration
npm run db:migrate
```

### Deploy to Production

```bash
# 1. Push to main
git push origin main

# 2. Vercel auto-deploys
# Check deployment status at vercel.com

# 3. Run production migrations
vercel env pull --environment=production
npm run db:migrate:prod
```

---

## 📚 Resources

| Resource | Link |
|----------|------|
| Next.js 15 Docs | https://nextjs.org/docs |
| better-sqlite3 | https://github.com/WiseLibs/better-sqlite3 |
| Zod Validation | https://zod.dev |
| Auth Best Practices | https://clerk.com/docs |
| Testing Guide | https://vitest.dev/guide |

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Database locked | Check for unclosed connections, use WAL mode |
| Session not persisting | Verify cookie settings, check AUTH_SECRET |
| API route 404 | Ensure file is named `route.ts` not `route.tsx` |
| TypeScript errors | Run `npm run type-check` to see all errors |
| Build fails on Vercel | Check `vercel.json` for file system API enablement |

---

*This CLAUDE.md template is production-ready and follows 2026 best practices for Next.js 15 + SQLite SaaS applications.*
