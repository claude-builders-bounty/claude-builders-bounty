# CLAUDE.md — Next.js 15 + SQLite SaaS

> Paste this into the root of a greenfield Next.js + SQLite project. Claude Code will pick up the context automatically.

---

## Stack & Versions

| Layer       | Choice                        | Version | Why                           |
|-------------|-------------------------------|---------|-------------------------------|
| Framework   | Next.js App Router            | 15.x    | Server Components, streaming |
| Runtime     | Node.js                       | 20 LTS  | LTS stability                |
| Language    | TypeScript (strict)           | 5.x     | Type safety matters           |
| Database    | SQLite via better-sqlite3     | 11.x    | Zero-config, file-based       |
| ORM         | Drizzle ORM                   | 0.x     | Type-safe SQL, good SQLite DX |
| Auth        | NextAuth.js v5 (Auth.js)      | 5.x     | App Router native             |
| Styling     | Tailwind CSS v4               | 4.x     | Utility-first, no runtime     |
| Validation  | Zod                           | 3.x     | Schema validation everywhere  |
| Testing     | Vitest + Testing Library      | latest  | Fast, ESM-native              |
| Linting     | ESLint flat config + Prettier | 9.x     | Consistent code style         |

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Protected route group
│   │   ├── layout.tsx      # Shared sidebar + auth check
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/
│   ├── api/                # Route handlers (REST)
│   │   └── [resource]/
│   │       └── route.ts
│   ├── layout.tsx          # Root layout (html, body, fonts)
│   └── globals.css
├── components/
│   ├── ui/                 # Reusable primitives (Button, Input, Modal...)
│   └── features/           # Feature-scoped composites
├── lib/
│   ├── db/                 # Database layer
│   │   ├── index.ts        # Drizzle client singleton
│   │   ├── schema.ts       # All table definitions
│   │   └── migrations/     # SQL migration files
│   ├── auth.ts             # NextAuth config
│   └── utils.ts            # Shared helpers (cn, formatDate, etc.)
├── server/
│   ├── queries/            # Typed query functions (one per domain)
│   └── actions.ts          # Server Actions (use server)
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types
└── env.ts                  # Zod-validated env vars
```

---

## Commands

```bash
npm run dev          # Start dev server (turbo mode)
npm run build        # Production build
npm run start        # Start production server
npm run test         # Run Vitest
npm run test:watch   # Vitest in watch mode
npm run lint         # ESLint
npm run db:generate  # Generate migration from schema changes
npm run db:migrate   # Apply pending migrations
npm run db:studio    # Open Drizzle Studio (GUI)
```

---

## Database & Migration Rules

### Schema goes in ONE place

All table definitions live in `src/lib/db/schema.ts`. Do not scatter schemas across files.

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),           // nanoid, not UUID
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull().default(sql`(unixepoch())`),
});
```

### Migration workflow

1. Edit `schema.ts`
2. Run `npm run db:generate` — creates a SQL migration in `migrations/`
3. Run `npm run db:migrate` — applies it
4. **Never edit migration files after they are generated.** If you made a mistake, generate a new migration to fix it.
5. **Never use `db.execute` for DDL.** Always go through Drizzle migrations.

### Query conventions

```typescript
// src/server_queries/users.ts
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export function getUserById(id: string) {
  return db.select().from(users).where(eq(users.id, id)).get();
}

export function getUserByEmail(email: string) {
  return db.select().from(users).where(eq(users.email, email)).get();
}
```

- One query file per domain (users.ts, projects.ts, invoices.ts)
- Every query returns typed data (Drizzle handles this)
- Use `.get()` for single rows, `.all()` for lists
- No raw SQL unless Drizzle genuinely can't express it — add a comment explaining why

---

## Component Patterns

### Server Components by default

Every component is a Server Component unless it needs interactivity or browser APIs.

```typescript
// app/(dashboard)/page.tsx — Server Component, no "use client"
import { getRecentProjects } from "@/server/queries/projects";
import { ProjectList } from "@/components/features/project-list";

export default async function DashboardPage() {
  const projects = await getRecentProjects();
  return <ProjectList projects={projects} />;
}
```

### Client Components only when needed

```typescript
"use client";

import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### UI primitives

- Keep `components/ui/` for generic, reusable pieces (Button, Input, Dialog, etc.)
- Feature components go in `components/features/`
- Use `cva` (class-variance-authority) for component variants, not inline ternaries
- Use `cn()` (clsx + tailwind-merge) for className merging

### Server Actions for mutations

```typescript
// src/server/actions.ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { db } from "@/lib/db";
import { projects } from "@/lib/db/schema";

const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function createProject(formData: FormData) {
  const input = createProjectSchema.parse({
    name: formData.get("name"),
    description: formData.get("description"),
  });

  await db.insert(projects).values({
    id: nanoid(),
    ...input,
  });

  revalidatePath("/dashboard");
}
```

Rules for Server Actions:
- Always validate input with Zod before touching the DB
- Always `revalidatePath` after mutations
- Never return sensitive data (strip passwords, tokens)
- Keep them in `src/server/actions.ts` or `src/server/actions/<domain>.ts`

---

## Naming Conventions

| Thing          | Convention              | Example                    |
|----------------|-------------------------|----------------------------|
| Files          | kebab-case              | `project-list.tsx`         |
| Components     | PascalCase              | `ProjectList`              |
| Functions      | camelCase               | `getUserByEmail`           |
| DB tables      | snake_case, plural      | `users`, `projects`        |
| DB columns     | snake_case              | `created_at`, `user_id`    |
| Env vars       | SCREAMING_SNAKE_CASE    | `DATABASE_URL`             |
| Route groups   | (parentheses)           | `(auth)`, `(dashboard)`    |
| API routes     | kebab-case              | `/api/reset-password`      |
| Server queries | `get<Resource>[By/For]` | `getUserById`, `getProjectsForUser` |
| Mutations      | `<verb><Resource>`      | `createProject`, `deleteUser` |
| Types          | PascalCase              | `Project`, `UserWithPlan`  |

---

## Environment Variables

All env vars are validated at build time via `src/env.ts` using `@t3-oss/env-nextjs`:

```typescript
// src/env.ts
import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    DATABASE_URL: z.string().default("file:./dev.db"),
    AUTH_SECRET: z.string(),
    AUTH_URL: z.string().default("http://localhost:3000"),
  },
  client: {
    // prefix with NEXT_PUBLIC_ for client-side access
  },
  runtimeEnv: {
    DATABASE_URL: process.env.DATABASE_URL,
    AUTH_SECRET: process.env.AUTH_SECRET,
    AUTH_URL: process.env.AUTH_URL,
  },
});
```

- Never access `process.env` directly in app code — always go through `env`
- Client-accessible vars must have `NEXT_PUBLIC_` prefix
- Add new vars to the schema before using them

---

## Error Handling

### API routes

```typescript
// app/api/projects/route.ts
import { NextResponse } from "next/server";
import { ZodError } from "zod";

export async function POST(request: Request) {
  try {
    // ... logic
    return NextResponse.json({ data }, { status: 201 });
  } catch (error) {
    if (error instanceof ZodError) {
      return NextResponse.json({ error: error.flatten() }, { status: 400 });
    }
    console.error("Failed to create project:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
```

### Server Components

Use `error.tsx` boundary files for graceful error UI:

```typescript
// app/(dashboard)/error.tsx
"use client";

export default function Error({ error, reset }: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="p-8">
      <h2>Something went wrong</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

---

## What We Don't Do (and Why)

| Don't                        | Why                                              |
|------------------------------|--------------------------------------------------|
| Use Prisma                   | Drizzle generates better SQL for SQLite, smaller bundle |
| Use `pages/` directory       | App Router is the standard; pages/ is legacy     |
| Use Redux / Zustand          | Server Components + URL state covers 95% of cases. Add Zustand only if you have complex client state that URL can't hold |
| Use `getServerSideProps`     | That's Pages Router. Use `async` Server Components |
| Raw SQL in route handlers    | Go through the query layer for type safety       |
| Store files in SQLite        | Use cloud storage (S3/R2) for files, store the URL |
| Use `any` type               | If you need to escape types, use `unknown` and narrow |
| CSS modules or styled-jsx    | Tailwind only. One styling system                |
| Middleware for data fetching  | Middleware runs on Edge; SQLite runs on Node. Fetch data in Server Components |
| Server Actions in client files | Keep them in `server/` for clear boundaries     |

---

## Auth Patterns

### Protect routes with middleware

```typescript
// middleware.ts
import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isAuth = !!req.auth;
  const isAuthPage = req.nextUrl.pathname.startsWith("/login")
    || req.nextUrl.pathname.startsWith("/register");

  if (isAuthPage && isAuth) {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }
  if (!isAuth && !isAuthPage) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
```

### Get current user in Server Components

```typescript
import { auth } from "@/lib/auth";

export default async function Page() {
  const session = await auth();
  if (!session?.user) redirect("/login");
  // ... use session.user.id, session.user.email
}
```

---

## Testing

### Co-locate test files

Place `*.test.ts` or `*.test.tsx` next to the file being tested:

```
src/lib/db/
├── schema.ts
└── schema.test.ts
```

### Test patterns

```typescript
// Server action test example
import { describe, it, expect, beforeEach } from "vitest";
import { createProject } from "../actions";

describe("createProject", () => {
  it("creates a project with valid input", async () => {
    const formData = new FormData();
    formData.set("name", "My Project");
    await createProject(formData);
    // assert DB state
  });

  it("rejects empty name", async () => {
    const formData = new FormData();
    formData.set("name", "");
    await expect(createProject(formData)).rejects.toThrow();
  });
});
```

- Use a separate test database (e.g. `file:./test.db`) — set via `DATABASE_URL` in test setup
- Reset the test DB in `beforeEach`
- Test server actions and query functions, not implementation details
