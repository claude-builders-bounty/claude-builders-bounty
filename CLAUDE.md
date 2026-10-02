# CLAUDE.md

## Stack & Versions
- **Next.js 15** with App Router
- **SQLite** via better-sqlite3 (for local development) or Turso (for production)
- **TypeScript** with strict mode enabled
- **Tailwind CSS** for styling
- **tRPC** for type-safe API routes
- **Prisma** as the ORM (with Prisma Migrate for schema management)

## Folder Structure
```
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth-related routes (grouped layout)
│   ├── (dashboard)/       # Dashboard routes (grouped layout)
│   ├── api/               # API routes (server actions)
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Homepage
├── components/            # Reusable UI components
│   ├── ui/                # Base UI components (shadcn/ui)
│   ├── forms/             # Form components
│   ├── layout/            # Layout components
│   └── charts/            # Data visualization components
├── lib/                   # Utility libraries
│   ├── db/                # Database connection and utilities
│   ├── auth/              # Authentication utilities
│   ├── utils/             # General utilities
│   └── validators/        # Zod schemas for validation
├── hooks/                 # Custom React hooks
├── prisma/                # Prisma schema and migrations
│   ├── migrations/        # Database migration files
│   └── schema.prisma      # Database schema
├── public/                # Static assets
└── types/                 # TypeScript type definitions
```

## SQL / Migration Conventions
1. **Schema Management**: Use Prisma Migrate for all schema changes
   - Run `npx prisma migrate dev` for development migrations
   - Never manually edit the database or SQLite files directly

2. **Naming Conventions**:
   - Tables: snake_case (e.g., `user_accounts`)
   - Foreign keys: `{table}_id` (e.g., `user_id`)
   - Indexes: `idx_{table}_{column}` (e.g., `idx_users_email`)

3. **Data Access**:
   - Use Prisma Client for all database operations
   - Never write raw SQL queries in application code
   - Use Prisma's transaction API for multi-operation transactions

4. **Environment-Specific Databases**:
   - Development: Use better-sqlite3 for fast local iteration
   - Production: Use Turso for scalable, cloud-hosted SQLite

## Component Patterns
1. **Component Organization**:
   - Create feature-specific folders in `components/`
   - Export components from index files for easier imports
   - Use barrel exports (`export * from './Button'`)

2. **Component Structure**:
   - Use TypeScript interfaces for component props
   - Implement proper prop validation with Zod where applicable
   - Include JSDoc comments for complex components

3. **Styling**:
   - Use Tailwind CSS classes directly (no CSS modules)
   - Create reusable utility classes in `globals.css` for repeated patterns
   - Prefer composition over inheritance for styling

4. **State Management**:
   - Use React hooks for local state
   - Implement custom hooks for complex state logic
   - Consider Zustand for global state that needs to persist across sessions

## What We Don't Do (And Why)
1. **No `pages/` directory**: We use the App Router exclusively (`app/`)

2. **No server components in client folders**: 
   - Keep client components in `app/` with `'use client'`
   - Server components should be in `app/` without the directive

3. **No manual database connection management**:
   - Use the Prisma singleton pattern provided by `@prisma/client`
   - Never create new database connections in request handlers

4. **No global CSS files outside `globals.css`**:
   - Keep styles scoped to components using Tailwind
   - Use CSS variables for theming, not separate CSS files

5. **No API routes without tRPC**:
   - Use tRPC for all client-server communication
   - REST API routes are reserved for third-party integrations only

## Development Commands
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npx prisma migrate dev` - Create and run migrations
- `npx prisma generate` - Generate Prisma client
- `npx prisma studio` - Open Prisma Studio (database GUI)

## Patterns to Follow
1. **Error Handling**:
   - Use tRPC error formatting for API errors
   - Implement proper error boundaries in React components
   - Log errors with appropriate context

2. **Authentication**:
   - Use NextAuth.js or Lucia Auth
   - Implement role-based access control (RBAC)
   - Secure API routes with middleware

3. **Data Fetching**:
   - Use tRPC queries for data fetching
   - Implement proper loading and error states
   - Use React Suspense for better UX

4. **Form Handling**:
   - Use react-hook-form with Zod validation
   - Implement proper form submission handling
   - Use server actions for form submissions where possible

## Anti-patterns to Avoid
1. **Direct DOM manipulation**: Use React's declarative approach
2. **Inline styles**: Use Tailwind CSS classes
3. **Prop drilling**: Use context or custom hooks
4. **Manual type definitions**: Use Prisma-generated types
5. **Hardcoded values**: Use environment variables or configuration
6. **Large components**: Break down into smaller, focused components
7. **Unnecessary re-renders**: Use React.memo and useCallback where appropriate
8. **Mixed concerns**: Keep components focused on a single responsibility