# CLAUDE.md - Next.js 15 + SQLite SaaS Project Guidelines

Opinionated, production-ready context guidelines for Claude Code agents working on greenfield Next.js 15 App Router + SQLite SaaS applications.

---

## 🛠️ Stack & Architecture Versions
- **Framework**: Next.js 15.x (App Router, Server Components by default)
- **Language**: TypeScript 5.x (Strict mode enabled)
- **Database**: SQLite 3 (using `better-sqlite3` and `drizzle-orm`)
- **Styling**: Tailwind CSS v3/v4 (Utility-first styling, HSL color tokens)
- **Authentication**: NextAuth.js / Auth.js (Session JWT / SQLite session store)

---

## 📁 Directory Structure & Conventions
```text
/
├── app/                  # Next.js App Router pages and Server Actions
│   ├── (auth)/           # Authentication route groups
│   ├── (dashboard)/      # Protected SaaS dashboard routes
│   └── api/              # API Route Handlers (REST endpoints)
├── components/           # Reusable UI components
│   ├── ui/               # Primitive UI elements (buttons, inputs, modals)
│   └── dashboard/        # Layout and feature components
├── db/                   # Database schemas and migration scripts
│   ├── schema.ts         # Drizzle SQLite table definitions
│   ├── index.ts          # Singleton SQLite connection instance
│   └── migrations/       # SQL migration files
├── lib/                  # Server utilities, helpers, and business logic
└── public/               # Static web assets
```

---

## ⚡ Development & Build Commands
```bash
npm run dev           # Start Next.js local development server (port 3000)
npm run db:generate   # Generate Drizzle migration files from schema.ts
npm run db:push       # Push schema changes directly to SQLite database
npm run db:studio     # Open Drizzle Studio database inspector UI
npm run test          # Execute Vitest / Jest unit test suite
npm run lint          # Execute ESLint & TypeScript type checking
```

---

## 🗄️ Database & SQL Rules (SQLite + Drizzle)
1. **Always Use Parameterized Queries**: Never concatenate raw user input into SQL string queries. Use Drizzle ORM bindings or `better-sqlite3` prepared statements (`stmt.run(param)`).
2. **Enable WAL Mode**: Always initialize SQLite connections with `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = NORMAL;` to enable concurrent reads and prevent database locking errors.
3. **Singleton Connection Pattern**: Keep a single global SQLite instance in `db/index.ts` to prevent multiple connection handle leaks during Hot Module Reloading (HMR) in development.

---

## 🛑 Anti-Patterns To Avoid (And Why)

| Anti-Pattern | Why It Is Prohibited |
| :--- | :--- |
| **Importing `better-sqlite3` in Client Components** | SQLite is a native Node.js C++ binding. Importing it in client components (`'use client'`) causes build crashes and exposes database handles to browsers. |
| **Raw SQL String Concatenation** | Exposes the application to SQL injection vulnerabilities. Always use parameterized queries. |
| **Mutating Database State in GET Handlers** | GET requests must remain idempotent and side-effect free per HTTP specifications. Use Server Actions or POST/PUT handlers for mutations. |
| **Directly Accessing `process.env` in Client Components** | Exposes private server keys. Only variables prefixed with `NEXT_PUBLIC_` are safe for browser code. |

---

## 🎯 Code Style & Component Rules
- **Server Components First**: Keep components server-rendered by default. Only add `'use client'` at the top of a file when interactive state (`useState`, `useEffect`, `onClick`) is strictly required.
- **Error Handling**: Wrap server actions and API handlers in try/catch blocks returning structured `{ success: false, error: message }` responses.
