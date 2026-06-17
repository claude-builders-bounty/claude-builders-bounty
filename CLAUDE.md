# CLAUDE.md - Next.js + SQLite SaaS Template

This document provides essential guidelines for AI agents to maintain consistency, quality, and efficiency when working on this Next.js + SQLite SaaS project.

## 🛠 Build & Development Commands

- **Install Dependencies**: `npm install`
- **Development Server**: `npm run dev` (starts Next.js on http://localhost:3000)
- **Build Project**: `npm run build`
- **Linting**: `npm run lint`
- **Run Tests**: `npm test` or `npx jest`

## 🗄 Database Management (SQLite)

The project uses SQLite for local development and lightweight production.

- **ORM**: Prisma (preferred) or Drizzle.
- **Migration**: `npx prisma migrate dev --name <migration_name>`
- **Studio**: `npx prisma studio` (visual editor for the SQLite database)
- **Reset DB**: `npx prisma migrate reset`
- **Seed Data**: `npm run seed`

**Guidelines**:
- Always define types in `schema.prisma` before implementing logic.
- Use transactions for multi-step write operations to ensure data integrity.
- Prefer indexed columns for frequently queried fields (e.g., `email`, `orgId`).

## 🎨 Coding Standards

### TypeScript & React
- **Strict Typing**: Avoid `any` at all costs. Use interfaces or types for all data structures.
- **Components**: Use Functional Components with Arrow Functions.
- **Styling**: Use Tailwind CSS for all UI. Avoid inline styles or external CSS files unless necessary.
- **State Management**: Prefer Server Components for data fetching. Use `useState` and `useContext` only in `'use client'` components.

### Next.js App Router
- **Server-First**: Default to Server Components. Move interactivity to the leaves of the component tree.
- **Routing**: Use file-based routing in the `app/` directory.
- **Data Fetching**: Use `async/await` directly in Server Components.
- **API Routes**: Implement logic in `app/api/` using Route Handlers.

### Validation & Error Handling
- **Input Validation**: Use **Zod** for all API request bodies and environment variables.
- **Error Boundaries**: Use `error.tsx` and `loading.tsx` files for graceful UI states.
- **Logging**: Use a structured logger (e.g., `pino` or `winston`) for server-side errors.

## 📂 Project Structure

- `/app`: Routes, pages, and layouts (App Router).
- `/components`: Reusable UI components (divided into `/ui` for primitives and `/features` for business logic).
- `/lib`: Shared utilities, database clients, and business logic services.
- `/hooks`: Custom React hooks.
- `/types`: Global TypeScript definitions.
- `/prisma`: Database schema and migrations.
- `/public`: Static assets.

## 🚀 Contribution Workflow

1. **Analyze**: Read the issue and identify affected files.
2. **Implement**: Write clean, modular code following the standards above.
3. **Verify**: Run `npm run lint` and `npm test` before committing.
4. **Commit**: Use descriptive commit messages (e.g., `feat: add user authentication`).
