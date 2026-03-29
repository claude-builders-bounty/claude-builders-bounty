# Next.js 15 + SQLite SaaS — CLAUDE.md Template

An opinionated, production-ready `CLAUDE.md` for a greenfield SaaS project.

## Setup

```bash
pnpm create next-app@latest my-saas --typescript --tailwind --app --src-dir
cd my-saas
pnpm add better-sqlite3 drizzle-orm drizzle-kit @lucia-auth/adapter-sqlite lucia zod
```

Then paste `CLAUDE.md` into the project root. Claude Code will understand the full context.

## What's covered

| Section | Content |
|---------|---------|
| Stack | Every dependency with rationale |
| Folder structure | Exact directory layout |
| Dev commands | All pnpm scripts |
| DB rules | Schema, migrations, singleton pattern |
| Component patterns | Server-first, client boundaries |
| Auth pattern | Lucia v3 with redirect guard |
| Naming rules | File/component/DB column conventions |
| Anti-patterns | 9 things we explicitly avoid and why |

## Verified

Tested by creating a greenfield Next.js 15 project and confirming Claude Code:
- Understands the folder structure without asking
- Generates correct Drizzle schemas
- Places files in the right directories
- Uses Server Actions instead of API routes for mutations
- Doesn't suggest Prisma, NextAuth, or tRPC

## License

MIT
