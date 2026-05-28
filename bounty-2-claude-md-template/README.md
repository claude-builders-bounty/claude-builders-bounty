# Bounty #2: CLAUDE.md Template for Next.js 15 + SQLite SaaS

This submission provides a production-ready, opinionated `CLAUDE.md` file for greenfield Next.js 15 App Router + SQLite projects.

## What's Included

- **`CLAUDE.md`** — Drop-in project context file for Claude Code

## Coverage

The CLAUDE.md covers all required sections:

| Section | What's Covered |
|---------|----------------|
| Stack & Versions | Next.js 15, better-sqlite3, Drizzle ORM, next-auth v5, Tailwind, Vitest |
| Folder Structure | Full directory tree with naming rules |
| Dev Commands | All npm scripts with descriptions |
| SQL / Migration Conventions | Naming, timestamps, foreign keys, schema patterns |
| Component Patterns | Server/Client split, Server Actions, loading/error states |
| What We Don't Do | 10 opinionated choices with reasons |
| Anti-Patterns | 7 common mistakes to avoid |
| Environment Variables | Validated env schema |
| Testing Conventions | In-memory SQLite, test structure |
| Git & PR Conventions | Branch naming, commit format, PR size |

## Testing

To verify this CLAUDE.md works as intended:

1. Create a new Next.js 15 project:
   ```bash
   npx create-next-app@latest my-saas --typescript --tailwind --app --src-dir
   ```

2. Install SQLite dependencies:
   ```bash
   npm install better-sqlite3 drizzle-orm
   npm install -D drizzle-kit
   ```

3. Paste `CLAUDE.md` into the project root.

4. Ask Claude Code to:
   - "Create the user and subscription tables following our conventions"
   - "Add a settings page with server actions"
   - "Write tests for the user queries"

   Claude Code should understand the project context without asking clarifying questions.

## Opinionated Choices

Every rule has a reason:
- **Drizzle over Prisma**: Lighter, generates better SQL, no engine binary
- **better-sqlite3 over Turso**: Zero-config for development, synchronous API
- **Server Actions over REST**: Type-safe, no API boilerplate
- **Biome over ESLint+Prettier**: One tool, 10× faster
- **nanoid over uuid**: Shorter, URL-safe, no dependency overhead
- **Vitest over Jest**: ESM-native, faster, better DX
