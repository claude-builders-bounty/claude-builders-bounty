# CLAUDE.md for Next.js 15 + SQLite SaaS Project

## Project Overview
- Full-stack Next.js 15 SaaS with App Router
- SQLite database via better-sqlite3 or Turso
- Authentication with NextAuth.js v5
- UI: shadcn/ui + Tailwind CSS
- Payments: Stripe, Emails: Resend

## Commands
```bash
npm install
npm run dev
npm run build
npm run db:migrate
npm run db:seed
npm run lint
npm run test
```

## Code Style
- TypeScript strictly, no any
- Server components by default
- Zod for API validation
- Prepared statements for DB queries
- Consistent JSON responses

## Project Structure
```
src/
├── app/
│   ├── (auth)/
│   ├── (dashboard)/
│   └── api/
├── components/
│   ├── ui/
│   └── forms/
├── lib/
│   ├── db.ts
│   ├── auth.ts
│   └── stripe.ts
├── server/
│   ├── actions.ts
│   └── queries.ts
└── styles/
    └── globals.css
```

## Database
- SQLite with better-sqlite3
- Migrations for schema changes
- Tables must have id, created_at, updated_at
- Foreign keys with CASCADE
- Index on frequent WHERE columns

## Authentication
- NextAuth.js v5, email/password + OAuth
- Protected dashboard routes with middleware
- Session token in HTTP-only cookie
- Never expose passwords to client

## Deployment
- Vercel or Node.js with SQLite
- Environment variables for secrets
- Automatic HTTPS
- Database backups with Litestream
