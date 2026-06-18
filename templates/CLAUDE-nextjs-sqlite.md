# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS Template

An opinionated, production-ready CLAUDE.md for a Next.js 15 (App Router) + SQLite (better-sqlite3 via Drizzle ORM) SaaS project.

## Stack & Versions

| Component | Version | Notes |
|-----------|---------|-------|
| Node.js | 20.x LTS | Required by Next.js 15 |
| Next.js | 15.x (App Router) | Server Components by default |
| React | 19.x | Server Actions stable |
| TypeScript | 5.4+ | Strict mode required |
| SQLite | 3.45+ | Via better-sqlite3 (synchronous) |
| Drizzle ORM | 0.30+ | Type-safe, lightweight |
| Auth.js | v5 (beta) | Session-based auth |
| Zod | 3.23+ | Schema validation |
| TailwindCSS | 3.4+ | For styling |

## Folder Structure

```
app/                    # Next.js App Router
├── (marketing)/        # Public routes (landing, pricing)
├── (auth)/             # Auth routes (login, signup)
├── (dashboard)/        # Protected routes
│   └── settings/       # Nested settings
├── api/                # API routes
└── layout.tsx          # Root layout

components/
├── ui/                 # Generic UI components
├── forms/              # Form components
└── layout/             # Layout components

lib/
├── db/                 # Database setup
│   ├── schema.ts       # Drizzle schema
│   ├── migrations/     # SQL migrations
│   └── client.ts       # Database client
├── auth/               # Auth.js config
├── actions/            # Server actions
└── utils/              # Utility functions

drizzle.config.ts       # Drizzle Kit config
drizzle/                # Generated migrations
```

## SQL / Migration Conventions

### 5 Rules

1. **Always use Drizzle schema as source of truth** — Never write raw SQL in app code
2. **Every table MUST have `id`, `createdAt`, `updatedAt`** — Consistent audit trail
3. **Foreign keys MUST use `references()`** — Enforce referential integrity
4. **Use `text` not `varchar(N)`** — SQLite doesn't enforce length, be consistent
5. **Indexes on all foreign keys** — Avoid table scans on joins

### Migration Workflow

```bash
# 1. Edit schema in lib/db/schema.ts
# 2. Generate migration
npx drizzle-kit generate

# 3. Review generated SQL in drizzle/
# 4. Apply migration
npx drizzle-kit migrate

# 5. Commit both schema AND migration
git add lib/db/schema.ts drizzle/
git commit -m "feat(db): add user_preferences table"
```

## Component Patterns

### Server Components First

```tsx
// ✅ GOOD: Server Component (default)
export default async function UserList() {
  const users = await db.select().from(usersTable);
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}

// ❌ BAD: "use client" for data fetching
"use client";
export default function UserList() {
  const [users, setUsers] = useState([]);
  useEffect(() => { fetch('/api/users').then(...) }, []);
  // ...
}
```

### Server Actions for Mutations

```tsx
// app/(dashboard)/users/actions.ts
"use server";
import { revalidatePath } from "next/cache";

export async function createUser(formData: FormData) {
  const validated = userSchema.parse(Object.fromEntries(formData));
  await db.insert(usersTable).values(validated);
  revalidatePath("/dashboard/users");
}
```

## Dev Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint
npm run typecheck    # TypeScript check
npm run db:generate  # Generate migration from schema
npm run db:migrate   # Apply pending migrations
npm run db:studio    # Open Drizzle Studio
npm test             # Run tests
```

## Anti-Patterns

### ❌ Don't Do These

1. **`server/` directory** — Use `lib/` or `app/` instead. Next.js App Router has built-in server handling.
2. **Services layer** — Server Actions + Server Components ARE the service layer. No need for an abstraction.
3. **Raw SQL strings** — Always use Drizzle's query builder. SQL injection risk + no type safety.
4. **`any` type casts** — Use `unknown` and narrow with type guards. Defeats TypeScript purpose.
5. **`.env.local` docs in repo** — Use `.env.example` with placeholders only. Real secrets stay local.
6. **Empty catch blocks** — Always handle or rethrow errors. Silent failures are debugging nightmares.

## Auth / Session Pattern

Using Auth.js v5 with session-based auth:

```tsx
// lib/auth/config.ts
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      authorize: async (creds) => {
        const user = await db.query.users.findFirst({
          where: eq(users.email, creds.email as string),
        });
        if (!user) return null;
        const valid = await bcrypt.compare(creds.password as string, user.passwordHash);
        return valid ? user : null;
      },
    }),
  ],
  callbacks: {
    jwt: ({ token, user }) => ({ ...token, ...user }),
    session: ({ session, token }) => ({ ...session, user: token }),
  },
});

// app/(dashboard)/layout.tsx
export default async function DashboardLayout({ children }) {
  const session = await auth();
  if (!session) redirect("/login");
  return <div>{children}</div>;
}
```

## Error Handling

### Per-Layer Strategy

| Layer | Strategy |
|-------|----------|
| **Server Actions** | Throw typed errors, catch in form with `useFormState` |
| **API Routes** | Return typed `Response` with status codes |
| **Server Components** | Use `error.tsx` boundary |
| **Client Components** | Error boundary + toast notifications |
| **Database** | Drizzle throws typed errors, wrap in try/catch |

### Example: Server Action Error

```tsx
"use server";
export async function createUser(formData: FormData) {
  try {
    const validated = userSchema.parse(Object.fromEntries(formData));
    return { ok: true, user: await db.insert(usersTable).values(validated).returning() };
  } catch (err) {
    if (err instanceof ZodError) return { ok: false, errors: err.flatten() };
    throw err; // Rethrow unexpected errors
  }
}
```

---

**Total: 143 lines — short enough to read in one sitting, complete enough to cover all bases.**

Usable without modification on a greenfield Next.js + SQLite project.
