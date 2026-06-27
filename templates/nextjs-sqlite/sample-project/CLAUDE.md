# CLAUDE.md — Next.js + SQLite SaaS Project

> This file provides Claude Code with context about your project structure, conventions, and patterns.

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x
- **Database**: SQLite via better-sqlite3
- **ORM**: Drizzle ORM
- **Styling**: Tailwind CSS 4.x
- **State Management**: React 19 with Server Components
- **Authentication**: NextAuth.js v5
- **Testing**: Vitest + React Testing Library

## Project Structure

```
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── api/
│   │   ├── auth/
│   │   └── trpc/
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/
│   ├── forms/
│   └── layouts/
├── lib/
│   ├── db/
│   │   ├── index.ts
│   │   ├── schema.ts
│   │   └── migrations/
│   ├── auth.ts
│   ├── trpc/
│   └── utils.ts
├── hooks/
├── types/
└── public/
```

## Dev Commands

```bash
npm run dev              # Start dev server
npm run build            # Build for production
npm run db:generate      # Generate migration files
npm run db:migrate       # Run migrations
npm run db:studio        # Open Drizzle Studio
npm run test             # Run tests
npm run lint             # Run ESLint
npm run typecheck        # Run TypeScript check
```

## Key Patterns

### Server Components (Default)
```typescript
export default async function Page() {
  const data = await fetchData();
  return <div>{data}</div>;
}
```

### Client Components (When Needed)
```typescript
'use client';
export function InteractiveComponent() {
  const [state, setState] = useState();
  return <button onClick={() => setState(!state)}>Toggle</button>;
}
```

### Database Queries
```typescript
// Always use Drizzle query builder
const users = await db.select().from(users).where(eq(users.email, email));
```

## Rules

1. **Server Components by Default** - Only add 'use client' when needed
2. **Type Safety** - Always use TypeScript, validate with Zod
3. **Database Safety** - Use parameterized queries (Drizzle handles this)
4. **Error Handling** - Use Error Boundaries for components
5. **Colocation** - Keep related files together