# 📋 CLAUDE.md Template for Next.js + SQLite SaaS

> Production-ready, opinionated conventions for modern SaaS development

## Overview

This CLAUDE.md template provides comprehensive conventions for building SaaS applications with:
- **Next.js 15** (App Router)
- **SQLite** (better-sqlite3)
- **Drizzle ORM**
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui**

## Quick Start

```bash
# 1. Create a new Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --app

# 2. Install dependencies
npm install drizzle-orm better-sqlite3 zod @hookform/resolvers
npm install -D drizzle-kit @types/better-sqlite3

# 3. Copy CLAUDE.md to your project root
cp CLAUDE.md my-saas/

# 4. Start developing
npm run dev
```

## What's Included

### 📁 Project Structure
- Opinionated folder organization
- Route groups for auth vs app
- Clear separation of concerns

### 🗄️ Database Conventions
- Drizzle ORM schema patterns
- Migration rules
- Query organization
- Type-safe database layer

### 🧩 Component Patterns
- Server Components by default
- Client Components when needed
- Server Actions for mutations
- Form handling with validation

### 🚫 Anti-Patterns
Clear list of what NOT to do and why:
- No `useEffect` for data fetching
- No `any` types
- No CSS-in-JS
- No direct SQL in components

## Testing

This template has been tested on a fresh Next.js + SQLite project:

✅ **Verified**: Claude Code understands context without clarifying questions
✅ **Verified**: All dev commands work as documented
✅ **Verified**: Project structure is intuitive

## File Structure

```
.
├── CLAUDE.md              # This file
├── README.md              # Project readme
└── examples/              # Example implementations
    ├── schema.ts
    ├── actions.ts
    └── page.tsx
```

## Key Decisions

| Decision | Reason |
|----------|--------|
| SQLite over PostgreSQL | Zero config, file-based, perfect for MVP |
| Drizzle over Prisma | Type-safe SQL, lightweight, no codegen |
| App Router over Pages | Server-first, less client JS |
| Tailwind over CSS-in-JS | No runtime overhead, works with RSC |

## License

MIT - Use freely in your projects

---

Created for the Claude Builders Bounty program 🦞
