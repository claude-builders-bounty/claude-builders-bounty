# CLAUDE.md - Next.js 15 App Router + SQLite SaaS Architecture Guidelines

## 🏗️ Architecture & Stack
- **Framework:** Next.js 15 (App Router, Server Actions, React 19)
- **Database:** SQLite via Drizzle ORM / Prisma
- **Auth:** NextAuth v5 (Auth.js) / Lucide Icons / Tailwind CSS v4
- **Payments:** Stripe webhook integration

## 🛠️ Essential Development Commands
```bash
# Development server
npm run dev

# Database migrations & Studio
npx drizzle-kit push
npx drizzle-kit studio

# Testing
npm run test
npm run test:e2e

# Production build
npm run build
npm run start
```

## 📐 Coding Conventions & Rules
- **Server Components:** Default to Server Components (`page.tsx`, `layout.tsx`). Use `'use client'` only for interactive state, animations, or forms.
- **Data Mutations:** Always use Server Actions with `zod` input validation and `revalidatePath()`.
- **Database Access:** Keep all DB queries in `src/db/queries/`. Never execute raw unvalidated SQL.
- **Error Handling:** Use `try/catch` in actions returning `{ success: boolean, error?: string, data?: T }`.
