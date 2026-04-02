# Project Context for Claude Code

## Stack & Versions

- Next.js 15.x (App Router)
- SQLite with better-sqlite3
- Node.js 20.x LTS
- TypeScript 5.x

## Dev Commands

```bash
npm run dev          # Start dev server on :3000
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Run ESLint
npm run db:migrate   # Run DB migrations
npm run db:seed      # Seed database
```

## Folder Structure

```
app/
  (auth)/           # Auth-related pages (login, signup)
    login/
    signup/
  (dashboard)/      # Protected dashboard pages
    page.tsx
    settings/
  api/              # API routes
    auth/
    users/
  layout.tsx
  page.tsx
components/
  ui/               # Reusable UI components
    button.tsx
    input.tsx
  forms/            # Form components
  layouts/          # Layout components
lib/
  db.ts             # Database connection
  auth.ts           # Auth utilities
  utils.ts          # Helper functions
migrations/         # SQL migration files
  001_init.sql
  002_add_users.sql
public/
  images/
types/
  index.ts          # Shared TypeScript types
```

## SQL / Migration Conventions

### Migration Files

- Located in `migrations/` folder
- Named with number prefix: `001_description.sql`
- Always include `up` and `down` (commented)

```sql
-- Migration: Create users table
-- Version: 001

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Rollback:
-- DROP TABLE users;
```

### Database Queries

- Use prepared statements
- Return typed results
- Handle errors gracefully

```typescript
import db from '@/lib/db';

export function getUser(id: number) {
  const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
  return stmt.get(id) as User | undefined;
}
```

## Component Patterns

### Server Components (default)

```tsx
// app/page.tsx - Server Component
import { getUser } from '@/lib/db';

export default async function Page() {
  const user = await getUser(1);
  return <div>{user?.name}</div>;
}
```

### Client Components (when needed)

```tsx
// components/counter.tsx
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

## What We Don't Do

### No ORM

- We use raw SQL with better-sqlite3
- Reasons: 
  - Full control over queries
  - Easier to debug
  - SQLite is simple enough
  - No abstraction overhead

### No Redux/Zustand

- Server Components handle state
- Use React Context only when necessary
- Keep state close to where it's used

### No CSS-in-JS

- Use Tailwind CSS for styling
- Keeps bundle small
- Better performance

### No GraphQL

- REST API routes are sufficient
- Simpler to understand
- Less over-fetching concerns with SQLite

### No Prisma

- Direct SQL is more transparent
- Migrations are just .sql files
- No schema sync issues

## Code Style

### Imports

```typescript
// Absolute imports with @ alias
import { Button } from '@/components/ui/button';
import { getUser } from '@/lib/db';

// Not relative imports from deep nesting
// ❌ import { Button } from '../../../components/ui/button';
```

### Error Handling

```typescript
// Use try-catch in actions
export async function deleteUser(id: number) {
  try {
    const stmt = db.prepare('DELETE FROM users WHERE id = ?');
    stmt.run(id);
    return { success: true };
  } catch (error) {
    console.error('Delete failed:', error);
    return { success: false, error: 'Failed to delete user' };
  }
}
```

### Type Safety

```typescript
// Define types in types/index.ts
export interface User {
  id: number;
  email: string;
  name: string | null;
  created_at: string;
}

// Use in functions
export function getUser(id: number): User | undefined {
  // ...
}
```

## Environment Variables

```bash
# .env.local
DATABASE_URL=./data.db
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000
```

## Testing

```bash
npm run test          # Run Jest tests
npm run test:watch    # Watch mode
npm run test:e2e      # Run Playwright e2e tests
```

## Deployment

- Build with `npm run build`
- SQLite file goes in `data/` folder
- Set NODE_ENV=production
- Use PM2 or similar for process management

## Common Tasks

### Add a new page

1. Create `app/new-page/page.tsx`
2. Add necessary queries in `lib/db.ts`
3. Create components in `components/`

### Add a new API route

1. Create `app/api/resource/route.ts`
2. Use standard HTTP methods (GET, POST, etc.)
3. Return JSON responses

### Add a migration

1. Create `migrations/003_description.sql`
2. Write SQL for schema change
3. Run `npm run db:migrate`
4. Update types in `types/index.ts`

## Anti-patterns to Avoid

- ❌ Fetching data in client components
- ❌ Using `useEffect` for data fetching
- ❌ Storing sensitive data in localStorage
- ❌ Skipping TypeScript types
- ❌ Large client bundles
- ❌ N+1 query problems
- ❌ Not using prepared statements
- ❌ Mixing server and client code incorrectly

## Performance Tips

1. Use Server Components by default
2. Only add 'use client' when necessary
3. Lazy load heavy components
4. Use React Suspense for loading states
5. Keep database queries efficient
6. Index frequently queried columns

## Security

- Always validate user input
- Use prepared statements (no SQL injection)
- Sanitize HTML before rendering
- Use HTTPS in production
- Keep secrets in environment variables
- Implement rate limiting on API routes
