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

