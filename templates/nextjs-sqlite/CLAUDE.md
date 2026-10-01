# CLAUDE.md — Next.js + SQLite Project Guide

This guide defines coding standards, build workflows, database patterns, and architectural rules for Claude Code when working in this Next.js (App Router) + SQLite codebase.

---

## 🚀 Quick Reference Commands

### Development & Build
- `npm run dev` — Start local development server (`http://localhost:3000`)
- `npm run build` — Build production application (`.next`)
- `npm run start` — Run production build server
- `npm run lint` — Run ESLint check
- `npm run typecheck` — Run TypeScript typecheck (`tsc --noEmit`)
- `npm test` — Run test runner (Vitest / Jest)

### Database Management (SQLite)
- `npm run db:migrate` — Apply SQLite database schema migrations
- `npm run db:push` — Push schema updates to local SQLite DB (`dev.db`)
- `npm run db:seed` — Seed initial database fixtures
- `npm run db:studio` — Open interactive database GUI / inspector

---

## 📐 Architecture & Conventions

### Next.js App Router Standards
- **Server Components by Default**: All components under `app/` are React Server Components (RSC) unless explicitly marked with `"use client"`.
- **Client Components**: Keep `"use client"` directives at the smallest possible component leaf node to minimize JavaScript bundle size.
- **Server Actions**: Place reusable server actions in `lib/actions/` or alongside routes in `actions.ts`. Annotate top with `"use server"`.
- **Route Handlers**: Use `app/api/.../route.ts` strictly for external webhooks or public REST APIs. Prefer Server Actions for internal UI data mutations.

### SQLite Database Guidelines
- **SQLite Engine**: Powered by `better-sqlite3` or `drizzle-orm` / `prisma`.
- **WAL Mode**: Ensure SQLite connection executes `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = NORMAL;` on connection setup for high concurrency and zero locking overhead.
- **Prepared Statements & Parameter Binding**: ALWAYS use parameterized queries (`SELECT * FROM users WHERE id = ?`). **NEVER** concatenate user strings directly into SQL statements.
- **Transaction Safety**: Wrap multi-step writes inside explicit database transactions (`db.transaction(...)`).

---

## 🎨 Code Style & Structure

```text
├── app/                  # Next.js App Router pages and route handlers
│   ├── api/              # Public REST API routes
│   └── (routes)/         # UI Route groups
├── components/           # UI Components
│   ├── ui/               # Primitive Shadcn/Radix components
│   └── forms/            # Form components with Zod validation
├── lib/                  # Application core utilities
│   ├── db/               # SQLite connection instance and migrations
│   ├── actions/          # Server Actions
│   └── env.ts            # Validated environment variables
└── types/                # Shared TypeScript type definitions
```

### TypeScript Rules
- Strict mode enabled (`"strict": true` in `tsconfig.json`).
- Explicitly type function parameter types and return types for exported modules.
- Use Zod schemas for runtime validation of Server Action inputs, API request payloads, and process environment variables (`env.ts`).

---

## 🔐 Security & Error Handling

- **Input Sanitization**: Validate all client inputs via Zod prior to database operations.
- **Error Boundaries**: Handle route-level failures using `app/error.tsx` and missing resources using `app/not-found.tsx`.
- **Secrets & Env**: Never commit `.env` or `.db` files to version control. Validate `process.env` at startup using Zod in `lib/env.ts`.
