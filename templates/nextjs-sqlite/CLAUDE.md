# Next.js 15 + SQLite SaaS Development Guidelines

This document provides strict, opinionated architectural and coding rules for building scalable SaaS applications with Next.js 15 App Router and SQLite (Drizzle ORM + better-sqlite3 / Turso).

---

## 1. Tech Stack & Core Versions

- **Framework:** Next.js 15.x (App Router, Server Actions, React 19)
- **Language:** TypeScript 5.x (Strict mode enabled, zero `any`)
- **Database:** SQLite with `better-sqlite3` (Local / VPS) or `@libsql/client` (Turso / Edge)
- **ORM & Migrations:** Drizzle ORM (`drizzle-orm`, `drizzle-kit`)
- **Styling:** Tailwind CSS v4, `clsx`, `tailwind-merge`
- **Validation:** Zod v3.x
- **Icons:** `lucide-react`
- **Auth:** Auth.js v5 / Lucia Auth (Session-based, stored in SQLite)

---

## 2. Project Directory Structure

```text
├── app/
│   ├── (auth)/                # Route group: login, register, forgot-password
│   ├── (dashboard)/           # Protected SaaS dashboard routes
│   │   ├── dashboard/page.tsx # Server Component data root
│   │   └── settings/page.tsx
│   ├── api/                   # Webhook endpoints ONLY (Stripe, external integrations)
│   ├── actions/               # Server Actions grouped by domain (auth, billing, teams)
│   ├── layout.tsx             # Root layout with fonts & providers
│   └── page.tsx               # Marketing landing page
├── components/
│   ├── ui/                    # Primitive components (Button, Input, Modal, Badge)
│   ├── dashboard/             # Domain-specific dashboard widgets
│   └── shared/                # Navbar, Footer, UserAvatar
├── db/
│   ├── schema/                # Drizzle schema split by domain (users.ts, orgs.ts, billing.ts)
│   │   └── index.ts           # Re-exports all table definitions
│   ├── migrations/            # Generated SQL migration files (drizzle-kit)
│   ├── client.ts              # SQLite connection instance with WAL mode
│   └── seed.ts                # Database seeding script
├── lib/
│   ├── auth.ts                # Session resolution & permission checks
│   ├── utils.ts               # cn() helper, date formatters, currency helpers
│   └── validation/            # Reusable Zod schemas
└── types/                     # Shared TypeScript interfaces
