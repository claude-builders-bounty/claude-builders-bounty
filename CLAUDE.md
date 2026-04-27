# CLAUDE.md — Next.js 15 + SQLite SaaS Projesi

> Bu dosyayı okuyan her agent: projeyi anlar, soru sormaz, hemen çalışır.

---

## 🏗️ Stack & Sürümler

- **Runtime:** Node.js 20+ (ESM)
- **Framework:** Next.js 15 App Router (RSC varsayılan)
- **Database:** SQLite via `better-sqlite3` (sync, server-side) veya `Turso` (edge-ready)
- **ORM:** Drizzle ORM (typesafe, migrations, lightweight)
- **Styling:** Tailwind CSS v4 (utility-first, component-friendly)
- **Auth:** NextAuth.js v5 ( Credentials + OAuth)
- **Deployment:** Vercel (serverless) — `nodejs20.x` runtime

---

## 📁 Folder Structure

```
/
├── app/                    # Next.js App Router — page + layout + route group
│   ├── (auth)/            # Route group: /login, /register, /forgot-password
│   ├── (dashboard)/       # Route group: /dashboard, /settings, /billing
│   ├── api/               # API routes — Route Handler (route.ts)
│   ├── page.tsx           # Landing page
│   ├── layout.tsx         # Root layout — fonts, providers, global styles
│   └── globals.css        # Tailwind base + design tokens
├── components/
│   ├── ui/                # Headless-style primitives — Button, Input, Dialog, etc.
│   └── feature/           # Feature-specific — DashboardCard, InvoiceTable, etc.
├── db/
│   ├── schema.ts          # Drizzle schema — users, sessions, subscriptions
│   ├── index.ts           # DB connection singleton (re-export)
│   └── migrations/        # Drizzle migration files (SQLite compatible)
├── lib/
│   ├── auth.ts            # NextAuth config — session, JWT, callbacks
│   ├── db.ts              # Server-only DB access (never import from client)
│   ├── utils.ts           # cn(), formatCurrency(), sleep(), retry()
│   └── constants.ts       # FREE_PLAN_LIMITS, RATE_LIMIT_* constants
├── hooks/
│   └── use*.ts            # Client hooks — useDebounce, useUser, useSubscription
├── types/
│   └── index.ts           # Shared TypeScript types — exclude 'any' typed params
└── drizzle.config.ts      # Drizzle Kit config
```

**Kural:** `app/` dışında `page.tsx` YOK. Route'lar hep `app/` altında.

---

## 🗄️ Database Migrations

### Schema Yazar Kuralları

```typescript
// ✅ DO: Drizzle schema syntax
export const users = sqliteTable('users', {
  id: text('id').primaryKey(),  // cuid2 — never auto-increment
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`CURRENT_TIMESTAMP`),
});

// ❌ DON'T: Prisma syntax, raw SQL strings in code, camelCase column names
```

### Migration Kuralları

```bash
# Schema değişikliği → migration üret
npx drizzle-kit generate --sqlite

# Migration'ı manual review et — otomatik üretilen her zaman kontrol edilmeli
# migrations/0000_*.sql içeriğini oku, regression riskini kontrol et

# Production'a uygula
npx drizzle-kit push  # DEV/CI için
npx drizzle-kit migrate # PROD — transactional değil, dikkat!
```

### SQLite Özel Kurallar

- **No FK constraint enforcement** — SQLite FK'ları disable et, application-layer'da kontrol et
- **JSON column** — `text('meta').notNull().default('{}')` olarak sakla, parse et
- **Date/Time** — `integer('ts', { mode: 'timestamp' })` — Unix epoch millisecond
- **Array/Set** — `text('tags').notNull().default('[]')` → `JSON.parse()` parse et

---

## 🎯 Component Patterns

### Server vs Client Component

```typescript
// app/dashboard/page.tsx — SERVER component (default)
// Bypass: 'use client' directive ile client component yapma, elevation/nested pattern kullan
// ❌ DON'T: 'use client' at page level — breaks RSC streaming benefits

// ✅ DO: Server component, client parts are children
export default async function DashboardPage() {
  const user = await getSession();
  return (
    <div>
      <DashboardHeader user={user} />          {/* Server — passes data */}
      <SubscriptionPlans client={<ClientComp />} />  {/* Client boundary */}
    </div>
  );
}
```

### Elevation Pattern (Server → Client data passing)

```typescript
// Client component data'yı prop olarak alır, state tutmaz
// ❌ DON'T: Client component içinde useEffect + fetch
// ✅ DO: Server parent data çeker, client child'a prop olarak ver
```

---

## 🚫 Anti-Patterns

| Anti-Pattern | Neden | Doğru Yaklaşım |
|---|---|---|
| `import { db } from '@/lib/db'` client-side | SQLite connection server-only | Sadece server component/Route Handler'da db import et |
| `new Date()` in schema default | TZ inconsistent | `sql\`CURRENT_TIMESTAMP\`` veya server timestamp |
| `any` typed function params | Silent failure | `unknown` + narrows, or explicit type union |
| Global CSS class names | Collision risk | Tailwind utility — tailwind.config.ts'de design tokens |
| Client component in layout | Hydration overhead | Route group boundary kullan, minimum client surface |

---

## 🛠️ Dev Commands

```bash
# Database
npx drizzle-kit generate      # Migration üret
npx drizzle-kit push           # Dev DB sync
npx drizzle-kit studio         # Visual schema editor (port 4983)

# Development
npm run dev                    # Next.js dev server (http://localhost:3000)
npm run build                  # Production build
npm run lint                   # ESLint + TypeScript check

# Testing
npm test                       # Jest unit tests
npm run test:e2e              # Playwright E2E (ci:headed, baseURL override)
```

---

## 🔐 Auth Kuralları

- **Password:** `bcryptjs` ile hash, minimum 12 karakter salt, nunca plaintext
- **Session:** JWT-based, 7-day expiry, refresh rotation
- **Credentials:** Sadece email/password — OAuth provider'lar ayrı
- **Rate limit:** Login attempt 5/min/IP, account lockout 15 min

---

## 💰 Subscription Model (Multi-Tier)

```typescript
// lib/constants.ts
export const PLANS = {
  FREE: { id: 'free', name: 'Free', limits: { api: 100, projects: 3 } },
  PRO: { id: 'pro', name: 'Pro', price: 9.99, limits: { api: 10000, projects: 50 } },
  TEAM: { id: 'team', name: 'Team', price: 29.99, limits: { api: -1, projects: -1 } },
} as const;

// Usage: Plan limitesini aşan API çağrısı → 429 rate limit response
```

---

## 📐 Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Database table | snake_case | `user_sessions` |
| Column | snake_case | `created_at` |
| Table column singular | NO — always plural | `users`, `invoices` |
| Function | camelCase | `createInvoice()`, `getUserByEmail()` |
| React component | PascalCase | `DashboardCard.tsx` |
| File (component) | PascalCase | `UserProfile.tsx` |
| File (utility) | camelCase | `formatCurrency.ts` |
| Env variable | SCREAMING_SNAKE | `DATABASE_URL`, `NEXTAUTH_SECRET` |

---

## ✅ Production Checklist (Her Deploy Öncesi)

```bash
# 1. Env variable'lar set mi?
grep -r "process.env\." app/ | grep -v "\.env\.example" | grep undefined

# 2. Build succeed mi?
npm run build  # exit 0 olmalı

# 3. Type error var mı?
npx tsc --noEmit  # exit 0 olmalı

# 4. Migration schema sync mi?
npx drizzle-kit check  # drift yoksa çık

# 5. Auth redirect loop risk?
# → middleware.ts'de /dashboard → /login redirect, session cookie domain doğru
```
