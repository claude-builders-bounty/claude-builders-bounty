
## Project Overview

Next.js SaaS starter with SQLite database. Monorepo-style structure with clear separation of concerns.

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Database**: SQLite via better-sqlite3
- **Styling**: Tailwind CSS
- **Language**: TypeScript (strict mode)
- **Testing**: Vitest + Testing Library
- **ORM**: Drizzle ORM (lightweight, type-safe)

## Project Structure

```
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Auth-related routes (login, register)
│   │   ├── (dashboard)/       # Protected dashboard routes
│   │   ├── api/               # API routes
│   │   └── layout.tsx         # Root layout
│   ├── components/            # React components
│   │   ├── ui/               # Reusable UI components (Button, Input, etc.)
│   │   ├── forms/            # Form components
│   │   └── layout/           # Layout components (Navbar, Sidebar, etc.)
│   ├── db/                   # Database layer
│   │   ├── schema/          # Drizzle schema definitions
│   │   ├── migrations/      # Database migrations
│   │   ├── index.ts         # Database connection
│   │   └── seed.ts          # Seed data
│   ├── lib/                 # Utility functions
│   │   ├── auth.ts          # Auth helpers
│   │   ├── api-error.ts     # API error handling
│   │   └── utils.ts         # General utilities
│   └── types/               # TypeScript type definitions
├── public/                  # Static assets
├── tests/                  # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── drizzle.config.ts       # Drizzle configuration
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Available Commands

```bash
# Development
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run start        # Start production server

# Database
npm run db:generate  # Generate migrations from schema changes
npm run db:migrate   # Apply pending migrations
npm run db:push      # Push schema changes directly (dev only)
npm run db:seed      # Seed database with sample data
npm run db:studio    # Open Drizzle Studio (GUI for SQLite)

# Testing
npm run test         # Run all tests
npm run test:watch   # Run tests in watch mode
npm run test:ui      # Run tests with UI (Vitest UI)
npm run test:coverage # Run tests with coverage report

# Code Quality
npm run lint         # ESLint
npm run lint:fix     # ESLint with auto-fix
npm run format       # Prettier formatting
npm run type-check   # TypeScript type checking
```

## Code Patterns & Conventions

### 1. Database Access Pattern

```typescript
// src/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database('sqlite.db');
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');

export const db = drizzle(sqlite, { schema });
```

### 2. API Route Pattern

```typescript
// src/app/api/teams/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { teams } from '@/db/schema';
import { requireAuth } from '@/lib/auth';
import { ApiError } from '@/lib/api-error';

export async function GET(request: NextRequest) {
  try {
    const user = await requireAuth(request);
    const userTeams = await db.query.teams.findMany({
      where: (teams, { eq }) => eq(teams.userId, user.id),
    });
    
    return NextResponse.json(userTeams);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(
        { error: error.message },
        { status: error.status }
      );
    }
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await requireAuth(request);
    const body = await request.json();
    
    const [team] = await db.insert(teams)
      .values({ ...body, userId: user.id })
      .returning();
    
    return NextResponse.json(team, { status: 201 });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(
        { error: error.message },
        { status: error.status }
      );
    }
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

### 3. Server Action Pattern

```typescript
// src/app/(dashboard)/teams/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { db } from '@/db';
import { teams } from '@/db/schema';
import { requireAuth } from '@/lib/auth';

export async function createTeam(formData: FormData) {
  const user = await requireAuth();
  const name = formData.get('name') as string;
  
  if (!name || name.length < 3) {
    throw new Error('Team name must be at least 3 characters');
  }
  
  await db.insert(teams).values({
    name,
    userId: user.id,
  });
  
  revalidatePath('/teams');
}
```

### 4. Component Pattern

```typescript
// src/components/ui/Button.tsx
'use client';

import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
```

## Database Schema Guide

### Naming Conventions
- Tables: plural lowercase (users, teams, subscriptions)
- Columns: snake_case (created_at, updated_at)
- Primary keys: `id` (auto-increment integer)
- Foreign keys: `{table}_id` (user_id, team_id)
- Timestamps: `created_at`, `updated_at` (automatically managed)

### Example Schema

```typescript
// src/db/schema/users.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  passwordHash: text('password_hash').notNull(),
  role: text('role', { enum: ['user', 'admin'] }).default('user').notNull(),
  createdAt: text('created_at')
    .default(sql`(current_timestamp)`)
    .notNull(),
  updatedAt: text('updated_at')
    .default(sql`(current_timestamp)`)
    .notNull(),
});

// src/db/schema/teams.ts
export const teams = sqliteTable('teams', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  slug: text('slug').notNull().unique(),
  userId: integer('user_id')
    .notNull()
    .references(() => users.id, { onDelete: 'cascade' }),
  createdAt: text('created_at')
    .default(sql`(current_timestamp)`)
    .notNull(),
  updatedAt: text('updated_at')
    .default(sql`(current_timestamp)`)
    .notNull(),
});

// src/db/schema/subscriptions.ts
export const subscriptions = sqliteTable('subscriptions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  teamId: integer('team_id')
    .notNull()
    .references(() => teams.id, { onDelete: 'cascade' }),
  plan: text('plan', { enum: ['free', 'pro', 'enterprise'] })
    .default('free')
    .notNull(),
  status: text('status', { enum: ['active', 'canceled', 'past_due'] })
    .default('active')
    .notNull(),
  currentPeriodStart: text('current_period_start').notNull(),
  currentPeriodEnd: text('current_period_end').notNull(),
  createdAt: text('created_at')
    .default(sql`(current_timestamp)`)
    .notNull(),
  updatedAt: text('updated_at')
    .default(sql`(current_timestamp)`)
    .notNull(),
});
```

## Testing Approach

### Unit Tests (Vitest)

```typescript
// tests/unit/lib/utils.test.ts
import { describe, it, expect } from 'vitest';
import { cn, formatDate } from '@/lib/utils';

describe('cn', () => {
  it('merges class names correctly', () => {
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2');
    expect(cn('px-4', false && 'hidden')).toBe('px-4');
  });
});

describe('formatDate', () => {
  it('formats ISO date string', () => {
    const result = formatDate('2024-01-15T10:30:00Z');
    expect(result).toContain('2024');
  });
});
```

### Integration Tests

```typescript
// tests/integration/api/teams.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { db } from '@/db';
import { teams, users } from '@/db/schema';

describe('Teams API', () => {
  beforeAll(async () => {
    // Seed test data
    await db.insert(users).values({
      email: 'test@example.com',
      name: 'Test User',
      passwordHash: 'hashed_password',
    });
  });

  afterAll(async () => {
    // Cleanup test data
    await db.delete(users);
  });

  it('creates a new team', async () => {
    const [team] = await db.insert(teams)
      .values({
        name: 'Test Team',
        slug: 'test-team',
        userId: 1,
      })
      .returning();

    expect(team.name).toBe('Test Team');
    expect(team.slug).toBe('test-team');
  });
});
```

## Environment Variables

```env
# .env.local
DATABASE_URL=file:./sqlite.db
NEXT_PUBLIC_APP_URL=http://localhost:3000
SESSION_SECRET=your-secret-key-min-32-chars
```

## Error Handling

```typescript
// src/lib/api-error.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number = 400
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function handleApiError(error: unknown) {
  if (error instanceof ApiError) {
    return { message: error.message, status: error.status };
  }
  
  console.error('Unexpected error:', error);
  return { message: 'Internal server error', status: 500 };
}
```

## Performance Guidelines

1. Use `next/image` for images
2. Implement proper caching with `stale-while-revalidate`
3. Use React Server Components by default
4. Minimize client components
5. Use `useMemo` and `useCallback` sparingly
6. Implement pagination for list endpoints
7. Use database indexing for frequent queries

## Security Best Practices

1. Always validate input with Zod
2. Use prepared statements (Drizzle handles this)
3. Implement rate limiting on API routes
4. Use HTTP-only cookies for sessions
5. Sanitize user input in database queries
6. Implement CSRF protection for forms
7. Use proper password hashing (bcrypt)

---
