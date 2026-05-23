# CLAUDE.md — Next.js + SQLite SaaS Project

## Project Structure
```
app/                    # Next.js 15 App Router
  (auth)/              # Auth routes
  (dashboard)/         # Protected dashboard routes
  api/                 # API route handlers
  layout.tsx           # Root layout
components/            # Shared React components
lib/
  db/                  # Database layer
  auth.ts              # Auth helpers
  utils.ts             # Utilities
tests/
types/
```

## Naming Conventions
- Files: kebab-case.ts   |  Components: PascalCase.tsx
- Functions: camelCase()  |  DB: snake_case
- API routes: app/api/resource/route.ts

## Commands
- `npm run dev` — Dev server  |  `npm run build` — Production build
- `npm run test` — Vitest  |  `npm run test:e2e` — Playwright
- `npm run lint` — ESLint  |  `npm run format` — Prettier
- `npm run db:push` — Push schema  |  `npm run db:migrate` — Migrations

## Rules
1. Server components by default
2. DB access through lib/db/queries.ts
3. Auth required on every protected route
4. Zod for form validation
5. Error boundaries per section
6. SEO metadata in layout.tsx
7. Promise.all for parallel fetches
8. Never useEffect for data fetching
9. No secrets in committed files
10. No `any` types — use `unknown`

## Commit Format
`feat:|fix:|chore:|docs:|refactor:|test:` + description
