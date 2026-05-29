# CLAUDE.md - Next.js 15 App Router + SQLite SaaS Project Guidelines

This document provides production-level guidelines for developing SaaS applications using Next.js 15 App Router with SQLite (better-sqlite3 or Turso).

## Project Structure

```
├── src/
│   ├── app/                 # App Router pages and layouts
│   │   ├── (auth)/          # Auth routes (login, register, etc.)
│   │   ├── (dashboard)/     # Protected routes
│   │   ├── api/             # API routes (Route Handlers)
│   │   └── layout.tsx       # Root layout
│   ├── components/          # Shared React components
│   │   ├── ui/              # Shadcn/ui or custom UI components
│   │   └── layout/          # Layout components (header, footer, etc.)
│   ├── lib/                 # Utility functions and shared logic
│   │   ├── db/              # Database connection and utilities
│   │   ├── auth/            # Authentication helpers
│   │   └── utils/           # General utilities
│   ├── hooks/               # Custom React hooks
│   ├── types/               # TypeScript type definitions
│   └── styles/              # CSS and Tailwind configuration
├── prisma/                  # Prisma schema and migrations (if using Prisma with SQLite)
│   ├── schema.prisma
│   └── migrations/
├── scripts/                 # Database scripts and utilities
│   ├── migrate.ts
│   └── seed.ts
├── public/                  # Static assets
├── tests/                   # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .github/                 # GitHub Actions and issue templates
├── docs/                    # Documentation
├── .env.example             # Environment variables template
├── .eslintrc.js             # ESLint configuration
├── .prettierrc              # Prettier configuration
├── next.config.js           # Next.js configuration
├── package.json
├── README.md
└── CLAUDE.md                # This file
```

## Naming Conventions

### Files and Directories
- Use `kebab-case` for directories and files (e.g., `user-profile.tsx`, `api-utils.ts`)
- Use `PascalCase` for React components (e.g., `UserProfile.tsx`, `DataTable.tsx`)
- Use `camelCase` for variables, functions, and TypeScript interfaces/types
- Use `UPPER_SNAKE_CASE` for environment variables and constants

### Database
- Table names: `snake_case` (e.g., `users`, `user_profiles`, `subscription_plans`)
- Column names: `snake_case` (e.g., `user_id`, `email_address`, `created_at`)
- Primary keys: `id` (integer auto-increment) or `uuid` (for distributed systems)
- Foreign keys: `{table_name}_id` (e.g., `user_id`, `plan_id`)
- Indexes: `idx_{table_name}_{column_name}` (e.g., `idx_users_email`)
- Constraints: Use descriptive names (e.g., `uk_users_email` for unique key)

### API Routes (App Router)
- Route handlers: Use `route.ts` or `route.js` files inside API route directories
- Segment naming: Use `kebab-case` for dynamic segments (e.g., `[userId]` becomes `[userId]` folder)
- Route groups: Use parentheses for route groups that don't affect URL path (e.g., `(auth)`)

## DB Migration Rules

### General Principles
1. **Never modify existing migrations** - Create new migrations for changes
2. **Always backup production data** before applying migrations
3. **Test migrations** on a copy of production data in staging
4. **Use transactions** for multi-table changes
5. **Document breaking changes** in migration comments

### Migration Workflow
1. Generate migration script using your preferred tool (Prisma, drizzle, or raw SQL)
2. Review the generated SQL for correctness
3. Apply to development database first
4. Test application functionality
5. Apply to staging database
6. Monitor for issues
7. Apply to production during low-traffic period
8. Verify application functionality post-migration

### SQLite Specific Considerations
- SQLite has limited `ALTER TABLE` support - consider creating new tables and copying data
- Use `PRAGMA foreign_keys=ON;` to enforce foreign key constraints
- For Turso: Use `turso db shell` to apply migrations
- For better-sqlite3: Use transactions and prepare statements

### Migration Tools
- **Prisma**: Use `prisma migrate dev` and `prisma migrate deploy`
- **Drizzle ORM**: Use `drizzle-kit generate` and `drizzle-kit migrate`
- **Raw SQL**: Number migration files sequentially (e.g., `001_init.sql`, `002_add_user_index.sql`)

## Development Commands

### Setup
```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Initialize database (if using Prisma)
npx prisma generate
npx prisma db push  # For development only
# OR
npm run db:generate   # For drizzle
npm run db:push       # For drizzle

# Seed initial data (optional)
npm run seed
```

### Development
```bash
# Start development server
npm run dev

# Start with Turso (if applicable)
TURSO_DATABASE_URL=... npm run dev

# Run database studio (Prisma)
npx prisma studio

# Run migrations (Prisma)
npx prisma migrate dev --name init

# Run migrations (Drizzle)
npm run db:migrate
```

### Testing
```bash
# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run linting
npm run lint

# Run type checking
npm run type-check

# Run end-to-end tests (Playwright/Cypress)
npm run test:e2e
```

### Production
```bash
# Build for production
npm run build

# Start production server
npm start

# Apply production migrations (Prisma)
npx prisma migrate deploy

# Apply production migrations (Drizzle)
npm run db:migrate:prod
```

## Recommended Patterns

### Database Access
1. **Use a singleton database connection** for better-sqlite3:
   ```typescript
   // lib/db/sqlite.ts
   import Database from 'better-sqlite3';
   
   const sqlite = new Database(process.env.DATABASE_URL!, {});
   export default sqlite;
   ```
   
2. **For Turso**, use the official SDK with connection pooling:
   ```typescript
   // lib/db/turso.ts
   import { Client } from '@turso/libsql';
   
   const client = new Client({
     url: process.env.TURSO_DATABASE_URL!,
     authToken: process.env.TURSO_AUTH_TOKEN!
   });
   
   export const db = client.execute;
   ```

3. **Abstract data access** with a repository pattern:
   ```typescript
   // lib/repositories/userRepository.ts
   import db from '@/lib/db/sqlite';
   
   export class UserRepository {
     async findById(id: number) {
       return db.get('SELECT * FROM users WHERE id = ?', [id]);
     }
     
     async create(user: Omit<User, 'id'>) {
       const result = db.run(
         'INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)',
         [user.email, user.name, user.password_hash]
       );
       return { id: result.lastInsertRowid, ...user };
     }
   }
   ```

### Authentication
1. **Use next-auth** with SQLite adapter for session management
2. **Implement proper password hashing** using bcrypt or argon2
3. **Use HTTP-only cookies** for token storage
4. **Implement rate limiting** on authentication endpoints
5. **Validate all inputs** using Zod or Joi

### Error Handling
1. **Create centralized error handling** middleware for API routes
2. **Log errors** to a monitoring service (Sentry, LogRocket)
3. **Return appropriate HTTP status codes** (400, 401, 403, 404, 500)
4. **Don't expose internal errors** to clients in production
5. **Use try/catch** for asynchronous operations

### Performance Optimization
1. **Use database indexing** for frequently queried columns
2. **Implement pagination** for large datasets (limit/offset or keyset pagination)
3. **Use caching** (Redis or in-memory) for frequently accessed data
4. **Optimize images** using Next.js Image component
5. **Leverage server components** for data fetching to reduce client-side JavaScript
6. **Use streaming** for large responses with `async` generators

### Security
1. **Use helmet** or equivalent headers middleware
2. **Implement CSP** (Content Security Policy) headers
3. **Validate and sanitize** all user inputs
4. **Use parameterized queries** to prevent SQL injection
5. **Implement proper CORS** policies
6. **Regularly update dependencies** using `npm audit` and `npm update`
7. **Use environment variables** for secrets (never hardcode)

### Code Organization
1. **Separate concerns** - keep UI, business logic, and data access layers distinct
2. **Use custom hooks** for encapsulating reusable logic
3. **Create reusable components** in `/components/ui`
4. **Use TypeScript strict mode** for better type safety
5. **Implement feature flags** for gradual rollouts
6. **Use constants** for magic strings and numbers

## Anti-Patterns to Avoid

### Database
1. **Don't use `SELECT *`** in production queries - specify exact columns needed
2. **Avoid N+1 queries** - use JOINs or batch loading techniques
3. **Don't store large binary data** in SQLite - use object storage (S3, Cloudinary) and store references
4. **Avoid complex transactions** that lock tables for extended periods
5. **Don't ignore database constraints** - let the database enforce data integrity
6. **Avoid string concatenation** for SQL queries - use parameterized statements

### Next.js/App Router
1. **Don't fetch data in client components** when it can be done on the server
2. **Avoid excessive use of `useState` and `useEffect`** for data fetching - use server components or SWR/react-query
3. **Don't block the main thread** with heavy computations - use Web Workers or serverless functions
4. **Avoid nested layouts** that cause unnecessary re-renders
5. **Don't ignore loading and error states** - implement proper UI skeletons and error boundaries
6. **Avoid using `dangerouslySetInnerHTML`** unless absolutely necessary and sanitized

### Performance
1. **Don't load all data at once** - implement pagination or infinite scrolling
2. **Avoid large bundle sizes** - use dynamic import() and code splitting
3. **Don't ignore image optimization** - always use Next.js Image component with proper sizing
4. **Avoid synchronous operations** in API routes that block the event loop
5. **Don't forget to close database connections** in long-running processes

### Security
1. **Don't store secrets** in client-side code or public repositories
2. **Avoid hardcoding** API keys or database credentials
3. **Don't disable security features** for convenience (CORS, CSP, etc.)
4. **Avoid using eval()** or similar dangerous functions
5. **Don't ignore security warnings** from dependencies
6. **Avoid using outdated cryptographic algorithms** (MD5, SHA1)

### Maintenance
1. **Don't ignore TypeScript errors** - fix them or provide proper type definitions
2. **Avoid duplicating code** - extract reusable functions and components
3. **Don't leave commented-out code** in the repository - use version control
4. **Avoid inconsistent code formatting** - use Prettier and ESLint
5. **Don't skip code reviews** - even for small changes
6. **Avoid hardcoding business logic** in UI components - keep it in services or hooks

## Optional: Example schema.sql

Below is an example SQLite schema for a basic SaaS application with users, subscriptions, and teams:

```sql
-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token TEXT,
    reset_token TEXT,
    reset_token_expires DATETIME,
    role TEXT DEFAULT 'user', -- user, admin, super_admin
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- User profiles (optional, for extended user info)
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    avatar_url TEXT,
    bio TEXT,
    website TEXT,
    location TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Subscription plans
CREATE TABLE IF NOT EXISTS subscription_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    price_cents INTEGER NOT NULL, -- Stored in cents to avoid floating point issues
    interval TEXT NOT NULL CHECK (interval IN ('day', 'week', 'month', 'year')),
    features TEXT, -- JSON string of features
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- User subscriptions
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('trialing', 'active', 'canceled', 'past_due', 'unpaid')),
    current_period_start DATETIME NOT NULL,
    current_period_end DATETIME NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);

-- Indexes for subscriptions
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id