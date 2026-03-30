# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guide

**Opinionated, production-ready instructions for Claude Code agents working on Next.js 15 App Router + SQLite SaaS applications.**

This document assumes a greenfield project using:
- Next.js 15 (App Router)
- React 19
- TypeScript 5
- SQLite via `better-sqlite3` (or Turso)
- `concurrently` for dev process management
- ESLint + Prettier
- Jest + React Testing Library + Playwright

---

## 📦 Stack & Versions

| Tool | Version | Why |
|------|---------|-----|
| Node.js | 22.x (LTS) | Latest stable, V8 improvements, ES module support |
| Next.js | 15.x | App Router, Server Actions, Partial Prerendering |
| React | 19.x | Background rendering, improved hooks |
| TypeScript | 5.x | Strict mode, better type inference |
| SQLite | 3.x + `better-sqlite3` | Fast, zero-config, file-based, ACID compliant |
| Prisma | 6.x (optional) | ORM alternative if schema-first preferred |
| Vercel | Hosting | Edge functions, zero config |

---

## 🗂️ Folder Structure

```
my-saas/
├── app/                    # App Router pages
│   ├── (auth)/             # Auth group (login, register)
│   ├── dashboard/          # Protected pages
│   ├── api/                # Route handlers (REST/GraphQL)
│   ├── layout.tsx
│   ├── page.tsx            # Homepage
│   └── template.tsx
├── components/             # Shared UI components
│   ├── ui/                 # shadcn/ui or custom primitives
│   ├── forms/              # Form wrappers, validation
│   └── features/           # Feature-scoped components
├── lib/                    # Reusable utilities
│   ├── db/                 # Database connection & helpers
│   │   ├── connection.ts   # SQLite connection singleton
│   │   ├── migrations/     # SQL migration files
│   │   └── seed.ts         # Seed data for dev
│   ├── schemas/            # Zod schemas for validation
│   ├── utils/              # Pure helper functions
│   └── hooks/              # Custom React hooks
├── scripts/                # Build/dev scripts
│   ├── db-migrate.ts       # Migration runner
│   ├── db-seed.ts          # Database seeder
│   └── db-rollback.ts      # Rollback last migration
├── tests/                  # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── public/                 # Static assets
├── .env.example            # Env vars template
├── docker-compose.yml      # Optional: for dev container
├── Dockerfile              # Production image
├── next.config.mjs
├── package.json
├── tsconfig.json
└── CLAUDE.md               # This file
```

---

## 🏷️ Naming Conventions

- **Files**: kebab-case (`user-profile.tsx`, `use-auth.ts`)
- **Components**: PascalCase (`Button`, `UserCard`)
- **Functions/variables**: camelCase (`getUser`, `isValid`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_FILE_SIZE`, `DEFAULT_TIMEOUT`)
- **Classes**: PascalCase (`class Database {}`)
- **Interfaces/types**: PascalCase with `I` prefix optional (`User`, `IAuthResponse`)
- **Database tables**: snake_case plural (`users`, `subscription_plans`)
- **Migration files**: `YYYYMMDD_HHMMSS_description.sql` (e.g., `20260320_143000_add_user_table.sql`)
- **Environment variables**: `APP_` prefix for app-specific (`APP_DB_PATH`, `APP_JWT_SECRET`)

---

## 🗃️ Database & Migration Rules

### 1. Connection Setup (`lib/db/connection.ts`)

```typescript
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.APP_DB_PATH || path.join(process.cwd(), 'data', 'app.db');

// Ensure data directory exists
import fs from 'fs';
if (!fs.existsSync(path.dirname(DB_PATH))) {
  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
}

export const db = new Database(DB_PATH);

// Enable WAL mode for better concurrency
db.pragma('journal_mode = WAL');

// Foreign keys enabled by default in better-sqlite3? Yes, but explicit:
db.pragma('foreign_keys = ON');
```

### 2. Migration File Format

Each migration is a single SQL file with `UP` and `DOWN` sections:

```sql
-- UP: Add users table
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  encrypted_password TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- DOWN: Rollback users table
DROP TABLE IF EXISTS users;
```

### 3. Migration Runner (`scripts/db-migrate.ts`)

```typescript
#!/usr/bin/env ts-node

import { readdirSync, readFileSync } from 'fs';
import { join } from 'path';
import { db } from '../lib/db/connection';

const MIGRATIONS_DIR = join(process.cwd(), 'lib', 'db', 'migrations');

function runMigrations() {
  const files = readdirSync(MIGRATIONS_DIR)
    .filter(f => f.endsWith('.sql'))
    .sort(); // alphabetical = chronological due to timestamp prefix

  for (const file of files) {
    const sql = readFileSync(join(MIGRATIONS_DIR, file), 'utf-8');
    const sections = sql.split('-- DOWN:');
    const upSql = sections[0].trim();

    console.log(`Applying ${file}...`);
    db.exec(upSql);
  }

  console.log(`✅ Applied ${files.length} migrations`);
}

runMigrations();
```

Add to `package.json`:

```json
{
  "scripts": {
    "db:migrate": "ts-node scripts/db-migrate.ts",
    "db:seed": "ts-node scripts/db-seed.ts"
  }
}
```

### 4. Seed Data (`scripts/db-seed.ts`)

Idempotent seeding: use `INSERT OR IGNORE` or check existence.

```typescript
import { db } from '../lib/db/connection';

// Insert default subscription plans if not exist
const plans = [
  { id: 'free', price: 0, features: 'basic' },
  { id: 'pro', price: 29, features: 'advanced' },
];

for (const plan of plans) {
  db.run(
    `INSERT OR IGNORE INTO subscription_plans (id, price, features) VALUES (?, ?, ?)`,
    [plan.id, plan.price, plan.features]
  );
}

console.log('✅ Database seeded');
```

---

## 🔐 Security Patterns

### 1. Never信任客户端输入

Always validate with Zod in API routes or Server Actions:

```typescript
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(12),
  name: z.string().max(100),
});

// In Server Action or Route Handler
const validated = CreateUserSchema.parse(formData);
```

### 2. SQL Injection Prevention

**DO NOT:**
```typescript
db.run(`SELECT * FROM users WHERE email = '${email}'`); // VULNERABLE
```

**DO:**
```typescript
db.get('SELECT * FROM users WHERE email = ?', [email]); // Parameterized
```

`better-sqlite3` uses `?` placeholders. Never concatenate user input into SQL.

### 3. Password Handling

- Use `argon2` or `bcrypt` for hashing.
- Never store plaintext.
- Use constant-time comparison if needed.

```typescript
import argon2 from 'argon2';

const hash = await argon2.hash(password);
// Store `hash` in DB
```

### 4. Session Management

- Use signed, HTTP-only cookies for session tokens.
- Set `SameSite=Strict` and `Secure` in production.
- Rotate session IDs after login.

```typescript
import { serialize } from 'cookie';

const sessionToken = generateToken();
const serialized = serialize('session', sessionToken, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  maxAge: 60 * 60 * 24 * 7, // 1 week
  path: '/',
});

response.headers.append('Set-Cookie', serialized);
```

---

## 🌐 API Routes & Server Actions

### Prefer Server Actions for mutations

```typescript
'use server';

import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db/connection';

export async function createUser(formData: FormData) {
  const email = formData.get('email') as string;
  // Validate, insert, etc.
  db.run('INSERT INTO users (email) VALUES (?)', [email]);
  revalidatePath('/dashboard');
  return { success: true };
}
```

### Use Route Handlers for REST/GraphQL

```typescript
// app/api/users/route.ts
export async function GET(request: Request) {
  const users = db.prepare('SELECT id, email FROM users').all();
  return Response.json(users);
}
```

---

## 🎨 Component Patterns

### 1. Client vs Server Components

- Default: Server Component (no `'use client'`).
- Add `'use client'` only when you need:
  - `useState`, `useEffect`, event handlers
  - Browser APIs
  - React hooks

### 2. Forms: Use `react-hook-form` + Zod

```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const schema = z.object({ email: z.string().email() });

export function UserForm() {
  const { register, handleSubmit } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: any) => {
    'use server';
    // Server Action call
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      <button type="submit">Submit</button>
    </form>
  );
}
```

### 3. Data Fetching: Prefer `fetch` in Server Components

```typescript
// app/dashboard/page.tsx
export default async function Dashboard() {
  const data = await fetch(`${process.env.APP_URL}/api/stats`).then(r => r.json());
  return <StatsChart data={data} />;
}
```

### 4. Streaming with Suspense

Wrap heavy components in `<Suspense fallback={...}>`.

---

## 🚫 Anti-patterns

1. **No `use client` at root** — Keep layouts server-side unless absolutely necessary.
2. **No inline styles** — Use Tailwind or CSS modules.
3. **No magic numbers/strings** — Extract to constants (`lib/constants.ts`).
4. **No direct DB access from Client Components** — All DB calls go through Server Actions or API routes.
5. **No `any` types** — Use `unknown` or define proper interfaces.
6. **No console.log in production** — Use a logger (`pino` or `winston`) with level guards.
7. **No mutation in `getStaticProps`/`getServerSideProps`** — Those are for fetching only.
8. **No storing secrets in client-side code** — Only server-side access to env vars.

---

## 🧪 Testing

### Unit Tests (Jest)

Location: `tests/unit/`

```typescript
import { db } from '@/lib/db/connection';

describe('User model', () => {
  it('inserts a user', () => {
    const id = 'test-123';
    db.run('INSERT INTO users (id, email) VALUES (?, ?)', [id, 'test@example.com']);
    const user = db.get('SELECT * FROM users WHERE id = ?', [id]);
    expect(user.email).toBe('test@example.com');
  });
});
```

### Integration Tests (API routes)

Use `@vercel/next-test-utils` or `supertest` with a test database.

### E2E Tests (Playwright)

`tests/e2e/auth.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'admin@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

---

## 🛠️ Dev Commands

```json
{
  "scripts": {
    "dev": "concurrently \"next dev\" \"ts-node scripts/db-migrate.ts --watch\"",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --ext .ts,.tsx",
    "format": "prettier --write .",
    "db:migrate": "ts-node scripts/db-migrate.ts",
    "db:seed": "ts-node scripts/db-seed.ts",
    "db:rollback": "ts-node scripts/db-rollback.ts",
    "test": "jest",
    "test:e2e": "playwright test"
  }
}
```

---

## 📦 Dependencies

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "better-sqlite3": "^9.0.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.45.0",
    "@hookform/resolvers": "^3.3.0",
    "argon2": "^0.31.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "@types/react": "^19.0.0",
    "@types/better-sqlite3": "^7.6.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^15.0.0",
    "prettier": "^3.0.0",
    "ts-node": "^10.9.0",
    "jest": "^29.0.0",
    "@testing-library/react": "^14.0.0",
    "@playwright/test": "^1.40.0",
    "concurrently": "^8.0.0"
  }
}
```

---

## 🔧 Environment Variables (`.env.example`)

```bash
# Database
APP_DB_PATH=./data/app.db

# Auth
APP_JWT_SECRET=your-64-char-secret-key-here
APP_JWT_EXPIRY=7d

# App
APP_URL=http://localhost:3000
APP_ENV=development

# Email (optional)
APP_SMTP_HOST=smtp.example.com
APP_SMTP_PORT=587
APP_SMTP_USER=...
APP_SMTP_PASS=...
```

---

## ✅ Pre-commit Checklist

- [ ] TypeScript compiles without errors (`npm run build`)
- [ ] Lint passes (`npm run lint`)
- [ ] Format code (`npm run format`)
- [ ] Unit tests pass (`npm test`)
- [ ] Database migrations applied (`npm run db:migrate`)
- [ ] No secrets committed (use `dotenv` + `.gitignore`)
- [ ] No console.log statements left

---

## 📚 Further Reading

- Next.js 15 Docs: https://nextjs.org/docs
- SQLite Best Practices: https://www.sqlite.org/atomiccommit.html
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Prisma Guide (if used): https://www.prisma.io/docs

---

**Keep this file updated. If a pattern becomes widespread, codify it here.**