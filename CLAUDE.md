# CLAUDE.md - Project Intelligence & Engineering Standards

This document serves as the authoritative guide for AI coding agents (Claude Code, Cursor, etc.) to maintain architectural integrity and coding standards within this Next.js 15 + SQLite SaaS environment.

## Stack & Versions
- **Framework:** Next.js 15 (App Router) - *Stricly use Server Components by default.*
- **Language:** TypeScript (Strict Mode)
- **Database:** SQLite via `better-sqlite3` (Synchronous execution preferred for local-first simplicity).
- **Styling:** Tailwind CSS (Mobile-first, utility-only).
- **Validation:** Zod (Schema-first approach for all inputs/DB).
- **Component Library:** Radix UI / Shadcn UI patterns.

## 📂 Folder Structur & Responsibility
```text
├── app/                # Routing layer: Pages, Layouts, and Server Actions only.
├── components/
│   ├── ui/             # Pure, stateless primitive components (Shadcn style).
│   └── features/       # Domain-driven components (e.g., /auth, /billing).
├── lib/
│   ├── db/             # Database connection and schema definitions.
│   │   └── migrations/ # Versioned SQL migration files.
│   ├── utils/          # Pure, side-effect-free helper functions.
│   └── validations/    # Zod schemas for API and Form validation.
├── public/             # Static assets.
└── types/              # Global TypeScript interfaces and Type definitions.
```


## SQL & Migration Conventions

- **Schem Ownership**: All schema changes must be defined in `lib/db/schema.ts` and mirrored in a new migration file within `lib/db/migrations/`.
- **Migration Workflow**:
  1. Create a new migration file using the format: `[timestamp]_description.sql`.
  2. Execute the migration script to synchronize the `better-sqlite3` state.
  3. **Strict Rule**: Never use `ALTER TABLE` manually within application logic; all schema evolutions must be handled exclusively through migration files.
- **Data Access**: Use a dedicated `lib/db/queries.ts` file for complex read operations to keep Server Components clean and maintainable.

## Component Patterns

- **Server-First Approach**: All components within the `app/` directory must be **React Server Components (RSC)** by default, unless interactivity is explicitly required.
- **Interactivity Management**: Use the `'use client'` directive only at the lowest possible level (Leaf Components) to minimize client-side JavaScript bundles.
- **Data Fetching**: Fetch data directly within RSCs using `await`. **Do not** use `useEffect` or client-side fetching for initial data loading.
- **Action Pattern**: Use **Next.js Server Actions** for all mutations (`POST`, `PATCH`, `DELETE`). 
  - Always wrap actions in `try/catch` blocks.
  - Utilize `Zod` for rigorous input validation before processing.

## 🚫 What We Don't Do (And Why)

- **No `any` Type**: We enforc strict TypeScript typing to prevent runtime failures and maintain reliability in a SaaS environment.
- **No Client-side Fetching for Initial Data**: This practice degrades SEO performance and increases LCP (Largest Contentful Paint). Always prioritize RSC.
- **No Massive Components**: Any component exceeding **150 lines** must be refactored into smaller, domain-specific sub-components located in `components/features/`.
- **No Direct `process.env` Access in UI**: To prevent startup crashes and ensure type safety, always wrap environment variables in a validated `lib/env.ts` configuration using `Zod`.

## 🚀 Essentia Commands

| Command | Description |
| :--- | :--- |
| `npm run dev` | Start the local development server. |
| `npm run build` | Build the application for production. |
| `npm run migrate` | Execute pending SQLite migrations. |
| `npm run lint` | Check for architectural violations and code style errors. |

