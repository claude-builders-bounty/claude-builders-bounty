# CLAUDE.md — Next.js 15 + SQLite SaaS Project Template

Welcome to the opinionated guideline for structuring and developing a SaaS project using Next.js 15 App Router and SQLite (via better-sqlite3 or Turso). These conventions aim for maintainability, scalability, and production readiness.

---

## 1. Project Structure

```
/
├── app/                      # Next.js 15 App Router files and routes
│   ├── api/                  # API route handlers (server-only)
│   ├── (auth)/               # Auth-related routes (optional)
│   ├── (components)/         # Shared UI components
│   └── layout.tsx            # Root layout
├── db/                       # SQLite database logic and migrations
│   ├── migrations/           # Migration scripts (timestamped)
│   ├── client.ts             # DB client initialization (singleton)
│   └── schema.ts             # DB schema definitions (if needed)
├── lib/                      # Shared utilities and services (non-React)
├── components/               # React components used outside app/
├── styles/                   # CSS/SCSS or Tailwind config
├── public/                   # Static assets
├── scripts/                  # Dev scripts (e.g. migration runner)
├── .env                      # Environment variables (never commit secrets)
├── next.config.js            # Next.js config
├── package.json
└── README.md

```

### Why?
- Separates DB logic (`db/`) from app routes for clarity and reusability.
- Uses Next.js 15 App Router conventions for routing and layouts.
- Keeps shared utilities in `lib/` to avoid React context coupling.

---

## 2. Naming Conventions

- **Files & folders:** kebab-case (`user-profile.tsx`), except React components (PascalCase).
- **API Routes:** Use nested folders reflecting resource hierarchy (e.g., `app/api/users/[id]/route.ts`).
- **DB Migrations:** Timestamped filenames, e.g., `20240611-add-users-table.sql` or `.ts`.
- **Functions:** camelCase, descriptive.
- **Components:** PascalCase.

---

## 3. DB Migration Rules

- **Use timestamped migrations:** Each migration file must start with `YYYYMMDDHHMMSS-description`.
- **Atomic changes only:** Each migration should do one thing (e.g., add a table or column).
- **Idempotency:** Migrations must be safe to run once and track applied migrations.
- **Migration runner:** Provide a script in `scripts/migrate.ts` to apply migrations programmatically.
- **Never modify applied migrations:** To fix issues, create a new migration.

---

## 4. Dev Commands

```bash
# Install dependencies
npm install

# Run dev server (Next.js)
npm run dev

