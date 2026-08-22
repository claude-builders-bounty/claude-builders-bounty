# Next.js + SQLite SaaS Project Guidelines

This project uses Next.js (App Router), SQLite (`better-sqlite3`), and Tailwind CSS.
Follow these architectural guidelines and commands when developing.

## Commands
- **Run dev server:** `npm run dev`
- **Build production:** `npm run build`
- **Run migrations:** `npm run db:migrate`
- **Run linter:** `npm run lint`

## Architecture & Database
- Database: SQLite via `better-sqlite3`. Store the database file at `prisma/dev.db` (if using Prisma) or `db/sqlite.db`.
- Schema Migrations: Always create incremental SQL migration files or use Prisma/Drizzle standard commands. Do NOT manually edit the production SQLite database.
- Database access should be contained within `lib/db.ts` or similar abstractions, not instantiated per-request.

## Server Actions & Data Fetching
- Use React Server Components (RSC) for data fetching by default.
- Use Next.js Server Actions for mutations. 
- **Security:** ALWAYS validate input using `zod` inside Server Actions before touching the database. ALWAYS check user authentication/authorization in every Server Action.

## UI & Styling
- Tailwind CSS is used for all styling.
- Utilize `shadcn/ui` components for standard UI elements (buttons, dialogs, forms).
- Keep client components (`"use client"`) to the absolute minimum necessary (leaf nodes of the component tree).

## Coding Standards
- Use TypeScript (`.tsx`, `.ts`).
- Avoid `any` types.
- Follow ESLint warnings.
