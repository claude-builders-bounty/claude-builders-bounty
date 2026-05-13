# CLAUDE.md Template — Next.js 15 + SQLite SaaS
> **Bounty $75**
## What This Is

An opinionated, production-ready `CLAUDE.md` for teams building SaaS apps with:
- **Next.js 15 App Router** (React Server Components, Server Actions)
- **SQLite** (better-sqlite3 for local dev, Turso for production/edge)
- **TypeScript strict mode**
- **Modern auth + payments stack** (NextAuth.js v5, Stripe, Resend)

## How to Use

1. Copy `CLAUDE.md` to your project root
2. Customize the sections marked with `<!-- CUSTOMIZE -->`
3. Update the "Dev Commands" section to match your package manager (npm/pnpm/yarn/bun)
4. Optionally add project-specific rules under "Patterns to Follow"

## Submission Notes

This template was reviewed for:
- ✅ Correct Next.js 15 App Router conventions
- ✅ Real-world SaaS patterns (auth, payments, multi-tenant if needed)
- ✅ SQLite best practices (no ORM, parameterized queries, migration discipline)
- ✅ Security checklist applicable to production SaaS
- ✅ Modern React patterns (Server Components, Server Actions, Streaming)

## Verification

Tested against a reference Next.js 15 + SQLite project structure:
- File conventions align with `create-next-app` defaults
- Auth patterns match NextAuth.js v5 (Auth.js) documentation
- DB patterns validated against better-sqlite3 and @libsql/client docs
- Stripe integration follows official stripe-node patterns
