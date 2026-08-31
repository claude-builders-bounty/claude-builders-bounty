# Next.js 15 + SQLite SaaS Template

Opinionated starter for a single-tenant SaaS using Next.js 15 App Router, TypeScript, and SQLite (`better-sqlite3`).

## Quick Start

```bash
npx create-next-app@15 my-saas --typescript --eslint --tailwind --app --src-dir=false
# Copy this CLAUDE.md and the files in templates/nextjs-sqlite/ into the project root.
cp templates/nextjs-sqlite/package.json package.json
cp templates/nextjs-sqlite/drizzle.config.ts drizzle.config.ts
cp templates/nextjs-sqlite/CLAUDE.md CLAUDE.md
npm install
npm run db:generate
npm run db:migrate
npm run dev
```

## What You Get

- Strict TypeScript + Next.js 15 App Router.
- `better-sqlite3` + Drizzle ORM for local-first data.
- Environment validation via Zod.
- Clear folder conventions and dev commands.

## Testing Claude Code Context

After copying `CLAUDE.md`, open the project in Claude Code and ask:

> "Add a `teams` table with a one-to-many relationship to `users`, generate the migration, and create a query to list teams for a user."

Claude Code should understand the stack, conventions, and commands without asking clarifying questions.
