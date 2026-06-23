# Next.js + SQLite SaaS Template

A production-ready CLAUDE.md template for SaaS applications built with Next.js 14+ (App Router), SQLite via better-sqlite3, TypeScript, and Tailwind CSS.

## What's Included

- **`CLAUDE.md`** — Comprehensive project instructions for Claude Code, covering architecture decisions, coding standards, testing approach, database patterns, deployment guidance, and common pitfalls.

## Setup Instructions

### 1. Copy into Your Project

```bash
# Copy CLAUDE.md to your project root
cp CLAUDE.md /path/to/your-project/

# Commit it to your repo
cd /path/to/your-project
git add CLAUDE.md
git commit -m "Add CLAUDE.md project instructions for Claude Code"
```

### 2. Customize for Your Project

Edit the following sections in `CLAUDE.md` to match your specific project:

| Section | What to Customize |
|---|---|
| **Environment Variables** | Add/remove variables specific to your integrations |
| **Project Structure** | Adjust folder names if you deviate from the template |
| **Key Dependencies** | Add any additional packages your project uses |
| **Common Commands** | Add project-specific scripts from your `package.json` |
| **Deployment** | Update for your hosting platform (Vercel, Railway, Fly.io, etc.) |

### 3. Recommended Project Structure

If starting a new project from scratch, use this as your initial scaffolding:

```bash
# Create the recommended directory structure
mkdir -p app/\(auth\)/login app/\(dashboard\)/settings app/\(marketing\) app/api/auth/\[...nextauth\] app/api/v1/users
mkdir -p lib/db/migrations lib/db/queries lib/validations
mkdir -p components/ui components/forms components/layouts
mkdir -p hooks types scripts tests/unit tests/integration tests/e2e
mkdir -p public/images data
```

### 4. Required `package.json` Scripts

Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "typecheck": "tsc --noEmit",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:seed": "tsx scripts/seed.ts",
    "db:reset": "tsx scripts/reset.ts"
  }
}
```

### 5. Required Dependencies

```bash
# Core
npm install next react react-dom typescript @types/react @types/node better-sqlite3 @types/better-sqlite3

# Styling
npm install tailwindcss postcss autoprefixer clsx tailwind-merge class-variance-authority

# Auth & Billing
npm install next-auth stripe zod

# Dev & Testing
npm install -D vitest @testing-library/react @testing-library/jest-dom @playwright/test eslint prettier tsx
```

### 6. `.gitignore` Additions

Make sure your `.gitignore` includes:

```gitignore
# Environment
.env.local
.env.*.local

# Database
data/
*.db
*.db-journal
*.db-wal
*.db-shm

# Next.js
.next/
out/
```

## How Claude Code Uses CLAUDE.md

When you open your project in Claude Code, it automatically reads `CLAUDE.md` from the project root. This gives Claude:

- Understanding of your tech stack and architecture
- Knowledge of coding conventions and patterns to follow
- Awareness of project-specific commands and scripts
- Context about testing and deployment workflows
- Familiarity with common pitfalls to avoid

Claude will follow these instructions when generating code, suggesting changes, or helping debug issues.

## Template Sections

The `CLAUDE.md` includes guidance for:

| Section | Purpose |
|---|---|
| **Overview** | Tech stack summary |
| **Getting Started** | Prerequisites, setup steps, environment variables |
| **Project Structure** | Full directory tree with explanations |
| **Coding Standards** | Naming conventions, TypeScript rules, component patterns |
| **Server vs. Client Components** | When to use each (critical for Next.js App Router) |
| **Database Patterns** | Query patterns, transactions, migrations |
| **Testing** | Stack, commands, patterns, database isolation |
| **Database Migrations** | How to create and run migrations |
| **Common Commands** | Quick reference for all scripts |
| **Deployment** | Production checklist, SQLite considerations |
| **Common Pitfalls** | 8 documented pitfalls with code examples |
| **Adding a New Feature** | Step-by-step checklist |

## License

MIT
