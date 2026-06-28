# CLAUDE.md — Next.js + SQLite Project Template

> This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Next.js application with SQLite database integration using better-sqlite3 for synchronous, high-performance database operations.

## Development Commands

```bash
# Install dependencies
npm install

# Development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Type checking
npm run type-check

# Database migrations
npm run db:migrate

# Seed database (development)
npm run db:seed
```

## Architecture

### Tech Stack
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (strict mode)
- **Database**: SQLite via better-sqlite3
- **Styling**: Tailwind CSS
- **Testing**: Vitest + React Testing Library

### Directory Structure

```
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   └── [resource]/
│   │       └── route.ts   # REST endpoints
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   └── [feature]/        # Feature-specific components
├── lib/                  # Shared utilities
│   ├── db.ts            # Database connection & queries
│   ├── migrations.ts    # Migration runner
│   └── utils.ts         # Helper functions
├── migrations/           # SQL migration files
│   └── 001_initial.sql
├── types/               # TypeScript type definitions
└── tests/               # Test files (mirror app/ structure)
```

### Database Layer

**Connection**: `lib/db.ts`
- Uses better-sqlite3 for synchronous operations
- Connection pooling via singleton pattern
- Prepared statements for all queries (SQL injection prevention)

**Query Pattern**:
```typescript
import { db } from '@/lib/db';

// SELECT
const users = db.prepare('SELECT * FROM users WHERE active = ?').all(true);

// INSERT
const insert = db.prepare('INSERT INTO users (name, email) VALUES (?, ?)');
const result = insert.run(name, email);

// UPDATE
db.prepare('UPDATE users SET name = ? WHERE id = ?').run(newName, id);

// DELETE
db.prepare('DELETE FROM users WHERE id = ?').run(id);
```

**Migrations**: 
- Located in `migrations/` directory
- Run sequentially by filename (001_, 002_, etc.)
- Executed via `npm run db:migrate`
- Never modify existing migrations — create new ones

### API Routes

Follow RESTful conventions in `app/api/`:

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  const users = db.prepare('SELECT * FROM users').all();
  return NextResponse.json(users);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const insert = db.prepare('INSERT INTO users (name, email) VALUES (?, ?)');
  const result = insert.run(body.name, body.email);
  return NextResponse.json({ id: result.lastInsertRowid }, { status: 201 });
}
```

### Environment Variables

Create `.env.local` (never commit):

```bash
DATABASE_PATH=./data/app.db
NODE_ENV=development
```

Production: Set via hosting platform (Vercel, Railway, etc.)

## Code Style & Conventions

### TypeScript
- Strict mode enabled
- No `any` types — use `unknown` and narrow
- Prefer interfaces over types for object shapes
- Use `type` for unions, intersections, utilities

### React Components
- Functional components only (no class components)
- Props: Define interface at top of file
- Hooks: Custom hooks in `lib/hooks/`
- Server Components: Default (no `'use client'` unless needed)
- Client Components: Add `'use client'` directive at top

### Naming
- Files: kebab-case (`user-profile.tsx`)
- Components: PascalCase (`UserProfile`)
- Functions: camelCase (`getUserById`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)
- Database tables: snake_case (`user_profiles`)

### Error Handling
- API routes: Return appropriate HTTP status codes
- Use try-catch for database operations
- Log errors with context (use `console.error`)
- Never expose internal errors to client

## Testing

### Unit Tests
```typescript
// tests/lib/db.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { db } from '@/lib/db';

describe('Database', () => {
  beforeEach(() => {
    db.exec('DELETE FROM users');
  });

  it('should insert user', () => {
    const insert = db.prepare('INSERT INTO users (name) VALUES (?)');
    const result = insert.run('Test User');
    expect(result.lastInsertRowid).toBeDefined();
  });
});
```

### Component Tests
```typescript
// tests/components/UserCard.test.tsx
import { render, screen } from '@testing-library/react';
import { UserCard } from '@/components/UserCard';

describe('UserCard', () => {
  it('renders user name', () => {
    render(<UserCard name="John Doe" email="john@example.com" />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

## Common Tasks

### Adding a New Feature

1. **Database**: Create migration in `migrations/`
2. **Types**: Define interfaces in `types/`
3. **API**: Create route in `app/api/[feature]/route.ts`
4. **Components**: Build UI in `components/[feature]/`
5. **Tests**: Add tests mirroring file structure
6. **Docs**: Update this CLAUDE.md if adding new patterns

### Debugging

```bash
# Enable debug logging
DEBUG=app:* npm run dev

# Check database
sqlite3 data/app.db ".tables"
sqlite3 data/app.db "SELECT * FROM users LIMIT 5;"

# View build errors
npm run build 2>&1 | grep -i error
```

## Deployment

### Vercel (Recommended)
```bash
npm i -g vercel
vercel
```

Environment variables: Set in Vercel dashboard

### Docker
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Gotchas

1. **better-sqlite3 is synchronous** — Don't use in serverless functions with cold starts (use libsql or turso instead)
2. **Migrations are one-way** — Never edit past migrations
3. **Server Components by default** — Add `'use client'` only when using hooks/browser APIs
4. **SQLite file locking** — Only one writer at a time (use WAL mode for better concurrency)
5. **No ORM** — Write raw SQL (prevents abstraction leaks, better performance)

## Security Checklist

- [ ] All queries use prepared statements (no string interpolation)
- [ ] Input validation on API routes (use zod or similar)
- [ ] Environment variables not committed
- [ ] Database file not in public directory
- [ ] CORS configured if exposing API
- [ ] Rate limiting on public endpoints

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [better-sqlite3](https://github.com/WiseLibs/better-sqlite3)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
