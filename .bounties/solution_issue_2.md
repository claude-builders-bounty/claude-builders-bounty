# Solution for [github/issues_2]: [claude-builders-bounty/claude-builders-bounty] [BOUNTY $75] TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project

- **Reward:** $75.00 USDC
- **Target URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2
- **AI Brain:** gemini-2.5-flash
- **Tokens Used:** 9010 (~$0.0180 USD compute cost)

---

I will create a comprehensive `CLAUDE.md` file tailored for a Next.js 15 App Router and SQLite (using `better-sqlite3` or Turso) SaaS project. This file will be opinionated, covering project structure, naming conventions, database migration rules, development commands, component patterns, and anti-patterns, ensuring it's production-ready and easily understandable by an AI like Claude.

The solution will include:
1.  **Root Cause Analysis**: Understanding the need for a `CLAUDE.md` and how it helps AI and human developers.
2.  **Architecture Design**: Structuring the `CLAUDE.md` to cover all required sections and ensure clarity and conciseness.
3.  **Production-Ready Code/Patch Implementation**: The `CLAUDE.md` file itself.
4.  **Testing Verification Steps**: Instructions on how to test the `CLAUDE.md` with a new project and an AI.

---

### Root Cause Analysis

The core problem this bounty addresses is the need for clear, consistent, and easily digestible project documentation, especially for AI assistants like Claude. In a typical SaaS project, developers often make implicit architectural decisions, follow unwritten conventions, and use various tools without a centralized, opinionated guide. This leads to:

*   **Inconsistent Codebase**: Different developers might use different patterns, naming conventions, or even approaches to database interactions.
*   **Onboarding Challenges**: New team members (human or AI) struggle to understand the project's philosophy and structure quickly.
*   **AI Misinterpretation**: Without explicit guidelines, AI models might make incorrect assumptions about the project's intent, leading to less accurate code suggestions, refactorings, or explanations.
*   **Maintenance Headaches**: Over time, the lack of a guiding document makes the project harder to maintain, debug, and extend.

A `CLAUDE.md` file, specifically designed to be consumed by AI, acts as a "project constitution." It provides a single source of truth for the project's architectural decisions, conventions, and best practices. For AI, it offers a rich context, allowing it to understand the project's "personality" and provide more relevant and accurate assistance. For humans, it serves as a quick reference and a guide for maintaining consistency.

The specific requirements for Next.js 15 App Router and SQLite (better-sqlite3/Turso) mean the `CLAUDE.md` must address the unique aspects of these technologies, such as server components, data fetching strategies, and SQLite-specific migration patterns.

---

### Architecture Design

The `CLAUDE.md` will be structured logically, following the requested sections and adding a few more for completeness and clarity. The design principles are:

1.  **Opinionated**: Every rule will have a clear rationale, avoiding generic statements.
2.  **Concise**: While comprehensive, it will avoid excessive verbosity.
3.  **Actionable**: Provide clear instructions and examples where appropriate.
4.  **AI-Friendly**: Use clear headings, bullet points, code blocks, and direct language to make it easy for AI to parse and understand.
5.  **Greenfield Ready**: Designed to be dropped into a new project with minimal modifications.

**Sections Breakdown:**

*   **Project Overview**: A brief introduction to the project's purpose and core technologies.
*   **Stack & Versions**: Explicitly list key technologies and their preferred versions.
*   **Development Environment & Commands**: Essential setup steps and common development scripts.
*   **Folder Structure**: A detailed, hierarchical view of the project's directory layout with explanations for each major directory.
*   **Naming Conventions**: Rules for files, folders, variables, functions, and components.
*   **Data Layer & SQLite Conventions**:
    *   Database connection and client setup.
    *   Migration strategy (using a tool like `node-sqlite-migrations` or similar).
    *   SQL query patterns.
    *   Schema design principles.
*   **Component Patterns (Next.js App Router)**:
    *   Server Components vs. Client Components usage.
    *   Data fetching strategies.
    *   Error handling.
    *   Loading states.
    *   Form handling.
*   **API Routes (Route Handlers)**: Conventions for `route.ts` files.
*   **Styling**: Preferred styling approach (e.g., Tailwind CSS).
*   **Authentication & Authorization**: High-level approach.
*   **Testing Strategy**: Brief mention of testing tools and philosophy.
*   **What We Don't Do (Anti-Patterns)**: Explicitly list practices to avoid and why.
*   **Deployment**: Brief notes on deployment considerations.
*   **How to Contribute**: A quick guide for developers.

Each section will build upon the previous one, creating a coherent narrative for the project's architecture.

---

### Production-Ready Code/Patch Implementation

Here is the `CLAUDE.md` file.

### File: CLAUDE.md

```markdown
# CLAUDE.md - Project Blueprint: Next.js 15 (App Router) + SQLite SaaS

This document serves as the definitive architectural and development guide for our Next.js 15 (App Router) and SQLite-powered SaaS project. It outlines our core philosophies, conventions, and best practices to ensure consistency, maintainability, and scalability. This guide is opinionated and designed to be easily understood by both human developers and AI assistants like Claude.

## 1. Project Overview

This project is a typical SaaS application built for rapid development and high performance. We leverage Next.js 15's App Router for modern web development, focusing on Server Components for optimal data fetching and rendering. SQLite (via `better-sqlite3` for local dev/testing, or Turso for production) is our chosen database for its simplicity, embedded nature, and excellent performance for many SaaS use cases.

**Core Principles:**
*   **Server-First**: Prioritize Server Components for data fetching and rendering to minimize client-side JavaScript and improve initial load times.
*   **Explicit Data Flow**: Clearly define where data is fetched and how it flows through components.
*   **Convention Over Configuration**: Follow established patterns to reduce cognitive load.
*   **Performance-Oriented**: Optimize for speed and efficiency at every layer.
*   **Maintainability**: Write clear, modular, and testable code.

## 2. Stack & Versions

We adhere to specific versions to maintain stability and leverage the latest features responsibly.

*   **Runtime**: Node.js `^20.x`
*   **Framework**: Next.js `^15.0.0-rc.0` (App Router)
*   **Language**: TypeScript `^5.x`
*   **Database**: SQLite (via `better-sqlite3` `^9.x` for local/dev, or Turso for production)
*   **ORM/Query Builder**: Drizzle ORM `^0.30.x` (preferred for type safety and migrations)
*   **Styling**: Tailwind CSS `^3.x`
*   **Authentication**: NextAuth.js `^5.x` (Auth.js)
*   **Validation**: Zod `^3.x`
*   **Environment Variables**: `dotenv` / Next.js built-in env handling

## 3. Development Environment & Commands

### 3.1. Setup

1.  **Node.js**: Ensure Node.js `^20.x` is installed. We recommend `nvm` for managing Node versions.
2.  **Dependencies**: `pnpm install` (we use pnpm for faster, more efficient dependency management).
3.  **Environment Variables**: Create a `.env.local` file based on `.env.example`.
    *   `DATABASE_URL="file:./sqlite.db"` (for local `better-sqlite3`)
    *   `AUTH_SECRET="<generate-a-strong-secret>"`
    *   `NEXTAUTH_URL="http://localhost:3000"`
4.  **Database Initialization**:
    *   `pnpm db:migrate` (runs pending migrations, creating `sqlite.db` if it doesn't exist).

### 3.2. Common Commands

*   `pnpm dev`: Starts the Next.js development server.
*   `pnpm build`: Builds the application for production.
*   `pnpm start`: Starts the production server (after `pnpm build`).
*   `pnpm lint`: Runs ESLint for code quality checks.
*   `pnpm format`: Formats code using Prettier.
*   `pnpm test`: Runs tests (e.g., Vitest/Playwright).
*   `pnpm db:generate`: Generates Drizzle migration files based on schema changes.
*   `pnpm db:migrate`: Applies pending database migrations.
*   `pnpm db:studio`: Opens Drizzle Studio for database inspection (if configured).

## 4. Folder Structure

Our folder structure is designed for clarity, modularity, and adherence to Next.js App Router conventions.

```
.
├── app/                      # Next.js App Router root
│   ├── (auth)/               # Route group for authentication pages (e.g., /login, /signup)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx        # Auth layout (no nav, etc.)
│   ├── (dashboard)/          # Route group for authenticated user pages (e.g., /dashboard, /settings)
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── settings/
│   │   │   └── page.tsx
│   │   └── layout.tsx        # Dashboard layout (with sidebar, nav)
│   ├── api/                  # Route Handlers for API endpoints
│   │   ├── auth/             # NextAuth.js API routes
│   │   │   └── [...nextauth]/route.ts
│   │   └── webhooks/
│   │       └── stripe/route.ts
│   ├── favicon.ico
│   ├── global-error.tsx      # Global error boundary for the entire app
│   ├── layout.tsx            # Root layout for the entire application
│   ├── loading.tsx           # Root loading UI
│   └── page.tsx              # Root page (e.g., landing page)
├── components/               # Reusable UI components
│   ├── ui/                   # Shadcn/UI or similar primitive components (e.g., Button, Input)
│   │   ├── button.tsx
│   │   └── input.tsx
│   ├── auth/                 # Auth-specific components (e.g., LoginForm, UserMenu)
│   │   └── login-form.tsx
│   ├── dashboard/            # Dashboard-specific components (e.g., Sidebar, Header)
│   │   └── sidebar.tsx
│   └── shared/               # General application components (e.g., Footer, Logo)
│       └── logo.tsx
├── lib/                      # Backend utilities, server-side logic, and shared helpers
│   ├── auth.ts               # NextAuth.js configuration and helpers
│   ├── db.ts                 # Database client initialization and connection
│   ├── actions.ts            # Server Actions (colocated with components or here for global actions)
│   ├── utils.ts              # General utility functions (e.g., formatters, helpers)
│   ├── constants.ts          # Global constants
│   └── types.ts              # Global TypeScript types/interfaces
├── db/                       # Database-related files (schema, migrations)
│   ├── schema.ts             # Drizzle ORM schema definition
│   ├── migrate.ts            # Script to run migrations
│   └── migrations/           # Drizzle migration files
│       ├── 0000_initial_schema.ts
│       └── ...
├── public/                   # Static assets (images, fonts)
├── styles/                   # Global styles (e.g., Tailwind CSS entry point)
│   └── globals.css
├── tests/                    # End-to-end and integration tests (e.g., Playwright)
├── .env.example              # Example environment variables
├── .eslintrc.json            # ESLint configuration
├── next.config.mjs           # Next.js configuration
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json             # TypeScript configuration
└── tailwind.config.ts        # Tailwind CSS configuration
```

**Rationale:**
*   **Route Groups `()`**: Used to organize routes without affecting the URL path, allowing for distinct layouts (e.g., `(auth)` for login/signup, `(dashboard)` for authenticated user areas).
*   **`components/ui`**: Dedicated for UI primitives, often generated by tools like Shadcn/UI, ensuring a consistent design system.
*   **`lib/`**: A clear separation for server-side logic, database interactions, and shared utilities. This keeps `app/` focused on routing and UI.
*   **`db/`**: Centralizes all database-specific concerns, making it easy to manage schema and migrations.

## 5. Naming Conventions

Consistency in naming is crucial for readability and maintainability.

*   **Files & Folders**: `kebab-case` (e.g., `user-profile.tsx`, `login-form.tsx`).
*   **Components**: `PascalCase` (e.g., `UserProfile`, `LoginForm`).
*   **TypeScript Interfaces/Types**: `PascalCase` (e.g., `User`, `ProductData`).
*   **Variables & Functions**: `camelCase` (e.g., `userName`, `fetchUserData`).
*   **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `MAX_ITEMS_PER_PAGE`).
*   **Database Tables**: `snake_case` (plural, e.g., `users`, `products`).
*   **Database Columns**: `snake_case` (e.g., `created_at`, `user_id`).
*   **Migration Files**: `timestamp_description.ts` (e.g., `0001_add_users_table.ts`).

## 6. Data Layer & SQLite Conventions

We use Drizzle ORM for type-safe schema definition, querying, and migrations with SQLite.

### 6.1. Database Client (`lib/db.ts`)

```typescript
// lib/db.ts
import { createClient } from '@libsql/client'; // For Turso
import { drizzle } from 'drizzle-orm/libsql'; // For Turso
// import Database from 'better-sqlite3'; // For better-sqlite3
// import { drizzle } from 'drizzle-orm/better-sqlite3'; // For better-sqlite3
import * as schema from '@/db/schema';
import 'server-only'; // Ensure this file is only used on the server

// For Turso (production)
const client = createClient({
  url: process.env.DATABASE_URL!,
  authToken: process.env.DATABASE_AUTH_TOKEN!,
});
export const db = drizzle(client, { schema });

// For better-sqlite3 (local development)
// const sqlite = new Database(process.env.DATABASE_URL || 'sqlite.db');
// export const db = drizzle(sqlite, { schema });
```
**Rationale:** `server-only` ensures database access is restricted to the server, preventing accidental client-side exposure and promoting secure data fetching patterns. We use conditional imports/exports for Turso vs. `better-sqlite3` based on environment variables or build targets.

### 6.2. Schema Definition (`db/schema.ts`)

Define your database schema using Drizzle ORM.

```typescript
// db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const users = sqliteTable('users', {
  id: text('id').notNull().primaryKey(), // UUIDs for primary keys
  name: text('name'),
  email: text('email').notNull().unique(),
  emailVerified: integer('email_verified', { mode: 'timestamp' }),
  image: text('image'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(CURRENT_TIMESTAMP)`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(CURRENT_TIMESTAMP)`),
});

export const products = sqliteTable('products', {
  id: text('id').notNull().primaryKey(),
  name: text('name').notNull(),
  description: text('description'),
  price: integer('price').notNull(), // Store currency as cents
  userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(CURRENT_TIMESTAMP)`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(CURRENT_TIMESTAMP)`),
});
```
**Rationale:**
*   **UUIDs for IDs**: Use `text` for `id` columns to store UUIDs, providing globally unique identifiers and simplifying merging/replication.
*   **`snake_case`**: Consistent with SQL best practices.
*   **`integer` for Timestamps**: SQLite stores dates as integers (Unix timestamps) or text. We prefer `integer` with `mode: 'timestamp'` for consistency and easier manipulation.
*   **`sql`(CURRENT_TIMESTAMP)**: Use Drizzle's `sql` helper for default timestamps.
*   **`onDelete: 'cascade'`**: Define foreign key constraints with appropriate cascade rules.
*   **Price as `integer`**: Store monetary values as integers (e.g., cents) to avoid floating-point precision issues.

### 6.3. Migrations (`db/migrations/` & `db/migrate.ts`)

We use Drizzle Kit for generating and applying migrations.

1.  **Generate Migration**: After changing `db/schema.ts`, run `pnpm db:generate`. This creates a new migration file in `db/migrations/`.
2.  **Review Migration**: Always review the generated SQL in the migration file to ensure it matches your intent.
3.  **Apply Migration**: Run `pnpm db:migrate` to apply pending migrations to your database.

```typescript
// db/migrate.ts
import { migrate } from 'drizzle-orm/libsql/migrator'; // For Turso
// import { migrate } from 'drizzle-orm/better-sqlite3/migrator'; // For better-sqlite3
import { db } from '@/lib/db';
import path from 'path';

async function runMigrations() {
  try {
    console.log('Starting database migrations...');
    await migrate(db, { migrationsFolder: path.resolve(__dirname, './migrations') });
    console.log('Database migrations completed successfully!');
  } catch (error) {
    console.error('Error during database migrations:', error);
    process.exit(1);
  }
}

runMigrations();
```
**Rationale:**
*   **Automated Generation**: Drizzle Kit simplifies migration creation.
*   **Manual Review**: Crucial to prevent unintended schema changes.
*   **`db/migrate.ts`**: A dedicated script for running migrations, ensuring they are applied consistently.

### 6.4. Data Fetching Patterns

All data fetching should occur on the server, typically within Server Components or Server Actions.

*   **Server Components**: Fetch data directly using `await db.query...` or `await fetch(...)`.
    ```typescript
    // app/dashboard/page.tsx (Server Component)
    import { db } from '@/lib/db';
    import { users } from '@/db/schema';
    import { eq } from 'drizzle-orm';

    export default async function DashboardPage() {
      const allUsers = await db.query.users.findMany();
      // ... render UI
    }
    ```
*   **Server Actions**: For mutations (create, update, delete).
    ```typescript
    // app/dashboard/actions.ts (Server Action)
    'use server';
    import { db } from '@/lib/db';
    import { users } from '@/db/schema';
    import { eq } from 'drizzle-orm';
    import { revalidatePath } from 'next/cache';

    export async function deleteUser(userId: string) {
      await db.delete(users).where(eq(users.id, userId));
      revalidatePath('/dashboard'); // Invalidate cache for relevant path
    }
    ```
**Rationale:**
*   **Security**: Database credentials and logic remain on the server.
*   **Performance**: Data is fetched and rendered on the server, sending only HTML to the client.
*   **Simplicity**: Direct database access without an intermediate API layer for internal data.
*   **`revalidatePath`**: Essential for ensuring UI reflects data changes after mutations.

## 7. Component Patterns (Next.js App Router)

### 7.1. Server Components vs. Client Components

*   **Default to Server Components**: All components are Server Components by default. Use them for:
    *   Data fetching (direct database access, `fetch`).
    *   Rendering static or server-generated content.
    *   Passing data to Client Components as props.
*   **Use Client Components Sparingly**: Only when interactivity or browser APIs are required.
    *   Add `'use client';` at the top of the file.
    *   Use for: state management, event listeners, browser-specific APIs (e.g., `localStorage`), animations.
    *   Pass data down from Server Components.
    *   Keep them small and focused on UI logic.

```typescript
// app/dashboard/page.tsx (Server Component)
import { db } from '@/lib/db';
import { users } from '@/db/schema';
import UserList from '@/components/dashboard/user-list'; // Client Component

export default async function DashboardPage() {
  const usersData = await db.query.users.findMany();
  return (
    <div>
      <h1>Dashboard</h1>
      <UserList users={usersData} /> {/* Pass server-fetched data to client component */}
    </div>
  );
}

// components/dashboard/user-list.tsx (Client Component)
'use client';
import { useState } from 'react';
import type { User } from '@/db/schema'; // Import types

interface UserListProps {
  users: User[];
}

export default function UserList({ users }: UserListProps) {
  const [filter, setFilter] = useState('');
  const filteredUsers = users.filter(user => user.name?.includes(filter));

  return (
    <div>
      <input type="text" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter users" />
      <ul>
        {filteredUsers.map(user => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </div>
  );
}
```
**Rationale:** Minimizes client-side JavaScript, improves performance, and simplifies data management by keeping data fetching close to the database.

### 7.2. Loading States (`loading.tsx`)

Use `loading.tsx` files within route segments to automatically show a loading UI while the segment's data is being fetched.

```typescript
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return <p>Loading dashboard data...</p>;
}
```
**Rationale:** Provides immediate feedback to users, improving perceived performance.

### 7.3. Error Handling (`error.tsx`, `global-error.tsx`)

*   **`error.tsx`**: Catches errors for a specific route segment and displays a fallback UI.
    ```typescript
    // app/dashboard/error.tsx
    'use client'; // Error boundaries must be Client Components

    import { useEffect } from 'react';

    export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void; }) {
      useEffect(() => {
        console.error(error);
      }, [error]);

      return (
        <div>
          <h2>Something went wrong in the dashboard!</h2>
          <button onClick={() => reset()}>Try again</button>
        </div>
      );
    }
    ```
*   **`global-error.tsx`**: Catches errors for the entire application, including the root `layout.tsx`.
    ```typescript
    // app/global-error.tsx
    'use client';

    export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void; }) {
      return (
        <html>
          <body>
            <h2>Something went wrong globally!</h2>
            <button onClick={() => reset()}>Try again</button>
          </body>
        </html>
      );
    }
    ```
**Rationale:** Graceful degradation, preventing entire application crashes and providing recovery options.

### 7.4. Forms & Server Actions

All form submissions should leverage Next.js Server Actions for mutations.

```typescript
// app/settings/profile-form.tsx (Client Component, but uses Server Action)
'use client';
import { useFormStatus } from 'react-dom';
import { updateUserProfile } from './actions'; // Server Action

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Saving...' : 'Save Profile'}
    </button>
  );
}

export default function ProfileForm({ user }: { user: { id: string; name: string; email: string } }) {
  return (
    <form action={updateUserProfile}>
      <input type="hidden" name="id" value={user.id} />
      <input type="text" name="name" defaultValue={user.name} />
      <input type="email" name="email" defaultValue={user.email} />
      <SubmitButton />
    </form>
  );
}

// app/settings/actions.ts (Server Action)
'use server';
import { db } from '@/lib/db';
import { users } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

export async function updateUserProfile(formData: FormData) {
  const id = formData.get('id') as string;
  const name = formData.get('name') as string;
  const email = formData.get('email') as string;

  // Basic validation (use Zod for robust validation)
  if (!name || !email) {
    throw new Error('Name and email are required.');
  }

  await db.update(users)
    .set({ name, email, updatedAt: new Date() })
    .where(eq(users.id, id));

  revalidatePath('/settings');
  redirect('/settings?success=true'); // Redirect after successful mutation
}
```
**Rationale:** Server Actions provide a secure, performant, and type-safe way to handle mutations without building explicit API routes for every form. `useFormStatus` provides pending states for UI feedback.

## 8. API Routes (Route Handlers)

Use Route Handlers (`route.ts`) for external APIs, webhooks, or when a traditional REST endpoint is genuinely needed (e.g., for third-party integrations). For internal data mutations, prefer Server Actions.

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: NextRequest) {
  const body = await req.text();
  const signature = headers().get('stripe-signature');

  if (!signature) {
    return new Response('No Stripe signature header', { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err: any) {
    console.error(`Webhook Error: ${err.message}`);
    return new Response(`Webhook Error: ${err.message}`, { status: 400 });
  }

  // Handle the event
  switch (event.type) {
    case 'customer.subscription.created':
      // ... handle subscription creation
      break;
    // ... other event types
    default:
      console.warn(`Unhandled event type ${event.type}`);
  }

  return NextResponse.json({ received: true });
}
```
**Rationale:** Clear separation of concerns. Route Handlers are for public/external APIs, while Server Actions are for internal, authenticated mutations.

## 9. Styling

We use **Tailwind CSS** for utility-first styling.

*   **Configuration**: `tailwind.config.ts` for theme, plugins, etc.
*   **Global Styles**: `styles/globals.css` for `@tailwind` directives and any base styles.
*   **Component Styling**: Apply Tailwind classes directly in JSX.
*   **`clsx` / `cn`**: Use `clsx` (or a custom `cn` utility) for conditionally joining class names.
*   **Shadcn/UI**: Preferred for pre-built, customizable UI components that integrate seamlessly with Tailwind.

## 10. Authentication & Authorization

We use **NextAuth.js (Auth.js)** for authentication.

*   **Configuration**: `lib/auth.ts` for providers, callbacks, and database adapter.
*   **API Route**: `app/api/auth/[...nextauth]/route.ts` handles all authentication flows.
*   **Session Management**: Use `getServerSession` (or `auth()` from `next-auth/react` in Server Components) to access session data on the server.
*   **Client-side**: Use `useSession` hook for client-side session access.
*   **Authorization**: Implement authorization checks on the server (e.g., in Server Actions or Route Handlers) by checking the user's role or ID against the requested resource.

## 11. Testing Strategy

*   **Unit Tests**: Vitest for isolated component and utility function testing.
*   **Integration Tests**: Vitest for testing interactions between multiple units (e.g., database functions, API handlers).
*   **End-to-End (E2E) Tests**: Playwright for simulating user flows in a real browser environment.
*   **Database Seeding**: Use a dedicated script (`db/seed.ts`) for populating the database with test data.

## 12. What We Don't Do (Anti-Patterns)

These are practices to avoid, along with the reasons why.

*   **❌ Client-side Data Fetching (unless necessary)**: Avoid `useEffect` with `fetch` in Client Components for initial data loads.
    *   **Why**: Leads to waterfalls, slower initial page loads, and requires an API layer for data that could be fetched directly on the server.
*   **❌ Direct Database Access in Client Components**: Never import `lib/db.ts` or similar database clients into a Client Component.
    *   **Why**: Exposes sensitive database credentials and logic to the client, creating severe security vulnerabilities.
*   **❌ Over-reliance on `useState` / `useEffect` for global state**: For global state, prefer React Context or a lightweight state management library (e.g., Zustand) if truly necessary, but first, consider if the state can be managed on the server or passed down via props.
    *   **Why**: Can lead to prop drilling, performance issues, and complex state management logic. Server Components often reduce the need for complex client-side state.
*   **❌ Generic API Routes for CRUD**: Avoid creating `/api/users`, `/api/products` REST endpoints for internal data manipulation.
    *   **Why**: Server Actions provide a more integrated, type-safe, and performant way to handle mutations directly from components without an explicit API layer. Reserve API routes for external integrations.
*   **❌ Manual SQL String Concatenation**: Never build SQL queries by concatenating user input directly.
    *   **Why**: High risk of SQL injection attacks. Always use Drizzle ORM's safe query builders or parameterized queries.
*   **❌ Large, Monolithic Client Components**: Keep Client Components small, focused, and responsible for specific interactive UI elements.
    *   **Why**: Improves performance by reducing client-side JavaScript bundles and makes components easier to reason about and test.
*   **❌ Unhandled Errors**: Always implement `error.tsx` and `global-error.tsx` to provide graceful error handling.
    *   **Why**: Prevents bad user experience and provides a clear path for debugging.
*   **❌ Hardcoding Sensitive Information**: Never hardcode API keys, secrets, or database credentials directly in the code.
    *   **Why**: Security risk. Use environment variables (`.env.local`, `process.env`).
*   **❌ Inconsistent Naming**: Mixing `camelCase`, `kebab-case`, `PascalCase` arbitrarily.
    *   **Why**: Reduces readability and increases cognitive load for developers.

## 13. Deployment

*   **Platform**: Vercel (for Next.js) and Turso (for SQLite) are the recommended deployment platforms.
*   **Environment Variables**: Ensure all necessary environment variables (e.g., `DATABASE_URL`, `DATABASE_AUTH_TOKEN`, `AUTH_SECRET`, `NEXTAUTH_URL`) are configured in the deployment environment.
*   **Build Process**: The `pnpm build` command should run automatically on deployment.
*   **Migrations**: Ensure migrations are run as part of the deployment process (e.g., a pre-build step or a dedicated deployment hook).

## 14. How to Contribute

1.  **Fork** the repository.
2.  **Clone** your fork.
3.  **Install dependencies**: `pnpm install`.
4.  **Create a new branch**: `git checkout -b feature/your-feature-name`.
5.  **Make changes**: Adhere to the conventions outlined in this `CLAUDE.md`.
6.  **Run tests**: `pnpm test`.
7.  **Format & Lint**: `pnpm format` and `pnpm lint`.
8.  **Commit changes**: Write clear, concise commit messages.
9.  **Push to your branch**.
10. **Open a Pull Request** to the `main` branch, describing your changes.

---
```

---

### Testing Verification Steps

To verify that the `CLAUDE.md` is usable without modification on a greenfield project and that Claude Code understands the context, follow these steps:

1.  **Create a New Next.js Project**:
    ```bash
    pnpm create next-app my-saas-app --ts --eslint --tailwind --app --src-dir --use-pnpm
    cd my-saas-app
    ```
    *Self-correction*: The prompt specifies Next.js 15, which is currently in RC. The `create next-app` command might install Next.js 14 by default. After creation, manually update `next` and `react` dependencies in `package.json` to their latest RC versions (e.g., `^15.0.0-rc.0` for `next`, `^19.0.0-rc-0` for `react` and `react-dom`).

2.  **Install Drizzle ORM and SQLite Dependencies**:
    ```bash
    pnpm add drizzle-orm better-sqlite3 @libsql/client
    pnpm add -D drizzle-kit
    ```

3.  **Integrate `CLAUDE.md`**:
    *   Create a file named `CLAUDE.md` in the root of the `my-saas-app` project.
    *   Paste the entire content of the `CLAUDE.md` provided above into this new file.

4.  **Set up Basic Project Structure (as per `CLAUDE.md`)**:
    *   Create the `db` folder: `mkdir db`
    *   Create `db/schema.ts`:

---

### Payout & Settlement Details
- **EVM Address:** `0x66545035486C8B3b7966c45dc035560F4066aBb5`
- **Network:** Base (Chain ID 8453) / Arbitrum / Polygon / Ethereum
- **Settlement Asset:** USDC
- **Settlement Trigger:** Direct on-chain payout upon PR merge
