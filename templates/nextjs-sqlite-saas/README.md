# Next.js 15 + SQLite SaaS CLAUDE.md

Production-ready Claude Code context for a greenfield SaaS using Next.js 15 App Router and SQLite.

## Setup

1. Copy `CLAUDE.md` into the root of a new Next.js 15 + SQLite project.
2. Run Claude Code from that project root and ask for a first feature.
3. Keep the conventions unless a product requirement explicitly changes them.

The template is intentionally opinionated: it chooses raw SQL migrations, a service/repository split, Server Components by default, Zod runtime validation, and strict boundaries between UI, services, and database access.

## Validation

Run:

```bash
node validate-template.mjs
```

The validator checks that the template covers the bounty-required sections and includes explicit `Reason:` guidance for the rules.
