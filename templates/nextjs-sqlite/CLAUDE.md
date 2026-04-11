# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated, production-ready guide for AI assistants working on this codebase.

---

## 📁 Project Structure

```
project/
├── src/
│   ├── app/                    # Next.js 15 App Router
│   │   ├── (auth)/            # Auth route group
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── (dashboard)/       # Protected routes
│   │   │   ├── dashboard/
│   │   │   └── settings/
│   │   ├── api/               # API routes
│   │   │   ├── auth/
│   │   │   ├── users/
│   │   │   └── webhooks/
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   │
│   ├── components/
│   │   ├── ui/                # Base UI components
│   │   ├── forms/             # Form components
│   │   └── layouts/           # Layout components
│   │
│   ├── lib/
│   │   ├── db.ts              # SQLite connection
│   │   ├── auth.ts            # Auth utilities
│   │   └── utils.ts           # Helper functions
│   │
│   └── types/
│       └── index.ts           # TypeScript types
│
├── migrations/                 # Database migrations
├── public/                     # Static assets
├── tests/                      # Test files
│
├── .env.local                  # Environment variables
├── drizzle.config.ts          # DB config
├── next.config.js
├── package.json
└── tsconfig.json
```

---

## 🛠️ Development Commands

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run production server
npm run start

# Database
npm run db:generate    # Generate migration
npm run db:migrate     # Run migration
npm run db:push        # Push schema (dev)
npm run db:studio      # Open Drizzle Studio

# Testing
npm run test           # Run tests
npm run test:watch     # Watch mode
npm run test:coverage  # Coverage report

# Linting
npm run lint           # Check issues
npm run lint:fix       # Auto-fix
```

---

## 📝 Naming Conventions

### Files & Folders
- **Components**: PascalCase (`Button.tsx`, `UserCard.tsx`)
- **Utilities**: camelCase (`formatDate.ts`, `validateEmail.ts`)
- **API Routes**: kebab-case (`/api/auth/callback`, `/api/user-preferences`)
- **Pages**: lowercase (`page.tsx`, `layout.tsx`)

### Variables & Functions
```typescript
// ✅ Good
const userCount = 10;
const isLoading = false;
const handleSubmit = async () => {};
const getUserById = (id: string) => {};

// ❌ Bad
const count = 10;
const loading = false;
const submit = async () => {};
const user = (id) => {};
```

### Components
```typescript
// ✅ Good - Named export
export function UserProfile({ user }: UserProfileProps) {
  return <div>{user.name}</div>;
}

// ❌ Bad - Default export for components
export default function UserProfile() {}
```

---

## 🗄️ Database Rules

### Schema Location
- Define schemas in `src/lib/db/schema/`
- One file per table: `users.ts`, `posts.ts`, `comments.ts`

### Migration Workflow
```bash
# 1. Modify schema
# 2. Generate migration
npm run db:generate

# 3. Review migration file in migrations/
# 4. Apply migration
npm run db:migrate
```

### Query Patterns
```typescript
// ✅ Good - Use Drizzle ORM
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

const user = await db.select().from(users).where(eq(users.id, id));

// ❌ Bad - Raw SQL (unless necessary)
const user = await db.execute(sql`SELECT * FROM users WHERE id = ${id}`);
```

---

## 🎨 Patterns to Follow

### API Routes
```typescript
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const validated = schema.parse(body);

    // Create user...
    return NextResponse.json({ success: true, data: user });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Invalid request' },
      { status: 400 }
    );
  }
}
```

### Server Components (Default)
```typescript
// app/(dashboard)/dashboard/page.tsx
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export default async function DashboardPage() {
  const allUsers = await db.select().from(users);

  return (
    <div>
      {allUsers.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  );
}
```

### Client Components (Interactive)
```typescript
// components/forms/UserForm.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function UserForm() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // Submit logic...
    router.refresh();
  };

  return <form onSubmit={handleSubmit}>...</form>;
}
```

---

## 🚫 Anti-Patterns to Avoid

### 1. Fetching in Client Components
```typescript
// ❌ Bad
'use client';
export function UserList() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    fetch('/api/users').then(r => r.json()).then(setUsers);
  }, []);

  return <div>{users.map(...)}</div>;
}

// ✅ Good - Fetch in Server Component, pass as prop
export default async function UserPage() {
  const users = await db.select().from(users);
  return <UserList users={users} />;
}
```

### 2. Ignoring Loading States
```typescript
// ❌ Bad
export default function Page() {
  return <Suspense fallback={<Loading />}>
    <AsyncComponent />
  </Suspense>;
}
```

### 3. Storing Secrets in Client Code
```typescript
// ❌ Never do this
const API_KEY = 'sk-xxx';

// ✅ Use environment variables
const API_KEY = process.env.API_KEY;
```

### 4. Direct DOM Manipulation
```typescript
// ❌ Bad
document.getElementById('form').submit();

// ✅ Good - Use React state
<form onSubmit={handleSubmit}>
```

---

## 🔐 Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL="./local.db"
NEXTAUTH_SECRET="your-secret-key"
NEXTAUTH_URL="http://localhost:3000"
```

---

## ✅ Checklist Before PR

- [ ] TypeScript compiles without errors
- [ ] All tests pass
- [ ] Lint passes
- [ ] No console.logs in production code
- [ ] Environment variables documented
- [ ] Migration files reviewed
- [ ] Loading states implemented
- [ ] Error boundaries added
- [ ] SEO metadata set
- [ ] Accessibility tested

---

## 📚 Key Dependencies

- **Next.js 15** - App Router, Server Components
- **Drizzle ORM** - Type-safe SQL
- **better-sqlite3** - Local SQLite
- **NextAuth.js** - Authentication
- **Zod** - Validation
- **Tailwind CSS** - Styling
- **Vitest** - Testing

---

_This file guides AI assistants. Update as the project evolves._
