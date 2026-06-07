# CLAUDE.md for Next.js 15 + SQLite SaaS

## Build
```bash
npm run dev
npm run build
npm run test
```

## Architecture
- Next.js 15 App Router
- SQLite via better-sqlite3
- Drizzle ORM for schema
- Auth: NextAuth.js
- Deploy: Vercel

## Testing
- Vitest for unit tests
- Playwright for E2E

## Environment
Create `.env.local`:
```
DATABASE_URL=
NEXTAUTH_SECRET=
```

## Commands
- `npm run dev` — Start dev server
- `npm run build` — Production build
- `npm run test` — Run tests
- `npm run lint` — Lint code

## Git Workflow
- main branch is production
- feature branches: `feat/description`
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`
