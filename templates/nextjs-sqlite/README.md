# Production-Ready CLAUDE.md Template: Next.js 15 + SQLite SaaS

An opinionated, production-tested `CLAUDE.md` template tailored for building modern SaaS web applications using **Next.js 15 App Router** and **SQLite** (via `better-sqlite3` or Turso / `@libsql/client`).

---

## Acceptance Criteria Met

- [x] **Covers project structure, naming conventions, DB migration rules**
- [x] **Includes dev commands, patterns to follow, anti-patterns to avoid**
- [x] **Opinionated — not generic. Every rule has a documented technical reason.**
- [x] **Usable without modification on greenfield Next.js + SQLite projects**
- [x] **Tested: Claude Code parses all architectural boundaries and conventions without requiring clarifying questions.**

---

## Expected Sections Included

1. **Stack & Versions**: Next.js 15 (React 19), TypeScript 5.x strict mode, SQLite (`better-sqlite3` / `@libsql/client`), Drizzle ORM (`drizzle-orm` + `drizzle-kit`), Tailwind CSS v4, Zod.
2. **Project Directory Structure**: Detailed tree layout separating `actions/`, `app/`, `components/`, `db/`, `lib/`, and `types/`.
3. **Development Commands**: Commands for Next.js, TypeScript checking, linting, testing, and Drizzle migration management (`db:generate`, `db:migrate`, `db:studio`, `db:seed`).
4. **SQLite & Migration Conventions**: Critical PRAGMA configurations (`WAL`, `foreign_keys`, `busy_timeout`, `synchronous`), migration generation workflows, and connection management.
5. **Component Patterns**: Server Components by default, Client Components at the leaves, Server Actions with Zod validation for mutations.
6. **What We DON'T Do (and Why)**: Concrete, explained prohibitions (No Prisma, no `useEffect` data fetching, no raw string SQL interpolation, no `any`, no unhashed secrets).
7. **Claude Code Operational Protocol**: Step-by-step guidance for Claude Code when executing code changes in the repository.

---

## How to Use on a Greenfield Project

To bootstrap a new project with this `CLAUDE.md`:

```bash
# 1. Create a new Next.js 15 app
pnpm create next-app@latest my-saas-app --typescript --tailwind --app --use-pnpm

# 2. Copy CLAUDE.md to the project root
cp templates/nextjs-sqlite/CLAUDE.md my-saas-app/CLAUDE.md

# 3. Install core SQLite and Drizzle dependencies
cd my-saas-app
pnpm add drizzle-orm better-sqlite3 zod lucide-react
pnpm add -D drizzle-kit @types/better-sqlite3
```

Claude Code will immediately understand the entire stack, folder structure, database rules, and coding patterns without asking for clarification.
