# Opinionated Next.js and SQLite project instructions

AI-assisted deliverable for the $75 bounty in [issue #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2).

The file is intentionally opinionated: it chooses Next.js 15 App Router, React 19, TypeScript strict mode, pnpm, Drizzle, better-sqlite3 locally, Turso/libSQL in deployment, Zod, Vitest, and Playwright. It includes the requested stack, directory contract, naming rules, migration safety, development commands, server/client boundaries, testing, security, anti-patterns, and definition of done.

## Local validation

Run tests/validate_claude_md.py. It creates a temporary greenfield-style project, copies CLAUDE.md into it, checks every required section and rule, rejects unresolved template placeholders, and verifies that the core command and migration instructions are present.

The bounty’s final acceptance check asks a contributor to paste the file into a new Next.js project and confirm Claude Code follows it without clarification. This package does not perform that authenticated Claude Code interaction because it would require a user account/login. The file is statically validated and ready for that user-controlled final check.

## AI disclosure

This deliverable was created with AI assistance. A human contributor should review the policy language against the maintainer’s expectations and disclose AI use in the pull request if required.
