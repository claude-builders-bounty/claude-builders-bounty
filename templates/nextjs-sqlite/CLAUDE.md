# CLAUDE.md — Context Rules for Next.js + SQLite (Drizzle ORM)

## Overview & Architecture
This project is built on **Next.js (App Router)** paired with a local or embedded **SQLite** database using **Drizzle ORM**. All agentic and human developers should adhere strictly to the following architectural patterns and conventions.

---

## Next.js App Router Guidelines

1. **Server Components by Default**:
   - Every component in `app/` is a React Server Component (RSC) unless explicitly marked with `'use client'`.
   - Fetch database records directly in Server Components using Drizzle queries.
   - Keep client-side state contained in isolated leaf components.

2. **Server Actions (`'use server'`)**:
   - Colocate mutation logic in server action files (e.g., `app/actions/*.ts` or within route directories).
   - Always validate incoming client inputs with schema libraries (e.g., `zod`) before running database queries.
   - Return structured results: `{ success: true, data?: T }` or `{ success: false, error: string }`.
   - Use `revalidatePath()` or `revalidateTag()` to purge relevant caches after mutations.

3. **Routing & Layouts**:
   - Organize domain routes cleanly using route groups `(group)` where appropriate.
   - Use `loading.tsx` for Suspense boundaries and `error.tsx` for graceful client fault isolation.

---

## Drizzle ORM + SQLite Guidelines

1. **Schema Definition**:
   - Maintain all schema definitions in `src/db/schema/` or `db/schema.ts`.
   - Use SQLite column primitives provided by `drizzle-orm/sqlite-core` (e.g., `sqliteTable`, `text`, `integer`, `real`).
   - Use integer timestamps for dates: `integer('created_at', { mode: 'timestamp' })`.
   - Define foreign key relations with cascading rules where required.

2. **Database Client Singleton**:
   - Instantiate the SQLite connection singleton in `src/db/index.ts` using `better-sqlite3` or `@libsql/client`.
   - Ensure the database connection handles hot reload gracefully in Next.js development mode using `globalThis`.

3. **Migration Workflow**:
   - Do not edit raw migration SQL files manually unless resolving a merge conflict.
   - Generate migration files: `npm run db:generate`
   - Apply migrations: `npm run db:migrate`
   - Use `npm run db:push` only during early prototyping.

---

## TypeScript Strict Mode & Coding Standards

1. **Strict Type Safety**:
   - TypeScript `strict` mode is enabled. No implicit `any` types.
   - Infer types directly from Drizzle schemas using `$inferSelect` and `$inferInsert`:
     ```ts
     import { type InferSelectModel, type InferInsertModel } from 'drizzle-orm';
     import { users } from '@/db/schema';

     export type User = InferSelectModel<typeof users>;
     export type NewUser = InferInsertModel<typeof users>;
     ```
2. **Naming Conventions**:
   - PascalCase for React components and TypeScript interfaces/types.
   - camelCase for functions, variables, and Server Actions.
   - snake_case for SQLite database column names.
   - kebab-case for file names and route paths.

3. **Error Handling**:
   - Handle expected errors without throwing unhandled exceptions in Server Actions.
   - Wrap raw SQLite/disk operations in try/catch blocks with contextual error logs.

---

## Common Commands

- `npm run dev`: Start Next.js development server
- `npm run build`: Build production Next.js bundle
- `npm run lint`: Run ESLint checks
- `npm run db:generate`: Generate Drizzle migration files from schema
- `npm run db:migrate`: Execute pending SQLite migrations
- `npm run db:studio`: Launch Drizzle Studio web interface
- `npm test`: Run test suite
