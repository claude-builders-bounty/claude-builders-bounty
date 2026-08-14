```markdown
# 🧠 CLAUDE.md: Next.js 15 + SQLite SaaS Architecture Guide

> **Context:** This project is a high-performance B2B/B2C SaaS built on **Next.js 15 (App Router)** and **SQLite**. 
> The goal of this file is to reduce cognitive load by enforcing a "Server-First" mental model where the Database 
> (`lib/db.sqlite`) is the single source of truth, exposed via typed server actions.
>
> **Version:** `1.0.0`  
> **Target IDE:** VS Code / Cursor  
> **Last Updated:** `[CURRENT_DATE]`

---

## 1. 🗂 The Data Layer (SQLite & Migrations)

We treat SQLite not just as a file, but as the immutable record of state. Use `better-sqlite3` (or `drizzle-orm`) 
for type-safety and synchronous speed on Server Components.

### Folder: `/lib/data`
The absolute source of truth for your database connection instance.

```bash
/app/routes/  # API routes only if needed
/lib/db/      # The DB instance singleton
/lib/migrations/ # Raw SQL scripts for seeding/upgrades
/types/index.ts  # If using a separate Types layer
```

### Naming Convention: PascalCase vs `snake_case`
- **DB Columns:** Prefer `camelCase` for direct JS readability in TS, but enforce strict typing. 
- **File Names:** PascalCase for components (`UserForm.tsx`).

### The "Singleton" Rule
The DB connection should feel like a singleton. If you need to access data anywhere inside an App Router route (Server or Client), **import the `db` object from `@/lib/data`**, not directly from the file path.

---

## 2. 📐 Folder Structure & Layouts

We use a granular `/app` structure but rely on `layout.tsx` to handle metadata routing logic so files stay clean.

```text
src/ (or root)
├── app/                    # App Router Root
│   ├── layout.tsx         # Global shell + font + meta
│   ├── page.tsx           # Default landing
│   └── dashboard/         # Specific feature areas
├── lib/                   # Shared Logic
│   ├── data/              # The SQLite Instance (Singleton)
│   ├── actions/           # Server Actions for mutations
│   └── utils/              # Pure functions (clamps, formatters)
└── components/            # UI Primitives & Atomic Components
```

---

## 3. 🧠 SQL / Migration Conventions

### The Migration Pattern
Use **Drizzle Kit** or a `migrations` folder for raw SQL scripts. 
Every migration file must start with `up()` and optionally handle `down()`.
- **Pattern:** `src/db/migrations/001_create_users.sql`
- **Rule:** Keep migrations atomic (one file, one logical change).

### The "Query" Pattern
Avoid raw `SELECT *` on the client. Use field-specific selections to keep React hydration cheap.
```typescript
// ✅ GOOD: Select only needed fields for Client Component mapping
const users = await db.user.findMany({ 
  select: { id, name: true } // Drizzle example or specific column names 
});

// ❌ BAD: Raw findMany without select (forces JSON serialization)
```

---

## 4. 🎨 Component Patterns & State

### Server vs Client Logic
The default mindset is **Server Components**. Use `use()` to pull data down into Client components, only when necessary.

1.  **Atomic Components:** `<Button>`, `<Card>` (Headless style).
2.  **Compound Components:** Use children (`<Modal><Header /></Modal>`) for nesting complexity.
3.  **Async Loading States:** If fetching on the server, use `async/await` patterns inside Server Functions before returning JSX.

### Naming Logic
- **Components:** `PascalCase` (e.g., `DataTable.tsx`).
- **Sub-parts:** `camelCase` if deeply nested within other components to break visual flow.
- **Imports:** Favor tree-shaking imports (`from './components/header'`) over loose `import { Button } from '@/'`.

---

## 5. ⚠️ What We Don't Do (Anti-Patterns)

Avoid these unless you have a specific reason. This file is the guardrail against drift.

| Avoid | Adopt Instead | Why? |
| :--- | :--- | :--- |
| `fetch` from DB on Client | **Server Actions** or `react-query` | Prevents hydrating the same state 50 times. |
| Hardcoded IDs in SQL | **Enums / Named Tables** | Makes migration painless when schema changes. |
| Direct File Imports (`from './data'`) | **Aliased Import** (`import { db } from '@/lib/data'`) | Handles path resolution and caching correctly. |
| `any` in the DB Layer | **TypeScript Interfaces** | The file is typed; use it or feel pain. |

---

## 6. 🧪 Dev Commands Reference

Add these to your `package.json` scripts so Claude knows exactly how you develop. Paste this into CLAUDE.md:

```json
{
  "scripts": {
    "db:init": "npx drizzle-kit generate --config=drizzle.config.ts", 
    "db:migrate": "node -r @libsql/migrations/run",
    "dev": "next dev --turbo", // Fastest refresh
    "build": "next build"
  }
}
```

---

## 7. 🧩 Example: The "Perfect" User Flow

Refer to this mental model when analyzing code flow. It dictates where logic lives.

1.  **Load Data:** Server Component calls `await db.user.find(...)`.
2.  **Map to UI:** Returns a JSON object that is immediately mapped to React primitives (`{ user: data => <Avatar user={data} /> }`).
3.  **Mutate Action:** User clicks button -> Triggers Server Action -> Commits DB -> Flushes Cache -> Re-renders.

---

**End of CLAUDE.md**
```