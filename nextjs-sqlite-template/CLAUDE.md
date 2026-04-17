# Next.js 15 + SQLite SaaS Project

## Stack

- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite with better-sqlite3
- **ORM**: Drizzle ORM
- **Styling**: Tailwind CSS
- **Auth**: NextAuth.js

## Project Structure

```
/app                    # Next.js App Router pages
  /(auth)              # Auth routes (login, register)
  /(dashboard)         # Protected dashboard routes
  /api                 # API routes
/components            # React components
/lib                   # Utilities and shared code
  /db                  # Database schema and migrations
  /auth                # Auth configuration
/public                # Static assets
```

## Naming Conventions

### Files
- Components: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatDate.ts`)
- API routes: `route.ts`
- Database schema: `schema.ts`

### Variables
- React components: `PascalCase`
- Functions/hooks: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Database tables: `snake_case`

## Database Rules

### Migrations
1. Always use `drizzle-kit` for migrations
2. Never modify existing migration files
3. Create new migration for every schema change
4. Test migrations locally before committing

```bash
# Create migration
npm run db:generate -- "add_users_table"

# Apply migration
npm run db:migrate
```

### SQL Conventions
- Table names: `snake_case` plural (e.g., `users`, `user_sessions`)
- Column names: `snake_case` (e.g., `created_at`, `user_id`)
- Primary keys: `id` (INTEGER PRIMARY KEY)
- Timestamps: `created_at`, `updated_at` (ISO 8601)
- Foreign keys: `<table>_id` (e.g., `user_id`)

### Schema Definition
```typescript
// ✅ DO: Use Drizzle schema
export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  createdAt: text('created_at').notNull().default(sql`(datetime('now'))`),
});

// ❌ DON'T: Raw SQL for schema definitions
```

## Component Patterns

### Server Components (default)
- Fetch data directly in component
- No "use client" unless needed
- Use `async/await` for data fetching

### Client Components
- Add `"use client"` at top
- Use React hooks for interactivity
- Keep client components small

### File Organization
```
/components
  /ui          # Base UI components (Button, Input, Card)
  /features    # Feature-specific components
  /layouts     # Layout components
```

## API Routes

### Structure
```typescript
// ✅ DO: Export named handler
export async function GET(request: Request) {
  const data = await fetchData();
  return Response.json(data);
}

// ❌ DON'T: Export default function
```

### Error Handling
```typescript
// ✅ DO: Return structured errors
return Response.json(
  { error: 'User not found', code: 'USER_NOT_FOUND' },
  { status: 404 }
);

// ❌ DON'T: Throw errors in API routes
throw new Error('User not found');
```

## What We Don't Do

### No Direct SQL Queries in Components
```typescript
// ❌ DON'T
const users = db.query('SELECT * FROM users');

// ✅ DO: Use Drizzle ORM
const users = await db.select().from(usersTable);
```

### No Server Actions Without Validation
```typescript
// ❌ DON'T: No validation
export async function createUser(data: unknown) {
  await db.insert(usersTable, data);
}

// ✅ DO: Validate with Zod
import { z } from 'zod';
const UserSchema = z.object({ email: z.string().email(), password: z.string().min(8) });
export async function createUser(data: z.infer<typeof UserSchema>) { ... }
```

### No "any" Types
```typescript
// ❌ DON'T
function processData(data: any) { ... }

// ✅ DO: Use proper types
function processData(data: User[]) { ... }
```

### No Magic Strings
```typescript
// ❌ DON'T
if (user.role === 'admin') { ... }

// ✅ DO: Use constants
if (user.role === UserRole.ADMIN) { ... }
```

## Development Commands

```bash
npm run dev          # Start development server
npm run build        # Production build
npm run db:studio    # Open Drizzle Studio
npm run db:generate  # Generate migrations
npm run db:migrate   # Apply migrations
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript check
```

## Testing

```bash
npm test             # Run all tests
npm run test:watch   # Watch mode
npm run test:coverage # Coverage report
```

## Environment Variables

```
DATABASE_URL=./data/app.db
NEXTAUTH_SECRET=your-secret
NEXTAUTH_URL=http://localhost:3000
```

## Anti-Patterns

1. **No N+1 queries** - Use JOINs or batch queries
2. **No large dependencies** - Keep bundle small
3. **No secrets in code** - Use environment variables
4. **No synchronous database operations in Server Components** - Use proper async patterns
5. **No inline styles** - Use Tailwind classes