# CLAUDE.md - Next.js 15 + SQLite SaaS

**Stack**: Next.js 15 (App Router) + SQLite (better-sqlite3) + TypeScript + Tailwind CSS

---

## 📦 Stack & Versions

```json
{
  "next": "^15.0.0",
  "react": "^19.0.0",
  "typescript": "^5.6.0",
  "better-sqlite3": "^11.0.0",
  "tailwindcss": "^3.4.0",
  "zod": "^3.23.0"
}
```

**Why these choices:**
- Next.js 15 App Router: Server Components by default, better performance
- SQLite (better-sqlite3): Zero-config, file-based, perfect for SaaS MVP
- Zod: Runtime validation, type-safe forms
- Tailwind: Rapid UI development, consistent design

---

## 📁 Folder Structure

```
my-saas/
├── app/                      # Next.js App Router
│   ├── (auth)/              # Auth routes (login, signup, reset)
│   │   ├── login/
│   │   ├── signup/
│   │   └── layout.tsx       # Auth layout (no sidebar)
│   ├── (dashboard)/         # Protected dashboard routes
│   │   ├── dashboard/
│   │   ├── settings/
│   │   └── layout.tsx       # Dashboard layout (with sidebar)
│   ├── api/                 # API routes
│   │   ├── webhooks/
│   │   └── trpc/
│   ├── globals.css
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Landing page
├── components/
│   ├── ui/                  # Reusable UI components
│   ├── forms/               # Form components
│   └── dashboard/           # Dashboard-specific components
├── lib/
│   ├── db.ts                # Database connection
│   ├── schema.ts            # Zod schemas
│   └── utils.ts             # Utility functions
├── db/
│   ├── migrations/          # SQL migration files
│   └── seed.ts              # Seed data
├── hooks/                   # React hooks
├── types/                   # TypeScript types
└── next.config.ts
```

**Why this structure:**
- Route groups `(auth)` and `(dashboard)` separate layouts cleanly
- `lib/` for shared logic, `components/` for UI only
- `db/migrations/` keeps SQL versioned and reviewable

---

## 🗄️ Database Conventions

### Migration Rules

1. **Every migration is a SQL file** with sequential numbering:
   ```
   db/migrations/
   ├── 001_create_users.sql
   ├── 002_create_sessions.sql
   └── 003_add_user_preferences.sql
   ```

2. **Migration file format:**
   ```sql
   -- 001_create_users.sql
   -- Up
   CREATE TABLE IF NOT EXISTS users (
     id TEXT PRIMARY KEY,
     email TEXT UNIQUE NOT NULL,
     password_hash TEXT NOT NULL,
     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
   );

   -- Down
   DROP TABLE IF EXISTS users;
   ```

3. **Never modify old migrations** — always create a new one.

4. **Run migrations on startup** (dev) or manually (prod):
   ```bash
   npm run db:migrate
   ```

### Query Patterns

```typescript
// ✅ GOOD: Prepared statements, type-safe
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(userId) as User | undefined;

// ❌ BAD: String interpolation (SQL injection)
const user = db.query(`SELECT * FROM users WHERE id = '${userId}'`);
```

---

## 🏗️ Component Patterns

### Server Components by Default

```tsx
// ✅ GOOD: Server Component (default)
async function UserProfile({ userId }: { userId: string }) {
  const user = await db.getUser(userId);
  return <div>{user.name}</div>;
}

// ❌ BAD: Unnecessary 'use client'
```

### Client Components Only When Needed

```tsx
// ✅ GOOD: Client component with clear reason
'use client';

export function SearchInput() {
  const [query, setQuery] = useState('');
  // Needs useState, so must be client
  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

### Form Pattern (Server Actions)

```tsx
// ✅ GOOD: Server Action with Zod validation
async function createAccount(formData: FormData) {
  const email = formData.get('email');
  const password = formData.get('password');
  
  const result = authSchema.safeParse({ email, password });
  if (!result.success) {
    return { error: result.error.flatten() };
  }
  
  await createUser(result.data);
  revalidatePath('/dashboard');
}
```

---

## 📝 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Utils | camelCase | `formatDate.ts` |
| DB Tables | snake_case, plural | `users`, `user_preferences` |
| DB Columns | snake_case | `created_at`, `user_id` |
| API Routes | kebab-case | `/api/webhooks/stripe` |
| Files | Match export | `UserProfile.tsx` exports `UserProfile` |

---

## 🚫 Anti-Patterns (What We Don't Do)

### 1. No useEffect for Data Fetching

```tsx
// ❌ BAD: useEffect data fetching
useEffect(() => {
  fetch('/api/user').then(setUser);
}, []);

// ✅ GOOD: Server Component or SWR
async function Page() {
  const user = await getUser();
  return <UserProfile user={user} />;
}
```

**Why:** Server Components eliminate waterfalls, better SEO.

### 2. No Global State for Server Data

```tsx
// ❌ BAD: Redux/Zustand for server data
const user = useStore(state => state.user);

// ✅ GOOD: Server fetch + props
const user = await getCurrentUser();
return <Dashboard user={user} />;
```

**Why:** Server data doesn't need client state. Use props.

### 3. No Raw SQL Without Prepared Statements

```tsx
// ❌ BAD: SQL injection risk
db.query(`SELECT * FROM users WHERE email = '${email}'`);

// ✅ GOOD: Prepared statement
db.prepare('SELECT * FROM users WHERE email = ?').get(email);
```

**Why:** Security. Always.

### 4. No `any` Type

```tsx
// ❌ BAD
function process(data: any) { ... }

// ✅ GOOD
function process(data: UserData) { ... }
// or
function process(data: unknown) {
  if (!isValidUserData(data)) throw new Error('Invalid');
  // ...
}
```

**Why:** TypeScript's value is type safety. `any` defeats the purpose.

### 5. No Inline Styles

```tsx
// ❌ BAD
<div style={{ marginTop: '16px' }}>

// ✅ GOOD
<div className="mt-4">
```

**Why:** Tailwind is consistent, theme-aware, and purged in production.

---

## 🛠️ Dev Commands

```bash
# Development
npm run dev              # Start dev server (http://localhost:3000)
npm run db:migrate       # Run database migrations
npm run db:seed          # Seed database with test data

# Production
npm run build            # Build for production
npm run start            # Start production server
npm run db:migrate:prod  # Run migrations in production

# Quality
npm run lint             # ESLint
npm run type-check       # TypeScript check
npm run test             # Run tests
```

---

## 🔐 Security Rules

1. **Always validate input** with Zod (client and server)
2. **Never trust client data** — re-validate on server
3. **Use parameterized queries** — no string interpolation in SQL
4. **Hash passwords** with bcrypt/argon2 — never plaintext
5. **CSRF protection** on all state-changing mutations
6. **Rate limit** API routes (especially auth)

---

## 📚 Testing Strategy

```
__tests__/
├── components/          # Component tests (Vitest + Testing Library)
├── lib/                 # Unit tests for utilities
└── e2e/                 # E2E tests (Playwright)
```

**Priority:**
1. E2E tests for critical paths (signup, login, checkout)
2. Unit tests for business logic (pricing, permissions)
3. Component tests for complex UI (forms, dashboards)

---

## 🎯 Quick Start Checklist

For a new feature:

- [ ] Create route in `app/(dashboard)/feature/`
- [ ] Add DB migration if needed (`db/migrations/`)
- [ ] Create Zod schema (`lib/schema.ts`)
- [ ] Build Server Component first
- [ ] Add Client Component only if interactivity needed
- [ ] Write E2E test for critical path
- [ ] Run `npm run lint && npm run type-check`

---

**Last updated:** 2026-03-28
**Maintained by:** Engineering Team
