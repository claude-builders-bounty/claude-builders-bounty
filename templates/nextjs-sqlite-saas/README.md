# Next.js 15 + SQLite SaaS CLAUDE.md Template

Install in 3 steps:

1. Create or open a Next.js 15 App Router project.
2. Copy `templates/nextjs-sqlite-saas/CLAUDE.md` to the project root.
3. Start Claude Code in that root and ask it to implement a small SaaS workflow.

This template is opinionated for TypeScript, server components by default, SQLite migrations, service-layer authorization, Zod validation, and small client components.

## Smoke Test Prompt

After copying the file into a greenfield project, run this prompt in Claude Code:

```text
Using this CLAUDE.md, add an authenticated team invite workflow with SQLite persistence. First summarize the project conventions you will follow, then list the files you would create before editing. Do not edit files.
```

The expected response should name the App Router/server-action flow, keep SQL under `db/queries`, put business logic in `server/services`, include a migration under `db/migrations`, and avoid asking which stack or database to use.

See `samples/nextjs-sqlite-claude-smoke.md` for an example Claude Code response from a fresh `create-next-app` scaffold.
