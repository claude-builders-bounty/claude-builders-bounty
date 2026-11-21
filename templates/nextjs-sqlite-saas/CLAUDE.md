# CLAUDE.md – Next.js 15 (App Router) + SQLite (better‑sqlite3 / Turso) + Drizzle ORM SaaS Template

## 1️⃣ Stack & Exact Versions
| Layer | Package | Version |
|-------|---------|---------|
| **Framework** | next | 15.1.0 |
| **React** | react | 19.0.0 |
| **React‑DOM** | react-dom | 19.0.0 |
| **Language** | typescript | 5.7.0 |
| **Type‑checking** | @tsconfig/strictest | 2.0.0 |
| **Database Engine** | better-sqlite3 | 9.5.0 |
| **Remote SQLite (Turso)** | @libsql/client | 0.5.0 |
| **ORM** | drizzle‑orm | 0.31.0 |
| **Drizzle SQLite Driver** | drizzle‑orm/sqlite‑better‑sqlite3 | 0.31.0 |
| **Styling** | tailwindcss | 4.0.0 |
| **Auth** | lucia | 2.5.0 |
| **Auth Adapter** | @lucia-auth/adapter‑better‑sqlite3 | 2.5.0 |
| **Validation** | zod | 3.23.0 |
| **Utility** | ulid | 2.3.0 |
| **Testing** | vitest | 2.0.0 |
| **Linting** | eslint | 9.10.0 |
| **Formatting** | prettier | 3.3.0 |

All dependencies are pinned in `package.json` with exact versions (`"next": "15.1.0"` etc.) to guarantee reproducible builds.

---

## 2️⃣ Opinionated Folder Structure
```
/src
 ├─ /app                # Next.js 15 App Router – pages are React Server Components by default
 │   ├─ layout.tsx
 │   ├─ page.tsx
 │   └─ … (route folders)
 ├─ /components
 │   └─ /ui             # Tailwind‑styled, fully typed UI primitives
 ├─ /db
 │   ├─ schema.ts       # Drizzle table definitions (single source of truth)
 │   ├─ /migrations     # Drizzle migration files (timestamped)
 │   └─ client.ts       # Exported `db` instance (server‑only)
 ├─ /server
 │   ├─ actions         # Server Actions – Zod‑validated, `use server` guard
 │   └─ queries         # Pure DB query functions – `import "server-only"` enforced
 ├─ /lib
 │   ├─ auth.ts         # Lucia init + session helpers
 │   └─ utils.ts        # ULID generator, date helpers, etc.
 └─ /types
     └─ index.ts        # Global TypeScript types (e.g., Session, User)
```

*All files under `src/server` and `src/db` are **server‑only** – they import `"server-only"` at the top to guarantee they never bundle to the client.*

---

## 3️⃣ SQL & Migration Conventions
### 3.1 Pragmas (executed on every DB connection)
```ts
// src/db/client.ts
import Database from "better-sqlite3";

export const db = new Database(process.env.DATABASE_URL, {
  // WAL mode for concurrent reads/writes
  fileMustExist: false,
});

db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");
db.pragma("synchronous = NORMAL");
```

### 3.2 Schema Rules
* Primary keys: **ULID** (`TEXT NOT NULL PRIMARY KEY`) – monotonic, avoids B‑tree fragmentation.
* Timestamps: `INTEGER NOT NULL` – UTC milliseconds since epoch.
* All foreign keys are **STRICT** (`ON DELETE RESTRICT`, `ON UPDATE CASCADE`).

### 3.3 Drizzle Migration Pattern
```ts
// src/db/migrations/20241015T123456_create_users.ts
import { sql } from "drizzle-orm";
export default async function up(db) {
  await db.run(sql`
    CREATE TABLE users (
      id TEXT PRIMARY KEY,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
  `);
}
export async function down(db) {
  await db.run(sql`DROP TABLE users;`);
}
```

*All migrations run inside a single transaction (`db.transaction(async (tx) => { … })`). No raw, un‑parameterized strings are ever interpolated – we always use `sql` tagged template literals which safely escape values.*

### 3.4 Why No Runtime Schema Changes?
* SQLite is file‑based; altering tables on‑the‑fly corrupts WAL logs and breaks replication (Turso).  
* Production stability demands immutable schema after deployment; migrations are the only path to change.

---

## 4️⃣ Component & Data Fetching Patterns
### 4.1 React Server Components (RSC) by default
* All files in `src/app` are **RSC** unless they contain `"use client"` at the top.
* UI primitives (`src/components/ui/*`) are **client components** only when they need interactivity.

### 4.2 Server Actions
```tsx
// src/server/actions/createPost.ts
"use server";

import { z } from "zod";
import { db } from "@/db/client";
import { posts } from "@/db/schema";
import { ulid } from "ulid";

const CreatePostSchema = z.object({
  title: z.string().min(3).max(120),
  content: z.string().min(10),
});

export async function createPost(formData: FormData) {
  const parsed = CreatePostSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!parsed.success) throw new Error("Invalid input");

  const { title, content } = parsed.data;
  const now = Date.now();

  await db.insert(posts).values({
    id: ulid(),
    title,
    content,
    createdAt: now,
    updatedAt: now,
  });
}
```
*All Server Actions are **Zod‑validated** and throw on failure – the client receives a 400‑style error automatically.*

### 4.3 `server-only` Guard on DB Queries
```ts
// src/server/queries/getUser.ts
import "server-only";
import { db } from "@/db/client";
import { users } from "@/db/schema";

export async function getUserById(id: string) {
  return db.select().from(users).where(eq(users.id, id)).get();
}
```

### 4.4 Optimistic UI Rules
* Mutations performed via Server Actions return a **Promise**; UI components call them with `useTransition` for instant feedback.
* Never use `useEffect` to poll the same data that a Server Action already updates – rely on **revalidation** (`revalidatePath`) or **React Server Component streaming**.

---

## 5️⃣ Development & Testing Commands
```bash
# Install exact versions
pnpm install

# Run dev server (hot‑reloading, strict TS)
pnpm dev

# Generate Typescript types from Drizzle schema
pnpm db:generate
#   => runs `drizzle-kit generate:sqlite --out src/db/schema.ts`

# Apply pending migrations (creates DB if missing)
pnpm db:migrate
#   => runs `drizzle-kit migrate --config drizzle.config.ts`

# Run unit & integration tests (Vitest, jsdom for client components)
pnpm test

# Full type‑check (noEmit)
pnpm typecheck
```

Add the following scripts to `package.json`:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "db:generate": "drizzle-kit generate:sqlite --out src/db/schema.ts",
    "db:migrate": "drizzle-kit migrate --config drizzle.config.ts",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  }
}
```

---

## 6️⃣ What We **DO NOT** Do (And Why)

| Anti‑Pattern | Reason |
|--------------|--------|
| **Prisma (or any heavy binary) in serverless/edge** | Prisma bundles native binaries that inflate bundle size and fail on edge runtimes. SQLite + Drizzle is pure‑JS/TS and fits the low‑latency edge model. |
| **API Routes for internal mutations** | Duplicates logic, bypasses Server Actions, and forces manual auth checks. Server Actions keep auth, validation, and DB access together, reducing surface area. |
| **Client‑side `useEffect` data fetching for core resources** | Causes waterfall requests, SEO loss, and stale data. Server Components fetch data at render time, guaranteeing fresh content and better SEO. |
| **UUIDv4 primary keys** | Random distribution fragments SQLite B‑trees, leading to slower inserts and larger files. ULID/UUIDv7 are monotonic, preserving B‑tree locality. |
| **Running raw, unparameterized SQL strings** | Opens the door to SQL injection and makes migrations non‑deterministic. Drizzle’s `sql` tag + parameter binding guarantees safety. |
| **Dynamic schema changes at runtime** | SQLite files cannot safely alter tables while serving traffic; migrations must be applied offline and version‑controlled. |
| **Storing timestamps as ISO strings** | Takes more space and requires parsing on every query. Integer UTC ms is compact and index‑friendly. |
| **Mixing client and server logic in the same file** | Breaks tree‑shaking and can accidentally ship secrets to the browser. Enforce `use client` only where UI interactivity is required. |

---

## 7️⃣ Quick Start Checklist
1. `pnpm install`
2. Copy `.env.example` → `.env.local` and set `DATABASE_URL` (local file path or Turso URL + token)
3. `pnpm db:migrate`
4. `pnpm dev`
5. Open `http://localhost:3000` – you should see the starter page with a protected route (`/dashboard`) that uses Lucia session.

--- 

*This template is deliberately opinionated to enforce a **secure, performant, and maintainable** codebase for SaaS products built on Next.js 15, SQLite, and Drizzle ORM.*
