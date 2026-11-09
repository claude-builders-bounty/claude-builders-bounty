# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this project.

## Project Overview

{{PROJECT_NAME}} - {{PROJECT_DESCRIPTION}}

A {{STACK}} application built for {{PURPOSE}}.

## Tech Stack

- **Framework:** {{FRAMEWORK}} (Next.js {{VERSION}})
- **Database:** SQLite via {{ORM}} ({{ORM_NAME}})
- **Language:** TypeScript {{TS_VERSION}}
- **Styling:** {{STYLING}} (Tailwind CSS)
- **Authentication:** {{AUTH}} (NextAuth.js / Lucia / Better Auth)
- **API:** REST + Server Actions
- **Deployment:** {{DEPLOY_TARGET}} (Vercel / Docker / fly.io)

## Project Structure

```
├── app/                 # Next.js App Router (route handlers, pages)
├── components/          # React components (client + server)
├── lib/                 # Shared utilities, DB client, auth helpers
├── hooks/               # Custom React hooks
├── types/               # TypeScript type definitions
├── prisma/              # Prisma schema & migrations (if using Prisma)
├── better-sqlite3/      # SQLite setup (if using better-sqlite3)
├── public/              # Static assets
├── tests/               # Vitest / Playwright tests
├── package.json
├── tsconfig.json
├── next.config.js
└── .env.example         # Copy to .env.local and fill in secrets
```

## Database (SQLite)

This project uses SQLite with {{ORM}}.

### Schema Location

`prisma/schema.prisma` (Prisma) or `lib/db.ts` (better-sqlite3 / drizzle)

### Common Commands

```bash
# Prisma
npx prisma migrate dev
npx prisma studio
npx prisma generate

# Drizzle
npx drizzle-kit migrate
```

### Key Tables

{{TABLES}}

## Available Scripts

```bash
# Install dependencies
npm install

# Run development server (with Turbopack)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint

# Run type check
tsc --noEmit

# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Database studio
npx prisma studio
```

## Code Conventions

### TypeScript

- Use strict mode (`"strict": true` in tsconfig.json)
- Prefer interfaces for public API shapes, types for internal aliases
- Export types explicitly; avoid implicit `any`
- Use Zod for runtime validation at API boundaries

### React / Next.js

- Use Server Components by default; mark client components with `'use client'`
- Colocate styles with components using Tailwind CSS classes
- Use Server Actions for form mutations (`'use server'`)
- Handle loading and error states with `loading.tsx` and `error.tsx`

### File Naming

- Components: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatDate.ts`)
- Route handlers: `route.ts` inside `app/[route]/route.ts`
- Server Actions: colocated in the component file or `actions.ts`

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
DATABASE_URL="file:./dev.db"
NEXTAUTH_SECRET="your-secret"
NEXTAUTH_URL="http://localhost:3000"
{{EXTRA_ENV}}
```

## Testing

- Unit tests: Vitest
- E2E tests: Playwright
- Run: `npm test`

## AI Agent Guidelines

When working on this project as a Claude Code agent:

1. **Read `prisma/schema.prisma`** before modifying database-related code
2. **Run `tsc --noEmit`** after TypeScript changes
3. **Run `npm run lint`** before submitting PRs
4. **Run `npm test`** to verify no regressions
5. **Use Zod schemas** for all API input validation
6. **Prefer Server Components** unless interactivity is required
7. **Wrap all DB mutations** in try/catch with proper error responses

## Common Tasks

### Add a new API route

1. Create `app/api/[resource]/route.ts`
2. Export `GET`, `POST`, `PUT`, `DELETE` handlers as needed
3. Validate input with Zod
4. Return proper JSON responses with status codes

### Add a new database model

1. Edit `prisma/schema.prisma`
2. Run `npx prisma migrate dev --name [migration_name]`
3. Run `npx prisma generate`
4. Update Zod schemas and TypeScript types

### Add a new page

1. Create `app/[route]/page.tsx`
2. Use Server Component by default
3. Add navigation link in layout or header component
