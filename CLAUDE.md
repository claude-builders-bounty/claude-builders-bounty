# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

## Stack & Versions (locked)

- **Runtime:** Node.js 22 LTS
- **Framework:** Next.js 15 (App Router only — no `pages/`)
- **Database:** SQLite via `better-sqlite3` (local dev) or Turso (production)
- **ORM:** Drizzle ORM (lightweight, SQL-first, no magic)
- **Auth:** NextAuth.js v5 (Auth.js) with credential + OAuth providers
- **Styling:** Tailwind CSS v4 + shadcn/ui (Radix primitives)
- **Validation:** Zod (shared types between client/server)
- **Payments:** Stripe (checkout sessions + webhooks)
- **Email:** Resend (transactional + marketing)
- **Hosting:** Vercel (edge functions for webhooks, ISR for public pages)

## Folder Structure (opinionated)

