# Next.js 15 + SQLite SaaS template

Copy `CLAUDE.md` unchanged to the root of a new Next.js 15 App Router project before starting Claude Code. It assumes React 19, strict TypeScript, Node.js 22+, and `better-sqlite3` 13 for a single persistent application instance.

The guide keeps database access on the Node server, makes migrations explicit, and calls out when a local SQLite file is the wrong deployment model. Each rule includes the reason behind it so a fresh project can use the file without extra setup.

This template was AI-assisted and tested in a fresh `create-next-app@15.5.26` fixture with Claude Code. The fixture's migration, tests, lint, typecheck, production build, runtime smoke check, and dependency audit all passed.

A repeatable read-only Claude Code comprehension check, including its exact prompt and limits, is recorded in [`verification/issue-2-claude-code-smoke-20260928.md`](../../verification/issue-2-claude-code-smoke-20260928.md).
