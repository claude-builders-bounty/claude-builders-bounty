# CLAUDE.md — Next.js + SQLite SaaS

> Opinionated development guide for Next.js 16 App Router projects with Prisma + SQLite.
> Every rule comes from production experience shipping real apps.

## Stack & Versions

- **Next.js 16** (App Router) — `next@16.2.4`
- **React 19** — Server Components by default, `"use client"` only when needed
- **Prisma 7** + **better-sqlite3** adapter — `@prisma/client@^7.8.0`
- **Tailwind CSS 4** — `@import "tailwindcss"` in globals.css
- **NextAuth v5** — `next-auth@^5.0.0-beta.31`
- **TypeScript 5.7** — strict mode ON

## Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout — keep minimal
│   ├── page.tsx            # Landing page (server component)
│   ├── globals.css         # Tailwind + CSS variables
│   ├── (main)/             # Route group for authenticated pages
│   │   └── dashboard/
│   │       └── page.tsx    # Server component → passes data to client
│   ├── api/                # API route handlers
│   │   └── tasks/
│   │       └── route.ts    # GET, POST, PATCH, DELETE
│   └── admin/              # Admin section (protected)
├── components/             # Shared components
│   ├── ui/                 # Primitive UI components (buttons, inputs)
│   └── layout/             # Layout components (topbar, footer, sidebar)
├── lib/                    # Shared utilities
│   ├── prisma.ts           # Singleton PrismaClient
│   ├── auth.ts             # NextAuth configuration
│   └── permissions.ts      # Authorization logic
└── hooks/                  # Client-side React hooks
```

**DO NOT:**
- Put business logic in components — extract to `lib/`
- Create files in the root `src/` directory
- Mix server and client code in the same file

## SQL / Migration Rules

### Prisma Schema

```prisma
datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}
```

### Prisma Client Singleton

```ts
// src/lib/prisma.ts — use this exact pattern
import { PrismaClient } from "@prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient | undefined };

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    adapter: new PrismaBetterSqlite3({
      url: process.env.DATABASE_URL || "file:./prisma/dev.db",
    }),
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
```

### Migration Workflow

1. Edit `prisma/schema.prisma`
2. Run `npx prisma db push` (preferred over `migrate` for solo dev)
3. Run `npx prisma generate`
4. Delete `.next` directory
5. Restart dev server

**PITFALL:** After schema changes, `.next` cache can cause stale type errors. Always `rm -rf .next && npm run dev`.

### Database Paths

- Development: `DATABASE_URL="file:./prisma/dev.db"`
- Production: `DATABASE_URL="file:/absolute/path/prisma/dev.db"`
- **Never** hardcode WSL home paths in `prisma.ts`. Always use `process.env.DATABASE_URL` with a production-appropriate fallback.

### Query Patterns

```ts
// Server Component — ALWAYS use select, never include
const items = await prisma.task.findMany({
  where: { published: true },
  orderBy: { sortOrder: "asc" },
  select: {
    id: true, title: true, status: true,
    // Include relations as needed
    images: { orderBy: { sort: "asc" }, select: { url: true } },
  },
});

// Pass to client component via props after serialization
const plain = JSON.parse(JSON.stringify(items));
return <ClientComponent data={plain} />;
```

## Server/Client Component Patterns

### Server Component → Client Component Data Flow

```tsx
// page.tsx (server component)
export default async function Page() {
  const data = await prisma.item.findMany({ ... });
  const plain = JSON.parse(JSON.stringify(data));
  return <ClientComponent items={plain} />;
}

// ClientComponent.tsx ("use client")
export default function ClientComponent({ items }: { items: Item[] }) {
  const [filter, setFilter] = useState("all");
  // Client-side filtering, sorting, UI state
}
```

### When to Use "use client"

- ✅ User interaction (forms, buttons, clicks)
- ✅ Browser APIs (window, document, localStorage)
- ✅ React hooks (useState, useEffect, useRef)
- ✅ Client-side state management
- ❌ Data fetching from database
- ❌ File system operations
- ❌ Environment variable access
- ❌ Authentication checks

### Hydration Pitfalls

**NEVER do this in render:**
```tsx
// ❌ BREAKS HYDRATION
const [seed, setSeed] = useState(() => Date.now());
```

**ALWAYS do this:**
```tsx
// ✅ FIXED
const [seed, setSeed] = useState(0);  // Same on server & client

useEffect(() => {
  setSeed(Date.now());  // Only runs client-side
}, []);
```

`useState` initializers run on BOTH server and client during hydration. Any non-deterministic value (Date.now(), Math.random()) will cause a hydration mismatch and React will silently drop your entire component tree.

### Dynamic Rendering

```tsx
// Add to server components that need fresh data on every request
export const dynamic = "force-dynamic";
```

Without this, Next.js may statically generate the page at build time and never update it.

## Dev Commands

```bash
npm run dev          # Start dev server (Turbopack)
npm run build        # Production build
npm start            # Production server
npx prisma db push   # Sync schema to database
npx prisma generate  # Regenerate Prisma client
npx prisma studio    # GUI database browser
```

### Checking if Dev Server is Alive

```bash
lsof -ti:3000        # Returns PID if running
```

## Anti-Patterns (What We Don't Do)

1. **Don't use `prisma.include`** — Always `select`. Include fetches all columns, bloats memory.
2. **Don't hardcode paths** — Use `process.env.DATABASE_URL` with environment-appropriate fallbacks.
3. **Don't put `Date.now()` in `useState` initializer** — Causes hydration mismatch.
4. **Don't mix server/client imports** — Server components can't import `"use client"` modules except as JSX.
5. **Don't use `min-h-screen` for layout** — Use `h-screen` + `overflow-y-auto` on content. `min-h-screen` allows infinite growth, prevents scroll.
6. **Don't call client-only functions from server components** — Inline server-safe equivalents instead.
7. **Don't forget `force-dynamic`** — Pages that query a database at request time need this export.
8. **Don't use `pm2 restart`** — Always `pm2 stop && rm -rf .next && npm run build && pm2 start`.
9. **Don't ship without testing the API balance** — Run `curl` to verify the server returns 200 before telling the user it's done.
10. **Don't build on a 2GB RAM VPS** — Build locally, upload `.next`.

## CSS Flexbox Scroll Rules

For any page with independent scrolling areas:
```
body:          h-screen overflow-hidden
Layout:        flex flex-col h-screen
  content:     flex-1 flex flex-col min-h-0
    scrollArea: flex-1 overflow-y-auto
```

Every flex child in the chain must have `min-h-0` or the scroll won't work.

## Deployment

```bash
# Build locally (more RAM)
rm -rf .next && npm run build && tar czf deploy.tar.gz .next

# Upload + deploy
scp deploy.tar.gz user@server:/tmp/
ssh user@server "
  pm2 stop app
  rm -rf /path/.next && tar xzf /tmp/deploy.tar.gz -C /path/
  pm2 start 'npx next start -p 3000' --name app --cwd /path
"
```

**PITFALL:** `pm2 start` without `--cwd` runs from the wrong directory and can't find `.next`. Always include `--cwd`.
