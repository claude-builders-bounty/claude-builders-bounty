# CLAUDE.md — Next.js + SQLite Project Template
# =============================================
# Drop this file in your project root. Claude Code auto-reads it every session.
# It defines your stack, conventions, commands, and architecture.

## Project Overview
- **Stack:** Next.js 15 (App Router) + SQLite (better-sqlite3) + Tailwind CSS + TypeScript
- **Purpose:** [Describe your app in one sentence]
- **Deployment:** Vercel (frontend) + SQLite file on persistent volume

## Commands
```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint + Prettier check
npm run lint:fix     # Auto-fix lint issues
npm run db:init      # Initialize SQLite database
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed with sample data
npm test             # Run all tests (vitest)
npm test -- --watch  # Watch mode
```

## Architecture

### Directory Structure
```
src/
├── app/            # Next.js App Router pages & API routes
│   ├── api/        # API route handlers
│   ├── (auth)/     # Auth-grouped routes
│   └── layout.tsx  # Root layout
├── components/     # Reusable React components
│   ├── ui/         # Primitive UI (buttons, inputs, etc.)
│   └── features/   # Feature-specific components
├── lib/            # Shared utilities
│   ├── db.ts       # SQLite connection singleton
│   ├── auth.ts     # Auth helpers
│   └── utils.ts    # General utilities
├── types/          # TypeScript type definitions
└── styles/         # Global styles
database/
├── schema.sql      # SQLite schema definition
├── migrations/     # Numbered migration files
└── seed.sql        # Seed data
```

### Database (SQLite via better-sqlite3)
```typescript
// src/lib/db.ts — Singleton connection
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.DATABASE_PATH || './database/data.db';
let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(path.resolve(DB_PATH));
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}

// Use in API routes:
// import { getDb } from '@/lib/db';
// const db = getDb();
// const users = db.prepare('SELECT * FROM users').all();
```

### API Route Pattern
```typescript
// src/app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getDb } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    const db = getDb();
    const users = db.prepare('SELECT id, name, email FROM users').all();
    return NextResponse.json({ users });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch users' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const db = getDb();
    const stmt = db.prepare('INSERT INTO users (name, email) VALUES (?, ?)');
    const result = stmt.run(body.name, body.email);
    return NextResponse.json({ id: result.lastInsertRowid }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create user' }, { status: 500 });
  }
}
```

## Coding Conventions

### TypeScript
- Strict mode enabled. No `any` unless absolutely necessary.
- Use `interface` for object shapes, `type` for unions/utilities.
- API responses must have typed interfaces.

### React Components
- Server Components by default. Add `'use client'` only when needed.
- One component per file. File name = component name (PascalCase).
- Props interface exported: `export interface ButtonProps { ... }`

### Naming
- Files: kebab-case (`user-profile.tsx`)
- Components: PascalCase (`UserProfile`)
- Functions: camelCase (`getUserById`)
- Database tables: snake_case, plural (`user_sessions`)
- API routes: plural nouns (`/api/users`, `/api/posts`)

### Error Handling
- API routes: try/catch with typed error responses
- Database: use transactions for multi-statement operations
```typescript
const db = getDb();
const tx = db.transaction(() => {
  db.prepare('INSERT INTO users ...').run(...);
  db.prepare('INSERT INTO profiles ...').run(...);
});
tx(); // Rolls back on any error
```

### Testing
- Vitest for unit/integration tests
- Test file next to source: `utils.test.ts`
- Database tests use in-memory SQLite:
```typescript
import Database from 'better-sqlite3';
const db = new Database(':memory:');
```

## Environment Variables
```env
DATABASE_PATH=./database/data.db
JWT_SECRET=xxx          # For auth tokens
NEXT_PUBLIC_APP_URL=    # Public URL
```

## Common Tasks

### Adding a new database table
1. Create migration: `database/migrations/003_add_table_name.sql`
2. Update `database/schema.sql`
3. Create TypeScript types in `src/types/`
4. Add API routes in `src/app/api/table-name/`

### Adding a new page
1. Create `src/app/page-name/page.tsx`
2. If it needs data, fetch in the Server Component:
```typescript
import { getDb } from '@/lib/db';
export default async function Page() {
  const db = getDb();
  const data = db.prepare('SELECT ...').all();
  return <div>{/* render */}</div>;
}
```

### Adding auth to a route
```typescript
import { verifyToken } from '@/lib/auth';
export async function GET(request: NextRequest) {
  const user = await verifyToken(request);
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  // ... authorized logic
}
```

## Dependencies
```json
{
  "next": "^15.0.0",
  "better-sqlite3": "^11.0.0",
  "typescript": "^5.5.0",
  "tailwindcss": "^3.4.0",
  "vitest": "^2.0.0"
}
```

## Notes
- SQLite WAL mode for concurrent reads. Single writer at a time — batch writes.
- Avoid `SELECT *` in production queries. List columns explicitly.
- API routes are Edge-compatible by default. better-sqlite3 requires Node runtime — set `export const runtime = 'nodejs'` when using the database.
- This file evolves with the project. Update it when conventions change.
