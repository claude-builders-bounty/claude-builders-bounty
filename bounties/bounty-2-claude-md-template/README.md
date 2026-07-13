# CLAUDE.md Template — Next.js 15 + SQLite SaaS

A comprehensive, opinionated `CLAUDE.md` template for AI coding agents (Claude Code) working on a Next.js SaaS project with SQLite via Turso and Drizzle ORM.

## What This Is

`CLAUDE.md` is a project guide file that Claude Code reads at the start of every session. It gives the AI agent the context it needs to write code that matches your project's conventions, tech stack, and architecture.

This template covers:

- **Stack decisions** — Next.js 15 App Router, React 19, TypeScript strict, Drizzle + Turso, Tailwind v4, shadcn/ui, NextAuth v5
- **Build/run/test commands** — exact `npm run` scripts an agent should use
- **Code style** — Server Components by default, Server Actions for mutations, Zod validation, file naming
- **Directory layout** — where everything lives (`src/app`, `src/db/schema`, `src/actions`, etc.)
- **Architecture patterns** — data fetching with `Promise.all`, auth guards in layouts, streaming with Suspense
- **Database workflow** — schema → generate → review → migrate
- **Testing setup** — Vitest + Testing Library patterns with real examples
- **Common gotchas** — SQLite enum limitations, Turso foreign keys, NextAuth performance, revalidation rules

## How to Use

1. **Copy `CLAUDE.md`** to the root of your Next.js SaaS project.
2. **Tailor the contents** to your actual setup:
   - Update build commands if you use pnpm/yarn/bun
   - Swap Biome for ESLint if that's your setup
   - Adjust the directory tree if your project differs
   - Update package versions to match your lockfile
3. **Commit it** to your repository.

Claude Code (and other AI agents) will automatically pick up `CLAUDE.md` from the project root and use it as context for code generation.

## Example: Minimal Starter

```bash
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir
cd my-saas
cp /path/to/CLAUDE.md ./CLAUDE.md
# Then add drizzle, turso, next-auth, etc.
```

## Design Philosophy

This template follows these principles:

1. **Opinionated over generic** — makes real decisions so the AI doesn't guess
2. **Practical examples over abstract docs** — every pattern has runnable code
3. **Agent-first** — written for how LLMs consume context (clear sections, consistent formatting, explicit commands)
4. **SaaS-specific** — includes auth guards, team scoping, billing patterns, webhooks — not just generic Next.js advice

## What's Not Included

- Docker configuration
- CI/CD pipelines (GitHub Actions, etc.)
- Monitoring / observability setup
- E2E testing (Playwright/Cypress)
- Storybook or component documentation
- API client generation (tRPC or OpenAPI)

These are intentionally omitted to keep the template focused and maintainable. Add them as your project grows.

## License

MIT — use freely in your own projects.
