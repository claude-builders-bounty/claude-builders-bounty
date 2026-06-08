# Next.js 15 + SQLite SaaS CLAUDE.md Template

This template is for greenfield SaaS applications using Next.js 15 App Router with either `better-sqlite3` or Turso/libSQL.

Copy `CLAUDE.md` to the root of a new project before starting Claude Code. It gives the agent concrete rules for project structure, naming, migrations, database access, server/client boundaries, auth, billing, testing, security, and PR expectations.

The template is intentionally opinionated: each rule includes a reason so the agent can apply the guidance when the exact file structure differs.

Optional validation:

```bash
node templates/nextjs15-sqlite-saas/validate-template.mjs
```

