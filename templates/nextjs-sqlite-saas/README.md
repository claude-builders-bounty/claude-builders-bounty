# Next.js 15 + SQLite SaaS — CLAUDE.md Template

An opinionated, production-ready `CLAUDE.md` for building SaaS applications with Next.js 15 App Router and SQLite (via better-sqlite3).

## What is this?

A `CLAUDE.md` file tells Claude Code how your project works — its conventions, structure, and rules. This template provides a complete set of conventions for a common SaaS stack so you can drop it into your project and start building with consistent, well-reasoned patterns from day one.

## How to use

### 1. Copy

```bash
cp templates/nextjs-sqlite-saas/CLAUDE.md /path/to/your-nextjs-project/CLAUDE.md
```

### 2. Customize

Open the file and adjust to your project:

- Update version numbers if you are using different versions
- Add or remove sections based on your stack (e.g., swap `next-auth` for `lucia-auth`)
- Add project-specific conventions (API naming, deployment targets, etc.)

### 3. Build

Start using Claude Code in your project. It will follow the conventions defined in `CLAUDE.md`.

## What the template covers

| Section                      | What it defines                                                   |
|------------------------------|-------------------------------------------------------------------|
| **Stack & Versions**         | Exact technologies and versions used                              |
| **Project Structure**        | Full directory tree with explanations for each directory           |
| **Naming Conventions**       | Files, SQL tables, columns, indexes, TypeScript types, env vars   |
| **SQL & Migrations**         | Schema-first approach, numbered migrations, query patterns        |
| **Component Patterns**       | Server vs. Client Components, props, colocation                   |
| **Dev Commands**             | Every npm script with description                                 |
| **Environment Variables**    | Required vars, typed config pattern                               |
| **Error Handling**           | Route handlers, error boundaries, logging                         |
| **Testing**                  | Vitest setup, test database, file colocation                      |
| **What We Don't Do (and Why)** | Anti-patterns with clear reasoning for each                    |

## Design principles

1. **Every rule has a reason.** No arbitrary conventions. Each rule includes a "why" so developers understand the intent and can make informed exceptions.

2. **Server-first.** React Server Components by default. Client Components only when interactivity requires it.

3. **Schema-first.** The SQL schema file is the source of truth. No ORM magic, no generated migrations.

4. **Explicit over implicit.** Named exports over defaults. Direct imports over barrels. Typed config over scattered `process.env`.

## Target stack

- **Next.js 15** with App Router and React Server Components
- **TypeScript 5** in strict mode
- **SQLite** via better-sqlite3 (zero-config, single-file database)
- **Tailwind CSS 4** for styling
- **next-auth v5** or **lucia-auth** for authentication
- **Vitest** for testing
- **Stripe** for payments (optional)
